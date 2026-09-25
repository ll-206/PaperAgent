"""V2 Research Mode 路由：创建/执行/查询科研任务并持久化。"""
from __future__ import annotations

import json
import os

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.backend.crud.crud_user import query_user
from core.backend.db.models import Artifact, ResearchStep, ResearchTask
from core.backend.utils.utils import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
router = APIRouter()


def _get_user(token: str, db: Session):
    """同步获取当前用户（供 sync 端点使用，避免 async 依赖注入）。"""
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        username = payload.get("username")
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    user = query_user(db, username=username)
    if user is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user


class ResearchTaskCreate(BaseModel):
    goal: str
    mode: str = "research"
    document_ids: list[str] = []


@router.post("/research/tasks")
def create_task(
    req: ResearchTaskCreate,
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    user = _get_user(token, db)
    orchestrator = getattr(request.app, "research_orchestrator", None)
    if orchestrator is None:
        return {"status_code": 503, "msg": "Research 编排组件未初始化"}

    state = orchestrator.run(req.goal)

    # 持久化任务
    task = ResearchTask(
        task_id=state.task_id,
        lid=user.lid,
        goal=req.goal,
        mode=req.mode,
        status=state.status,
        plan_json=state.plan.model_dump_json(),
    )
    db.add(task)

    # 持久化步骤
    for r in state.step_results:
        db.add(ResearchStep(
            step_id=r.step_id,
            task_id=state.task_id,
            skill_name=next((s.skill for s in state.plan.steps if s.step_id == r.step_id), ""),
            status=r.status,
            output_json=json.dumps(r.output, ensure_ascii=False),
            error=r.error,
            duration_ms=r.duration_ms,
        ))

    # 持久化 artifacts
    for a in state.artifacts:
        db.add(Artifact(
            artifact_id=a.get("artifact_id", ""),
            task_id=state.task_id,
            type=a.get("type", ""),
            title=a.get("title", ""),
            data_json=json.dumps(a, ensure_ascii=False),
        ))

    db.commit()
    return {
        "status_code": 200,
        "msg": "Research task created",
        "data": {"task_id": state.task_id, "status": state.status},
    }


@router.get("/research/tasks")
def list_tasks(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    user = _get_user(token, db)
    tasks = db.query(ResearchTask).filter(ResearchTask.lid == user.lid).all()
    return {
        "status_code": 200,
        "msg": "ok",
        "data": [
            {"task_id": t.task_id, "goal": t.goal, "status": t.status, "mode": t.mode}
            for t in tasks
        ],
    }


@router.get("/research/tasks/{task_id}")
def get_task(
    task_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    user = _get_user(token, db)
    task = db.query(ResearchTask).filter(
        ResearchTask.task_id == task_id, ResearchTask.lid == user.lid
    ).first()
    if task is None:
        return {"status_code": 404, "msg": "任务不存在"}
    steps = db.query(ResearchStep).filter(ResearchStep.task_id == task_id).all()
    artifacts = db.query(Artifact).filter(Artifact.task_id == task_id).all()
    return {
        "status_code": 200,
        "msg": "ok",
        "data": {
            "task_id": task.task_id,
            "goal": task.goal,
            "status": task.status,
            "plan": json.loads(task.plan_json) if task.plan_json else None,
            "steps": [
                {
                    "step_id": s.step_id,
                    "skill_name": s.skill_name,
                    "status": s.status,
                    "error": s.error,
                    "duration_ms": s.duration_ms,
                }
                for s in steps
            ],
            "artifacts": [
                {
                    "artifact_id": a.artifact_id,
                    "type": a.type,
                    "title": a.title,
                    "data": json.loads(a.data_json) if a.data_json else {},
                }
                for a in artifacts
            ],
        },
    }
