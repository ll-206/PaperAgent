import unittest

from core.decision.engine import DecisionEngine, is_obvious_general_chat
from core.decision.schemas import IntentType


class FailingLLM:
    def invoke(self, _prompt):
        raise RuntimeError("the classifier should not be called for obvious greetings")


class GeneralChatIntentTests(unittest.TestCase):
    def test_common_greetings_are_general_chat(self):
        for query in ("hello", "Hello!", "hi", "你好", "您好！", "早上好"):
            with self.subTest(query=query):
                self.assertTrue(is_obvious_general_chat(query))

    def test_paper_request_with_greeting_is_not_short_circuited(self):
        self.assertFalse(is_obvious_general_chat("你好，请总结这篇论文"))

    def test_greeting_does_not_call_classifier_model(self):
        decision = DecisionEngine(FailingLLM()).decide_intent("hello")
        self.assertEqual(decision.intent, IntentType.GENERAL_CHAT)
        self.assertEqual(decision.reason_code, "CASUAL_GREETING")


if __name__ == "__main__":
    unittest.main()
