import unittest

from core.common.types import EvidenceChunk
from core.skills.builtin import LocalRetrievalInput, LocalRetrievalSkill


class FakeVectorDB:
    def __init__(self):
        self.calls = []

    def search_evidence(self, query, filter_by_document, k):
        self.calls.append((query, filter_by_document, k))
        return [EvidenceChunk(
            chunk_id="paper-1:p2",
            document_id="paper-1",
            source="paper.pdf",
            page_number=2,
            text="Relevant passage",
        )]


class LocalRetrievalTests(unittest.IsolatedAsyncioTestCase):
    async def test_research_uses_scoped_chroma_retrieval(self):
        vector_db = FakeVectorDB()
        result = await LocalRetrievalSkill().execute(
            LocalRetrievalInput(query="method", document_ids=["paper-1"], k=3),
            {"chroma_db": vector_db, "allowed_document_ids": ["paper-1"]},
        )
        self.assertTrue(result.ok)
        self.assertEqual(vector_db.calls, [
            ("method", {"documentID": {"$in": ["paper-1"]}}, 3)
        ])
        self.assertEqual(result.output["evidence"][0]["page_number"], 2)

    async def test_research_cannot_search_other_accounts_documents(self):
        vector_db = FakeVectorDB()
        result = await LocalRetrievalSkill().execute(
            LocalRetrievalInput(query="method", document_ids=["other-paper"]),
            {"chroma_db": vector_db, "allowed_document_ids": ["paper-1"]},
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "FORBIDDEN_DOCUMENT")
        self.assertEqual(vector_db.calls, [])


if __name__ == "__main__":
    unittest.main()
