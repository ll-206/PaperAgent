"""Attach replayed evidence text to E1 rows for human claim/citation review.

This does not change the original raw file. If retrieved doc/page ordering has
changed, the row is flagged and must not be treated as a matched replay.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVAL = HERE.parent
BACKEND = EVAL.parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ["CHROMA_ONNX_CACHE_DIR"] = str(BACKEND.parents[1] / "artifacts" / "competition_eval" / "onnx_cache")

from core.vectordb.chromadb import AcadeChroma
from main import ONNXEmbeddings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("e1_dir", type=Path)
    args = parser.parse_args()
    run_dir = args.e1_dir.resolve()
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status", "").startswith("invalid"):
        raise SystemExit("Invalid E1 run cannot be hydrated as formal evidence")
    questions = {r["question_id"]: r for r in csv.DictReader((EVAL / "datasets" / "qa_groundtruth.csv").open(encoding="utf-8-sig"))}
    doc_map = json.loads((EVAL / "raw" / "document_map.json").read_text(encoding="utf-8"))
    inverse = {value: key for key, value in doc_map.items()}
    index = EVAL / "raw" / "isolated_index"
    db = AcadeChroma(str(index / "layer1"), str(index / "layer2"), ONNXEmbeddings(), None)
    mismatches = 0
    with (run_dir / "evidence_ablation_enriched.jsonl").open("w", encoding="utf-8") as output:
        for line in (run_dir / "evidence_ablation.jsonl").open(encoding="utf-8"):
            row = json.loads(line)
            q = questions[row["question_id"]]
            selected_id = doc_map[q["selected_doc"]]
            scope_filter = None if row["variant"] == "VANILLA_RAG" else {"documentID": selected_id}
            chunks = db.search_evidence(q["query"], scope_filter, k=8)
            docs = [inverse.get(c.document_id, c.document_id) for c in chunks]
            pages = [c.page_number for c in chunks]
            row["evidence_replay_matches"] = docs == row["retrieved_docs"] and pages == row["retrieved_pages"]
            mismatches += not row["evidence_replay_matches"]
            row["evidence_chunks"] = [
                {"id": f"C{i}", "document": docs[i-1], "page": c.page_number, "chunk_id": c.chunk_id, "text": c.text}
                for i, c in enumerate(chunks, 1)
            ]
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"rows": sum(1 for _ in (run_dir / "evidence_ablation.jsonl").open(encoding="utf-8")), "replay_mismatches": mismatches}, ensure_ascii=False))


if __name__ == "__main__":
    main()
