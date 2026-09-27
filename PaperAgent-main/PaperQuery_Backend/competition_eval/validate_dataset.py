"""Validate frozen competition benchmark inputs before any formal scoring."""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
DATA = HERE / "datasets"
REQUIRED = {
    "paper_corpus.csv": {"paper_id", "cluster_id", "title", "pdf_path", "page_count", "text_extractable"},
    "qa_groundtruth.csv": {"question_id", "question_type", "query", "selected_doc", "gold_page", "gold_evidence", "answerable", "distractor_doc", "review_status"},
    "research_tasks.csv": {"task_id", "task_type", "goal", "selected_docs", "expected_artifact", "minimum_requirements"},
    "security_cases.csv": {"case_id", "scenario", "expected_status"},
}
EXPECTED_QA = {"normal": 30, "unanswerable": 10, "scope": 10}
EXPECTED_RESEARCH = {"single": 3, "comparison": 4, "report": 3}


def read_csv(path: Path, required: set[str], errors: list[str]) -> list[dict]:
    if not path.exists():
        errors.append(f"Missing {path.name}")
        return []
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = required - set(reader.fieldnames or [])
        if missing:
            errors.append(f"{path.name} missing columns: {sorted(missing)}")
        return list(reader)


def split_ids(value: str) -> set[str]:
    return {part.strip() for part in (value or "").split(";") if part.strip()}


def normalize_pdf_text(value: str) -> str:
    """Normalize PDF typography and line-end hyphenation for literal evidence matching."""
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", value)
    return " ".join(value.casefold().split())


def validate() -> dict:
    errors: list[str] = []
    rows = {name: read_csv(DATA / name, fields, errors) for name, fields in REQUIRED.items()}
    papers = rows["paper_corpus.csv"]
    paper_ids = {row.get("paper_id", "") for row in papers}
    if len(papers) != 10 or len(paper_ids) != 10:
        errors.append(f"paper_corpus requires 10 unique papers; found {len(papers)} rows / {len(paper_ids)} IDs")
    cluster_counts = collections.Counter(row.get("cluster_id") for row in papers)
    if sorted(cluster_counts.values()) != [5, 5]:
        errors.append(f"paper_corpus requires 2 clusters of 5; found {dict(cluster_counts)}")
    for row in papers:
        rel = row.get("pdf_path", "")
        if not rel or not (HERE / rel).is_file():
            errors.append(f"PDF missing: {rel or '<blank>'}")
            continue
        path=HERE/rel
        if row.get("sha256") and hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            errors.append(f"{row.get('paper_id')}: PDF hash changed")
        with fitz.open(path) as pdf:
            if str(len(pdf)) != row.get("page_count") or row.get("text_extractable") != "1":
                errors.append(f"{row.get('paper_id')}: page count or text extraction invalid")

    qa = rows["qa_groundtruth.csv"]
    qa_counts = collections.Counter(row.get("question_type") for row in qa)
    if dict(qa_counts) != EXPECTED_QA:
        errors.append(f"QA counts must be {EXPECTED_QA}; found {dict(qa_counts)}")
    question_ids = [row.get("question_id", "") for row in qa]
    if len(set(question_ids)) != len(question_ids) or not all(question_ids):
        errors.append("QA question_id values must be unique and nonblank")
    for qtype, per_paper in (("normal",3),("unanswerable",1),("scope",1)):
        counts=collections.Counter(row.get("selected_doc") for row in qa if row.get("question_type")==qtype)
        if any(counts.get(paper_id,0)!=per_paper for paper_id in paper_ids):
            errors.append(f"{qtype}: expected {per_paper} questions per paper; found {dict(counts)}")
    for row in qa:
        qid = row.get("question_id", "<blank>")
        selected = row.get("selected_doc", "")
        if selected not in paper_ids:
            errors.append(f"{qid}: selected_doc outside corpus")
        if row.get("review_status") != "human_verified":
            errors.append(f"{qid}: independent human evidence review pending")
        qtype = row.get("question_type")
        if qtype in ("normal", "scope"):
            try:
                page = int(row.get("gold_page", ""))
                paper = next(p for p in papers if p.get("paper_id") == selected)
                with fitz.open(HERE / paper["pdf_path"]) as pdf:
                    raw_page_text = pdf[page-1].get_text()
                raw_evidence = row.get("gold_evidence", "")
                literal_page = " ".join(raw_page_text.casefold().split())
                literal_evidence = " ".join(raw_evidence.casefold().split())
                literal_match = bool(literal_evidence and literal_evidence in literal_page)
                normalized_evidence = normalize_pdf_text(raw_evidence)
                normalized_match = bool(normalized_evidence and normalized_evidence in normalize_pdf_text(raw_page_text))
                if not (literal_match or normalized_match):
                    errors.append(f"{qid}: gold_evidence absent from gold_page")
            except (ValueError, IndexError, StopIteration, RuntimeError, KeyError):
                errors.append(f"{qid}: invalid gold_page or PDF")
            if row.get("answerable") != "1":
                errors.append(f"{qid}: answerable must be 1")
        elif qtype == "unanswerable" and row.get("answerable") != "0":
            errors.append(f"{qid}: unanswerable item must have answerable=0")
        if qtype == "scope":
            distractor = row.get("distractor_doc", "")
            if distractor not in paper_ids or distractor == selected:
                errors.append(f"{qid}: invalid distractor_doc")
    research = rows["research_tasks.csv"]
    research_counts = collections.Counter(row.get("task_type") for row in research)
    if dict(research_counts) != EXPECTED_RESEARCH:
        errors.append(f"Research counts must be {EXPECTED_RESEARCH}; found {dict(research_counts)}")
    if len({row.get("task_id") for row in research}) != len(research):
        errors.append("Research task IDs must be unique")
    for row in research:
        selected=split_ids(row.get("selected_docs",""))
        if not selected or not selected <= paper_ids or not row.get("minimum_requirements"):
            errors.append(f"{row.get('task_id','<blank>')}: invalid selected documents or success criteria")
    if len(rows["security_cases.csv"]) != 4:
        errors.append(f"security_cases requires 4 cases; found {len(rows['security_cases.csv'])}")
    if {row.get("case_id") for row in rows["security_cases.csv"]} != {"SEC01","SEC02","SEC03","SEC04"}:
        errors.append("Security case IDs must be SEC01 through SEC04")
    return {"ready": not errors, "counts": {name: len(items) for name, items in rows.items()}, "errors": errors}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "reports" / "dataset_validation.json")
    args = parser.parse_args()
    result = validate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ready"] else 2)
