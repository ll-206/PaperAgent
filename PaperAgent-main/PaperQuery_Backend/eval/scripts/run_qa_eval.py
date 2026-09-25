# -*- coding: utf-8 -*-
"""实验一 · 可信论文问答评测运行器。

在同一进程内分别驱动三套系统，对同一批问题作答并完整记录证据、决策与引用：
  - llm_only       ：不提供证据，直接问 LLM
  - basic_rag      ：旧 ONNX all-MiniLM 固定 Top-K 稠密检索（升级前 PaperQuery）
  - paperagent_full：Hybrid（BGE-M3+BM25→RRF→Reranker）+ Decision + Grounding + Citation

用法（在 PaperQuery_Backend 目录下）：
    python eval/scripts/run_qa_eval.py --system paperagent_full
    python eval/scripts/run_qa_eval.py --system basic_rag --limit 10
    python eval/scripts/run_qa_eval.py --system llm_only --config eval/configs/llm_only.yaml

输出：eval/results/<run_id>/{config.json, raw.jsonl, summary.csv, environment.json}
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ------------------------------ 环境与公共工具 ------------------------------
def _bootstrap() -> None:
    sys.path.insert(0, BACKEND_ROOT)
    os.chdir(BACKEND_ROOT)
    try:
        import dotenv
        dotenv.load_dotenv()
    except Exception:
        pass


def _load_yaml(path: str) -> dict:
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=BACKEND_ROOT,
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _llm_content(resp) -> str:
    return resp.content if hasattr(resp, "content") else str(resp)


def _evidence_to_dict(e) -> dict:
    return {
        "chunk_id": e.chunk_id,
        "document_id": e.document_id,
        "page": e.page_number,
        "text": e.text,
        "dense_score": e.dense_score,
        "sparse_score": e.sparse_score,
        "fusion_score": e.fusion_score,
        "rerank_score": e.rerank_score,
    }


# ------------------------------ 系统构建器 ------------------------------
class ONNXEmbeddings:
    """旧 Basic RAG 使用的 Chroma 内置 ONNX MiniLM 嵌入（与 main.py 保持一致）。"""

    def __init__(self):
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
        cache_dir = os.getenv("CHROMA_ONNX_CACHE_DIR")
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            ONNXMiniLM_L6_V2.DOWNLOAD_PATH = cache_dir
        self._ef = ONNXMiniLM_L6_V2()

    def embed_documents(self, texts):
        return self._ef(texts)

    def embed_query(self, text):
        return self._ef([text])[0]


def build_basic_retriever(cfg: dict):
    """旧 layer1（ONNX）固定 Top-K 检索器。"""
    from langchain_chroma import Chroma
    layer_dir = os.getenv(cfg["retrieval"].get("chroma_dir_env", "CHROMA_LAYER1_DIR"),
                          "./res/layer1")
    db = Chroma(persist_directory=layer_dir, embedding_function=ONNXEmbeddings())
    return db, int(cfg["retrieval"].get("top_k", 4))


def build_full_components():
    """PaperAgent Full：Hybrid Pipeline + DecisionEngine + GroundingVerifier。"""
    import pickle
    from langchain_chroma import Chroma
    from core.common.config import settings
    from core.decision.engine import DecisionEngine
    from core.llm.LLM import LLM
    from core.evidence.grounding import GroundingVerifier
    from core.retrieval.dense import BGE3Embeddings, DenseRetriever
    from core.retrieval.sparse import BM25Retriever
    from core.retrieval.reranker import BGEReranker
    from core.retrieval.pipeline import RetrievalPipeline

    llm = LLM()
    embedding = BGE3Embeddings(settings.BGE_M3_MODEL_PATH)
    chroma_v2 = Chroma(persist_directory=settings.CHROMA_LAYER1_V2_DIR,
                       embedding_function=embedding)
    with open(os.path.join(settings.BM25_INDEX_DIR, "corpus.pkl"), "rb") as f:
        corpus = pickle.load(f)
    pipeline = RetrievalPipeline(
        DenseRetriever(chroma_v2), BM25Retriever(corpus),
        BGEReranker(settings.RERANKER_MODEL_PATH), cfg=settings,
    )
    decision = DecisionEngine(llm.get_llm("deepseek"))
    grounding = GroundingVerifier(decision)
    return llm, pipeline, decision, grounding, settings


def _full_search(pipeline, query, doc_ids, final_k):
    """带可调 final_k 的 Hybrid 检索（供 Adaptive 扩检使用）。"""
    cfg = pipeline.cfg
    dense = pipeline.dense.search(query, doc_ids, cfg.DENSE_K)
    sparse = pipeline.sparse.search(query, doc_ids, cfg.SPARSE_K)
    from core.retrieval.fusion import reciprocal_rank_fusion
    fused = reciprocal_rank_fusion([dense, sparse], c=cfg.RRF_C)
    return pipeline.reranker.rerank(query, fused[:cfg.RERANK_CANDIDATES], final_k)


# ------------------------------ 三套系统作答 ------------------------------
def answer_llm_only(item, cfg, llm):
    t0 = time.time()
    resp = llm.get_llm(cfg.get("model", "deepseek")).invoke(
        cfg["answer"]["prompt_template"].format(question=item["question"])
    )
    return {
        "answer": _llm_content(resp), "abstained": False,
        "citations": [], "retrieved_evidence": [], "decision": {},
        "latency_ms": int((time.time() - t0) * 1000),
    }


def answer_basic_rag(item, cfg, llm, db, top_k):
    from core.retrieval.dense import build_document_filter
    from core.common.types import EvidenceChunk
    t0 = time.time()
    # 检索先行（本地 ONNX，不依赖外部 API），失败不阻断后续
    retrieved = []
    evidence_text = ""
    try:
        where = build_document_filter(item.get("document_ids"))
        docs_scores = db.similarity_search_with_score(
            item["question"], k=top_k, filter=where
        )
        evidence_text = "\n\n".join(
            f"[资料{i}] {d.page_content}" for i, (d, _s) in enumerate(docs_scores, 1)
        )
        for d, s in docs_scores:
            m = d.metadata or {}
            retrieved.append(_evidence_to_dict(EvidenceChunk(
                chunk_id=m.get("chunk_id", ""), document_id=m.get("documentID", ""),
                source="", page_number=int(m.get("page_number", 0) or 0),
                text=d.page_content, dense_score=float(s),
            )))
    except Exception as e:
        retrieval_error = str(e)
    else:
        retrieval_error = None

    # LLM 作答（外部 API，失败则留空并记录，检索证据仍保留）
    answer, llm_error = "", None
    try:
        prompt = cfg["answer"]["prompt_template"].format(
            evidence=evidence_text or "（无）", question=item["question"]
        )
        answer = _llm_content(llm.get_llm(cfg.get("model", "deepseek")).invoke(prompt))
    except Exception as e:
        llm_error = str(e)
    return {
        "answer": answer, "abstained": False,
        "citations": [], "retrieved_evidence": retrieved,
        "decision": {k: v for k, v in
                     {"retrieval_error": retrieval_error, "llm_error": llm_error}.items()
                     if v},
        "latency_ms": int((time.time() - t0) * 1000),
    }


def answer_paperagent_full(item, cfg, llm, pipeline, decision, grounding, settings):
    from core.evidence.formatter import build_citations, format_evidence
    t0 = time.time()
    doc_ids = item.get("document_ids")
    decision_log = {}

    # 1. Hybrid 检索（本地模型，先行且不依赖外部 API）
    final_k = int(cfg["retrieval"].get("final_k", settings.FINAL_K))
    try:
        evidence = _full_search(pipeline, item["question"], doc_ids, final_k)
    except Exception as e:
        evidence = []
        decision_log["retrieval_error"] = str(e)
    evidence_text, citation_map = format_evidence(evidence)

    # 2. Intent（LLM，独立容错）
    try:
        intent = decision.decide_intent(item["question"], "")
        decision_log["intent"] = intent.intent.value
    except Exception as e:
        decision_log["intent_error"] = str(e)[:120]

    # 3. Evidence Judge（LLM，独立容错）
    try:
        ev = decision.decide_evidence(item["question"], evidence_text)
        decision_log["evidence_decision"] = ev.decision
        decision_log["evidence_score"] = ev.evidence_score
    except Exception as e:
        ev = None
        decision_log["evidence_judge_error"] = str(e)[:120]

    # 4. Adaptive 扩检：EXPAND_LOCAL 且允许扩检时，放大 final_k 重检一轮
    if (ev is not None and ev.decision == "EXPAND_LOCAL"
            and cfg["retrieval"].get("adaptive_expand", False)
            and int(cfg["retrieval"].get("max_retrieval_rounds", 1)) >= 2):
        try:
            evidence = _full_search(pipeline, item["question"], doc_ids, final_k + 4)
            evidence_text, citation_map = format_evidence(evidence)
            ev = decision.decide_evidence(item["question"], evidence_text)
            decision_log["evidence_decision_round2"] = ev.decision
            decision_log["evidence_score_round2"] = ev.evidence_score
        except Exception as e:
            decision_log["expand_error"] = str(e)[:120]

    # 5. 证据不足 → 按配置弃答（不强行生成）
    if ev is not None and ev.decision in ("ABSTAIN", "SEARCH_EXTERNAL"):
        if cfg["decision"].get("abstain_on_insufficient", True):
            msg = "当前本地证据不足，无法可靠回答。"
            if ev.decision == "SEARCH_EXTERNAL":
                msg += "建议通过外部学术搜索补充相关论文。"
            decision_log["grounding_passed"] = False
            return {
                "answer": msg, "abstained": True, "citations": [],
                "retrieved_evidence": [_evidence_to_dict(e) for e in evidence],
                "decision": decision_log,
                "latency_ms": int((time.time() - t0) * 1000),
            }

    # 6. 带引用生成答案（LLM，独立容错）
    answer = ""
    try:
        prompt = cfg["answer"]["prompt_template"].format(
            evidence=evidence_text, question=item["question"]
        )
        answer = _llm_content(llm.get_llm(cfg.get("model", "deepseek")).invoke(prompt))
    except Exception as e:
        decision_log["answer_error"] = str(e)[:120]

    # 7. Grounding 校验（LLM，独立容错）
    citations = build_citations(citation_map)
    if answer:
        try:
            passed, report = grounding.verify(
                item["question"], answer, citations, citation_map)
            decision_log["grounding_passed"] = passed
            decision_log["grounding_confidence"] = report.get("confidence")
            decision_log["unsupported_claims"] = report.get("unsupported_claims", [])
        except Exception as e:
            decision_log["grounding_error"] = str(e)[:120]

    return {
        "answer": answer, "abstained": False,
        "citations": [
            {"id": c.citation_id, "document_id": c.document_id,
             "page": c.page_number, "chunk_id": c.chunk_id}
            for c in citations
        ],
        "retrieved_evidence": [_evidence_to_dict(e) for e in evidence],
        "decision": decision_log,
        "latency_ms": int((time.time() - t0) * 100),
    }


# ------------------------------ 主流程 ------------------------------
def run(system: str, config_path: str, dataset_path: str, limit: int | None,
        tag: str | None) -> str:
    _bootstrap()
    cfg = _load_yaml(config_path)
    with open(dataset_path, "r", encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]
    if limit:
        items = items[:limit]

    # 按需构建（重型模型只加载对应系统所需的部分）
    from core.llm.LLM import LLM
    llm = LLM()
    basic_db, basic_k = (None, 4)
    pipeline = decision = grounding = settings = None
    if system == "basic_rag":
        basic_db, basic_k = build_basic_retriever(cfg)
    elif system == "paperagent_full":
        llm, pipeline, decision, grounding, settings = build_full_components()

    run_id = (tag or system) + "-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = os.path.join(BACKEND_ROOT, "eval", "results", run_id)
    os.makedirs(out_dir, exist_ok=True)

    raw_rows = []
    for i, item in enumerate(items, 1):
        print(f"[{i}/{len(items)}] {item['id']} ({item['category']}) ...", flush=True)
        try:
            if system == "llm_only":
                r = answer_llm_only(item, cfg, llm)
            elif system == "basic_rag":
                r = answer_basic_rag(item, cfg, llm, basic_db, basic_k)
            else:
                r = answer_paperagent_full(
                    item, cfg, llm, pipeline, decision, grounding, settings
                )
        except Exception as e:
            r = {"answer": "", "abstained": False, "citations": [],
                 "retrieved_evidence": [], "decision": {"error": str(e)},
                 "latency_ms": 0}
        row = {
            "id": item["id"], "category": item["category"],
            "question": item["question"], "system": system,
            "expected_route": item["expected_route"],
            "gold_answer": item["gold_answer"],
            "gold_evidence": item.get("gold_evidence", []),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            **r,
        }
        raw_rows.append(row)

    # 写 raw.jsonl
    with open(os.path.join(out_dir, "raw.jsonl"), "w", encoding="utf-8") as f:
        for r in raw_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 写 summary.csv
    with open(os.path.join(out_dir, "summary.csv"), "w", encoding="utf-8-sig",
              newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "category", "abstained", "n_citations",
                    "n_evidence", "grounding_passed", "latency_ms"])
        for r in raw_rows:
            w.writerow([
                r["id"], r["category"], r["abstained"], len(r["citations"]),
                len(r["retrieved_evidence"]),
                r["decision"].get("grounding_passed", ""), r["latency_ms"],
            ])

    # 写 config.json 与 environment.json
    with open(os.path.join(out_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    env = {
        "system": system, "run_id": run_id,
        "dataset": os.path.basename(dataset_path), "n_items": len(items),
        "python": platform.python_version(), "platform": platform.platform(),
        "git_commit": _git_commit(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    with open(os.path.join(out_dir, "environment.json"), "w", encoding="utf-8") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)

    print(f"\n完成。结果目录：{out_dir}")
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", required=True,
                        choices=["llm_only", "basic_rag", "paperagent_full"])
    parser.add_argument("--config", default=None)
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--tag", default=None)
    args = parser.parse_args()

    config = args.config or f"eval/configs/{args.system}.yaml"
    dataset = args.dataset or "eval/datasets/qa_200.jsonl"
    run(args.system, config, dataset, args.limit, args.tag)


if __name__ == "__main__":
    main()
