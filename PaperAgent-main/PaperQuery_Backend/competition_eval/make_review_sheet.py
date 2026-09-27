"""Create a human scoring sheet from a complete 50-question Ask run."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("ask_run",type=Path,help="raw/formal-ask-... or raw/draft-ask-...")
    args=parser.parse_args()
    run=args.ask_run.resolve()
    rows=[json.loads(line) for line in (run/"ask_runs.jsonl").open(encoding="utf-8")]
    if len(rows)!=50:
        raise SystemExit(f"Expected 50 Ask results, found {len(rows)}")
    gt={row["question_id"]:row for row in csv.DictReader((HERE/"datasets"/"qa_groundtruth.csv").open(encoding="utf-8-sig"))}
    output=run/"ask_review.csv"
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing review sheet: {output}")
    fields=["question_id","question_type","selected_doc","query","gold_page","gold_evidence",
            "http_status","error","answer_raw","decision","cited_pages","citation_correct","refusal_correct","leakage","reviewer_notes"]
    with output.open("w",encoding="utf-8-sig",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=fields)
        writer.writeheader()
        for row in rows:
            q=gt[row["question_id"]]
            cited=set(re.findall(r"\[C(\d+)\]",row.get("answer_raw") or ""))
            citation_by_id={str(item.get("id","")).removeprefix("C"):item for item in row.get("citations") or []}
            pages=[]
            for cite_id in sorted(cited,key=int):
                citation=citation_by_id.get(cite_id)
                pages.append(f"C{cite_id}:{citation.get('page')}" if citation else f"C{cite_id}:MISSING")
            writer.writerow({"question_id":row["question_id"],"question_type":q["question_type"],
                             "selected_doc":q["selected_doc"],"query":q["query"],"gold_page":q["gold_page"],
                             "gold_evidence":q["gold_evidence"],"http_status":row.get("http_status"),
                             "error":row.get("error") or "","answer_raw":row.get("answer_raw", ""),
                             "decision":row.get("decision"),"cited_pages":";".join(pages),
                             "citation_correct":"","refusal_correct":"","leakage":"","reviewer_notes":""})
    print(output)

if __name__=="__main__":
    main()
