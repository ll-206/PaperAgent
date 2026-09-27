"""Build an isolated layer-1 corpus index with the product's chunking and MiniLM code."""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ["CHROMA_ONNX_CACHE_DIR"] = str(BACKEND.parents[1] / "artifacts" / "competition_eval" / "onnx_cache")
import dotenv
dotenv.load_dotenv()

from main import ONNXEmbeddings
from core.utils.util import cal_file_md5, split_text_into_chunks
from core.vectordb.chromadb import AcadeChroma


def main():
    root=HERE / "raw" / "isolated_index"
    root.mkdir(parents=True,exist_ok=True)
    db=AcadeChroma(str(root / "layer1"),str(root / "layer2"),ONNXEmbeddings(),None)
    papers=list(csv.DictReader((HERE/"datasets"/"paper_corpus.csv").open(encoding="utf-8")))
    results=[]
    for paper in papers:
        path=HERE/paper["pdf_path"]
        document_id=cal_file_md5(path)
        existing=db.chroma_db_layer1._collection.get(where={"documentID":document_id},include=["metadatas"])
        if existing["ids"]:
            count=len(existing["ids"])
            elapsed=None
            status="already_indexed"
        else:
            chunks=[]
            metadata=[]
            with fitz.open(path) as pdf:
                for number,page in enumerate(pdf,1):
                    for chunk in split_text_into_chunks(page.get_text("text")):
                        chunks.append(chunk)
                        metadata.append({"source":str(path),"documentID":document_id,
                                         "knowledge_name":"competition_eval","page_number":number})
            if not chunks:
                raise RuntimeError(f"{paper['paper_id']}: no extractable chunks")
            started=time.perf_counter()
            db.add_paper_to_layer1(chunks,metadata)
            elapsed=round((time.perf_counter()-started)*1000,2)
            count=len(chunks)
            status="indexed"
        result={"paper_id":paper["paper_id"],"document_id":document_id,"chunk_count":count,
                "index_time_ms":elapsed,"status":status,"pdf_sha256":paper["sha256"]}
        results.append(result)
        print(json.dumps(result,ensure_ascii=False),flush=True)
    (HERE/"raw"/"index_runs.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in results),encoding="utf-8")
    (HERE/"raw"/"document_map.json").write_text(json.dumps({r["paper_id"]:r["document_id"] for r in results},indent=2),encoding="utf-8")

if __name__=="__main__":
    main()
