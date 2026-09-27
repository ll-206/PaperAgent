# PaperAgent 最小正式竞赛评测结果

评测日期：2026-09-26。数据集为 10 篇公开论文、50 道 Ask（30 Normal、10 Unanswerable、10 Scope Trap）、10 个 Research 任务、4 个安全边界用例和 30 次预热后检索请求。人工复核后的 Ground Truth SHA-256 为 `15b556a2146ab02352e7f112326b7ac39ef625fbf7b6869c31b2e9768e65801a`；`validate_dataset.py` 返回 `ready=true`。人工 Ask 审阅表 SHA-256 为 `0ad4b455ca6cc0f492b36b8987b1c1dc0432493f07c58a852ba1053653379bed`。

## 六项核心指标

| 能力 | 指标 | 测试规模 | 正式结果 |
|---|---|---:|---:|
| Evidence Retrieval | 页码级 Recall@5 ↑ | 30 Normal | **14/30 = 46.7%** |
| Evidence Grounding | Citation Accuracy ↑ | 30 Normal + 10 Scope | **39/40 = 97.5%** |
| Evidence Awareness | Appropriate Refusal Rate ↑ | 10 Unanswerable | **10/10 = 100%** |
| Scope Control | Cross-document Leakage Rate ↓ | 10 Scope Trap | **0/10 = 0%** |
| Agent Execution | Research Task Success Rate ↑ | 10 Tasks | **10/10 = 100%** |
| Runtime Efficiency | Retrieval P95 ↓ | 30 warmed runs | **60.76 ms** |

工程质量补充：Ask 鉴权与文档归属的 4 个安全边界用例 **4/4 通过**。

## 评分口径和边界

- Recall@5 判断 Top-5 检索结果中是否包含人工确认的 PDF 证据页，属于**页码级**指标；这次仅 14/30，说明当前检索召回仍是明显短板。不能将其写成证据 chunk 召回率或领先检索性能。
- Citation Accuracy 采用人工复核的 40 条实际带引用回答：引用页是否支持输出中的核心答案。40/40 条均有引用，其中 39 条判定正确。它**不等于答案正确率**。Q003 的回答为“四个”，冻结 gold evidence 为“三个”；人工审阅认为引用的正文结果页支持回答，因此 `citation_correct=1`，同时在 `reviewer_notes` 中记录该不一致，冻结题库没有修改。Q017 是唯一 `citation_correct=0`：核心答案 SMD 正确，但实际引用的 P06 第 19 页未直接支持所述定义及附加细节；直接证据在第 6 页。
- Appropriate Refusal Rate 只针对 10 道经过全文检查的精确数值不可回答题；10 条回答均未编造要求的数值，并明确表示证据不足。
- Cross-document Leakage Rate 只针对本次 10 道相似论文干扰题；人工检查回答内容与引用后，未发现越过当前 selected document 的情况。不能推断系统在所有主题和输入下均不会泄漏。
- Research Task Success Rate 按预设最小条件计分：计划只用注册技能、步骤执行成功、产生预期类型 Artifact。10/10 达标。该指标不评价 Artifact 的学术质量或每项结论的正确性。
- Retrieval P95 来自预热后连续 30 次本地检索请求，不包含外部 LLM 的生成时间，也不是并发负载性能。

## 可追溯原始文件

- 检索：`raw/formal-retrieval-20260926T144543Z/retrieval_runs.jsonl` 与 `metrics.json`。
- Ask：`raw/formal-ask-merged-20260926T152216Z/ask_runs.jsonl`、`ask_review.csv`、`merge_manifest.json`。原始 50 次尝试中 Q048–Q050 因 DeepSeek HTTP 402 失败；用户确认继续使用当前 API key 后，同模型、同冻结题目的三次重试成功。原始两轮记录均保留，合并脚本只替换失败记录。
- Research：`raw/formal-research-20260926T144730Z/research_runs.jsonl` 与 `metrics.json`。
- 安全：`raw/security_boundary/`。
- 机器可读总表：`metrics/formal-20260926T153126Z/final_metrics.csv` 与 `summary.json`。
- 人工 Ground Truth 复核说明和变更记录：`reports/GROUND_TRUTH_REVIEW_REPORT.md`、`reports/annotation_change_log.csv`。

当前工作区含未提交代码改动，Git HEAD 为 `b919e181135de77fd73f2cc4add590cf179846c3`。数据集及当前相关代码哈希记录在 `reports/formal_execution_manifest.json`；该清单在第一次 Ask 运行后生成，不是第一次运行瞬间的完整源码快照。

## 用于技术方案的结论

本次数据支持 PaperAgent 在所测集合中的引用支持性、证据不足时拒答、所选文档边界和受控 Research 执行能力；同时暴露了页码级检索召回只有 46.7% 的改进空间。技术方案应如实呈现两者，避免把强项描述为先进 Retrieval 算法。
