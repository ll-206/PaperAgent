# 50 条 QA 的人工复核说明

打开 `qa_groundtruth.csv`，逐条对照 `corpus/P01.pdf` 至 `P10.pdf`。`selected_doc` 是唯一允许的论文；`gold_page` 为 PDF 阅读器中的第 1 起页码，`gold_evidence` 是自动提取的候选摘录。自动摘录只保证文字出现在该页，不保证它充分回答问题。

对 Q001–Q030（正常题）和 Q041–Q050（Scope Trap）：确认所标页与摘录直接支持问题答案；若不支持，修改 `query`、`gold_page` 和 `gold_evidence`，并确保摘录逐字出现在对应 PDF 页。Scope Trap 还需确认 `distractor_doc` 是同主题、未选中的论文，且有相似概念足以形成干扰。

对 Q031–Q040（不可回答题）：检索所选论文全文，确认没有足以回答该问题的精确事实。若论文已有答案，应换题；不能只因为某一页没有答案就标为不可回答。

每条完成后把 `review_status` 从 `pending` 改为 `human_verified`。保留其他列与行数；总量必须是每篇论文 3 条正常题、1 条不可回答题、1 条 Scope Trap。不要运行 `draft_groundtruth.py --force`，它会覆盖人工修改。

所有 50 条复核完成后运行：

```powershell
.\.venv\Scripts\python.exe competition_eval\validate_dataset.py
```

只有输出 `"ready": true` 才能运行不带 `--draft` 的正式评测命令。人工复核者及修改记录建议另存 `annotation_change_log.csv`，避免覆盖来源证据。
