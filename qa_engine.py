"""
问答引擎 - 负责匹配问题和答案
"""

import pandas as pd
import jieba
import os


class PetQAEngine:
    """宠物疾病问答引擎"""

    def __init__(self, csv_path="data/diseases.csv"):
        """
        初始化引擎，加载知识库
        """
        self.csv_path = csv_path
        self.load_data()

        # 停用词（过滤掉没意义的词）
        self.stopwords = [
            "的",
            "了",
            "吗",
            "呢",
            "怎么",
            "如何",
            "什么",
            "为啥",
            "为什么",
        ]

        print(f"✅ 问答引擎初始化成功，已加载 {len(self.df)} 条疾病知识")

    def load_data(self):
        """加载CSV数据"""
        if not os.path.exists(self.csv_path):
            print(f"⚠️ 警告：找不到文件 {self.csv_path}")
            self.df = pd.DataFrame(
                columns=["疾病", "物种", "关键词", "症状", "回答", "紧急"]
            )
        else:
            self.df = pd.read_csv(self.csv_path)

    def preprocess(self, text):
        """
        对输入文本进行预处理（分词、过滤）
        """
        if not isinstance(text, str):
            return []

        # 使用jieba分词
        words = jieba.lcut(text)

        # 过滤停用词和单字
        words = [w for w in words if w not in self.stopwords and len(w) > 1]

        return words

    def search(self, question, top_k=3):
        """
        搜索最匹配的疾病 - 宽松匹配版
        """
        # 对问题进行分词
        question_words = self.preprocess(question)

        # 如果没有有效关键词，返回空
        if not question_words:
            return []

        print(f"🔍 提取的关键词：{question_words}")

        results = []

        # 遍历每一行数据
        for idx, row in self.df.iterrows():
            score = 0
            matched = False

            # 检查问题是否包含疾病名
            if row["疾病"] in question:
                score += 0.5
                matched = True

            # 检查关键词（宽松匹配）
            if not pd.isna(row["关键词"]):
                keywords = str(row["关键词"]).split()
                for kw in keywords:
                    if kw in question:
                        score += 0.3
                        matched = True

            # 检查症状（宽松匹配）
            if not pd.isna(row["症状"]):
                symptoms = str(row["症状"]).split()
                for sym in symptoms:
                    if sym in question:
                        score += 0.2
                        matched = True

            if matched:
                results.append(
                    {
                        "disease": row["疾病"],
                        "species": row["物种"],
                        "answer": row["回答"],
                        "symptoms": row["症状"],
                        "urgent": int(row["紧急"]),
                        "score": min(round(score, 2), 1.0),
                    }
                )

        # 按得分排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def get_answer(self, question):
        """
        获取最终答案
        """
        results = self.search(question)

        if not results:
            return {
                "success": False,
                "message": "😥 抱歉，没有找到匹配的疾病。建议换一种描述方式，或咨询专业兽医。",
                "urgent": 0,
                "results": [],
            }

        return {
            "success": True,
            "results": results,
            "urgent": max([r["urgent"] for r in results]),  # 只要有一个紧急就算紧急
            "message": f"找到 {len(results)} 个可能相关的疾病",
        }

    def get_statistics(self):
        """
        获取知识库统计信息
        """
        if self.df is None or len(self.df) == 0:
            return {"total": 0, "by_species": {"狗": 0, "猫": 0}, "urgent_count": 0}

        stats = {
            "total": len(self.df),
            "by_species": self.df["物种"].value_counts().to_dict(),
            "urgent_count": int(self.df["紧急"].sum()),
        }

        return stats


# 测试代码
if __name__ == "__main__":
    # 创建引擎实例
    engine = PetQAEngine()

    # 测试几个问题
    test_questions = [
        "我家狗狗呕吐拉稀没精神",
        "猫肚子变大不吃东西",
        "狗身上掉毛有皮屑",
    ]

    for q in test_questions:
        print("\n" + "=" * 50)
        print(f"问题：{q}")
        result = engine.get_answer(q)
        if result["success"]:
            print(f"找到 {len(result['results'])} 个结果")
            for i, r in enumerate(result["results"]):
                print(f"\n{i + 1}. {r['disease']} (匹配度：{r['score']})")
                print(f"   紧急：{'是' if r['urgent'] else '否'}")
                print(f"   回答：{r['answer'][:50]}...")
        else:
            print(result["message"])
