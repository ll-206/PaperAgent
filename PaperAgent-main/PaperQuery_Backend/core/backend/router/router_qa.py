"""V2 Ask Mode 可信问答路由。

流程：Intent → Retrieval → Evidence Judge → Answer → Grounding → SSE 分片输出。
旧 /chat/* 作为兼容接口保留，新前端走 /qa/stream。
"""
from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.backend.db.models import ActivityEvent, Document, TMPDocument
from core.backend.router.dependencies import get_db
from core.backend.utils.utils import get_current_user
from core.backend.router.req_res_schema import QARequest
from core.decision.engine import DecisionEngine
from core.decision.external_search import (
    classify_external_request,
    make_research_prompt,
    make_search_keywords,
    normalize_papers,
)
from core.decision.prompts import ANSWER_PROMPT, GENERAL_CHAT_PROMPT
from core.decision.schemas import EvidenceDecision, IntentType
from core.evidence.formatter import build_citations, format_evidence
from core.skills.paper_search import PaperSearchSkill

router = APIRouter()


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _stream_model_text(agent, prompt: str):
    """统一提取 LangChain 流式消息中的文本 token。"""
    stream = (
        agent.chat_simple(prompt)
        if hasattr(agent, "chat_simple")
        else agent.get_llm().stream(prompt)
    )
    for chunk in stream:
        content = chunk.content if hasattr(chunk, "content") else str(chunk)
        if isinstance(content, str) and content:
            yield content


@router.post("/qa/stream")
def qa_stream(
    qa: QARequest,
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if qa.document_ids:
        selected_ids = set(qa.document_ids)
        owned_ids = {
            row.uid for row in db.query(Document.uid).filter(
                Document.lid == user.lid, Document.uid.in_(selected_ids)
            ).all()
        }
        owned_ids.update(
            row.uid for row in db.query(TMPDocument.uid).filter(
                TMPDocument.lid == user.lid, TMPDocument.uid.in_(selected_ids)
            ).all()
        )
        if not selected_ids.issubset(owned_ids):
            raise HTTPException(status_code=403, detail="部分论文不在当前账号的资料库中")

    # Count submitted Ask requests for this account. The event contains no question text.
    db.add(ActivityEvent(lid=user.lid, event_type="ask"))
    db.commit()

    trace_id = uuid.uuid4().hex[:12]
    agent = getattr(request.app, "chat_agents", {}).get(qa.model)
    if agent is None:
        agent = getattr(request.app, "chat_agents", {}).get("deepseek")
    decision_engine = (
        DecisionEngine(agent.get_llm())
        if agent is not None
        else getattr(request.app, "decision_engine", None)
    )
    chroma_db = getattr(request.app, "chroma_db", None)

    def generate():
        # 1. Intent 判断
        external_kind = classify_external_request(qa.question)
        intent = None
        if external_kind:
            yield _sse("meta", {
                "trace_id": trace_id,
                "route": "EXTERNAL_RESEARCH",
                "intent": IntentType.RESEARCH_TASK.value,
            })
        elif decision_engine is not None:
            intent = decision_engine.decide_intent(qa.question, qa.conversation_context)
            route = "GENERAL_CHAT" if intent.intent == IntentType.GENERAL_CHAT else "LOCAL_RAG"
            yield _sse("meta", {
                "trace_id": trace_id,
                "route": route,
                "intent": intent.intent.value,
            })

        # 普通聊天不需要论文证据，直接交给当前模型自然回答。
        if intent is not None and intent.intent == IntentType.GENERAL_CHAT:
            fallback_answer = "你好！很高兴见到你。你现在想查询、阅读或研究哪篇论文呢？"
            if agent is not None:
                prompt = GENERAL_CHAT_PROMPT.format(
                    question=qa.question,
                    conversation_context=qa.conversation_context or "（暂无）",
                )
            yield _sse("decision", {
                "decision": "GENERAL_CHAT",
                "evidence_score": 1.0,
                "confidence": intent.confidence,
            })
            streamed = False
            if agent is not None:
                try:
                    for text in _stream_model_text(agent, prompt):
                        streamed = True
                        yield _sse("delta", {"text": text})
                except Exception:
                    # 模型暂时不可用时仍给出友好的问候，不回退到证据不足提示。
                    pass
            if not streamed:
                yield _sse("delta", {"text": fallback_answer})
            yield _sse("grounding", {
                "passed": True,
                "confidence": 1.0,
                "skipped": True,
                "reason": "GENERAL_CHAT",
            })
            yield _sse("citations", {"items": []})
            return

        # 2. 检索
        evidence = []
        if chroma_db is not None and qa.document_ids:
            evidence = chroma_db.search_evidence(
                qa.question,
                {"documentID": {"$in": qa.document_ids}},
                k=8,
            )

        # 3. 证据格式化 + 引用映射
        evidence_text, citation_map = format_evidence(evidence)

        # 4. Evidence Judge
        if decision_engine is not None:
            ev = (
                EvidenceDecision(decision="SEARCH_EXTERNAL", confidence=1.0, evidence_score=0.0)
                if external_kind
                else decision_engine.decide_evidence(qa.question, evidence_text)
            )
            search_external = ev.decision == "SEARCH_EXTERNAL"
            yield _sse("decision", {
                "decision": "SEARCH_EXTERNAL" if search_external else ev.decision,
                "evidence_score": ev.evidence_score,
                "confidence": ev.confidence,
            })
            if search_external:
                yield _sse("search_status", {"state": "preparing", "text": "正在结合所选论文和目标领域提取检索词…"})
                keywords = (
                    make_search_keywords(
                        decision_engine.llm,
                        qa.question,
                        evidence_text,
                        kind=external_kind or "literature",
                    )
                    if not ev.search_keywords
                    else ev.search_keywords[:3]
                )
                yield _sse("search_status", {
                    "state": "searching",
                    "text": "正在检索 arXiv / OpenAlex：" + "、".join(keywords),
                })
                result = asyncio.run(PaperSearchSkill().run(
                    {"keywords": keywords, "max_results": 8}
                ))
                papers = normalize_papers(result.output.get("papers", [])) if result.ok else []
                yield _sse("external_papers", {
                    "items": papers,
                    "keywords": keywords,
                    "provider": result.output.get("provider", "") if result.ok else "",
                    "warning": result.output.get("warning", "") if result.ok else result.error_message,
                })
                if papers:
                    yield _sse("search_status", {
                        "state": "answering",
                        "text": f"从 {result.output.get('provider', '学术来源')} 找到 {len(papers)} 篇论文，正在对照摘要整理建议…",
                    })
                    if agent is not None:
                        prompt = make_research_prompt(
                            qa.question, evidence_text, papers, kind=external_kind or "literature"
                        )
                        try:
                            for text in _stream_model_text(agent, prompt):
                                yield _sse("delta", {"text": text})
                        except Exception:
                            yield _sse("delta", {"text": "已找到相关论文，请先查看下方题目和摘要，再选择需要核查的 PDF。"})
                    else:
                        yield _sse("delta", {"text": "已找到相关论文，请查看下方结果并选择需要进一步阅读的 PDF。"})
                else:
                    yield _sse("delta", {"text": "已尝试外部学术搜索，但目前未取得可展示的论文结果。请调整研究领域或关键词后重试。"})
                yield _sse("search_status", {"state": "done", "text": "外部学术检索已完成"})
                yield _sse("grounding", {"passed": False, "confidence": ev.confidence, "reason": "EXTERNAL_METADATA_ONLY"})
                yield _sse("citations", {
                    "items": [
                        {
                            "id": c.citation_id,
                            "documentID": c.document_id,
                            "knowledgeID": c.knowledge_id,
                            "page": c.page_number,
                            "chunk_id": c.chunk_id,
                        }
                        for c in build_citations(citation_map)
                    ]
                })
                return
            if ev.decision == "ABSTAIN":
                yield _sse("delta", {"text": "当前所选论文没有足够证据回答该问题。"})
                yield _sse("grounding", {"passed": False, "confidence": ev.confidence})
                return

        # 5. Answer 生成（带引用）
        answer = ""
        if agent is not None:
            prompt = ANSWER_PROMPT.format(question=qa.question, evidence=evidence_text)
            for text in _stream_model_text(agent, prompt):
                answer += text
                yield _sse("delta", {"text": text})

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

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
