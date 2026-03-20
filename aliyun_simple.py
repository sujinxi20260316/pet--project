import os
import csv
import time
import json
from dashscope import Generation

# ==================== 配置 ====================
# 阿里云API配置
MODEL_NAME = "deepseek-r1"  # 可选 qwen-turbo, qwen-plus, qwen-max

# 输出文件名（固定，用于增量更新）
OUTPUT_CSV = "data/diseases.csv"

# 物种列表（可自由增删）
SPECIES_LIST = ["猫", "狗", "鸟", "兔", "仓鼠"]

# 每个物种生成疾病名称的数量
MAX_DISEASES = 20  # 可改为您需要的数量（如500）


# ==================== 阿里云生成疾病名称 ====================
def fetch_disease_names(species, target=MAX_DISEASES):
    """
    使用阿里云通义千问生成指定物种的疾病名称列表
    :param species: 物种名称，如"猫"
    :param target: 需要生成的疾病数量
    :return: 疾病名称列表（英文）
    """
    prompt = f"""
请列出{target}种最常见的{species}疾病名称，只输出疾病名称，每行一个，不要序号，不要额外说明。
要求疾病名称使用英文，例如：{species} leukemia virus
"""
    try:
        response = Generation.call(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            result_format="message",
            temperature=0.7,
            max_tokens=2000  # 根据 target 调整，500条约需1500 tokens
        )
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            # 按行分割，去除空行和可能的序号
            lines = content.strip().split('\n')
            diseases = []
            for line in lines:
                clean = line.strip()
                if clean and not clean.startswith('```'):
                    # 去除可能的序号（如 "1. Feline leukemia virus"）
                    if '.' in clean and clean.split('.')[0].strip().isdigit():
                        clean = clean.split('.', 1)[1].strip()
                    diseases.append(clean)
            diseases = diseases[:target]
            print(f"✅ 阿里云生成 {len(diseases)} 个 {species} 疾病名称")
            return diseases
        else:
            print(f"⚠️ 阿里云生成失败: {response.code} - {response.message}")
            return []
    except Exception as e:
        print(f"⚠️ 生成异常: {e}")
        return []


# ==================== 阿里云API增强模块 ====================
def enhance_disease_with_qwen(disease_name, species):
    """
    调用通义千问为疾病生成症状、病因、家庭建议
    返回字典
    """
    prompt = f"""
你是一个专业的宠物医疗顾问。请为以下疾病提供简洁准确的信息，以JSON格式输出。
疾病名称：{disease_name}
物种：{species}

请包含以下字段：
- symptoms: 主要症状（中文，用逗号分隔）
- causes: 主要病因（中文）
- home_care: 家庭护理建议（中文）
- vet_urgent: 是否需要立即就医（是/否）

只输出JSON，不要有其他文字。
"""
    try:
        response = Generation.call(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            result_format="message",
            temperature=0.5,
            max_tokens=300
        )
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            # 提取JSON部分（避免模型输出多余内容）
            json_str = content.strip()
            if json_str.startswith("```json"):
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif json_str.startswith("```"):
                json_str = json_str.split("```")[1].split("```")[0].strip()
            data = json.loads(json_str)
            # 确保字段存在
            return {
                "disease_name": disease_name,
                "species": species,
                "symptoms": data.get("symptoms", ""),
                "causes": data.get("causes", ""),
                "home_care": data.get("home_care", ""),
                "vet_urgent": data.get("vet_urgent", "未知")
            }
        else:
            print(f"⚠️ API错误 {response.code}: {response.message}")
            return None
    except Exception as e:
        print(f"⚠️ 处理异常: {e}")
        return None


# ==================== 主程序 ====================
def main():
    print("=" * 60)
    print("🐾 宠物医疗知识库构建器")
    print("=" * 60)

    # 1. 读取已有知识库（如果存在），记录 (疾病名称, 物种) 对
    existing_pairs = set()
    if os.path.exists(OUTPUT_CSV):
        try:
            with open(OUTPUT_CSV, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_pairs.add((row['disease_name'], row['species']))
            print(f"📂 已存在知识库，包含 {len(existing_pairs)} 条记录")
        except Exception as e:
            print(f"⚠️ 读取已有CSV失败，将重新创建: {e}")

    all_enhanced = []  # 用于统计本次新增的总数

    # 2. 循环处理每个物种
    for species in SPECIES_LIST:
        print(f"\n【处理物种：{species}】")

        # 2.1 获取该物种的最新疾病名称列表
        disease_names = fetch_disease_names(species, target=MAX_DISEASES)
        if not disease_names:
            print(f"⚠️ 未能获取 {species} 的疾病列表，跳过")
            continue

        # 2.2 筛选出该物种中尚未存在的疾病
        to_process = [name for name in disease_names if (name, species) not in existing_pairs]
        existing_count = sum(1 for p in existing_pairs if p[1] == species)
        print(f"  新增疾病：{len(to_process)} 种（已有 {existing_count} 种）")

        if not to_process:
            print(f"  ✅ {species} 知识库已是最新，无需更新")
            continue

        # 2.3 调用阿里云API增强新增疾病
        enhanced = []
        for idx, name in enumerate(to_process, 1):
            print(f"  正在处理 ({idx}/{len(to_process)}): {name}")
            rec = enhance_disease_with_qwen(name, species)
            if rec:
                enhanced.append(rec)
                # 立即标记为已处理（但循环内不会重复，主要用于后续统计）
                existing_pairs.add((name, species))
            time.sleep(2)  # 避免API限频

        # 2.4 将新增数据追加到CSV
        if enhanced:
            file_exists = os.path.exists(OUTPUT_CSV)
            with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=enhanced[0].keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerows(enhanced)
            print(f"  ✅ 已追加 {len(enhanced)} 条 {species} 疾病到 {OUTPUT_CSV}")
            all_enhanced.extend(enhanced)
        else:
            print(f"  ⚠️ {species} 没有新增数据被成功增强")

    print(f"\n🎉 全部处理完成！本次共新增 {len(all_enhanced)} 条记录。")


if __name__ == "__main__":
    main()
