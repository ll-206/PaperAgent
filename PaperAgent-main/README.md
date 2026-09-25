# PaperAgent

PaperAgent 是一个面向论文阅读、论文知识库管理和可信问答的 AI Agent 应用。项目支持上传 PDF 论文，将论文切分为向量知识库，并通过「混合检索 + 结构化决策 + 反幻觉校验」的可信 RAG 链路，实现基于论文证据的问答、翻译、笔记、多文件 Chat 以及可编排的科研任务（Research Mode）。

## 功能亮点

- **Library 论文知识库**：创建知识库、上传 PDF、查看处理状态、按标签和文件名检索论文。
- **后台异步向量化**：上传文件后由 `vector.py` 独立完成 PDF 解析、文本切分、摘要生成和 ChromaDB 向量入库。
- **Hybrid Retrieval 混合检索**：BGE-M3 Dense + BM25 Sparse → RRF 融合 → bge-reranker-v2-m3 重排，替换旧 ONNX 固定 Top-K 检索。
- **Decision Engine 结构化决策**：Intent / Evidence Judge 分级判断，证据不足时 Fail-closed 如实拒答而非编造。
- **Grounding 反幻觉校验**：规则校验引用 ID + LLM Judge 拆分 Claim，检测无依据陈述（Unsupported Claim）。
- **结构化 Citation 与跳页**：回答自动带 `[C#]` 引用，点击跳转到对应 PDF 页。
- **Research Mode 科研任务**：目标 → Planner 拆解计划 → Executor 顺序执行 8 个内置 Skills → Verifier 校验 → 交付结构化 Artifact，任务与步骤落库可追踪。
- **Skill Framework 可扩展工具**：统一的 Skill 契约，内置检索/对比/抽取/报告等 8 个 Skills，预留 Quantum 工具骨架。
- **Reader 问答助手**：在 PDF 阅读页内对当前论文提问，基于当前论文 `documentID` 做单文件检索。
- **多模型 Chat**：支持 DeepSeek、Kimi K3、OpenAI 三类 OpenAI-compatible Chat API，并可在前端切换。
- **SSE 流式回答**：后端使用 Server-Sent Events 流式返回（meta / decision / grounding / citations / delta），前端边接收边渲染。

## 技术栈

**Frontend**

- Vue 3 / TypeScript / Vite
- Pinia + Vuex / Vue Router
- Element Plus / Tailwind CSS
- Markdown-it + highlight.js
- Fetch ReadableStream / SSE

**Backend**

- Python / FastAPI / Uvicorn
- SQLAlchemy / SQLite
- LangChain / LangChain-Chroma
- ChromaDB / PyMuPDF
- JWT / Tencent Cloud TMT

**AI / Agent**

- DeepSeek / Kimi K3 / OpenAI-compatible Chat API
- BGE-M3 Dense Embedding（FlagEmbedding）
- BM25（rank-bm25 + jieba）
- bge-reranker-v2-m3（CrossEncoder 重排）
- RRF 融合检索
- Decision Engine / Grounding Verify（反幻觉）
- Research Planner / Executor / Verifier / Orchestrator
- Skill Framework（8 个内置 Skills + Quantum 骨架）

## 项目结构

```text
PaperAgent/
├── PaperQuery_Frontend/      # Vue 3 前端
├── PaperQuery_Backend/       # FastAPI 后端和向量化任务
│   ├── core/retrieval/       # Hybrid Retrieval（dense/sparse/fusion/reranker/pipeline）
│   ├── core/decision/        # Decision Engine（Intent/Evidence/Relatedness/Grounding）
│   ├── core/evidence/        # 证据格式化 + Grounding 反幻觉校验
│   ├── core/research/        # Research Mode（planner/executor/verifier/orchestrator）
│   ├── core/skills/          # Skill Framework（8 内置 Skills + quantum 骨架）
│   └── eval/                 # 实验一评测（数据集/脚本/配置/结果）
├── start_all.ps1             # Windows 一键启动脚本
├── 快速启动.md               # 组员安装与启动说明
└── README.md
```

## 本地运行

### 一键启动（推荐）

在项目根目录执行 `start_all.ps1`，脚本会自动依次启动后端 API（`main.py`，`:8001`）、向量化 Worker（`vector.py`）和前端（Vite，`:8080`）：

```powershell
.\start_all.ps1
```

启动完成后：

```text
前端页面   http://127.0.0.1:8080   （账号 admin / 123456）
后端 API   http://127.0.0.1:8001
```

> 首次部署请先阅读 [快速启动.md](./快速启动.md)，按步骤安装 Node.js、创建 `.venv` 并安装依赖、`npm install`。脚本会自动检测缺失项并给出提示。

### 1. 后端配置

```powershell
cd PaperQuery_Backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirement.txt
copy .env.example .env
```

编辑 `.env`，填入模型和翻译服务配置：

```env
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE=https://api.deepseek.com
KIMI_API_KEY=
KIMI_API_BASE=https://api.moonshot.cn/v1
OPENAI_API_KEY=
OPENAI_API_BASE=
TENCENT_SECRET_ID=
TENCENT_SECRET_KEY=

# V2 Hybrid Retrieval / Research（可选，默认已配置）
BGE_M3_MODEL_PATH=./models/bge-m3
RERANKER_MODEL_PATH=./models/bge-reranker-v2-m3
CHROMA_LAYER1_V2_DIR=./res/layer1_v2
BM25_INDEX_DIR=./res/bm25
```

启动后端 API：

```powershell
python main.py
```

默认监听：

```text
http://127.0.0.1:8001
```

> 首次启动会加载 BGE-M3 与 Reranker 模型，约需 10~20 秒；若模型目录缺失，会降级为基础检索。

### 2. 启动文档向量化后台任务

另开一个终端：

```powershell
cd PaperQuery_Backend
.\.venv\Scripts\activate
python vector.py
```

`vector.py` 不监听端口，持续扫描数据库中 `documentStatus=0` 的文档并完成 PDF 解析、向量化和状态更新。

### 3. 前端配置

```powershell
cd PaperQuery_Frontend
npm install
copy config\.env.example config\.env.dev
npm run dev -- --host 127.0.0.1
```

如果 `8080` 被占用，Vite 会自动切换端口。

## 运行说明

- 本项目不需要本地部署聊天大模型。
- 本地负责 PDF 解析、混合检索、RAG 上下文构建、结构化决策与接口编排。
- DeepSeek、Kimi K3、OpenAI 的回答由远程 API 生成。
- BGE-M3 / Reranker 为本地嵌入与重排模型，用于可信检索与反幻觉校验，不是聊天大模型。
- ChromaDB 会在本地缓存一个 ONNX embedding 模型，用于 `vector.py` 的向量检索。
- 上传 PDF 后，必须保持 `vector.py` 运行，否则 Library 页面会停留在「排队中」。

## 核心流程

```text
上传 PDF
  -> 写入 SQLite 文档记录
  -> vector.py 异步解析 PDF
  -> 文本切分与 embedding
  -> 写入 ChromaDB
  -> 更新文档状态为完成
  -> Ask Mode：Intent -> Hybrid Retrieval -> Evidence Judge -> Answer -> Grounding -> Citation
  -> Research Mode：Planner -> Executor(Skills) -> Verifier -> Artifact
  -> SSE 流式返回答案
```

## 评测（实验一 · 可信问答与反幻觉）

`PaperQuery_Backend/eval/` 下提供三套对比系统的评测框架（`llm_only` / `basic_rag` / `paperagent_full`），含 48 条种子数据集、构建/运行/评分三个脚本。详见 [eval/README.md](./PaperQuery_Backend/eval/README.md)。

## 已优化内容

- 移除硬编码密钥，统一改为 `.env` 配置。
- 修复 Kimi K3 `temperature` 参数兼容问题。
- 修复 Reader 问答 SSE 半包解析导致的空白回答。
- 将 ChromaDB ONNX 缓存移动到项目目录，避免 Windows 用户目录权限问题。
- 修复「处理中」卡死与上传后不显示的问题。
- 修复「Stream is undefined」模型调用错误。
- 依赖版本锁定（transformers / FlagEmbedding / huggingface-hub / peft 兼容矩阵）。
- 前端品牌名统一为 PaperAgent。
