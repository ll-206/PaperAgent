# -*- coding: utf-8 -*-
"""实验一 · Grounding 与反幻觉评分器。

读取一个或多个 run 的 raw.jsonl，计算技术方案规定的三项指标：
  1. Answer Accuracy      ：对照 gold answer/evidence，LLM-as-judge 判 correct/partial/wrong
  2. Unsupported Claim Rate：把回答拆成原子 Claim，逐条判 Supported/Unsupported/Contradicted
  3. Citation Accuracy     ：每条 Citation 是否真正支撑回答中的 Claim
并额外统计：
  - 证据不足类（unanswerable/cross_doc）的正确拒答率（反幻觉关键指标）
  - 证据不足类仍强行作答且含无依据 Claim 的幻觉率

用法（在 PaperQuery_Backend 目录下）：
    python eval/scripts/score_grounding.py eval/results/paperagent_full-20260924-100000
    python eval/scripts/score_grounding.py eval/results/runA eval/results/runB   # 多系统对比
输出：每个 run 目录下 scored.jsonl、metrics.json，并打印横向对比表。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

CLAIM_PROMPT = """把下面的回答拆解成若干个可独立核验的原子事实陈述（Claim），并依据给定证据逐条判定。
问题：{question}
回答：{answer}
可用证据（[E#] 编号）：
{evidence}

对每个 Claim 输出：
- text : 该原子陈述
- verdict : supported（证据直接支持）/ contradicted（证据明确反驳）/ unsupported（证据中找不到依据）
- evidence_ids : 支撑它的证据编号数组（没有则为空数组）
严格输出 JSON：{{"claims":[{{"text":"...","verdict":"...","evidence_ids":[]}}]}}，不要解释。"""

ANSWER_PROMPT = """请判定【候选回答】相对【参考答案】的正确性。
问题：{question}
参考答案：{gold}
候选回答：{answer}
判定等级：correct（关键事实一致且无实质性错误）/ partial（答对部分或有小瑕疵）/ wrong（关键错误或答非所问）
严格输出 JSON：{{"label":"correct|partial|wrong","reason":"..."}}，不要解释。"""

CITATION_PROMPT = """判定每条引用证据是否真正支撑回答中的相关陈述。
问题：{question}
回答：{answer}
引用列表：
{citations}
对每条引用输出 id 与 supports（true 仅当该引用文本确实支撑回答中的某个陈述）。
严格输出 JSON：{{"items":[{{"id":"...","supports":true}}]}}，不要解释。"""


def _llm():
    from core.llm.LLM import LLM
    return LLM().get_llm("deepseek")


def _json_from_llm(llm, prompt: str, retries: int = 2):
    for k in range(retries + 1):
        try:
            resp = llm.invoke(prompt)
            text = resp.content if hasattr(resp, "content") else str(resp)
            text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
            m = re.search(r"\{.*\}", text, re.S)
            return json.loads(m.group(0) if m else text)
        except Exception:
            if k == retries:
                return None
            time.sleep(1.0)
    return None


def _norm_chars(s: str) -> set:
    # 保留中英文与数字字符，去空白与标点，用于字符级重叠计算
    return set(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", s or ""))


def retrieval_recall(row: dict) -> dict:
    """纯规则判定 Gold Evidence 是否被召回（不依赖 LLM）。
    命中条件：存在同页码的检索片段，且 gold quote 字符在该片段中占比 >= 0.6。
    """
    gold = [g for g in row.get("gold_evidence", []) if g.get("quote")]
    retrieved = row.get("retrieved_evidence", [])
    hit = 0
    for g in gold:
        gchars = _norm_chars(g.get("quote", ""))
        if not gchars:
            continue
        for e in retrieved:
            if int(e.get("page", -1)) != int(g.get("page", -2)):
                continue
            echars = _norm_chars(e.get("text", ""))
            overlap = len(gchars & echars) / len(gchars)
            if overlap >= 0.6:
                hit += 1
                break
    return {"gold_total": len(gold), "gold_hit": hit}


def score_row(row: dict, llm) -> dict:
    category = row["category"]
    answer = row.get("answer", "") or ""
    evidence = row.get("retrieved_evidence", [])
    abstained = bool(row.get("abstained", False))
    expected_insufficient = row["expected_route"] in ("ABSTAIN", "SEARCH_EXTERNAL")

    result = {
        "id": row["id"], "category": category, "system": row["system"],
        "abstained": abstained,
    }

    # ---------- Answer Accuracy ----------
    if abstained:
        # 该拒答时拒答 = correct；不该拒答却拒答 = wrong
        result["answer_label"] = "correct" if expected_insufficient else "wrong"
    else:
        judged = _json_from_llm(llm, ANSWER_PROMPT.format(
            question=row["question"], gold=row.get("gold_answer", ""), answer=answer))
        result["answer_label"] = judged["label"] if judged and "label" in judged else "unknown"

    # ---------- Claim 拆解与 Grounding ----------
    evidence_text = "\n".join(
        f"[E{i+1}] {e.get('text','')}" for i, e in enumerate(evidence)
    ) or "（系统未提供任何证据）"
    claims = []
    # 拒答（abstained）不含事实主张，不参与 Claim 拆解与 UCR
    if answer.strip() and not abstained:
        cj = _json_from_llm(llm, CLAIM_PROMPT.format(
            question=row["question"], answer=answer, evidence=evidence_text))
        if cj and "claims" in cj:
            claims = cj["claims"]
    result["claims"] = claims
    n_unsup = sum(1 for c in claims if c.get("verdict") in ("unsupported", "contradicted"))
    result["n_claims"] = len(claims)
    result["n_unsupported_claims"] = n_unsup

    # ---------- Citation Accuracy ----------
    citations = row.get("citations", [])
    cite_supports = {}
    if citations:
        # 建立 id -> chunk 文本
        ev_by_chunk = {e.get("chunk_id"): e.get("text", "") for e in evidence}
        cit_lines = []
        for c in citations:
            txt = ev_by_chunk.get(c.get("chunk_id"), "")
            cit_lines.append(f"- id={c['id']} page={c.get('page')} 文本：{txt[:600]}")
        cj = _json_from_llm(llm, CITATION_PROMPT.format(
            question=row["question"], answer=answer, citations="\n".join(cit_lines)))
        if cj and "items" in cj:
            cite_supports = {it["id"]: bool(it.get("supports")) for it in cj["items"]}
    result["citation_supports"] = cite_supports
    result["n_citations"] = len(citations)
    result["n_citations_supported"] = sum(1 for v in cite_supports.values() if v)

    # ---------- 反幻觉标记 ----------
    # 证据不足类问题：未拒答且出现无依据 Claim = 幻觉
    result["hallucinated_on_insufficient"] = (
        expected_insufficient and not abstained and n_unsup > 0
    )
    result["correct_abstain"] = expected_insufficient and abstained
    result.update(retrieval_recall(row))
    return result


def aggregate(scored: list[dict]) -> dict:
    def acc(rows):
        if not rows:
            return 0.0
        score = {"correct": 1.0, "partial": 0.5, "wrong": 0.0, "unknown": 0.0}
        return sum(score.get(r["answer_label"], 0.0) for r in rows) / len(rows)

    total_claims = sum(r["n_claims"] for r in scored)
    total_unsup = sum(r["n_unsupported_claims"] for r in scored)
    total_cites = sum(r["n_citations"] for r in scored)
    total_cites_sup = sum(r["n_citations_supported"] for r in scored)
    gold_total = sum(r.get("gold_total", 0) for r in scored)
    gold_hit = sum(r.get("gold_hit", 0) for r in scored)
    insuff = [r for r in scored if r["category"] in ("unanswerable", "cross_doc")]

    by_category = {}
    for cat in ("answerable_single", "unanswerable", "cross_doc"):
        rows = [r for r in scored if r["category"] == cat]
        gt = sum(r.get("gold_total", 0) for r in rows)
        gh = sum(r.get("gold_hit", 0) for r in rows)
        by_category[cat] = {
            "n": len(rows),
            "answer_accuracy": round(acc(rows), 4),
            "unsupported_claim_rate": round(
                (sum(r["n_unsupported_claims"] for r in rows) /
                 max(1, sum(r["n_claims"] for r in rows))), 4),
            "retrieval_recall_at_k": round(gh / max(1, gt), 4),
        }

    return {
        "n_items": len(scored),
        "answer_accuracy": round(acc(scored), 4),
        "unsupported_claim_rate": round(total_unsup / max(1, total_claims), 4),
        "citation_accuracy": round(total_cites_sup / max(1, total_cites), 4),
        "retrieval_recall_at_k": round(gold_hit / max(1, gold_total), 4),
        "gold_evidence_hit": gold_hit, "gold_evidence_total": gold_total,
        "correct_abstain_rate_on_insufficient": round(
            sum(1 for r in insuff if r["correct_abstain"]) / max(1, len(insuff)), 4),
        "hallucination_rate_on_insufficient": round(
            sum(1 for r in insuff if r["hallucinated_on_insufficient"])
            / max(1, len(insuff)), 4),
        "by_category": by_category,
    }


def process_run(run_dir: str, llm) -> dict:
    raw_path = os.path.join(run_dir, "raw.jsonl")
    with open(raw_path, "r", encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    scored = []
    for i, r in enumerate(rows, 1):
        print(f"  scoring {i}/{len(rows)} {r['id']} ...", flush=True)
        scored.append(score_row(r, llm))
    with open(os.path.join(run_dir, "scored.jsonl"), "w", encoding="utf-8") as f:
        for s in scored:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    metrics = aggregate(scored)
    with open(os.path.join(run_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dirs", nargs="+", help="一个或多个结果目录（含 raw.jsonl）")
    args = parser.parse_args()

    sys.path.insert(0, BACKEND_ROOT)
    os.chdir(BACKEND_ROOT)
    try:
        import dotenv
        dotenv.load_dotenv()
    except Exception:
        pass

    llm = _llm()
    all_metrics = {}
    for d in args.run_dirs:
        print(f"== 评分 {d} ==")
        all_metrics[os.path.basename(os.path.normpath(d))] = process_run(d, llm)

    # 横向对比表
    print("\n================ 指标对比 ================")
    header = ["run", "N", "AnswerAcc", "UCR", "CitationAcc",
              "CorrectAbstain", "HallucOnInsuff"]
    print("{:<32}{:>4}{:>10}{:>8}{:>12}{:>14}{:>16}".format(*header))
    for name, m in all_metrics.items():
        print("{:<32}{:>4}{:>10}{:>8}{:>12}{:>14}{:>16}".format(
            name[:31], m["n_items"],
            f'{m["answer_accuracy"]:.3f}', f'{m["unsupported_claim_rate"]:.3f}',
            f'{m["citation_accuracy"]:.3f}',
            f'{m["correct_abstain_rate_on_insufficient"]:.3f}',
            f'{m["hallucination_rate_on_insufficient"]:.3f}'))


if __name__ == "__main__":
    main()
