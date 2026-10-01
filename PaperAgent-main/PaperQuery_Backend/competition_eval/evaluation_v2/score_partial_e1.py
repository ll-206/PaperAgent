"""Auditable single-reviewer E1 scoring on the 181 exact-evidence rows.

Core-answer labels were assigned by reading each answer against the frozen QA key.
Q003 is ambiguous in the source paper and is reported as a sensitivity case.
Claim support is an answer-level 0/0.5/1 judgment on answerable rows only.
Citation accuracy is an answer-level judgment for cited Full answers only.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REVIEW = HERE / "metrics" / "e1_review.csv"

# Strictly against the frozen gold answer; omission of a required item is incorrect.
WRONG_ALL = {"Q003", "Q005", "Q015", "Q017", "Q018", "Q023", "Q047"}
WRONG_VARIANTS = {
    "Q006": {"VANILLA_RAG"},
    "Q008": {"VANILLA_RAG", "SCOPE_EVIDENCE", "PAPERAGENT_FULL"},
    "Q026": {"VANILLA_RAG"},
    "Q049": {"VANILLA_RAG"},
}
NOTES = {
    "Q003": "Frozen key says 3, but the same paper's Results section says 4 with a TQA-split caveat; exclude or adjudicate before formal publication.",
    "Q005": "Required 7B and 13B; answers give only 7B.",
    "Q006": "Vanilla answer omits retrieval-augmented Llama2-chat and includes unrelated CRAG comparisons.",
    "Q008": "Vanilla names the Pile; Evidence/Full abstain; required answer is large-scale web search.",
    "Q015": "Required GPT-3 language-modeling improvement is 6.3%; all answers omit it.",
    "Q017": "Required Server Machine Dataset is SMD; answer says SWaT.",
    "Q018": "Required average absolute F1 gain is 18.76%; answers omit or give a different figure.",
    "Q023": "Required answer is SMD; available answers abstain.",
    "Q026": "Vanilla abstains, though it mentions SMAP and MSL without identifying them as the answer.",
    "Q047": "Required focus score-based self-conditioning is omitted.",
    "Q049": "Vanilla abstains; Scope variants identify SMAP/MSL as NASA datasets.",
}

# Answer-level factual support of the available retrieved evidence, as defined
# in the experiment design: 1=all material facts supported; 0.5=some supported;
# 0=unsupported or a refusal to an answerable question. These judgments are
# deliberately separate from correctness against the frozen gold key.
PARTIAL_SUPPORT_ALL = {"Q001", "Q005", "Q012", "Q018", "Q047"}
NO_SUPPORT_ALL = {"Q015", "Q017", "Q023"}
NO_SUPPORT_VARIANTS = {
    "Q008": {"VANILLA_RAG", "SCOPE_EVIDENCE", "PAPERAGENT_FULL"},
    "Q049": {"VANILLA_RAG"},
}
PARTIAL_SUPPORT_VARIANTS = {
    "Q006": {"VANILLA_RAG"},
    "Q026": {"VANILLA_RAG"},
    "Q041": {"SCOPE_EVIDENCE", "PAPERAGENT_FULL"},
}

# Under the earlier formal evaluation's answer-level rule, a citation passes
# when the cited page(s) support the output's central assertion. A missing C#
# ID fails. Q003 passes because its cited Results page explicitly says four,
# although the frozen abstract-based answer key says three.
FULL_CITATION_FAILURES = {"Q010", "Q017", "Q018"}


def main() -> None:
    with REVIEW.open(encoding="utf-8-sig", newline="") as file:
        rows = [r for r in csv.DictReader(file) if r["evidence_replay_matches"] == "True"]
    if len(rows) != 181:
        raise ValueError(f"Expected 181 exactly replayed rows, got {len(rows)}")
    details = []
    by_variant: dict[str, Counter] = {}
    valid_ref_count = 0
    total_ref_count = 0
    support_points = 0.0
    support_denominator = 0
    citation_pass = 0
    citation_denominator = 0
    for r in rows:
        qid, variant = r["question_id"], r["variant"]
        correct = int(qid not in WRONG_ALL and variant not in WRONG_VARIANTS.get(qid, set()))
        chunks = json.loads(r["evidence_chunks_json"])
        refs = re.findall(r"\[C(\d+)\]", r["answer_raw"])
        valid_refs = sum(1 <= int(ref) <= len(chunks) for ref in refs)
        total_ref_count += len(refs)
        valid_ref_count += valid_refs
        v = by_variant.setdefault(variant, Counter())
        v["rows"] += 1
        v["correct"] += correct
        support = None
        if r["question_type"] in {"normal", "scope"}:
            support = (
                0.0 if qid in NO_SUPPORT_ALL or variant in NO_SUPPORT_VARIANTS.get(qid, set())
                else 0.5 if qid in PARTIAL_SUPPORT_ALL or variant in PARTIAL_SUPPORT_VARIANTS.get(qid, set())
                else 1.0
            )
            support_points += support
            support_denominator += 1
            v["support_points"] += support
            v["answerable_rows"] += 1
        citation = None
        if variant == "PAPERAGENT_FULL" and r["question_type"] in {"normal", "scope"} and refs:
            citation = int(qid not in FULL_CITATION_FAILURES and valid_refs == len(refs))
            citation_pass += citation
            citation_denominator += 1
        if r["question_type"] == "scope":
            # Manual inspection of all 36 exact scope answers found no assertions
            # sourced from another paper. This is distinct from retrieval contamination.
            v["scope_rows"] += 1
        details.append({
            "question_id": qid,
            "variant": variant,
            "question_type": r["question_type"],
            "core_correct_strict_gold": correct,
            "answer_level_claim_support_0_0_5_1": support,
            "scope_answer_leakage": 0 if r["question_type"] == "scope" else None,
            "full_citation_supports_core_0_1": citation,
            "citation_marker_count": len(refs),
            "citation_marker_valid_count": valid_refs,
            "review_note": NOTES.get(qid, ""),
        })
    full = [r for r in details if r["variant"] == "PAPERAGENT_FULL"]
    result = {
        "status": "partial_manual_review_not_formal_human_review_metrics",
        "denominator": len(rows),
        "core_answer_correct_strict_frozen_gold": [sum(r["core_correct_strict_gold"] for r in details), len(rows)],
        "q003_ambiguity_sensitivity_if_paper_body_accepted": [sum(r["core_correct_strict_gold"] for r in details) + 4, len(rows)],
        "scope_final_answer_leakage_exact_rows": [0, sum(r["question_type"] == "scope" for r in details)],
        "paperagent_full_scope_final_answer_leakage": [0, sum(r["question_type"] == "scope" for r in full)],
        "answer_level_claim_support_points": [support_points, support_denominator],
        "answer_level_claim_support_percentage": round(100 * support_points / support_denominator, 1),
        "full_citation_accuracy_given_citation": [citation_pass, citation_denominator],
        "citation_marker_validity_all_variants_not_semantic_accuracy": [valid_ref_count, total_ref_count],
        "citation_marker_validity_full_not_semantic_accuracy": [sum(r["citation_marker_valid_count"] for r in full), sum(r["citation_marker_count"] for r in full)],
        "by_variant": {k: dict(v) for k, v in sorted(by_variant.items())},
        "caveats": [
            "Single-reviewer judgments; these are not independent double-blind labels.",
            "Claim support is answer-level mean of 0/0.5/1 on 146 answerable exact-evidence rows; 35 unanswerable rows are excluded.",
            "Citation accuracy is answer-level support of the central assertion, conditional on a citation in the Full variant, matching the earlier formal evaluation's rule.",
            "Q003 has contradictory counts in the same source paper.",
            "Citation marker validity only tests that [C#] resolves to a retrieved chunk; it does not test factual support.",
            "The 19 rows with nondeterministic evidence replay are excluded from all figures here.",
        ],
    }
    (HERE / "metrics" / "partial_e1_review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with (HERE / "metrics" / "partial_e1_review_rows.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(details[0]))
        writer.writeheader()
        writer.writerows(details)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
