"""运行状态与无副作用测试接口。"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.backend.router.dependencies import get_db
from core.backend.router.router_user import get_current_user

router = APIRouter()


class EchoRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


def component_status(app) -> dict:
    llm_manager = getattr(app, "llm", None)
    configured_models = (
        sorted(llm_manager.get_all_llms().keys())
        if llm_manager is not None
        else []
    )
    return {
        "database": False,  # 由 ready 端点执行真实 SQL 后覆盖
        "deepseek": "deepseek" in configured_models,
        "kimi": "kimi" in configured_models,
        "zhipu": "zhipu" in configured_models,
        "vector_database": getattr(app, "chroma_db", None) is not None,
        "hybrid_retrieval": getattr(app, "retrieval_pipeline", None) is not None,
        "research": getattr(app, "research_orchestrator", None) is not None,
    }


@router.get("/health/live", summary="进程存活检查")
def health_live():
    return {
        "status": "ok",
        "service": "paperagent-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready", summary="依赖就绪检查")
def health_ready(request: Request, db: Session = Depends(get_db)):
    components = component_status(request.app)
    try:
        db.execute(text("SELECT 1"))
        components["database"] = True
    except Exception:
        components["database"] = False

    required = ("database", "deepseek", "vector_database", "research")
    is_ready = all(components[name] for name in required)
    payload = {
        "status": "ready" if is_ready else "not_ready",
        "components": components,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(payload, status_code=200 if is_ready else 503)


@router.get("/test/capabilities", summary="读取当前测试能力")
def test_capabilities(request: Request, _user=Depends(get_current_user)):
    components = component_status(request.app)
    return {
        "status_code": 200,
        "data": {
            "models": [
                name for name in ("deepseek", "kimi", "zhipu")
                if components.get(name)
            ],
            "features": {
                "ask_sse": True,
                "library": components["vector_database"],
                "research": components["research"],
                "hybrid_retrieval": components["hybrid_retrieval"],
                "session_history": True,
            },
            "test_endpoints": [
                "GET /health/live",
                "GET /health/ready",
                "GET /test/capabilities",
                "POST /test/echo",
                "GET /test/sse",
            ],
        },
    }


@router.post("/test/echo", summary="认证与 JSON 往返测试")
def test_echo(payload: EchoRequest, _user=Depends(get_current_user)):
    return {
        "status_code": 200,
        "data": {"message": payload.message, "length": len(payload.message)},
    }


@router.get("/test/sse", summary="不调用模型的 SSE 连通性测试")
def test_sse(_user=Depends(get_current_user)):
    def generate():
        events = (
            ("meta", {"route": "TEST", "stream": True}),
            ("delta", {"text": "Paper"}),
            ("delta", {"text": "Agent"}),
            ("done", {"ok": True}),
        )
        for event, data in events:
            yield f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )
