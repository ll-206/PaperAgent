# PaperAgent 50 QA Ground Truth 人工复核报告

## 复核结论

- 复核对象：P01–P10 共 10 篇 PDF，`qa_groundtruth.csv` 共 50 条。
- 结构保持不变：30 条 normal、10 条 unanswerable、10 条 scope；每篇论文 5 条。
- 最终 `review_status`：50/50 均为 `human_verified`。
- 对 Q001–Q030 与 Q041–Q050：逐条核对 `selected_doc`、PDF 页码和证据是否直接支持问题。
- 对 Q031–Q040：对所选论文全文检索并人工核对，未发现能够给出题目所要求“精确数值”的证据，因此 10 条均保留为不可回答题。
- 对所有可回答题/Scope Trap：最终 `gold_evidence` 均可在所标 PDF 页中定位（按标准化空白/断词规则核对）。

## 人工修订

共对 8 条记录做了内容级调整：

| ID | 调整 |
|---|---|
| Q003 | 缩短证据到直接支持“3 个 open-domain QA tasks”的句子，去除 PDF 断词干扰 |
| Q014 | 将单数 benchmark 改为 two benchmarks，与 NQ + TriviaQA 一致 |
| Q019 | 缩短为直接支持 TranAD self-conditioning 的单句证据 |
| Q023 | 从结果表页改到数据集说明页，明确 SMD = Server Machine Dataset |
| Q026 | 将单数 spacecraft dataset 改为复数，并改到明确说明 SMAP/MSL 的页面 |
| Q047 | 与 Q019 一致，使用直接证据句 |
| Q049 | 强化 Scope Trap：P09 对 P06，二者都含 NASA spacecraft datasets |
| Q050 | 强化 Scope Trap：改测 TimesNet anomaly-detection F1-score，P06 也含同类 F1 概念 |

详细改动见 `annotation_change_log.csv`。

## 不可回答题复核

Q031–Q040 均针对精确训练成本、碳排、峰值内存、GPU-hour、API 单次费用、焦耳/功耗或云托管成本等数值。
全文检索相关术语并检查实验/实现部分后，没有发现能够直接回答这些“精确数值”的证据。
个别论文会出现相关但不同的信息（例如硬件型号、显存占用、GPU 单价或一般性的 cost/energy 字样），但均不足以回答对应问题，因此仍应判定为 unanswerable。

## 冻结信息

- 输出文件：`qa_groundtruth_human_verified.csv`
- 行数：50
- SHA-256：`15b556a2146ab02352e7f112326b7ac39ef625fbf7b6869c31b2e9768e65801a`

下一步应将该文件替换/复制到项目的正式 `qa_groundtruth.csv` 位置，然后执行：

```powershell
.\.venv\Scripts\python.exe competition_eval\validate_dataset.py
```

只有校验结果为 `"ready": true` 后，才运行不带 `--draft` 的正式评测。
