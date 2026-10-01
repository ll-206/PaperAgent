"""Summarize objective E1/E2/E3 fields; never invent human quality labels."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def rows(path: Path):
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def ratio(n, d):
    return {"n": n, "N": d, "percentage": round(100 * n / d, 1) if d else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("e1", type=Path)
    parser.add_argument("e2", type=Path)
    parser.add_argument("e3", type=Path)
    args = parser.parse_args()
    paths = [p.resolve() for p in (args.e1, args.e2, args.e3)]
    for path in paths:
        manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("status", "").startswith("invalid") or manifest.get("status") == "probe":
            raise SystemExit(f"Cannot summarize invalid/probe run: {path}")
    enriched_path = paths[0] / "evidence_ablation_enriched.jsonl"
    e1 = rows(enriched_path if enriched_path.exists() else paths[0] / "evidence_ablation.jsonl")
    e2 = rows(paths[1] / "research_ablation.jsonl")
    e3 = rows(paths[2] / "continuity_runs.jsonl")
    questions = {r["question_id"]: r for r in csv.DictReader((HERE.parent / "datasets" / "qa_groundtruth.csv").open(encoding="utf-8-sig"))}
    if len(e1) != 200 or len(e2) != 40 or len(e3) != 16:
        raise SystemExit(f"Incomplete runs: E1={len(e1)}/200, E2={len(e2)}/40, E3={len(e3)}/16")
    by_variant = defaultdict(list)
    for row in e1:
        by_variant[row["variant"]].append(row)
    evidence = {}
    for variant, group in by_variant.items():
        scope = [r for r in group if r["question_type"] == "scope"]
        unanswerable = [r for r in group if r["question_type"] == "unanswerable"]
        evidence[variant] = {
            "completed": len(group), "errors": sum(bool(r["error"]) for r in group),
            "exact_evidence_available": ratio(sum(r.get("evidence_replay_matches") is True for r in group), len(group)),
            "retrieval_scope_leakage": ratio(sum(any(doc not in r["selected_docs"] for doc in r["retrieved_docs"]) for r in scope), len(scope)),
            "explicit_abstain_decisions": ratio(sum(r["evidence_decision"] in {"ABSTAIN", "SEARCH_EXTERNAL"} for r in unanswerable), len(unanswerable)),
            "answer_correctness": "pending_human_review",
            "claim_support_rate": "pending_human_review",
            "appropriate_refusal_rate": "pending_human_review",
            "answer_scope_leakage": "pending_human_review",
            "citation_accuracy": "pending_human_review",
        }
    research = {}
    for variant in ("OPEN_PLANNER", "PAPERAGENT_CONTROLLED"):
        group = [r for r in e2 if r["variant"] == variant]
        research[variant] = {
            "completed": len(group), "errors": sum(bool(r["error"]) for r in group),
            "plan_valid": ratio(sum(bool(r["plan_valid"]) for r in group), len(group)),
            "plans_with_invalid_skill": ratio(sum(r["invalid_skill_count"] > 0 for r in group), len(group)),
            "plans_with_invalid_dependency": ratio(sum(r["invalid_dependency_count"] > 0 for r in group), len(group)),
            "task_success_minimal": ratio(sum(bool(r["task_success_by_minimal_rule"]) for r in group), len(group)),
            "minimum_requirements_content": "pending_human_review",
            "artifact_source_traceability": "pending_human_review",
        }
    continuity = {}
    for condition in ("STATELESS", "PAPERAGENT_WORKSPACE"):
        group = [r for r in e3 if r["condition"] == condition]
        continuity[condition] = {
            "completed": len(group), "errors": sum(bool(r["error"]) for r in group),
            "task_parent_link": ratio(sum(bool(r.get("task_preserved")) for r in group), len(group)),
            "artifact_parent_link": ratio(sum(bool(r.get("artifact_reused_by_parent_link")) for r in group), len(group)),
            "selected_scope_into_research": ratio(sum(bool(r.get("selected_docs_preserved_into_research")) for r in group), len(group)),
            "workflow_completion_minimal": ratio(sum(bool(r.get("session_success_by_minimal_rule")) for r in group), len(group)),
            "scripted_reentry_mean": round(sum(r.get("manual_reentry_count", 0) for r in group) / len(group), 2),
            "answer_content_continuity": "pending_human_review",
        }
    summary = {
        "status": "objective_summary_pending_human_review",
        "e1": evidence, "e2": research, "e3": continuity,
        "notes": [
            "E1 retrieval_scope_leakage is a property of retrieved docs, not generated-answer leakage.",
            "E2 task_success_minimal is plan/execution/artifact-type only, not research quality.",
            "E3 scripted_reentry_mean is a modeled UI operation count, not observed human behavior.",
            "No answer correctness, claim support, citation correctness or artifact factual traceability has been imputed.",
            "Rows with evidence_replay_matches=false cannot be used for exact claim/citation review; retain as raw model outputs or retry with explicit authorization and captured evidence.",
        ],
    }
    out = HERE / "metrics"
    out.mkdir(exist_ok=True)
    path = out / "objective_summary.json"
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    # Review sheets retain the source row identifiers and evidence/answer payloads.
    with (out / "e1_review.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["question_id", "variant", "question_type", "question", "selected_doc", "gold_page", "gold_evidence", "answer_raw", "retrieved_docs", "retrieved_pages", "evidence_chunks_json", "evidence_replay_matches", "answer_correct_0_1", "claim_support_0_0.5_1", "appropriate_refusal_0_1", "answer_scope_leak_0_1", "citation_correct_0_1", "reviewer_notes"])
        for r in e1:
            q = questions[r["question_id"]]
            writer.writerow([r["question_id"], r["variant"], r["question_type"], q["query"], q["selected_doc"], q["gold_page"], q["gold_evidence"], r["answer_raw"], ";".join(r["retrieved_docs"]), ";".join(map(str, r["retrieved_pages"])), json.dumps(r.get("evidence_chunks", []), ensure_ascii=False), r.get("evidence_replay_matches", ""), "", "", "", "", "", ""])
    with (out / "e2_review.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["task_id", "variant", "repeat_id", "goal", "minimum_requirements", "artifacts_json", "requirements_met_0_1", "traceable_claim_count", "total_claim_count", "reviewer_notes"])
        for r in e2:
            writer.writerow([r["task_id"], r["variant"], r["repeat_id"], r["goal"], r["minimum_requirements"], json.dumps(r["artifacts"], ensure_ascii=False), "", "", "", ""])
    print(path)


if __name__ == "__main__":
    main()
