# E1–E3 机制对照实验

源码仓库仅保存实验脚本、输入清单和结果说明；PDF 语料、隔离索引、逐条原始输出及人工复核底表属于本地实验数据，不随源码发布。完整复核需从实验负责人处取得相同批次的数据快照。

本目录保存基于 `competition_eval` 冻结语料的新一轮对照实验。E4 不执行。运行时使用同一模型完成每组实验的全部变体；不同模型的原始记录不能合并计分。原有 2026-09-26 DeepSeek 正式评测仍是历史绝对能力结果，不能直接充当本轮 GLM 对照组。

## 数据与实现

- E1：50 道冻结 QA × 4 变体。共享同一 ONNX/Chroma 索引、Top-8、模型、温度、token 上限及产品 `ANSWER_PROMPT`；变体仅改变检索范围、独立 Evidence Decision 与 Grounding 验证。全库检索、所选论文检索分别对应 Vanilla 和 Scope。这里的“Vanilla”指**无代码级范围过滤及独立证据判定的检索生成对照**，回答提示词本身仍包含证据不足时拒答的指令，因此不能当作完全无防护的通用 RAG。Evidence/Full 使用产品 `DecisionEngine`；Full 额外调用 `GroundingVerifier`。为了保持固定语料，`SEARCH_EXTERNAL` 只记录为无法在本地回答，不执行外部搜索。**Grounding 验证当前只报告状态，不自动修改已生成的回答**，因此不能预设它提高答案正确率。
- E2：10 个冻结 Research Goal × 开放规划器/产品受控规划器 × 2 次。开放规划器获得同一工具描述，但不受产品规划提示词与计划校验约束；不存在的 Skill 不执行。两组使用同一 `Executor` 和相同的本地论文/目标。`plan_valid` 检查已注册技能、既有且在前的依赖及唯一步骤 ID；它比产品 Planner 当前的静态校验略严格，原始计划与错误完整保留。
- E3：8 个脚本化连续科研场景 × 独立会话/工作空间。通过隔离的 `TestClient` 调用实际 Ask 和 Research 路由。Research 仍按当前前端传 `document_ids=[]`；研究目标中显式给出本地文档 ID，以便 Planner 读取正确论文。工作空间条件在第 4 步传 `parent_task_id`，独立会话则由用户重新提供前轮结果摘要。`manual_reentry_count` 是根据脚本交互设计计算的操作次数，**不是人类参与者实测**。

E1 的答案正确性、事实支持度、正确拒答、生成答案中的越界与引用正确性须人工复核；E2 的最低内容要求及 Artifact 事实溯源也须人工复核。`summarize.py` 只输出机器可直接证实的指标，并生成待审 CSV。E3 的 API 链接与最小完成率可自动统计，但答案内容连续性需要人工复核。指标解释必须保留分母和失败样本。

## 运行

在 `PaperQuery_Backend` 目录中，先确保 10 篇冻结 PDF 和独立 Chroma 索引已准备好，然后运行：

```powershell
.\.venv\Scripts\python.exe competition_eval\validate_dataset.py
.\.venv\Scripts\python.exe competition_eval\evaluation_v2\run_e1.py --limit 50 --model zhipu
.\.venv\Scripts\python.exe competition_eval\evaluation_v2\run_e2.py --limit 10 --repeats 2 --model zhipu
.\.venv\Scripts\python.exe competition_eval\evaluation_v2\run_e3.py --limit 8 --model zhipu
```

三组全部完成后，以各自的实际 `raw_results/formal-e*` 路径运行：

```powershell
.\.venv\Scripts\python.exe competition_eval\evaluation_v2\hydrate_e1.py <E1目录>
.\.venv\Scripts\python.exe competition_eval\evaluation_v2\summarize.py <E1目录> <E2目录> <E3目录>
```

实际执行时应先 `hydrate_e1.py`，再 `summarize.py`，使待审表含引用编号对应的原文片段。人工填写 `metrics/e1_review.csv`、`metrics/e2_review.csv` 的必填评分列后，运行 `score_reviews.py`；它会拒绝不完整表，不以空值冒充零分或通过。

每个运行目录都有 `manifest.json`，含模型、配置、语料哈希与状态。探针、因模型额度耗尽而中断的批次必须保留 `probe` 或 `invalid_interrupted` 标签，不得混入正式汇总。脚本需真实模型 API 额度；若出现 HTTP 402，停止该模型的后续请求，完整重跑同一模型，不能将不同模型的片段拼接成一组正式结果。

本轮正式结果及反例见 `RESULTS.md`。E3 的 `artifact_reused_by_parent_link` 仅表示前轮有产物且后轮保留父任务链接，不代表已经验证后轮答案使用了产物内容。
