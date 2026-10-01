"""E1: paired scope/evidence/grounding ablation on the frozen Ask set.

The four variants use the same corpus, retriever, model, temperature, token
limit and question order. This is an offline evaluation harness, not the UI
route. Human answer/support/citation review is intentionally separate.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

import dotenv

HERE = Path(__file__).resolve().parent
EVAL = HERE.parent
BACKEND = EVAL.parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ["CHROMA_ONNX_CACHE_DIR"] = str(BACKEND.parents[1] / "artifacts" / "competition_eval" / "onnx_cache")
dotenv.load_dotenv()

from competition_eval.validate_dataset import validate
from core.decision.engine import DecisionEngine
from core.decision.prompts import ANSWER_PROMPT
from core.evidence.formatter import build_citations, format_evidence
from core.evidence.grounding import GroundingVerifier
from core.llm.LLM import LLM
from core.vectordb.chromadb import AcadeChroma
from main import ONNXEmbeddings

VARIANTS = ("VANILLA_RAG", "SCOPE_RAG", "SCOPE_EVIDENCE", "PAPERAGENT_FULL")


def content(response):
    return response.content if hasattr(response, "content") else str(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", default="zhipu")
    parser.add_argument("--pairs", type=Path, help="JSON list of [question_id, variant] exact retries")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    check = validate()
    if not check["ready"]:
        raise SystemExit(f"Frozen dataset failed validation: {check['errors']}")
    questions = list(csv.DictReader((EVAL / "datasets" / "qa_groundtruth.csv").open(encoding="utf-8-sig")))
    questions = questions[args.start - 1:args.start - 1 + args.limit]
    pairset = {tuple(pair) for pair in json.loads(args.pairs.read_text(encoding="utf-8"))} if args.pairs else None
    doc_map = json.loads((EVAL / "raw" / "document_map.json").read_text(encoding="utf-8"))
    index = EVAL / "raw" / "isolated_index"
    if not (index / "layer1" / "chroma.sqlite3").exists():
        raise SystemExit("Isolated Chroma index is missing")
    db = AcadeChroma(str(index / "layer1"), str(index / "layer2"), ONNXEmbeddings(), None)
    llm = LLM().get_llm(args.model).bind(temperature=0, max_tokens=2048)
    decision_engine = DecisionEngine(llm)
    verifier = GroundingVerifier(decision_engine)
    run_id = "probe" if args.probe else "retry" if pairset is not None else "formal"
    run_id += "-e1-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or HERE / "raw_results" / run_id
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "run_id": run_id, "status": "probe" if args.probe else "formal_raw_pending_human_review",
        "dataset_sha256": hashlib.sha256((EVAL / "datasets" / "qa_groundtruth.csv").read_bytes()).hexdigest(),
        "model": args.model, "temperature": 0, "max_tokens": 2048, "top_k": 8,
        "start": args.start, "question_count": len(questions), "pair_count": len(pairset) if pairset is not None else len(questions) * len(VARIANTS), "variants": VARIANTS,
        "method": "Product retriever, DecisionEngine, ANSWER_PROMPT, GroundingVerifier; external search disabled for fixed-corpus comparison; SEARCH_EXTERNAL is recorded as no-answer.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output / "evidence_ablation.jsonl").open("w", encoding="utf-8") as file:
        for question in questions:
            selected = question["selected_doc"]
            selected_id = doc_map[selected]
            for variant in VARIANTS:
                if pairset is not None and (question["question_id"], variant) not in pairset:
                    continue
                started = time.perf_counter()
                row = {
                    "run_id": run_id, "question_id": question["question_id"],
                    "question_type": question["question_type"], "variant": variant,
                    "selected_docs": [selected], "model": args.model, "temperature": 0,
                    "top_k": 8, "max_tokens": 2048, "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "retrieved_docs": [], "retrieved_pages": [], "evidence_decision": None,
                    "answer_raw": "", "citations": [], "grounding": None, "error": None,
                }
                try:
                    scope_filter = None if variant == "VANILLA_RAG" else {"documentID": selected_id}
                    chunks = db.search_evidence(question["query"], scope_filter, k=8)
                    row["retrieved_docs"] = [next((k for k, v in doc_map.items() if v == c.document_id), c.document_id) for c in chunks]
                    row["retrieved_pages"] = [c.page_number for c in chunks]
                    row["evidence_replay_matches"] = True
                    row["evidence_chunks"] = [
                        {"id": f"C{i}", "document": row["retrieved_docs"][i - 1], "page": c.page_number, "chunk_id": c.chunk_id, "text": c.text}
                        for i, c in enumerate(chunks, 1)
                    ]
                    evidence, citation_map = format_evidence(chunks)
                    if variant in ("SCOPE_EVIDENCE", "PAPERAGENT_FULL"):
                        decision = decision_engine.decide_evidence(question["query"], evidence)
                        row["evidence_decision"] = decision.decision
                    if row["evidence_decision"] in ("ABSTAIN", "SEARCH_EXTERNAL") or not chunks:
                        row["answer_raw"] = "当前证据不足，无法在所选论文中可靠回答。"
                    else:
                        prompt = ANSWER_PROMPT.format(
                            question=question["query"], evidence=evidence,
                            selected_papers="全部论文（未限定）" if variant == "VANILLA_RAG" else selected,
                        )
                        row["answer_raw"] = content(llm.invoke(prompt))
                        if not row["answer_raw"].strip():
                            raise RuntimeError("Model returned empty answer; this run is invalid")
                    if variant == "PAPERAGENT_FULL":
                        citations = build_citations(citation_map)
                        passed, report = verifier.verify(question["query"], row["answer_raw"], citations, citation_map)
                        row["grounding"] = {"passed": passed, **report}
                        row["citations"] = [
                            {"id": c.citation_id, "document": next((k for k, v in doc_map.items() if v == c.document_id), c.document_id), "page": c.page_number}
                            for c in citations
                        ]
                except Exception as exc:
                    row["error"] = f"{type(exc).__name__}: {str(exc)[:600]}"
                    row["traceback"] = traceback.format_exc(limit=3)
                row["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
                file.write(json.dumps(row, ensure_ascii=False) + "\n")
                file.flush()
                print(question["question_id"], variant, "ok" if not row["error"] else row["error"], int(row["latency_ms"]), flush=True)
                if row["error"] and ("402" in row["error"] or "Insufficient Balance" in row["error"]):
                    manifest["status"] = "invalid_interrupted"
                    manifest["invalid_reason"] = row["error"]
                    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
                    raise SystemExit("Model balance exhausted; stopped before further requests")
    print(output)


if __name__ == "__main__":
    main()
