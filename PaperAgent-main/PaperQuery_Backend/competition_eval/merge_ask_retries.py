"""Merge successful exact-question retries while preserving every raw attempt."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("initial_run", type=Path)
    parser.add_argument("retry_run", type=Path)
    args = parser.parse_args()
    initial_path = args.initial_run.resolve() / "ask_runs.jsonl"
    retry_path = args.retry_run.resolve() / "ask_runs.jsonl"
    initial, retry = read_jsonl(initial_path), read_jsonl(retry_path)
    qa_path = HERE / "datasets" / "qa_groundtruth.csv"
    expected = list(csv.DictReader(qa_path.open(encoding="utf-8-sig", newline="")))
    expected_ids = [row["question_id"] for row in expected]
    if len(expected_ids) != 50 or len(set(expected_ids)) != 50:
        raise SystemExit("Frozen QA set must have 50 unique question IDs")
    if len(initial) != 50 or [row["question_id"] for row in initial] != expected_ids:
        raise SystemExit("Initial run must contain all 50 attempts in frozen order")
    failures = {row["question_id"] for row in initial if row.get("error") or row.get("http_status") != 200}
    if len(retry) != len(failures) or {row["question_id"] for row in retry} != failures:
        raise SystemExit(f"Retry IDs do not exactly match failed IDs: {sorted(failures)}")
    initial_by_id = {row["question_id"]: row for row in initial}
    retry_by_id = {row["question_id"]: row for row in retry}
    merged = []
    for qa in expected:
        qid = qa["question_id"]
        row = retry_by_id.get(qid, initial_by_id[qid])
        if row.get("error") or row.get("http_status") != 200:
            raise SystemExit(f"{qid}: retry still failed")
        if row["selected_doc"] != qa["selected_doc"] or row["question_type"] != qa["question_type"]:
            raise SystemExit(f"{qid}: question metadata changed")
        if row["model"] != initial_by_id[qid]["model"]:
            raise SystemExit(f"{qid}: model differs between attempts")
        merged.append(row)
    run_id = "formal-ask-merged-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = HERE / "raw" / run_id
    output.mkdir(parents=True, exist_ok=False)
    with (output / "ask_runs.jsonl").open("w", encoding="utf-8") as file:
        for row in merged:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest = {
        "run_id": run_id,
        "status": "formal_merged_exact_retries",
        "initial_attempt": str(initial_path),
        "retry_attempt": str(retry_path),
        "replaced_failed_question_ids": sorted(failures),
        "question_file_sha256": hashlib.sha256(qa_path.read_bytes()).hexdigest(),
        "model": merged[0]["model"],
        "completed_count": len(merged),
    }
    (output / "merge_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(output)


if __name__ == "__main__":
    main()
