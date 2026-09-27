"""Four Ask boundary cases on two isolated accounts, with raw status records."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
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
dotenv.load_dotenv()
from core.backend.db.database import Base
from core.backend.db.models import Document, User
from core.backend.router.dependencies import get_db
from main import app

def main():
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine)
    with Session() as db:
        db.add_all([
            User(username="security-A",password="unused",lid="A"),
            User(username="security-B",password="unused",lid="B"),
            Document(uid="A-paper",knowledgeID="test",lid="A",documentName="a.pdf",documentPath="a.pdf"),
            Document(uid="B-paper",knowledgeID="test",lid="B",documentName="b.pdf",documentPath="b.pdf"),
        ])
        db.commit()
    def test_db():
        with Session() as db:
            yield db
    app.dependency_overrides[get_db]=test_db
    def token(minutes):
        return jwt.encode({"username":"security-A","exp":dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=minutes)},
                          os.environ["SECRET_KEY"],algorithm=os.environ["ALGORITHM"])
    client=TestClient(app)
    def post(auth,doc):
        return client.post("/qa/stream",headers={"Authorization":f"Bearer {auth}"} if auth else {},
                           json={"question":"hello","document_ids":[doc] if doc else []})
    rows=[]
    try:
        responses=[
            ("SEC01",[post(None,None)],[401]),
            ("SEC02",[post("invalid.jwt.token",None),post(token(-1),None)],[401,401]),
            ("SEC03",[post(token(10),"B-paper")],[403]),
            ("SEC04",[post(token(10),"A-paper")],[200]),
        ]
        for case_id,resps,expected in responses:
            actual=[response.status_code for response in resps]
            rows.append({"case_id":case_id,"expected":expected,"actual":actual,"pass":actual==expected})
    finally:
        app.dependency_overrides.clear()
        client.close()
        engine.dispose()
    output=HERE/"raw"/"security_boundary"
    output.mkdir(parents=True,exist_ok=True)
    (output/"security_runs.jsonl").write_text("".join(json.dumps(row)+"\n" for row in rows),encoding="utf-8")
    metrics={"passed":sum(row["pass"] for row in rows),"total":len(rows),"scope":"Ask JWT and document ownership; in-process two-account test"}
    (output/"metrics.json").write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(metrics,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
