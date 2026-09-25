# PaperAgent 后端（V2）

PaperAgent 论文查询 AI Agent 的后端服务。基于 FastAPI，围绕论文库提供
**可信问答（Ask Mode）**、**研究编排（Research Mode）** 与知识库管理能力，
核心手段是「混合检索 + 证据决策 + 反幻觉校验 + 结构化引用」。

## 技术栈

- **Web 框架**：FastAPI + uvicorn（默认端口 8001）
- **检索**：BGE-M3 Dense + BM25 Sparse → RRF 融合 → bge-reranker-v2-m3 重排
  （`core/retrieval/`）
- **决策**：DecisionEngine（Intent / Relatedness / Evidence，Fail-closed；`core/decision/`）
- **反幻觉**：Grounding Verifier（Claim 拆分 + 规则/LMM-Judge；`core/evidence/grounding.py`）
- **研究编排**：Planner → Executor → Verifier → Artifact（`core/research/`、`core/artifact/`）
- **Skills**：内置 8 个技能（PaperSearch / PaperReader / Extract / CitationVerify 等，`core/skills/`）
- **存储**：SQLite（业务数据，`core/backend/db/`）+ ChromaDB（V2 向量索引，`./res/layer1_v2`）+ BM25 语料（`./res/bm25`）
- **鉴权**：JWT
- **前端**：见 `../PaperQuery_Frontend`；AI 编排 / 文档解析 / 高亮等库见 `requirement.txt` / `req_win.txt`

## 数据流（Ask Mode）

前端 ChatGPT 式问答 → `POST /qa/stream`（SSE）→ 混合检索取结构化证据 →
DecisionEngine 判定（本地可答 / 需拒答 / 需扩检）→ Grounding 校验 →
以 `meta / decision / grounding / citations / delta` 事件流式返回，附可点击的 `[C#]` 引用。

## 使用方式

### 1. 准备环境

> Windows：后端依赖较多且体积大，建议 Conda/venv 隔离安装。
> 本项目已内置 `.venv`（Conda 环境），仅本机可用，无法随压缩包传递，请在新机器重建。

```powershell
cd PaperQuery_Backend
# 若重建环境：
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirement.txt
```

### 2. 配置 `.env`

从 `.env.example` 复制为 `.env`，填入 LLM 的 API Key（DeepSeek / Kimi 等）：

```
DEEPSEEK_API_KEY=sk-xxxx
# 其余 V2 配置（模型/索引路径）已有默认值，见 core/common/config.py
```

V2 关键默认路径（可在 `.env` 覆盖）：

| 配置项 | 默认值 |
|--------|--------|
| `INDEX_VERSION` | `v2-bge-m3-001` |
| `BGE_M3_MODEL_PATH` | `./models/bge-m3` |
| `RERANKER_MODEL_PATH` | `./models/bge-reranker-v2-m3` |
| `CHROMA_LAYER1_V2_DIR` | `./res/layer1_v2` |
| `BM25_INDEX_DIR` | `./res/bm25` |

### 3. 启动

```powershell
# 后端 API
.venv\Scripts\python.exe main.py          # 监听 http://127.0.0.1:8001

# 向量化 Worker（纯轮询、无端口，处理文档上传后的切块+向量化）
.venv\Scripts\python.exe vector.py
```

> 一键启动请直接用项目根目录的 `start_all.ps1`，会自动自检依赖并启动前后端。

### 4. V2 索引重建（可选）

需在论文量变化后重建 V2 混合检索索引：

```powershell
.venv\Scripts\python.exe scripts\reindex_v2.py
```

## 目录速览

```
core/
├── retrieval/    混合检索（dense / sparse / fusion / reranker / pipeline）
├── decision/     DecisionEngine
├── evidence/     Grounding、证据格式化
├── skills/       Skill Framework（8 内置技能）
├── research/     Research Orchestrator（Planner/Executor/Verifier）
├── artifact/     研究产物模型/构建器
├── backend/      Router、CRUD、DB 模型、鉴权
└── common/       配置、类型定义、通用工具
main.py           后端入口
vector.py         向量化轮询 Worker
scripts/reindex_v2.py  V2 索引重建
req_win.txt / requirement.txt  依赖清单
```