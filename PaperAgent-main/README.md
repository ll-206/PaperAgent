# PaperAgent

PaperAgent 是一个面向论文阅读、论文知识库管理和可信问答的 AI Agent 应用。项目支持上传 PDF 论文，将论文切分为向量知识库，并通过「ChromaDB 向量检索 + 结构化决策 + 证据校验」的 RAG 链路，实现基于论文证据的问答、翻译、笔记、多文件 Chat 以及可编排的科研任务（Research Mode）。

## 功能亮点

- **Library 论文知识库**：创建知识库、上传 PDF、查看处理状态、按标签和文件名检索论文。
- **后台异步向量化**：上传文件后由 `vector.py` 独立完成 PDF 解析、文本切分、摘要生成和 ChromaDB 向量入库。
- **论文向量检索**：ChromaDB 使用本地 ONNX embedding 索引论文片段，问答与 Research 均返回结构化证据。
- **Decision Engine 结构化决策**：Intent / Evidence Judge 分级判断，证据不足时 Fail-closed 如实拒答而非编造。
- **Grounding 反幻觉校验**：规则校验引用 ID + LLM Judge 拆分 Claim，检测无依据陈述（Unsupported Claim）。
- **结构化 Citation 与跳页**：回答自动带 `[C#]` 引用，点击跳转到对应 PDF 页。
- **Research Mode 科研任务**：目标 → Planner 拆解计划 → Executor 顺序执行 8 个内置 Skills → Verifier 校验 → 交付结构化 Artifact，任务与步骤落库可追踪。
- **Skill Framework 可扩展工具**：统一的 Skill 契约，内置检索/对比/抽取/报告等 8 个 Skills，预留 Quantum 工具骨架。
- **Reader 问答助手**：在 PDF 阅读页内对当前论文提问，基于当前论文 `documentID` 做单文件检索。
- **多模型 Chat**：支持 DeepSeek、Kimi K3、智谱 GLM 三类 OpenAI-compatible Chat API，并可在前端切换。
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

- DeepSeek / Kimi K3 / 智谱 GLM（OpenAI-compatible Chat API）
- ChromaDB + 本地 ONNX MiniLM 向量检索
- Decision Engine / Grounding Verify（反幻觉）
- Research Planner / Executor / Verifier / Orchestrator
- Skill Framework（8 个内置 Skills + Quantum 骨架）

## 项目结构

```text
PaperAgent/
├── PaperQuery_Frontend/      # Vue 3 前端
├── PaperQuery_Backend/       # FastAPI 后端和向量化任务
│   ├── core/retrieval/       # 保留的旧版混合检索实验代码，不接入运行服务
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
pip install -r req_win.txt
copy .env.example .env
```

编辑 `.env`，填入自己的模型 API Key 和随机 `SECRET_KEY`。英中翻译使用可选的离线包，安装方式见 [快速启动.md](./快速启动.md)：

```env
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE=https://api.deepseek.com
KIMI_API_KEY=
KIMI_API_BASE=https://api.moonshot.cn/v1
ZHIPU_API_KEY=
ZHIPU_API_BASE=https://open.bigmodel.cn/api/paas/v4/
ZHIPU_MODEL=glm-4-flash
# 本地论文向量索引
CHROMA_LAYER1_DIR=./res/layer1
CHROMA_LAYER2_DIR=./res/layer2
CHROMA_ONNX_CACHE_DIR=./res/onnx_models_v5/all-MiniLM-L6-v2
```

启动后端 API：

```powershell
python main.py
```

默认监听：

```text
http://127.0.0.1:8001
```

> 运行服务只使用 ChromaDB 的本地 ONNX embedding；无需下载 BGE-M3 或重排模型。

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

## 检索模型

服务首次向量化论文时会缓存 ChromaDB 使用的 ONNX MiniLM 模型。此前的 BGE-M3、BM25 与重排实验文件仍保留在 `core/retrieval/` 和 `eval/`，不参与当前服务启动或问答链路。

## 运行说明

- 本项目不需要本地部署聊天大模型。
- 本地负责 PDF 解析、向量检索、RAG 上下文构建、结构化决策与接口编排。
- DeepSeek、Kimi K3、智谱 GLM 的回答由远程 API 生成。
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
  -> Ask Mode：Intent -> ChromaDB Retrieval -> Evidence Judge -> Answer -> Grounding -> Citation
  -> Research Mode：Planner -> Executor(Skills) -> Verifier -> Artifact
  -> SSE 流式返回答案
```

## 评测（实验一 · 可信问答与反幻觉）

`PaperQuery_Backend/eval/` 下提供三套对比系统的评测框架（`llm_only` / `basic_rag` / `paperagent_full`），含 48 条种子数据集、构建/运行/评分三个脚本。详见 [eval/README.md](./PaperQuery_Backend/eval/README.md)。

> 其中 `paperagent_full` 是历史混合检索实验配置，不代表当前服务的检索架构；相关结果不能直接作为当前版本的效果指标。

核心技术与创新点的实现范围见 [核心技术与创新点.md](./核心技术与创新点.md)。

## 已优化内容

- 移除硬编码密钥，统一改为 `.env` 配置。
- 修复 Kimi K3 `temperature` 参数兼容问题。
- 修复 Reader 问答 SSE 半包解析导致的空白回答。
- 将 ChromaDB ONNX 缓存移动到项目目录，避免 Windows 用户目录权限问题。
- 修复「处理中」卡死与上传后不显示的问题。
- 修复「Stream is undefined」模型调用错误。
- 依赖版本锁定（transformers / FlagEmbedding / huggingface-hub / peft 兼容矩阵）。
- 前端品牌名统一为 PaperAgent。

## 健康检查与后续测试

后端启动后可直接访问交互式接口文档：`http://127.0.0.1:8001/docs`。项目还提供了以下稳定测试入口：

| 接口 | 认证 | 用途 |
|------|------|------|
| `GET /health/live` | 否 | 检查 API 进程是否存活 |
| `GET /health/ready` | 否 | 检查数据库、模型、向量库和 Research 是否就绪 |
| `GET /test/capabilities` | 是 | 查看当前注册模型与可测试功能 |
| `POST /test/echo` | 是 | 验证登录认证与 JSON 请求链路 |
| `GET /test/sse` | 是 | 无模型费用地验证 SSE 流式链路 |

一键执行只读冒烟测试：

```powershell
cd PaperQuery_Backend
.\.venv\Scripts\python.exe scripts\smoke_test.py
```

需要额外验证真实模型时，可指定一种模型（会产生一次 API 调用）：

```powershell
.\.venv\Scripts\python.exe scripts\smoke_test.py --with-model zhipu
```

前端建议使用 Node.js 20 LTS。本项目现有 `vue-tsc 1.x` 与 Node.js 24 不兼容；Vite 正式构建不受影响，但在 Node.js 24 下执行旧版 `vue-tsc --noEmit` 会失败。
