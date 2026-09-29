import unittest

from core.decision.external_search import classify_external_request


class ExternalSearchIntentTests(unittest.TestCase):
    def test_explicit_transfer_requests_take_fast_external_route(self):
        queries = (
            "把这篇论文的 idea 用于联邦学习方向有什么建议？",
            "能否把该方法迁移到医学影像领域？",
            "这个机制在推荐系统场景能怎么用？",
            "如何把这个 idea 用在机器人任务中？",
            "从这篇论文出发还能衍生哪些新方向？",
            "我想把这个算法推广到医疗场景。",
            "Apply this method to federated learning.",
            "Could this idea work in federated learning?",
        )
        for query in queries:
            with self.subTest(query=query):
                self.assertEqual(classify_external_request(query), "transfer")

    def test_explicit_literature_requests_take_fast_external_route(self):
        queries = (
            "帮我找几篇相关论文。",
            "检索最近关于联邦学习的文献。",
            "有没有类似的方法或工作？",
            "推荐一些最新研究。",
            "与已有研究比较有何区别？",
            "这个方向的最新进展是什么？",
            "find related papers on federated learning",
            "去 arXiv 找相关论文",
        )
        for query in queries:
            with self.subTest(query=query):
                self.assertEqual(classify_external_request(query), "literature")

    def test_selected_paper_facts_and_local_comparisons_stay_local(self):
        queries = (
            "这篇论文用了几块 GPU？",
            "论文中提到的相关工作有哪些？",
            "请总结这篇论文的方法。",
            "比较我选中的两篇论文。",
            "这篇论文在什么数据集上实验？",
            "根据文中第 3 页解释方法。",
            "How many GPU hours does this paper report?",
            "你好",
        )
        for query in queries:
            with self.subTest(query=query):
                self.assertIsNone(classify_external_request(query))


if __name__ == "__main__":
    unittest.main()
