"""V2 Research Mode 路由：创建/执行/查询科研任务并持久化。"""
from __future__ import annotations

import json
import os
import uuid
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.backend.crud.crud_user import query_user
from core.backend.db.models import Artifact, Document, ResearchStep, ResearchTask
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
    document_ids: list[str] = Field(default_factory=list)
    parent_task_id: str | None = None


def _json_safe(value: Any) -> Any:
    """把 Skill/第三方库结果递归转换成可持久化的 JSON 数据。"""
    if isinstance(value, Enum):
        return _json_safe(value.value)
    if isinstance(value, BaseModel):
        return _json_safe(value.model_dump())
    if isinstance(value, dict):
        return {
            str(key.value if isinstance(key, Enum) else key): _json_safe(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    return value


def _json_dumps(value: Any) -> str:
    # default=str 是最后一道保护，避免某个新 Skill 返回第三方自定义对象时整项任务丢失。
    return json.dumps(_json_safe(value), ensure_ascii=False, default=str)


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

    owned_ids = {
        row.uid for row in db.query(Document.uid).filter(Document.lid == user.lid).all()
    }
    if req.document_ids and not set(req.document_ids).issubset(owned_ids):
        raise HTTPException(status_code=403, detail="部分论文不在当前账号的资料库中")
    allowed_ids = list(dict.fromkeys(req.document_ids)) if req.document_ids else list(owned_ids)

    parent = None
    prior_artifacts = []
    if req.parent_task_id:
        parent = db.query(ResearchTask).filter(ResearchTask.task_id == req.parent_task_id, ResearchTask.lid == user.lid).first()
        if parent is None:
            raise HTTPException(status_code=404, detail="上一轮研究任务不存在")
        prior_artifacts = [json.loads(item.data_json) for item in db.query(Artifact).filter(Artifact.task_id == parent.task_id).all() if item.data_json]
    prior_digest = "\n".join(f"- {item.get('title', '')}: {str(item.get('markdown') or item.get('report') or item.get('papers') or item.get('raw') or '')[:500]}" for item in prior_artifacts[:4])
    planning_goal = req.goal if not parent else f"{req.goal}\n\n上一轮研究目标：{parent.goal}\n上一轮结果：\n{prior_digest[:1800]}"

    try:
        state = orchestrator.run(planning_goal, context={"allowed_document_ids": allowed_ids, "parent_task_id": req.parent_task_id, "prior_artifacts": prior_artifacts})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Research 执行失败: {exc}") from exc

    # 持久化任务
    task = ResearchTask(
        task_id=state.task_id,
        lid=user.lid,
        goal=req.goal,
        mode=req.mode,
        parent_task_id=req.parent_task_id,
        status=state.status,
        plan_json=state.plan.model_dump_json(),
    )
    try:
        db.add(task)

        # 持久化步骤
        for r in state.step_results:
            db.add(ResearchStep(
                step_id=r.step_id,
                task_id=state.task_id,
                skill_name=next((s.skill for s in state.plan.steps if s.step_id == r.step_id), ""),
                status=r.status,
                output_json=_json_dumps(r.output),
                error=r.error,
                duration_ms=r.duration_ms,
            ))

        # 持久化 artifacts。Skill 可不指定 ID，由路由生成稳定的唯一 ID。
        for artifact in state.artifacts:
            safe_artifact = _json_safe(artifact)
            artifact_id = safe_artifact.get("artifact_id") or uuid.uuid4().hex
            safe_artifact["artifact_id"] = artifact_id
            db.add(Artifact(
                artifact_id=artifact_id,
                task_id=state.task_id,
                type=safe_artifact.get("type", ""),
                title=safe_artifact.get("title", ""),
                data_json=_json_dumps(safe_artifact),
            ))

        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Research 结果保存失败: {exc}") from exc
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
    tasks = (
        db.query(ResearchTask)
        .filter(ResearchTask.lid == user.lid)
        .order_by(ResearchTask.created_at.desc())
        .all()
    )
    return {
        "status_code": 200,
        "msg": "ok",
        "data": [
            {
                "task_id": t.task_id,
                "goal": t.goal,
                "status": t.status,
                "mode": t.mode,
                "parent_task_id": t.parent_task_id,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
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
            "parent_task_id": task.parent_task_id,
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
