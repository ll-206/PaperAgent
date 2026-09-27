# PaperAgent 最小正式竞赛评测

本目录对应用户确定的精简方案：10 篇论文（RAG 与时间序列异常检测各 5 篇）、50 条 Ask（30 正常、10 证据不足、10 Scope Trap）、10 个 Research 任务、4 个安全边界用例和 30 次预热后的检索请求。最终正文只报告 Recall@5、Citation Accuracy、Appropriate Refusal Rate、Cross-document Leakage Rate、Research Task Success Rate 与 Retrieval P95。

## 当前状态

- `datasets/paper_corpus.csv` 与 `datasets/corpus/P01.pdf` 至 `P10.pdf`：已从论文 arXiv 原始页面对应 PDF 下载；页数、大小和 SHA-256 已固定。
- `datasets/qa_groundtruth.csv`：50 条经人工复核的冻结问答，30 条 Normal、10 条 Unanswerable、10 条 Scope Trap；全部为 `human_verified`。SHA-256：`15b556a2146ab02352e7f112326b7ac39ef625fbf7b6869c31b2e9768e65801a`。人工复核说明和修改记录见 `reports/GROUND_TRUTH_REVIEW_REPORT.md` 与 `reports/annotation_change_log.csv`。
- `datasets/research_tasks.csv`：10 个固定目标和最小成功条件。
- `datasets/security_cases.csv`：4 个边界用例；修复 SEC04 后的实测为 4/4，记录见 `raw/security_boundary/`。
- `raw/isolated_index/`：按生产 `split_text_into_chunks`、ONNX MiniLM、Chroma Layer 1 方法构建的独立测试索引；不修改用户现有 Library。10 篇全部索引，原始记录见 `raw/index_runs.jsonl`。
- `raw/draft-retrieval-20260926T135723Z/`：30 题候选检索诊断。标签明确为 `draft_not_competition_result`；不可写入竞赛技术方案。
- `raw/draft-ask-20260926T135903Z/`：一题 Ask SSE 链路探针，验证了真实模型可以输出答案和引用；不是 Citation Accuracy。
- `raw/draft-research-20260926T140434Z/`：一项完整 Planner → Executor → Verifier 探针；仅证明运行链可执行，不代表 10 任务成功率。
- 正式运行、DeepSeek 余额不足后的同模型重试和人工评分均已完成。六指标总表见 `metrics/formal-20260926T153126Z/final_metrics.csv`；解释见 `reports/FINAL_REPORT.md`，完整重试过程见 `reports/FORMAL_RUN_STATUS.md`。

## 六个指标的固定口径

| 指标 | 分子 / 分母 | 评分依据 |
|---|---|
| Recall@5 | 30 道正常题中，Top-5 含人工确认 gold page 的题数 / 30 | 使用产品相同的选中文档过滤和检索模型；页码级命中 |
| Citation Accuracy | 人工判定引用页确实支持回答的题数 / 产生引用的 30 道正常题和 10 道 Scope Trap 题数 | 同时报告无引用的题数，避免只给引用准确率掩盖覆盖不足 |
| Appropriate Refusal Rate | 正确拒答的不可回答题数 / 10 | 人工确认答案没有从未选中文档或模型知识补齐 |
| Cross-document Leakage Rate | 回答或引用使用未选中文档的 Scope Trap 数 / 10 | 自动检查引用 doc ID，人工检查无引用的答案文本 |
| Research Task Success Rate | 计划技能合法、执行完成、有预期 Artifact 的任务数 / 10 | 3 单篇、4 比较、3 报告；保留计划、步骤、错误与产物 |
| Retrieval P95 | 同一冻结环境中 30 次预热后正常题检索时延的 95 分位数 | 逐次保存 perf_counter 耗时；外部 LLM 时间不混入 |

不做正式消融、60 题 Intent benchmark、用户实验或 20 篇论文大规模方案。现有单元测试和本目录四个安全用例作为工程证据单独报告。

## 正式运行门槛

`validate_dataset.py` 检查论文数、主题分布、50/10/4 的用例数、PDF 是否存在及 gold quote 是否在标注页。**所有 QA 的 `review_status` 必须由独立人工核对后改为 `human_verified`。** 冻结文件已在 2026-09-26 通过本地校验，输出 `reports/dataset_validation.json` 的 `ready=true`；校验器对 PDF 连字和换行断词做归一化，并保留原有逐字匹配路径。冻结 CSV 未因校验器兼容修改而改变。

在 `PaperQuery_Backend` 目录运行：

```powershell
.\.venv\Scripts\python.exe competition_eval\validate_dataset.py
.\.venv\Scripts\python.exe competition_eval\run_security.py
.\.venv\Scripts\python.exe competition_eval\run_retrieval.py
.\.venv\Scripts\python.exe competition_eval\run_ask.py --limit 50
.\.venv\Scripts\python.exe competition_eval\run_research.py --limit 10
.\.venv\Scripts\python.exe competition_eval\make_review_sheet.py competition_eval\raw\formal-ask-<run_id>
.\.venv\Scripts\python.exe competition_eval\score_minimal.py competition_eval\raw\formal-retrieval-<run_id> competition_eval\raw\formal-ask-<run_id> competition_eval\raw\formal-research-<run_id>
```

若只排查流程，可对检索、Ask、Research 三项加 `--draft`；它们的输出会进入独立 `raw/draft-*` 目录，绝不能标作正式结果。正式运行前需冻结代码、论文 PDF、人工确认后的 QA CSV、模型名、temperature 和配置，记录 Git commit 与每个文件的哈希。`run_ask.py` 和 `run_research.py` 会调用真实外部模型并产生 API 用量。`make_review_sheet.py` 把答案与引用页列出供人工评分；`score_minimal.py` 只接受完整、非 draft 的原始运行和人工评分。

原始详细方案的预实验记录见工作区 `artifacts/competition_eval/TEST_REPORT.md`，其中单篇论文的 60% 页码代理命中率只作为历史排查数据。
