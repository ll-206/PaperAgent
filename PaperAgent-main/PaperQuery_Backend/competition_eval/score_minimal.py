"""Compute the six competition metrics only from complete frozen raw runs and reviews."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path

from validate_dataset import validate

HERE=Path(__file__).resolve().parent

def jsonl(path):
    return [json.loads(line) for line in path.open(encoding="utf-8")]

def pct(values,p):
    values=sorted(values)
    return values[max(0,min(len(values)-1,int((len(values)-1)*p+.5)))]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("retrieval_run",type=Path)
    parser.add_argument("ask_run",type=Path)
    parser.add_argument("research_run",type=Path)
    args=parser.parse_args()
    validation=validate()
    if not validation["ready"]:
        raise SystemExit("Human-reviewed dataset gate is not ready")
    paths=[p.resolve() for p in (args.retrieval_run,args.ask_run,args.research_run)]
    if any(p.name.startswith("draft-") for p in paths):
        raise SystemExit("Draft runs cannot produce official metrics")
    retrieval=jsonl(paths[0]/"retrieval_runs.jsonl")
    ask=jsonl(paths[1]/"ask_runs.jsonl")
    research=jsonl(paths[2]/"research_runs.jsonl")
    review=list(csv.DictReader((paths[1]/"ask_review.csv").open(encoding="utf-8-sig",newline="")))
    if (len(retrieval),len(ask),len(research),len(review))!=(30,50,10,50):
        raise SystemExit(f"Incomplete runs/reviews: {[len(retrieval),len(ask),len(research),len(review)]}")
    if any(row.get("error") or row.get("http_status")!=200 for row in ask):
        raise SystemExit("Ask run contains API errors; resolve and rerun before scoring")
    if len({row["question_id"] for row in retrieval})!=30 or len({row["question_id"] for row in ask})!=50:
        raise SystemExit("Duplicate or missing question IDs")
    if len({row["task_id"] for row in research})!=10:
        raise SystemExit("Duplicate or missing Research task IDs")
    normal=[row for row in review if row["question_type"]=="normal"]
    unanswerable=[row for row in review if row["question_type"]=="unanswerable"]
    scope=[row for row in review if row["question_type"]=="scope"]
    if (len(normal),len(unanswerable),len(scope))!=(30,10,10):
        raise SystemExit("Review type counts are incorrect")
    cited=[row for row in normal+scope if row["cited_pages"].strip()]
    if any(row["citation_correct"] not in {"0","1"} for row in cited):
        raise SystemExit("Citation review incomplete")
    if any(row["refusal_correct"] not in {"0","1"} for row in unanswerable):
        raise SystemExit("Refusal review incomplete")
    if any(row["leakage"] not in {"0","1"} for row in scope):
        raise SystemExit("Scope leakage review incomplete")
    hits=sum(bool(row["page_hit_at_5"]) for row in retrieval)
    correct_citations=sum(int(row["citation_correct"]) for row in cited)
    refusals=sum(int(row["refusal_correct"]) for row in unanswerable)
    leaks=sum(int(row["leakage"]) for row in scope)
    successes=sum(bool(row["success_by_minimal_rule"]) for row in research)
    latencies=[float(row["latency_ms"]) for row in retrieval]
    metric_rows=[
        ("Recall@5",hits/30,hits,30,"30 normal questions; gold page in Top-5"),
        ("Citation Accuracy",correct_citations/len(cited) if cited else None,correct_citations,len(cited),"Manual support check of cited answer pages across 30 normal and 10 scope questions"),
        ("Appropriate Refusal Rate",refusals/10,refusals,10,"Manual review of 10 unanswerable answers"),
        ("Cross-document Leakage Rate",leaks/10,leaks,10,"Manual plus citation review of 10 scope traps"),
        ("Research Task Success Rate",successes/10,successes,10,"Registered skills; successful steps; expected artifact"),
        ("Retrieval P95 (ms)",pct(latencies,.95),None,30,"30 warmed sequential retrieval requests"),
    ]
    output=HERE/"metrics"/("formal-"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    output.mkdir(parents=True,exist_ok=False)
    with (output/"final_metrics.csv").open("w",encoding="utf-8",newline="") as file:
        writer=csv.writer(file)
        writer.writerow(["metric","result","numerator","denominator","definition"])
        writer.writerows(metric_rows)
    summary={"status":"formal","retrieval_run":str(paths[0]),"ask_run":str(paths[1]),"research_run":str(paths[2]),
             "citation_coverage":len(cited)/40,"citation_questions":len(cited),
             "security_boundary":json.loads((HERE/"raw"/"security_boundary"/"metrics.json").read_text(encoding="utf-8")),
             "metric_rows":metric_rows}
    (output/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(output)

if __name__=="__main__":
    main()
