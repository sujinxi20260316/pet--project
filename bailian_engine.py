"""
阿里云百炼平台 - DeepSeek API 调用引擎
"""

from dashscope import Generation
import os
import json


class BailianDeepSeekEngine:
    """阿里云百炼 DeepSeek 引擎"""

    def __init__(self, api_key=None, model="deepseek-r1"):
        """
        初始化引擎
        :param api_key: 阿里云百炼 API Key
        :param model: 模型名称
            - deepseek-r1: DeepSeek推理模型（推荐）
            - deepseek-v3: DeepSeek对话模型
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.model = model

        if not self.api_key:
            print("⚠️ 请设置阿里云百炼 API Key")

    def build_system_prompt(self, pet_info=None):
        """构建系统提示词"""
        prompt = """你是一个专业的宠物医疗顾问，名叫"宠医助手"。请基于兽医学知识回答宠物健康问题。

【回答规则】
1. 仅回答与宠物健康相关的问题
2. 回答要通俗易懂，适合宠物主人理解
3. 不确定时明确说"建议咨询兽医"
4. 遇到紧急情况必须强调"立即就医"
5. 注明这是AI建议，不能替代专业兽医诊断

【回答格式】
- 可能原因：列出1-3种可能性
- 家庭处理：给出临时处理建议
- 就医指征：什么情况需要去医院
"""

        if pet_info:
            prompt += (
                f"\n【宠物档案】\n{json.dumps(pet_info, ensure_ascii=False, indent=2)}"
            )

        return prompt

    def ask(self, question, pet_info=None):
        """
        向 DeepSeek 提问
        """
        if not self.api_key:
            return {
                "success": False,
                "answer": "请先设置阿里云百炼 API Key",
                "urgent": False,
            }

        try:
            # 构建消息
            messages = [
                {"role": "system", "content": self.build_system_prompt(pet_info)},
                {"role": "user", "content": question},
            ]

            # 调用 API
            response = Generation.call(
                api_key=self.api_key,
                model=self.model,
                messages=messages,
                result_format="message",
                temperature=0.7,
                max_tokens=2000,
            )

            # 解析返回结果
            if response.status_code == 200:
                answer = response.output.choices[0].message.content

                # 判断是否紧急
                urgent_keywords = [
                    "立即就医",
                    "马上送医",
                    "紧急",
                    "致命",
                    "抽搐",
                    "吐血",
                    "尿闭",
                    "昏迷",
                    "呼吸困难",
                    "口吐白沫",
                    "意识丧失",
                    "休克",
                ]
                is_urgent = any(kw in answer for kw in urgent_keywords)

                return {
                    "success": True,
                    "answer": answer,
                    "urgent": is_urgent,
                    "usage": response.usage,
                }
            else:
                return {
                    "success": False,
                    "answer": f"API调用失败：{response.message}",
                    "urgent": False,
                }

        except Exception as e:
            return {"success": False, "answer": f"发生错误：{str(e)}", "urgent": False}


# 测试代码
if __name__ == "__main__":
    # 在这里填入你的API Key
    engine = BailianDeepSeekEngine(api_key="sk-92056511e9544b6ca02a58581746ea3e")

    # 测试问题
    result = engine.ask("3个月大的金毛呕吐拉稀，没精神，怎么办")

    if result["success"]:
        print("=" * 60)
        print("🐕 问：3个月大的金毛呕吐拉稀，没精神，怎么办")
        print("💬 答：" + result["answer"])
        if result["urgent"]:
            print("⚠️ 紧急情况提醒！")
        if "usage" in result:
            print(f"\n📊 Token消耗：{result['usage']}")
    else:
        print("❌ 错误：" + result["answer"])
