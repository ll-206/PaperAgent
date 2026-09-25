"""V2 Ask Mode 可信问答路由。

流程：Intent → Retrieval → Evidence Judge → Answer → Grounding → SSE 分片输出。
旧 /chat/* 作为兼容接口保留，新前端走 /qa/stream。
"""
from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer

from core.backend.router.req_res_schema import QARequest
from core.decision.prompts import ANSWER_PROMPT
from core.evidence.formatter import build_citations, format_evidence

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
router = APIRouter()


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/qa/stream")
def qa_stream(qa: QARequest, request: Request, token: str = Depends(oauth2_scheme)):
    trace_id = uuid.uuid4().hex[:12]
    decision_engine = getattr(request.app, "decision_engine", None)
    pipeline = getattr(request.app, "retrieval_pipeline", None)
    chroma_db = getattr(request.app, "chroma_db", None)

    def generate():
        # 1. Intent 判断
        if decision_engine is not None:
            intent = decision_engine.decide_intent(qa.question, qa.conversation_context)
            yield _sse("meta", {"trace_id": trace_id, "route": "LOCAL_RAG", "intent": intent.intent.value})

        # 2. 检索
        evidence = []
        if pipeline is not None and qa.document_ids:
            evidence = pipeline.search(qa.question, qa.document_ids)
        elif chroma_db is not None and qa.document_ids:
            evidence = chroma_db.search_evidence(
                qa.question,
                {"documentID": {"$in": qa.document_ids}},
                k=8,
            )

        # 3. 证据格式化 + 引用映射
        evidence_text, citation_map = format_evidence(evidence)

        # 4. Evidence Judge
        if decision_engine is not None:
            ev = decision_engine.decide_evidence(qa.question, evidence_text)
            yield _sse("decision", {
                "decision": ev.decision,
                "evidence_score": ev.evidence_score,
                "confidence": ev.confidence,
            })
            if ev.decision in ("ABSTAIN", "SEARCH_EXTERNAL"):
                msg = "当前本地证据不足，无法可靠回答。"
                if ev.decision == "SEARCH_EXTERNAL":
                    msg += "建议通过外部学术搜索补充相关论文。"
                yield _sse("delta", {"text": msg})
                yield _sse("grounding", {"passed": False, "confidence": ev.confidence})
                return

        # 5. Answer 生成（带引用）
        agent = getattr(request.app, "chat_agents", {}).get(qa.model)
        answer = ""
        if agent is not None:
            prompt = ANSWER_PROMPT.format(question=qa.question, evidence=evidence_text)
            resp = agent.get_llm().invoke(prompt)
            answer = resp.content if hasattr(resp, "content") else str(resp)

        # 6. Grounding Verify
        citations = build_citations(citation_map)
        if decision_engine is not None:
            from core.evidence.grounding import GroundingVerifier
            verifier = GroundingVerifier(decision_engine)
            grounding_passed, report = verifier.verify(
                qa.question, answer, citations, citation_map
            )
            yield _sse("grounding", {"passed": grounding_passed, "confidence": report["confidence"]})

        # 7. Citations
        yield _sse("citations", {
            "items": [
                {
                    "id": c.citation_id,
                    "documentID": c.document_id,
                    "knowledgeID": c.knowledge_id,
                    "page": c.page_number,
                    "chunk_id": c.chunk_id,
                }
                for c in citations
            ]
        })

        # 8. 分片输出答案（模拟流式）
        for i in range(0, len(answer), 3):
            yield _sse("delta", {"text": answer[i:i + 3]})

    return StreamingResponse(generate(), media_type="text/event-stream")
