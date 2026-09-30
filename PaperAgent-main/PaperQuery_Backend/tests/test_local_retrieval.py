import unittest
from types import SimpleNamespace

from core.common.types import EvidenceChunk
from core.skills.builtin import LocalRetrievalInput, LocalRetrievalSkill
from core.vectordb.chromadb import AcadeChroma


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
    def test_overview_uses_distinct_opening_chunks(self):
        class FakeCollection:
            def get(self, where, include):
                self.where = where
                return {
                    "ids": ["one", "duplicate", "two"],
                    "documents": ["abstract", "abstract", "method"],
                    "metadatas": [
                        {"page_number": 1},
                        {"page_number": 1},
                        {"page_number": 2},
                    ],
                }

        collection = FakeCollection()
        chroma = AcadeChroma.__new__(AcadeChroma)
        chroma.chroma_db_layer1 = SimpleNamespace(_collection=collection)
        chunks = chroma.get_opening_evidence(["paper-1"])

        self.assertEqual(collection.where, {"documentID": "paper-1"})
        self.assertEqual([chunk.text for chunk in chunks], ["abstract", "method"])
        self.assertEqual([chunk.page_number for chunk in chunks], [1, 2])

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
