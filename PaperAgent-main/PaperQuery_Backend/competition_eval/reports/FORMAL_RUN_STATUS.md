# PaperAgent 最小正式评测：当前执行状态

日期：2026-09-26。此文件保留本次冻结数据正式运行和重试的过程记录。人工评分已完成，最终六指标和解释见 `FINAL_REPORT.md`，机器可读结果见 `../metrics/formal-20260926T153126Z/final_metrics.csv`。

## 数据集冻结

- `datasets/qa_groundtruth.csv`：50 条 `human_verified`；30 Normal、10 Unanswerable、10 Scope Trap，每篇论文 5 题。
- SHA-256：`15b556a2146ab02352e7f112326b7ac39ef625fbf7b6869c31b2e9768e65801a`，与人工复核交付文件一致。
- `validate_dataset.py` 返回 `ready=true`、`errors=[]`，记录见 `dataset_validation.json`。PDF 连字和行末断词仅在校验器中归一化；冻结 CSV 未修改。
- 人工复核说明与修改记录分别保存在 `GROUND_TRUTH_REVIEW_REPORT.md`、`annotation_change_log.csv`。原候选数据保存在 `datasets/qa_groundtruth_draft_pre_review.csv`。

## 已完成结果

| 项目 | 本次结果 | 原始记录或限制 |
|---|---:|---|
| 页码级 Recall@5 | 14/30 = 46.7% | `raw/formal-retrieval-20260926T144543Z/` |
| 预热后 Retrieval P95 | 60.76 ms | 同一运行的 30 次请求 |
| Research 最小任务成功率 | 10/10 = 100% | `raw/formal-research-20260926T144730Z/`；只检查合法技能、步骤成功和预期产物类型，未评报告内容质量 |
| 安全边界回归 | 4/4 | `raw/security_boundary/` |
| 有效 Ask 回答 | 50/50 | `raw/formal-ask-merged-20260926T152216Z/`，含完整合并清单 |

## Ask 未完成原因

`raw/formal-ask-20260926T144554Z/ask_runs.jsonl` 含全部 50 次初次尝试，其中 Q001–Q047 成功、Q048–Q050 失败。失败请求返回 `ExceptionGroup`，底层外部模型错误为 HTTP 402 `Insufficient Balance`。对 Q048 使用相同冻结题目和同一 `deepseek` 模型进行单题复测，仍返回相同 402；失败复测记录保存在 `raw/formal-ask-20260926T151638Z/`。

用户随后确认继续使用当前 DeepSeek API key。`raw/formal-ask-20260926T151959Z/` 中 Q048–Q050 均返回 200。`merge_ask_retries.py` 只用成功重试替换原始失败行，保留同模型、同题号、同文档及全部原始尝试，生成 `raw/formal-ask-merged-20260926T152216Z/`。该目录的 `merge_manifest.json` 记录三个替换题号和冻结文件哈希。

30 道 Normal 均产生引用；10 道 Unanswerable 均产生可检查的回答；10 道 Scope Trap 均有有效回答。`raw/formal-ask-merged-20260926T152216Z/ask_review.csv` 已填入人工判定；空白原版备份为同目录 `ask_review_blank.csv`。人工评分确认 40 道带引用的 Normal/Scope 中 39 道引用支持回答、10 道 Unanswerable 均正确拒答、10 道 Scope Trap 均未越界。Citation Accuracy 不能仅用 gold page 是否被引用替代。

人工判定表已由用户填写，并确认 30 Normal 与 10 Scope 的引用正确性、10 Unanswerable 的拒答正确性和 10 Scope 的越界情况。评分脚本据此生成正式六指标总表。数据文件和当前相关代码的哈希见 `formal_execution_manifest.json`；该清单在第一次 Ask 运行后生成，不能视为第一次运行瞬间的完整源码快照。Git HEAD 为 `b919e181135de77fd73f2cc4add590cf179846c3`，工作区有未提交改动。
