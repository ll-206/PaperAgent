"""Compute subjective E1/E2 metrics only after every required review cell is filled."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
METRICS = HERE / "metrics"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def score():
    qa = read_csv(METRICS / "e1_review.csv")
    research = read_csv(METRICS / "e2_review.csv")
    if len(qa) != 200 or len(research) != 40:
        raise ValueError(f"Incomplete review sheets: E1={len(qa)}, E2={len(research)}")
    missing = []
    for row in qa:
        key = row["question_id"] + "/" + row["variant"]
        if row.get("evidence_replay_matches") != "True":
            missing.append(key + ":exact_evidence_unavailable")
        if row["question_type"] in {"normal", "scope"}:
            for field in ("answer_correct_0_1", "claim_support_0_0.5_1"):
                if row[field] not in ({"0", "1"} if field == "answer_correct_0_1" else {"0", "0.5", "1"}):
                    missing.append(key + ":" + field)
        if row["question_type"] == "unanswerable" and row["appropriate_refusal_0_1"] not in {"0", "1"}:
            missing.append(key + ":appropriate_refusal_0_1")
        if row["question_type"] == "scope" and row["answer_scope_leak_0_1"] not in {"0", "1"}:
            missing.append(key + ":answer_scope_leak_0_1")
        if row["variant"] == "PAPERAGENT_FULL" and row["question_type"] in {"normal", "scope"} and re.search(r"\[C\d+\]", row["answer_raw"]):
            if row["citation_correct_0_1"] not in {"0", "1"}:
                missing.append(key + ":citation_correct_0_1")
    for row in research:
        key = row["task_id"] + "/" + row["variant"] + "/" + row["repeat_id"]
        if row["requirements_met_0_1"] not in {"0", "1"}:
            missing.append(key + ":requirements_met_0_1")
        if not row["traceable_claim_count"].isdigit() or not row["total_claim_count"].isdigit():
            missing.append(key + ":traceability_counts")
        elif int(row["traceable_claim_count"]) > int(row["total_claim_count"]):
            missing.append(key + ":traceability_count_exceeds_total")
    if missing:
        raise ValueError(f"Review incomplete or invalid ({len(missing)} cells); first: {missing[:15]}")
    result = {"status": "human_review_scored", "e1": {}, "e2": {}}
    for variant in sorted({r["variant"] for r in qa}):
        group = [r for r in qa if r["variant"] == variant]
        answerable = [r for r in group if r["question_type"] in {"normal", "scope"}]
        unanswerable = [r for r in group if r["question_type"] == "unanswerable"]
        scope = [r for r in group if r["question_type"] == "scope"]
        value = {
            "answer_correct": [sum(int(r["answer_correct_0_1"]) for r in answerable), len(answerable)],
            "claim_support_mean": round(sum(float(r["claim_support_0_0.5_1"]) for r in answerable) / len(answerable), 3),
            "appropriate_refusal": [sum(int(r["appropriate_refusal_0_1"]) for r in unanswerable), len(unanswerable)],
            "answer_scope_leakage": [sum(int(r["answer_scope_leak_0_1"]) for r in scope), len(scope)],
        }
        if variant == "PAPERAGENT_FULL":
            cited = [r for r in answerable if re.search(r"\[C\d+\]", r["answer_raw"])]
            value["citation_coverage"] = [len(cited), len(answerable)]
            value["citation_accuracy_given_citation"] = [sum(int(r["citation_correct_0_1"]) for r in cited), len(cited)]
        result["e1"][variant] = value
    for variant in sorted({r["variant"] for r in research}):
        group = [r for r in research if r["variant"] == variant]
        traceable = sum(int(r["traceable_claim_count"]) for r in group)
        total = sum(int(r["total_claim_count"]) for r in group)
        result["e2"][variant] = {
            "minimum_requirements_content": [sum(int(r["requirements_met_0_1"]) for r in group), len(group)],
            "source_traceability": [traceable, total],
        }
    path = METRICS / "human_review_metrics.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    print(score())
