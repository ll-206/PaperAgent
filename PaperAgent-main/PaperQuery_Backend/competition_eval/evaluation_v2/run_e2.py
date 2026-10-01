"""E2: Open Planner versus the product's controlled Research runtime."""
from __future__ import annotations

import argparse
import asyncio
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import traceback
import uuid
from pathlib import Path

import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

HERE = Path(__file__).resolve().parent
EVAL = HERE.parent
BACKEND = EVAL.parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ["CHROMA_ONNX_CACHE_DIR"] = str(BACKEND.parents[1] / "artifacts" / "competition_eval" / "onnx_cache")
dotenv.load_dotenv()
os.environ["AcadeAgent_DIR"] = ""

from competition_eval.validate_dataset import validate
from core.backend.db.database import Base
from core.backend.db.models import Document, User
from core.decision.engine import DecisionEngine
from core.llm.LLM import LLM
from core.research.executor import Executor
from core.research.orchestrator import ResearchOrchestrator
from core.research.planner import Planner, _clean_json
from core.research.schemas import TaskPlan
from core.research.verifier import Verifier
from core.vectordb.chromadb import AcadeChroma
from main import ONNXEmbeddings, _build_skill_registry

VARIANTS = ("OPEN_PLANNER", "PAPERAGENT_CONTROLLED")


def evaluate_plan(plan: dict | None, registry) -> dict:
    if not plan or not isinstance(plan.get("steps"), list):
        return {"invalid_skill_count": 0, "invalid_dependency_count": 0, "plan_valid": False}
    names = set(registry.names())
    steps = plan["steps"]
    ids = [str(s.get("step_id")) for s in steps]
    invalid_skills = sum(str(s.get("skill")) not in names for s in steps)
    invalid_deps = 0
    for i, step in enumerate(steps):
        invalid_deps += sum(dep not in ids[:i] for dep in step.get("depends_on", []))
    return {
        "invalid_skill_count": invalid_skills,
        "invalid_dependency_count": invalid_deps,
        "plan_valid": bool(steps) and not invalid_skills and not invalid_deps and len(ids) == len(set(ids)),
    }


def open_plan(llm, goal: str, registry) -> tuple[dict, str]:
    prompt = (
        "You are an open research planner. Draft a useful plan for the goal. "
        "The following tools are available, but you may propose other actions if necessary. "
        "Return JSON only with goal (string), steps (array), expected_artifacts (array of strings). "
        "Each step has step_id (string), title (string), skill (string), "
        "depends_on (array of prior step IDs), input (JSON object), "
        "success_criteria (array of strings). "
        "Do not assume any plan validator will revise your output.\n"
        f"Available tools: {json.dumps(registry.describe(), ensure_ascii=False)}\nGoal: {goal}"
    )
    response = llm.invoke(prompt)
    raw = response.content if hasattr(response, "content") else str(response)
    data = json.loads(_clean_json(raw))
    data["task_id"] = uuid.uuid4().hex[:12]
    return data, raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--model", default="zhipu")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    check = validate()
    if not check["ready"]:
        raise SystemExit(f"Frozen dataset failed validation: {check['errors']}")
    tasks = list(csv.DictReader((EVAL / "datasets" / "research_tasks.csv").open(encoding="utf-8")))
    tasks = tasks[args.start - 1:args.start - 1 + args.limit]
    doc_map = json.loads((EVAL / "raw" / "document_map.json").read_text(encoding="utf-8"))
    index = EVAL / "raw" / "isolated_index"
    if not (index / "layer1" / "chroma.sqlite3").exists():
        raise SystemExit("Isolated Chroma index is missing")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        session.add(User(username="competition-eval", password="unused", lid="competition-eval"))
        for paper_id, document_id in doc_map.items():
            session.add(Document(uid=document_id, knowledgeID="competition-eval", lid="competition-eval",
                                 documentName=f"{paper_id}.pdf", documentPath=str(EVAL / "datasets" / "corpus" / f"{paper_id}.pdf")))
        session.commit()
    db = AcadeChroma(str(index / "layer1"), str(index / "layer2"), ONNXEmbeddings(), None)
    llm = LLM().get_llm(args.model).bind(temperature=0, max_tokens=4096)
    registry = _build_skill_registry()
    ctx = {"chroma_db": db, "llm": llm, "decision_engine": DecisionEngine(llm), "db_factory": Session}
    runner = ResearchOrchestrator(Planner(llm, registry), Executor(registry, ctx), Verifier())
    run_id = ("probe" if args.probe else "formal") + "-e2-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = HERE / "raw_results" / run_id
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "run_id": run_id, "status": "probe" if args.probe else "formal_raw_pending_artifact_review",
        "dataset_sha256": hashlib.sha256((EVAL / "datasets" / "research_tasks.csv").read_bytes()).hexdigest(),
        "model": args.model, "temperature": 0, "max_tokens": 4096,
        "task_count": len(tasks), "repeats": args.repeats, "variants": VARIANTS,
        "method": "Both variants receive same goal, local documents and tool descriptions. Open Planner has no product prompt restrictions or validation; invalid plans are recorded and never executed. Controlled uses the product Planner/Executor/Verifier. Artifact content and traceability need human review.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        with (output / "research_ablation.jsonl").open("w", encoding="utf-8") as file:
            for task in tasks:
                selected = [part.strip() for part in task["selected_docs"].split(";") if part.strip()]
                goal = task["goal"]
                for paper_id in sorted(selected, key=len, reverse=True):
                    goal = re.sub(rf"\b{paper_id}\b", f"{paper_id} (document_id: {doc_map[paper_id]})", goal)
                for repeat_id in range(1, args.repeats + 1):
                    for variant in VARIANTS:
                        started = time.perf_counter()
                        row = {
                            "run_id": run_id, "task_id": task["task_id"], "task_type": task["task_type"],
                            "variant": variant, "repeat_id": repeat_id, "goal": goal, "selected_docs": selected,
                            "allowed_skills": registry.names(), "expected_artifact": task["expected_artifact"],
                            "minimum_requirements": task["minimum_requirements"], "generated_plan": None,
                            "raw_plan_text": None, "steps": [], "artifacts": [], "error": None,
                            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        }
                        try:
                            run_ctx = {"allowed_document_ids": [doc_map[p] for p in selected]}
                            if variant == "OPEN_PLANNER":
                                plan_data, raw = open_plan(llm, goal, registry)
                                row["raw_plan_text"] = raw
                                plan = TaskPlan.model_validate(plan_data)
                                row["generated_plan"] = plan.model_dump(mode="json")
                                quality = evaluate_plan(row["generated_plan"], registry)
                                row.update(quality)
                                if quality["plan_valid"]:
                                    steps = asyncio.run(Executor(registry, ctx).run(plan, context=run_ctx))
                                    row["steps"] = [s.model_dump(mode="json") for s in steps]
                                    row["artifacts"] = [a for s in steps for a in s.output.get("artifacts", []) if isinstance(a, dict)]
                            else:
                                state = runner.run(goal, context=run_ctx)
                                row["generated_plan"] = state.plan.model_dump(mode="json")
                                row.update(evaluate_plan(row["generated_plan"], registry))
                                row["steps"] = [s.model_dump(mode="json") for s in state.step_results]
                                row["artifacts"] = state.artifacts
                                row["runtime_status"] = state.status
                        except Exception as exc:
                            row["error"] = f"{type(exc).__name__}: {str(exc)[:700]}"
                            row["traceback"] = traceback.format_exc(limit=3)
                        row.update(evaluate_plan(row["generated_plan"], registry))
                        expected = "research_report" if task["expected_artifact"] == "report" else task["expected_artifact"]
                        row["artifact_generated"] = bool(row["artifacts"])
                        row["expected_artifact_present"] = any(a.get("type") == expected for a in row["artifacts"])
                        row["execution_success"] = bool(row["steps"]) and all(s["status"] == "SUCCESS" for s in row["steps"])
                        row["task_success_by_minimal_rule"] = bool(row["plan_valid"] and row["execution_success"] and row["expected_artifact_present"])
                        row["source_traceability_review"] = None
                        row["minimum_requirements_review"] = None
                        row["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
                        file.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
                        file.flush()
                        print(task["task_id"], repeat_id, variant, "success=" + str(row["task_success_by_minimal_rule"]), row["error"] or "", flush=True)
                        if row["error"] and ("402" in row["error"] or "Insufficient Balance" in row["error"]):
                            manifest["status"] = "invalid_interrupted"
                            manifest["invalid_reason"] = row["error"]
                            (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
                            raise SystemExit("Model balance exhausted; stopped before further requests")
    finally:
        engine.dispose()
    print(output)


if __name__ == "__main__":
    main()
