"""E3: scripted, isolated API workflow replay for context continuity.

The harness follows the current frontend contract: Ask submits selected IDs and
conversation memory; ResearchView creates a task with document_ids=[]; a next
round passes parent_task_id. It reports observed links and modeled re-entry
operations separately. It does not claim a human usability study.
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
import jwt
from fastapi.testclient import TestClient
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

from competition_eval.run_ask import parse_sse
from competition_eval.validate_dataset import validate
from core.backend.db.database import Base
from core.backend.db.models import Document, User
from core.backend.router.dependencies import get_db
from core.decision.engine import DecisionEngine
from core.llm.LLM import LLM
from core.research.executor import Executor
from core.research.orchestrator import ResearchOrchestrator
from core.research.planner import Planner
from core.research.verifier import Verifier
from core.vectordb.chromadb import AcadeChroma
from main import ONNXEmbeddings, _build_skill_registry, app


class EvalAgent:
    def __init__(self, llm):
        self.llm = llm

    def get_llm(self):
        return self.llm

    def chat_simple(self, prompt):
        return self.llm.stream(prompt)


class EvalProvider:
    def __init__(self, llm):
        self.llm = llm

    def get_stream_llm(self, model_name):
        return self.llm


def ask(client, headers, question, ids, memory, model):
    started = time.perf_counter()
    resp = client.post("/qa/stream", headers=headers, json={
        "question": question, "document_ids": ids,
        "conversation_context": memory, "model": model,
    })
    events = parse_sse(resp.text) if resp.status_code == 200 else []
    answer = "".join(e.get("data", {}).get("text", "") for e in events if e["event"] == "delta")
    return {
        "http_status": resp.status_code, "answer": answer,
        "route": next((e.get("data", {}).get("route") for e in events if e["event"] == "meta"), None),
        "decision": next((e.get("data", {}).get("decision") for e in events if e["event"] == "decision"), None),
        "citations": next((e.get("data", {}).get("items", []) for e in events if e["event"] == "citations"), []),
        "duration_sec": round(time.perf_counter() - started, 2),
        "error": None if resp.status_code == 200 else resp.text[:500],
    }


def research(client, headers, goal, parent_id=None):
    started = time.perf_counter()
    # ResearchView currently sends an empty selected-document list.
    resp = client.post("/research/tasks", headers=headers, json={
        "goal": goal, "mode": "research", "document_ids": [], "parent_task_id": parent_id,
    })
    data = resp.json() if resp.status_code == 200 else {}
    task_id = data.get("data", {}).get("task_id")
    detail = client.get(f"/research/tasks/{task_id}", headers=headers).json().get("data", {}) if task_id else {}
    return {
        "http_status": resp.status_code, "task_id": task_id,
        "parent_task_id": detail.get("parent_task_id"), "status": detail.get("status"),
        "plan": detail.get("plan"), "steps": detail.get("steps", []),
        "artifacts": detail.get("artifacts", []),
        "duration_sec": round(time.perf_counter() - started, 2),
        "error": None if resp.status_code == 200 else resp.text[:500],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--model", default="zhipu")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    check = validate()
    if not check["ready"]:
        raise SystemExit(f"Frozen corpus failed validation: {check['errors']}")
    sessions = list(csv.DictReader((HERE / "continuity_sessions.csv").open(encoding="utf-8")))
    sessions = sessions[args.start - 1:args.start - 1 + args.limit]
    doc_map = json.loads((EVAL / "raw" / "document_map.json").read_text(encoding="utf-8"))
    index = EVAL / "raw" / "isolated_index"
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        db.add(User(username="competition-eval", password="unused", lid="competition-eval"))
        for paper_id, doc_id in doc_map.items():
            db.add(Document(uid=doc_id, knowledgeID="competition-eval", lid="competition-eval",
                            documentName=f"{paper_id}.pdf", documentPath=str(EVAL / "datasets" / "corpus" / f"{paper_id}.pdf")))
        db.commit()

    def get_test_db():
        with Session() as db:
            yield db

    token = jwt.encode({
        "username": "competition-eval",
        "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=12),
    }, os.environ["SECRET_KEY"], algorithm=os.environ["ALGORITHM"])
    headers = {"Authorization": f"Bearer {token}"}
    llm = LLM().get_llm(args.model).bind(temperature=0, max_tokens=4096)
    registry = _build_skill_registry()
    chroma = AcadeChroma(str(index / "layer1"), str(index / "layer2"), ONNXEmbeddings(), None)
    research_ctx = {"chroma_db": chroma, "llm": llm, "decision_engine": DecisionEngine(llm), "db_factory": Session}
    orchestrator = ResearchOrchestrator(Planner(llm, registry), Executor(registry, research_ctx), Verifier())
    run_id = ("probe" if args.probe else "formal") + "-e3-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = HERE / "raw_results" / run_id
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "run_id": run_id, "status": "probe" if args.probe else "formal_raw_pending_content_review",
        "sessions_sha256": hashlib.sha256((HERE / "continuity_sessions.csv").read_bytes()).hexdigest(),
        "model": args.model, "temperature": 0, "max_tokens": 4096,
        "sessions": len(sessions), "conditions": ["STATELESS", "PAPERAGENT_WORKSPACE"],
        "method": "Isolated TestClient API replay. Research step follows current ResearchView document_ids=[]; continuation uses parent_task_id in workspace. Re-entry counts are scripted operations, not timed human actions. QA memory is sent by client, but local-RAG prompt may not consume it.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    app.dependency_overrides[get_db] = get_test_db
    try:
        with TestClient(app) as client:
            app.chroma_db = chroma
            app.chat_agents = {args.model: EvalAgent(llm)}
            app.decision_engine = DecisionEngine(llm)
            app.research_orchestrator = orchestrator
            app.llm = EvalProvider(llm)
            with (output / "continuity_runs.jsonl").open("w", encoding="utf-8") as file:
                for spec in sessions:
                    selected = spec["selected_docs"].split(";")
                    ids = [doc_map[p] for p in selected]
                    for condition in ("STATELESS", "PAPERAGENT_WORKSPACE"):
                        started = time.perf_counter()
                        row = {"run_id": run_id, "session_id": spec["session_id"], "condition": condition,
                               "selected_docs": selected, "steps": [], "error": None,
                               "timestamp": dt.datetime.now(dt.timezone.utc).isoformat()}
                        try:
                            first = ask(client, headers, spec["first_question"], ids[:1], "", args.model)
                            row["steps"].append({"step_id": 1, "type": "ask", **first})
                            if condition == "STATELESS":
                                followup_question = spec["followup_question"] + "\nEarlier answer supplied again: " + first["answer"][:700]
                                memory = ""
                            else:
                                followup_question = spec["followup_question"]
                                memory = f"User: {spec['first_question']}\nAssistant: {first['answer'][:700]}"
                            second = ask(client, headers, followup_question, ids, memory, args.model)
                            row["steps"].append({"step_id": 2, "type": "ask", "memory_submitted": bool(memory), **second})
                            document_hints = "; ".join(f"{paper_id} has local document_id {doc_map[paper_id]}" for paper_id in selected)
                            goal = (
                                spec["research_goal"] + f" Use only {', '.join(selected)}. "
                                f"These papers already exist in the local library: {document_hints}. "
                                "Read those local document IDs directly; do not search externally."
                            )
                            third = research(client, headers, goal)
                            row["steps"].append({"step_id": 3, "type": "research", "selected_scope_submitted": [], **third})
                            if condition == "STATELESS":
                                prior = " ".join(str(a.get("data", {}).get("markdown") or a.get("data", {}).get("report") or a.get("title") or "")[:400] for a in third["artifacts"][:2])
                                next_goal = spec["next_goal"] + " Produce a short source-linked research report.\nPrevious result manually supplied: " + prior[:800]
                                parent_id = None
                            else:
                                next_goal = spec["next_goal"] + " Produce a short source-linked research report from the prior artifact."
                                parent_id = third["task_id"]
                            fourth = research(client, headers, next_goal, parent_id=parent_id)
                            row["steps"].append({"step_id": 4, "type": "research", "selected_scope_submitted": [], **fourth})
                            row["task_preserved"] = bool(parent_id and fourth["parent_task_id"] == parent_id)
                            row["artifact_reused_by_parent_link"] = bool(row["task_preserved"] and third["artifacts"])
                            row["selected_docs_preserved_into_research"] = False
                            row["evidence_preserved_into_research"] = False
                            row["manual_reentry_count"] = 4 if condition == "STATELESS" else 1
                            row["session_success_by_minimal_rule"] = (
                                first["http_status"] == second["http_status"] == 200
                                and bool(first["answer"]) and bool(second["answer"])
                                and third["status"] == fourth["status"] == "SUCCESS"
                                and bool(third["artifacts"]) and bool(fourth["artifacts"])
                            )
                        except Exception as exc:
                            row["error"] = f"{type(exc).__name__}: {str(exc)[:700]}"
                            row["traceback"] = traceback.format_exc(limit=3)
                            row["session_success_by_minimal_rule"] = False
                        row["duration_sec"] = round(time.perf_counter() - started, 2)
                        file.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
                        file.flush()
                        print(spec["session_id"], condition, "success=" + str(row["session_success_by_minimal_rule"]), row["error"] or "", flush=True)
                        if row["error"] and ("402" in row["error"] or "Insufficient Balance" in row["error"]):
                            manifest["status"] = "invalid_interrupted"
                            manifest["invalid_reason"] = row["error"]
                            (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
                            raise SystemExit("Model balance exhausted; stopped before further requests")
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
    print(output)


if __name__ == "__main__":
    main()
