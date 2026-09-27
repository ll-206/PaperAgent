"""Run the ten fixed research goals against an isolated corpus and record every step."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path

import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

HERE=Path(__file__).resolve().parent
BACKEND=HERE.parent
sys.path.insert(0,str(BACKEND))
os.chdir(BACKEND)
os.environ["CHROMA_ONNX_CACHE_DIR"]=str(BACKEND.parents[1]/"artifacts"/"competition_eval"/"onnx_cache")
dotenv.load_dotenv()
os.environ["AcadeAgent_DIR"]=""

from core.backend.db.database import Base
from core.backend.db.models import Document, User
from core.decision.engine import DecisionEngine
from core.llm.LLM import LLM
from core.research.executor import Executor
from core.research.orchestrator import ResearchOrchestrator
from core.research.planner import Planner
from core.research.verifier import Verifier
from core.vectordb.chromadb import AcadeChroma
from main import ONNXEmbeddings, _build_skill_registry

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--draft",action="store_true")
    parser.add_argument("--limit",type=int,default=10)
    args=parser.parse_args()
    if not args.draft:
        from validate_dataset import validate
        if not validate()["ready"]:
            raise SystemExit("Dataset review gate failed; use --draft only for diagnostic runs")
    doc_map=json.loads((HERE/"raw"/"document_map.json").read_text(encoding="utf-8"))
    tasks=list(csv.DictReader((HERE/"datasets"/"research_tasks.csv").open(encoding="utf-8")))[:args.limit]
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine)
    with Session() as db:
        db.add(User(username="competition-eval",password="unused",lid="competition-eval"))
        for paper_id,doc_id in doc_map.items():
            db.add(Document(uid=doc_id,knowledgeID="competition-eval",lid="competition-eval",
                            documentName=f"{paper_id}.pdf",documentPath=str(HERE/"datasets"/"corpus"/f"{paper_id}.pdf")))
        db.commit()
    index=HERE/"raw"/"isolated_index"
    db=AcadeChroma(str(index/"layer1"),str(index/"layer2"),ONNXEmbeddings(),None)
    llm=LLM().get_llm("deepseek")
    registry=_build_skill_registry()
    ctx={"chroma_db":db,"llm":llm,"decision_engine":DecisionEngine(llm),"db_factory":Session}
    runner=ResearchOrchestrator(Planner(llm,registry),Executor(registry,ctx),Verifier())
    run_id=("draft" if args.draft else "formal")+"-research-"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output=HERE/"raw"/run_id
    output.mkdir(parents=True,exist_ok=False)
    rows=[]
    try:
        for task in tasks:
            selected=[x.strip() for x in task["selected_docs"].split(";") if x.strip()]
            goal=task["goal"]
            for paper_id in sorted(selected,key=len,reverse=True):
                goal=re.sub(rf"\b{paper_id}\b",f"{paper_id} (document_id: {doc_map[paper_id]})",goal)
            start=time.perf_counter()
            try:
                state=runner.run(goal,context={"allowed_document_ids":[doc_map[x] for x in selected]})
                plan=state.plan.model_dump(mode="json")
                steps=[step.model_dump(mode="json") for step in state.step_results]
                artifacts=state.artifacts
                valid_skills=all(step["skill"] in registry.names() for step in plan["steps"])
                all_steps=bool(steps) and all(step["status"]=="SUCCESS" for step in steps)
                needed="research_report" if task["expected_artifact"]=="report" else task["expected_artifact"]
                artifact_present=any(a.get("type")==needed for a in artifacts)
                success=valid_skills and all_steps and artifact_present
                error=None
                status=state.status
            except Exception as exc:
                plan=None;steps=[];artifacts=[];valid_skills=False;all_steps=False;artifact_present=False;success=False
                status="ERROR";error=f"{type(exc).__name__}: {str(exc)[:800]}"
            row={"run_id":run_id,"task_id":task["task_id"],"task_type":task["task_type"],"selected_docs":selected,
                 "goal_sent":goal,"plan":plan,"steps":steps,"artifacts":artifacts,"runtime_status":status,
                 "valid_skills":valid_skills,"all_steps_success":all_steps,"expected_artifact_present":artifact_present,
                 "success_by_minimal_rule":success,"duration_ms":round((time.perf_counter()-start)*1000,2),"error":error}
            rows.append(row)
            with (output/"research_runs.jsonl").open("a",encoding="utf-8") as file:
                file.write(json.dumps(row,ensure_ascii=False,default=str)+"\n")
            print(task["task_id"],status,"success="+str(success),round(row["duration_ms"]),error or "",flush=True)
    finally:
        engine.dispose()
    metrics={"run_id":run_id,"status":"draft_not_competition_result" if args.draft else "formal",
             "tasks_attempted":len(rows),"success_count":sum(r["success_by_minimal_rule"] for r in rows),
             "definition":"registered skills + all steps success + expected artifact type present; content quality requires review"}
    (output/"metrics.json").write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(metrics,ensure_ascii=False,indent=2))
    print(output)

if __name__=="__main__":
    main()
