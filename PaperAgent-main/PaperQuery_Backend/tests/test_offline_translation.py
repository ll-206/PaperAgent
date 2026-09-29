import unittest
from unittest.mock import patch

from core.backend.services.translate import Translator


class FakeTranslation:
    def __init__(self):
        self.chunks = []

    def translate(self, text):
        self.chunks.append(text)
        return text


class OfflineTranslationTests(unittest.TestCase):
    def test_pdf_line_breaks_and_long_selection_are_chunked(self):
        fake = FakeTranslation()
        source = "A para-\nmetric model handles evidence. " * 85
        with patch("core.backend.services.translate._english_to_chinese", return_value=fake):
            output = Translator().translate(source)
        self.assertGreater(len(fake.chunks), 1)
        self.assertTrue(all(len(chunk) <= 1200 for chunk in fake.chunks))
        self.assertNotIn("para-", output)
        self.assertEqual(output.count("parametric model handles evidence"), 85)


if __name__ == "__main__":
    unittest.main()
