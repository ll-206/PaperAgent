# 实验一 · 可信论文问答与反幻觉（Trustworthy QA & Anti-Hallucination）

本目录对应技术方案「三组验证实验」中的**实验一**，用于量化 PaperAgent Full
相对基线在**答案正确性、无依据陈述、引用准确性**上的改进，尤其是面对
**本地证据不足**的问题时，能否做到**如实拒答而非幻觉**。

---

## 1. 目录结构

```
eval/
├─ datasets/
│  ├─ qa_200.jsonl              # 评测数据集（当前为 48 条人工种子，可扩充至 200）
│  └─ _tmp_unanswerable.jsonl   # 冒烟测试用临时子集（可删除）
├─ scripts/
│  ├─ build_qa_dataset.py       # 数据集构建器（种子 + 可选 LLM 扩充）
│  ├─ run_qa_eval.py            # 评测运行器（驱动三套系统，记录证据/决策/引用）
│  └─ score_grounding.py        # 评分器（Answer Acc / UCR / Citation Acc / 拒答 / 召回）
├─ configs/
│  ├─ llm_only.yaml             # 无证据，直接问 LLM
│  ├─ basic_rag.yaml            # 旧 ONNX MiniLM 固定 Top-K（升级前 PaperQuery）
│  └─ paperagent_full.yaml      # Hybrid + Decision + Grounding + Citation（完整系统）
└─ results/<run_id>/            # 每次运行独立目录
   ├─ config.json               # 本次系统配置快照
   ├─ raw.jsonl                 # 每条：问题/答案/检索证据/决策/引用/时间戳
   ├─ summary.csv               # 每条摘要（拒答、引用数、证据数、耗时）
   ├─ scored.jsonl              # 评分明细（Claim 判定、引用支撑、召回命中）
   ├─ metrics.json              # 汇总指标
   └─ environment.json          # Python/平台/git commit/数据集/时间
```

## 2. 数据集说明

每条记录字段：`id / category / question / document_ids / gold_answer /
gold_evidence(页码+原文) / expected_route / difficulty / source`。

| 类别 | 含义 | 预期路由 | 当前条数 |
|------|------|----------|---------|
| `answerable_single` | 单文档可答，gold evidence 已标注 | LOCAL_RAG | 28 |
| `unanswerable` | 本地证据不足，应拒答 | ABSTAIN | 14 |
| `cross_doc` | 需多篇文档对比，当前库不足 | SEARCH_EXTERNAL | 6 |

> **现状约束（诚实说明）**：当前论文库中仅有 **1 份**中文 PDF（Day01 网络基础作业，
> documentID `70c1eaca0422998e00b2f77f01a985c2`），因此种子集为 **48 条**，
> 尚未达到技术方案规划的「30 篇论文 / 200 问」。扩充路径见第 5 节。

## 3. 三套对比系统

| 系统 | 检索 | 证据判定 | Grounding | 引用 |
|------|------|---------|-----------|------|
| LLM Only | 无 | 无 | 无 | 无 |
| Basic RAG | 旧 ONNX 固定 Top-K=4 | 无 | 无 | 无结构化引用 |
| PaperAgent Full | BGE-M3+BM25→RRF→Reranker | Intent/Evidence Judge | 规则+LLM Judge | 结构化 Citation |

## 4. 指标定义

- **Answer Accuracy**：对照 gold answer，LLM-as-judge 判 correct(1)/partial(0.5)/wrong(0)。
  证据不足类问题中，**如实拒答计为 correct**。
- **Unsupported Claim Rate (UCR)**：回答拆成原子 Claim，判
  Supported / Unsupported / Contradicted；UCR =（Unsupported+Contradicted）/ 总 Claim。
  拒答不含事实主张，不计入。
- **Citation Accuracy**：每条 Citation 的原文是否真正支撑回答中的陈述。
- **Correct Abstain Rate（证据不足类）**：该拒答时正确拒答的比例。
- **Hallucination Rate on Insufficient**：证据不足却强行作答且含无依据 Claim 的比例。
- **Retrieval Recall@K（纯规则，不耗 API）**：Gold Evidence 是否被同页检索片段召回
  （字符重叠 ≥ 0.6）。

## 5. 使用方法（务必使用后端 .venv 的 Python）

在 `PaperQuery_Backend` 目录下执行：

```powershell
# 1)（重新）生成种子数据集
.venv\Scripts\python.exe eval\scripts\build_qa_dataset.py

# 2) 运行某套系统（默认全量；--limit 控制条数）
.venv\Scripts\python.exe eval\scripts\run_qa_eval.py --system paperagent_full
.venv\Scripts\python.exe eval\scripts\run_qa_eval.py --system basic_rag
.venv\Scripts\python.exe eval\scripts\run_qa_eval.py --system llm_only

# 3) 评分（可一次传多个结果目录做横向对比）
.venv\Scripts\python.exe eval\scripts\score_grounding.py eval\results\<runA> eval\results\<runB>
```

扩充到 200 题（调用 LLM 基于 PDF 各页自动生成，`source=llm_generated`，
**需人工抽检后再用于正式结果**）：

```powershell
.venv\Scripts\python.exe eval\scripts\build_qa_dataset.py --expand 200
```

> 若要真正达到「30 篇论文」：将更多公开 PDF 放入 `res/pdf` 并在系统中完成
> V2 索引重建（BGE-M3 + BM25），再重跑 build 脚本；`cross_doc` 类问题需要
> 至少 2 篇已索引文档才有意义。

## 6. 冒烟测试结果（2026-09-24，小样本）

- **可答类（4 条，PaperAgent Full）**：AnswerAcc=1.000，UCR=0，答案均带 [C#] 引用，
  Grounding 通过；Retrieval Recall 命中。
- **证据不足类（3 条）对比**：

| 系统 | AnswerAcc | UCR | CorrectAbstain | HallucOnInsuff |
|------|----------|-----|----------------|----------------|
| PaperAgent Full | 1.000 | 0.000 | **1.000** | **0.000** |
| Basic RAG | 0.333 | 0.871 | 0.000 | **0.667** |

结论（小样本，仅验证链路与趋势）：PaperAgent 在证据不足时**全部正确拒答、零幻觉**；
Basic RAG 无拒答机制，3 题中有 2 题用模型内部知识强行输出无依据内容。
**正式结论需在 200 题 / 30 篇论文规模上复跑后得出。**

## 7. 已知约束

1. LLM 为外部 API：测试期间 DeepSeek 曾返回 402（余额不足）、Kimi 401、OpenAI 连接失败。
   脚本已对各 LLM 环节独立容错——**检索（本地）与 Retrieval Recall 不受 API 影响**，
   API 恢复后可直接复跑答案与评分。
2. 检索索引当前仅 4 个 chunk（单文档），DENSE_K=20 会被自动收敛到实际数量。
3. LLM 自动生成的问题与 LLM-as-judge 评分均存在模型偏差，关键数字建议人工复核。
