import unittest
from types import SimpleNamespace

from core.backend.router.router_system import component_status


class FakeLLMManager:
    def get_all_llms(self):
        return {"deepseek": object(), "kimi": object(), "zhipu": object()}


class SystemStatusTests(unittest.TestCase):
    def test_component_status_reports_configured_services(self):
        app = SimpleNamespace(
            llm=FakeLLMManager(),
            chroma_db=object(),
            retrieval_pipeline=None,
            research_orchestrator=object(),
        )
        status = component_status(app)
        self.assertTrue(status["deepseek"])
        self.assertTrue(status["kimi"])
        self.assertTrue(status["zhipu"])
        self.assertTrue(status["vector_database"])
        self.assertFalse(status["hybrid_retrieval"])
        self.assertTrue(status["research"])

    def test_component_status_handles_uninitialized_app(self):
        status = component_status(SimpleNamespace())
        self.assertFalse(any(status.values()))


if __name__ == "__main__":
    unittest.main()
