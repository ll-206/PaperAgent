"""Run the 30 normal questions through the product's scoped MiniLM retrieval."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0,str(BACKEND))
os.chdir(BACKEND)
os.environ["CHROMA_ONNX_CACHE_DIR"] = str(BACKEND.parents[1]/"artifacts"/"competition_eval"/"onnx_cache")
import dotenv
dotenv.load_dotenv()
from main import ONNXEmbeddings
from core.vectordb.chromadb import AcadeChroma
from validate_dataset import validate

def percentile(values,p):
    values=sorted(values)
    return values[max(0,min(len(values)-1,int((len(values)-1)*p+.5)))]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--draft",action="store_true",help="Run with pending human review; results are not competition metrics")
    args=parser.parse_args()
    validation=validate()
    if not validation["ready"] and not args.draft:
        raise SystemExit("Dataset gate failed. Review annotations before formal scoring; use --draft for a clearly labeled trial.")
    qa_path=HERE/"datasets"/"qa_groundtruth.csv"
    questions=[r for r in csv.DictReader(qa_path.open(encoding="utf-8-sig")) if r["question_type"]=="normal"]
    if len(questions)!=30:
        raise SystemExit("Expected 30 normal questions")
    doc_map=json.loads((HERE/"raw"/"document_map.json").read_text(encoding="utf-8"))
    index=HERE/"raw"/"isolated_index"
    db=AcadeChroma(str(index/"layer1"),str(index/"layer2"),ONNXEmbeddings(),None)
    # Warm the embedding model separately; the 30 timed requests then use a warm index.
    db.search_evidence("evaluation warmup",{"documentID":{"$in":[doc_map["P01"]]}},k=1)
    run_id=("draft" if args.draft else "formal")+"-retrieval-"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output=HERE/"raw"/run_id
    output.mkdir(parents=True,exist_ok=False)
    rows=[]
    for q in questions:
        doc_id=doc_map[q["selected_doc"]]
        start=time.perf_counter()
        evidence=db.search_evidence(q["query"],{"documentID":{"$in":[doc_id]}},k=5)
        duration=round((time.perf_counter()-start)*1000,2)
        gold_page=int(q["gold_page"])
        rows.append({"run_id":run_id,"question_id":q["question_id"],"query":q["query"],
                     "selected_doc":q["selected_doc"],"selected_document_id":doc_id,"gold_page":gold_page,
                     "retrieved":[{"document_id":e.document_id,"page":e.page_number,"chunk_id":e.chunk_id,"distance":e.dense_score} for e in evidence],
                     "latency_ms":duration,"page_hit_at_5":any(e.page_number==gold_page for e in evidence),
                     "outside_scope":any(e.document_id!=doc_id for e in evidence)})
    with (output/"retrieval_runs.jsonl").open("w",encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row,ensure_ascii=False)+"\n")
    latencies=[row["latency_ms"] for row in rows]
    hits=sum(row["page_hit_at_5"] for row in rows)
    metrics={"run_id":run_id,"status":"draft_not_competition_result" if args.draft else "formal",
             "n":len(rows),"page_recall_at_5":hits/len(rows),"hits":hits,
             "retrieval_p50_ms":percentile(latencies,.5),"retrieval_p95_ms":percentile(latencies,.95),
             "outside_scope_retrieval_count":sum(row["outside_scope"] for row in rows),
             "question_file_sha256":hashlib.sha256(qa_path.read_bytes()).hexdigest(),
             "metric_definition":"Top-5 contains the gold PDF page; draft pages await independent human verification" if args.draft else "Top-5 contains the independently verified gold PDF page; one selected paper per question"}
    (output/"metrics.json").write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(metrics,ensure_ascii=False,indent=2))
    print(output)

if __name__=="__main__":
    main()
