"""V2 索引重建脚本。

遍历数据库中 documentStatus=2 的 PDF，用新的 split_text 分块 + BGE-M3 embedding，
写入 V2 Chroma（CHROMA_LAYER1_V2_DIR）并生成 BM25 corpus。
"""
from __future__ import annotations

import os
import pickle
import sys

import dotenv

dotenv.load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fitz
from langchain_chroma import Chroma

from core.backend.db.database import SessionLocal
from core.backend.db.models import Document
from core.common.config import settings
from core.common.types import EvidenceChunk
from core.retrieval.dense import BGE3Embeddings
from core.utils.chunking import split_text


def build_records(doc: Document, filepath: str) -> list[dict]:
    """对单个 PDF 分块，生成带 chunk_id 的记录列表。"""
    pdf = fitz.open(filepath)
    records: list[dict] = []
    for page_num in range(len(pdf)):
        text = pdf.load_page(page_num).get_text("text")
        if not text:
            continue
        for ch in split_text(text):
            chunk_id = f"{doc.uid}:p{page_num + 1}:c{ch.index}"
            records.append({
                "text": ch.text,
                "metadata": {
                    "chunk_id": chunk_id,
                    "documentID": doc.uid,
                    "knowledgeID": doc.knowledgeID,
                    "page_number": page_num + 1,
                    "chunk_index": ch.index,
                    "source": filepath,
                    "index_version": settings.INDEX_VERSION,
                },
            })
    pdf.close()
    return records


def main() -> None:
    db = SessionLocal()
    docs = db.query(Document).filter(Document.documentStatus == 2).all()
    if not docs:
        print("没有 documentStatus=2 的文档，跳过。")
        return

    os.makedirs(settings.CHROMA_LAYER1_V2_DIR, exist_ok=True)
    os.makedirs(settings.BM25_INDEX_DIR, exist_ok=True)

    embedding = BGE3Embeddings(settings.BGE_M3_MODEL_PATH)
    chroma_v2 = Chroma(
        persist_directory=settings.CHROMA_LAYER1_V2_DIR,
        embedding_function=embedding,
    )

    corpus: list[EvidenceChunk] = []
    for doc in docs:
        filepath = os.getenv("AcadeAgent_DIR", ".") + doc.documentPath
        if not os.path.exists(filepath):
            print(f"跳过（文件不存在）: {doc.documentName}")
            continue
        records = build_records(doc, filepath)
        if not records:
            continue
        texts = [r["text"] for r in records]
        metadatas = [r["metadata"] for r in records]
        chroma_v2.add_texts(texts, metadatas)
        for r in records:
            m = r["metadata"]
            corpus.append(EvidenceChunk(
                chunk_id=m["chunk_id"],
                document_id=m["documentID"],
                knowledge_id=m["knowledgeID"],
                source=m["source"],
                page_number=m["page_number"],
                text=r["text"],
            ))
        print(f"已索引 {doc.documentName}: {len(records)} chunks")

    # 持久化 BM25 corpus
    corpus_path = os.path.join(settings.BM25_INDEX_DIR, "corpus.pkl")
    with open(corpus_path, "wb") as f:
        pickle.dump(corpus, f)

    print(f"\nV2 索引完成：{len(docs)} 个文档，共 {len(corpus)} 个 chunk")
    print(f"Chroma 目录: {settings.CHROMA_LAYER1_V2_DIR}")
    print(f"BM25 corpus: {corpus_path}")


if __name__ == "__main__":
    main()
