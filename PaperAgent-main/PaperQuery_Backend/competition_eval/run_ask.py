"""Record Ask SSE output on the isolated ten-paper corpus; never auto-score citations."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
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

HERE=Path(__file__).resolve().parent
BACKEND=HERE.parent
sys.path.insert(0,str(BACKEND))
os.chdir(BACKEND)
os.environ["CHROMA_ONNX_CACHE_DIR"]=str(BACKEND.parents[1]/"artifacts"/"competition_eval"/"onnx_cache")
dotenv.load_dotenv()

from core.backend.db.database import Base
from core.backend.db.models import Document, User
from core.backend.router.dependencies import get_db
from core.vectordb.chromadb import AcadeChroma
from main import ONNXEmbeddings, app

def parse_sse(text):
    events=[]
    for block in text.split("\n\n"):
        if not block.strip():
            continue
        name="message"
        data=[]
        for line in block.splitlines():
            if line.startswith("event:"):
                name=line[6:].strip()
            elif line.startswith("data:"):
                data.append(line[5:].strip())
        if data:
            try:
                events.append({"event":name,"data":json.loads("\n".join(data))})
            except json.JSONDecodeError:
                events.append({"event":name,"data_raw":"\n".join(data)})
    return events

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--draft",action="store_true")
    parser.add_argument("--limit",type=int,default=50)
    parser.add_argument("--start",type=int,default=1,help="One-based first question for an exact retry")
    parser.add_argument("--model",default="deepseek")
    args=parser.parse_args()
    if not args.draft:
        from validate_dataset import validate
        if not validate()["ready"]:
            raise SystemExit("Dataset review gate failed; use --draft only for diagnostic runs")
    doc_map=json.loads((HERE/"raw"/"document_map.json").read_text(encoding="utf-8"))
    questions=list(csv.DictReader((HERE/"datasets"/"qa_groundtruth.csv").open(encoding="utf-8-sig")))[args.start-1:args.start-1+args.limit]
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine)
    with Session() as db:
        db.add(User(username="competition-eval",password="unused",lid="competition-eval"))
        for paper_id,doc_id in doc_map.items():
            db.add(Document(uid=doc_id,knowledgeID="competition-eval",lid="competition-eval",
                            documentName=f"{paper_id}.pdf",documentPath=f"competition_eval/datasets/corpus/{paper_id}.pdf"))
        db.commit()
    def get_test_db():
        with Session() as db:
            yield db
    app.dependency_overrides[get_db]=get_test_db
    token=jwt.encode({"username":"competition-eval","exp":dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=4)},
                     os.environ["SECRET_KEY"],algorithm=os.environ["ALGORITHM"])
    index=HERE/"raw"/"isolated_index"
    run_id=("draft" if args.draft else "formal")+"-ask-"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output=HERE/"raw"/run_id
    output.mkdir(parents=True,exist_ok=False)
    raw=output/"ask_runs.jsonl"
    try:
        with TestClient(app) as client:
            app.chroma_db=AcadeChroma(str(index/"layer1"),str(index/"layer2"),ONNXEmbeddings(),None)
            with raw.open("w",encoding="utf-8") as file:
                for q in questions:
                    started=time.perf_counter()
                    try:
                        response=client.post("/qa/stream",headers={"Authorization":f"Bearer {token}"},
                                             json={"question":q["query"],"document_ids":[doc_map[q["selected_doc"]]],"model":args.model})
                        events=parse_sse(response.text)
                        error=None if response.status_code==200 else response.text[:500]
                        answer="".join(e.get("data",{}).get("text","") for e in events if e["event"]=="delta")
                        citations=next((e["data"].get("items",[]) for e in events if e["event"]=="citations"),[])
                        decision=next((e["data"].get("decision") for e in events if e["event"]=="decision"),None)
                        route=next((e["data"].get("route") for e in events if e["event"]=="meta"),None)
                    except Exception as exc:
                        response=None; events=[]; answer=""; citations=[]; decision=None; route=None
                        error=f"{type(exc).__name__}: {str(exc)[:500]}\n{traceback.format_exc()}"
                    row={"run_id":run_id,"question_id":q["question_id"],"question_type":q["question_type"],
                         "selected_doc":q["selected_doc"],"model":args.model,"http_status":response.status_code if response else None,
                         "route":route,"decision":decision,"answer_raw":answer,"citations":citations,"events":events,
                         "total_ms":round((time.perf_counter()-started)*1000,2),"error":error}
                    file.write(json.dumps(row,ensure_ascii=False)+"\n")
                    file.flush()
                    print(q["question_id"],row["http_status"],decision,len(citations),round(row["total_ms"]),error or "",flush=True)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
    print(output)

if __name__=="__main__":
    main()
