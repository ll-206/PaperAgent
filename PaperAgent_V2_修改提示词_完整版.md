# PaperAgent V2 工程改造 · 完整修改提示词

> 本提示词用于驱动 AI 对现有 PaperAgent（PaperQuery）工程执行 V2 改造。
> 内容完整包含两份输入文档的核心信息：
> ①《PaperAgent_AI软件创新_技术方案_正式版》（对外承诺的目标能力）
> ②《PaperAgent_V2_工程改造与落地实施方案》（对内可执行的改造手册）
> 使用方式：把本提示词连同项目代码目录（或代码包）一起提供给改造执行者，执行者按提示词分阶段实施并逐步交付验收。

---

## 〇、你的角色与任务

你是资深 AI 软件工程师，负责把现有 **PaperAgent（PaperQuery）** 工程升级为 **PaperAgent V2 · Trusted Research Agent Workspace**。

- **任务边界**：在现有 Vue3 + FastAPI + LangChain + ChromaDB 工程上**增量演进**，不进行无必要重写。
- **验收原则**：严格区分"当前已有能力"和"目标能力"。只有实际完成并通过验收的模块，才可在最终技术方案、演示视频或附件 A2 中表述为"已实现"。
- **实施原则**：机制可解释、功能可运行、结果可复现、证据可追溯；避免堆叠无法验证的概念。
- **产出**：改造后的完整代码 + 可复现的三组实验数据 + 最终验收清单逐项通过。

---

## 一、项目背景与产品定位（来自技术方案）

### 1.1 产品定位

**PaperAgent 是面向科研全过程的可信智能研究工作台**：以"可信决策、证据驱动、科研执行、专业 Skill 扩展"为主线，将传统论文问答升级为可规划、可检索、可验证、可交付科研成果的 **AI Research Agent Workspace**。

- 核心能力：可信论文问答｜多文档混合检索｜Research Mode｜Research Skills｜量子实验执行｜隐私可信扩展
- 技术栈：Vue 3 · TypeScript · FastAPI · LangChain · ChromaDB · BGE-M3 · BM25 · RRF · Reranker · SSE

### 1.2 背景与痛点

大模型已进入科研文献阅读场景，但科研任务具有"证据敏感、跨文档、长链路、强专业工具依赖"等特点。普通聊天模型难以保证答案严格来自用户论文；基础 PDF Chat 在多论文比较、证据不足识别、外部文献扩展、实验复现和成果整理上仍需大量人工操作。用户需要连续完成"检索—下载—阅读—做笔记—提取方法与实验—比较—核验引用—形成综述或实验报告"，这些步骤分散在多个工具之间，存在来源丢失和结论无法追溯问题。

核心痛点：
1. 文献证据与模型生成脱节；
2. 固定 Top-K RAG 难处理证据不足；
3. 复杂科研任务缺少可执行工作流；
4. 专业实验工具与 AI 助手割裂；
5. 实验室私有文献与科研行为存在隐私需求。

### 1.3 研发目标

- **可信**：回答可追溯到论文页码/片段，证据不足时主动扩展检索，而不是强行生成。
- **可执行**：系统能把复杂科研目标拆解为步骤，调用 Research Skills 完成检索、解析、比较、核验和报告生成。
- **可扩展**：以统一 Skill 接口连接外部科研软件，量子算法模拟作为首个专业工具落地案例。
- **可部署**：支持个人本地、实验室服务器和云端部署，预留隐私科研分析能力。

### 1.4 目标用户

| 用户/场景 | 核心任务 | 产品价值 |
|---|---|---|
| 学生科研 | 课程论文、开题调研、论文阅读、Related Work 整理 | 降低检索与整理成本 |
| 科研人员 | 多论文对比、方法/实验抽取、引用核验 | 提高证据追踪和研究产出效率 |
| 实验室/研发团队 | 私有文献知识库、团队研究任务、科研趋势分析 | 形成可部署的团队科研基础设施 |
| 专业计算场景 | 量子算法论文参数提取、模拟调用、实验报告 | 验证 AI 与专业科研软件的深度融合 |

### 1.5 核心功能边界

- **Ask Mode**：单篇/多篇论文 RAG 问答、选中文本解释、翻译、引用定位与来源展示。
- **Research Mode**：接受复杂科研目标，自动规划任务并调用搜索、阅读、抽取、比较、验证和报告 Skill。
- **Experiment Mode**：从论文中抽取实验参数并调用专业工具；首个案例为 Quantum Experiment Skill。
- **Library**：论文知识库、标签、处理状态、研究方向元数据与历史会话管理。
- **Trust Layer**：证据充分度判断、Grounding 校验、结构化决策、隐私科研分析扩展。

### 1.6 差异化目标

| 维度 | 普通 PDF Chat / 基础 RAG | PaperAgent V2 |
|---|---|---|
| 回答依据 | 固定检索后直接生成 | 证据充分度判断 + 动态扩展 + 最终 Grounding 校验 |
| 复杂任务 | 以多轮对话人工推进 | Planner 自动拆解并以 Artifact 为交付目标 |
| 专业工具 | 通常不执行外部科研软件 | 统一 Skill 接口接入量子模拟等专业工具 |
| 结果形态 | 聊天文本 | 答案 + 引用 + 比较表 + 研究报告 + 实验结果 |
| 扩展模式 | 功能耦合在单个 Agent 中 | Decision / Retrieval / Skills / Artifact 分层解耦 |

---

## 二、现有工程基线（改造前代码事实，来自实施方案第 1 章）

### 2.1 当前后端主链路（应作为改造起点，不废弃）

| 当前文件 | 当前职责 | V2 处理策略 |
|---|---|---|
| `core/agent/chatAgent.py` | Relatedness 判断、流式问答、摘要记忆 | 保留 ChatAgent 作为生成适配层；把决策逻辑迁移到 `core/decision` |
| `core/agent/dataprocessAgent.py` | PDF 分页、500 词切块、向量入库、论文摘要/分类 | 升级元数据、chunk_id/section、PaperCard；不再直接承担所有索引策略 |
| `core/vectordb/chromadb.py` | 两层 Chroma；similarity_search；固定 k=12 | 降级为 Dense Store Adapter；新增 `retrieval/pipeline.py` 统一组合 Dense/BM25/RRF/Reranker |
| `core/backend/router/router_llm.py` | 单/多论文问答、相关性判断、arXiv fallback、SSE | 拆为 qa 路由 + research 路由；统一 SSE Event 协议 |
| `vector.py` | 轮询 documentStatus=0，调用 DataProcessAgent | 保留 worker 机制；增加索引版本、失败原因、重建索引和 BGE-M3 初始化 |
| `main.py` | FastAPI + 多模型 ChatAgent + ChromaDB 初始化 | 改为 AppContainer：LLMRegistry、RetrievalPipeline、DecisionEngine、SkillRegistry、ResearchOrchestrator |
| `arxiv_client.py` | 按关键词返回 arXiv 元数据列表 | 升级为 PaperSearchSkill；保留客户端实现作为 Adapter |

### 2.2 当前前端主链路

| 当前文件 | 当前能力 | V2 需要增加 |
|---|---|---|
| `src/stores/messageList.ts` | 问答流、模型标签、摘要记忆、历史快照 | 接收 typed SSE；消息增加 citations/grounding/run_id；支持 Ask/Research 模式 |
| `src/api/chat.ts` | 上传临时论文、多论文 SSE、更新 memory | 拆为 qa.ts / research.ts / skill.ts；统一 SSE 解析器 |
| `views/chat/*` | 普通 Chat UI、当前绑定论文、历史会话 | 增加 ModeSwitch、DecisionTrace、EvidencePanel、ResearchPlan、ArtifactPanel |
| `views/pdf/pdfViewer.vue` | PDF 页码浏览、选中文本、浮动问答 | 支持 citation 点击跳页、高亮 evidence 文本 |
| `stores/chatHistory.ts` | 浏览器 localStorage 保存最近会话 | 保留轻量缓存；Research Task 改为后端持久化，不依赖 localStorage |

### 2.3 当前代码必须先修复的工程问题（9 项，P0 级）

| 问题 | 现状 | 必须修改原因 | 修改动作 |
|---|---|---|---|
| 检索结果被字符串化 | `query_paper_with_score_layer1_by_filter()` 返回 `str(docs)` | 丢失 documentID/page_number/score，无法做 Citation、RRF、Grounding | 返回 `List[EvidenceChunk]`，Router 不再传字符串上下文 |
| Judge 失败默认"相关" | `chat_judge_relate` 异常时 `is_relevant=True` | 失败会把不确定问题送入生成，反幻觉方向相反 | **Fail-closed**：异常 → NEED_MORE_EVIDENCE/ABSTAIN |
| 固定 k=12 | Chroma retriever `search_kwargs k=12` | 无法支持 Adaptive Top-K，也无法区分 QA/Research | 由 RetrievalConfig 与 Evidence Judge 动态调整 |
| Embedding 与方案不一致 | 当前 ONNXMiniLM_L6_V2 | 技术方案写 BGE-M3，需要真实迁移并重建向量 | 新增 BGE-M3 Embeddings；索引版本化 |
| 多文件聊天接口鉴权不完整 | `/chat/mulit_file_chat_generate_flow` 未声明 OAuth2 dependency | 竞赛演示尚可但正式软件不成熟 | 统一 `Depends(get_current_user)`，并校验文档归属 |
| 临时上传接口未鉴权 | `/document/multi_file_chat_upload` 当前未校验 user | 存在资源滥用与越权风险 | 增加身份、大小/类型限制、临时文件 TTL |
| 前端存在直接模型 API 历史实现 | `src/api/gpt.ts` 可从浏览器直接请求模型服务 | 密钥暴露风险，不应进入正式发布链路 | 废弃/删除；全部模型调用经 FastAPI |
| CORS 过宽 | `allow_origins=["*"]` 且 `allow_credentials=True` | 生产部署不安全 | 从配置读取 `FRONTEND_ORIGINS` 白名单 |
| 无数据库迁移工具 | `Base.metadata.create_all` | 新增 ResearchTask 等表后难以版本管理 | 引入 Alembic 或至少 `migrations/SQL` 版本脚本 |

### 2.4 当前已具备、必须保留的能力（V2 底座）

论文知识库、PDF 解析（PyMuPDF）、ChromaDB 双层向量检索、单/多论文对话、多模型切换（DeepSeek/Kimi K3/OpenAI-compatible）、Relatedness Judge、arXiv fallback、SSE 流式输出、历史会话、错误兜底、JWT 鉴权、翻译与笔记、论坛。

---

## 三、目标架构（来自实施方案第 2 章）

### 3.1 六层架构

交互层（Ask/Research/Experiment 入口）→ 科研决策层（模糊自然语言 → 结构化决策）→ Agent 执行层（任务计划/状态/重试）→ Research Skills（检索/解析/比较/核验/报告/量子模拟）→ 证据检索层（混合召回与重排序）→ 可信基础设施（存储/会话记忆/流式/隐私扩展）。

**分层职责原则**：Router 只负责协议，Decision 只负责判断，Retrieval 只负责找证据，Agent 只负责任务编排，Skill 只负责执行动作，Artifact 只负责交付结果。避免把所有逻辑塞回 chatAgent.py 或 router_llm.py。

### 3.2 目标后端目录（建议）

```
PaperQuery_Backend/
├─ core/
│  ├─ common/
│  │  ├─ types.py              # EvidenceChunk / Citation / AnswerPackage 等公共类型
│  │  ├─ errors.py             # 统一异常类型
│  │  └─ config.py             # Settings / 参数配置
│  ├─ retrieval/
│  │  ├─ dense.py              # BGE-M3 + Chroma Dense Retriever
│  │  ├─ sparse.py             # BM25 Retriever
│  │  ├─ fusion.py             # RRF
│  │  ├─ reranker.py           # bge-reranker-v2-m3
│  │  └─ pipeline.py           # Hybrid + Adaptive Top-K
│  ├─ decision/
│  │  ├─ schemas.py            # Pydantic typed decisions
│  │  ├─ prompts.py
│  │  └─ engine.py             # Intent/Relatedness/Evidence/Model/Completion
│  ├─ evidence/
│  │  ├─ formatter.py          # Evidence→LLM context
│  │  ├─ grounding.py          # Claim-Evidence 验证
│  │  └─ citation.py           # 引用编号/页码映射
│  ├─ research/
│  │  ├─ schemas.py            # TaskPlan / Step / TaskState
│  │  ├─ planner.py
│  │  ├─ executor.py
│  │  ├─ verifier.py
│  │  └─ orchestrator.py
│  ├─ skills/
│  │  ├─ base.py               # SkillContract
│  │  ├─ registry.py
│  │  ├─ paper_search.py
│  │  ├─ paper_reader.py
│  │  ├─ extract.py
│  │  ├─ compare.py
│  │  ├─ citation_verify.py
│  │  ├─ report.py
│  │  └─ quantum/
│  │     ├─ schemas.py
│  │     ├─ adapter.py
│  │     └─ skill.py
│  ├─ artifact/
│  │  ├─ models.py
│  │  └─ builder.py
│  ├─ agent/                   # 保留现有 ChatAgent / DataProcessAgent，逐步瘦身
│  ├─ llm/
│  └─ backend/
│     └─ router/
│        ├─ router_qa.py
│        ├─ router_research.py
│        ├─ router_skill.py
│        └─ router_document.py
├─ eval/
│  ├─ datasets/
│  ├─ scripts/
│  └─ results/
└─ vector.py
```

### 3.3 目标前端目录（建议）

```
PaperQuery_Frontend/src/
├─ api/
│  ├─ qa.ts
│  ├─ research.ts
│  ├─ skill.ts
│  └─ sse.ts
├─ stores/
│  ├─ messageList.ts
│  ├─ researchTask.ts
│  ├─ evidence.ts
│  └─ workspaceMode.ts
├─ views/
│  ├─ chat/
│  ├─ research/
│  │  ├─ ResearchView.vue
│  │  ├─ PlanPanel.vue
│  │  ├─ StepTimeline.vue
│  │  └─ ArtifactPanel.vue
│  └─ pdf/
└─ components/
   ├─ ModeSwitch.vue
   ├─ EvidencePanel.vue
   ├─ CitationChip.vue
   └─ DecisionBadge.vue
```

### 3.4 公共数据类型（V2 最大基础改造：检索/回答结果从字符串变结构化对象）

```python
# core/common/types.py
from pydantic import BaseModel, Field
from typing import Literal, Optional

class EvidenceChunk(BaseModel):
    chunk_id: str
    document_id: str
    knowledge_id: str | None = None
    source: str
    page_number: int
    text: str
    dense_score: float | None = None
    sparse_score: float | None = None
    fusion_score: float | None = None
    rerank_score: float | None = None
    section_title: str | None = None

class Citation(BaseModel):
    citation_id: str               # 如 C1
    document_id: str
    page_number: int
    chunk_id: str
    quote: str
    support_score: float | None = None

class AnswerPackage(BaseModel):
    answer: str
    citations: list[Citation] = []
    evidence_sufficient: bool = True
    grounding_passed: bool = True
    route: str = "LOCAL_RAG"
    trace_id: str | None = None
```

---

## 四、目标能力要求（来自技术方案四大创新）

### 4.1 创新一：Research Decision Engine

将 Intent、Relatedness、Evidence Sufficiency、Model Routing 与 Completion 等高频控制节点从自由文本生成中解耦，统一输出带置信度的结构化决策。初版由支持结构化输出的 LLM Judge 实现，后续可替换为专用决策模型；**不把 Jev 作为运行必需依赖**，避免对单一厂商模型形成技术依赖。

决策输出示例：

```json
{
  "decision": "EXPAND_SEARCH",
  "confidence": 0.87,
  "evidence_score": 0.41,
  "next_action": "ARXIV_SEARCH"
}
```

### 4.2 创新二：Evidence-Adaptive Hybrid RAG

检索层由 **BGE-M3 Dense 语义召回 + BM25 Sparse 关键词召回**组成，用 **Reciprocal Rank Fusion** 合并候选并经 **Reranker 重排**。与固定 Top-K 不同，根据证据分数动态决定是否扩大召回、改写 Query 或转向外部学术搜索，实现"先判断证据，再决定是否回答"。

### 4.3 创新三：Executable Research Agent

Research Mode 采用"目标—规划—执行—验证—交付"范式：用户提交科研目标 → Planner 生成任务图 → Executor 调用 Paper Search、Paper Reader、Method/Experiment Extract、Paper Compare、Citation Verify 与 Report Generate 等 Skills → Verifier 根据完成条件和证据覆盖度决定结束、补检索或重试。最终交付可直接使用的 **Artifact**（比较表、研究报告、实验结果），而非仅聊天文本。

### 4.4 创新四：Extensible Scientific Skill & Trusted Infrastructure

Skill Framework 将专业工具调用抽象为统一输入 Schema、执行器和结果解析器。量子算法模拟作为首个复杂专业 Skill：从论文识别算法与参数 → 参数校验 → 调用量子算法模拟性能优化工具 → 生成结构化实验结果与报告。机构级版本预留科研行为隐私分析接口（本地差分隐私相关技术积累），不暴露原始行为序列。

### 4.5 与常规方案能力对比（目标态）

| 能力 | 通用 LLM | 基础 PDF Chat | 基础 RAG | PaperAgent V2 |
|---|---|---|---|---|
| 单/多论文问答 | △ | ✓ | ✓ | ✓ |
| 证据充分度判断 | × | × | △ | ✓ |
| 外部证据扩展 | △ | × | × | ✓ |
| 复杂科研任务规划 | △ | × | × | ✓ |
| 科研 Artifact 交付 | △ | × | × | ✓ |
| 专业科研工具执行 | △ | × | × | ✓ |
| 可插拔 Skill 架构 | △ | × | × | ✓ |

---

## 五、技术选型（目标态）

| 模块 | 技术 | 选择依据 |
|---|---|---|
| 前端 | Vue 3 + TypeScript + Pinia | 组件化、状态可追踪，适合知识库/任务面板等复杂交互 |
| 后端 | FastAPI + Uvicorn | 异步接口、类型校验与 Python AI 生态兼容 |
| LLM | DeepSeek / Kimi / OpenAI-compatible | 统一 OpenAI-compatible 适配层，支持模型切换与路由 |
| 向量与检索 | ChromaDB + BGE-M3 + BM25 | 兼顾语义匹配与关键词/术语精确召回 |
| 排序融合 | RRF + Reranker | 融合多路候选并提升证据前排质量 |
| 任务执行 | Research Agent + Skills | 将复杂科研任务拆分为可执行、可重试步骤 |
| 传输 | SSE | 长任务与模型生成实时反馈，降低等待感知 |

---

## 六、分阶段改造要求（实施方案第 3～9 章，按序执行）

> 核心顺序：**先建立可追溯 Evidence 数据结构，再升级检索与结构化决策，然后构建 Research Task 状态机和 Skill Framework，Quantum Skill 最后作为真实专业工具落地案例接入。**

### 6.1 阶段一：重构 PDF 数据处理与索引元数据

目标：让每个检索片段拥有稳定的 `chunk_id`、页码、文档 ID 和可扩展元数据。这是附件 A1 字段设计、Evidence Panel 和三组实验可复现性的共同基础。

1. **改造 `split_text_into_chunks`**（当前 `core/utils/util.py` 只返回字符串）：改为返回文本及页内序号，优先使用 token/字符窗口 + overlap，避免英文论文中单纯 split() 造成公式、标点和段落结构丢失。

```python
# core/utils/chunking.py
from dataclasses import dataclass

@dataclass
class TextChunk:
    text: str
    index: int
    start_char: int
    end_char: int

def split_text(text: str, chunk_size: int = 1800, overlap: int = 250):
    # 首版可按字符实现；后续再替换为 token-aware splitter
    chunks = []
    start, idx = 0, 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(TextChunk(chunk, idx, start, end))
            idx += 1
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks
```

2. **参数初始值**：

| 参数 | 推荐初始值 | 依据 | 后续调优 |
|---|---|---|---|
| chunk_size | 约 1800 中文字符/等价英文字符窗口 | 兼顾段落语义与 Reranker 输入长度 | 实验一前在 1200/1800/2400 中小规模抽样 |
| overlap | 250 | 降低跨 chunk 证据断裂 | 根据 Evidence Hit Case 调整 |
| page_number | PDF 1-based 页码 | 前端直接跳页 | 固定 |
| chunk_id | `{documentID}:p{page}:c{idx}` | 稳定、可追踪、可去重 | 固定规则 |
| index_version | v2-bge-m3-001 | 支持 Embedding 变更后重建 | 每次模型/切块重大变化升级 |

3. **改造 `DataProcessAgent.add_newpaper()`**：
   - 保留 fitz 按页读取，每页调用新 `split_text()`，为每个 chunk 生成 `chunk_id`；
   - metadata 增加 `chunk_id`、`page_number`、`documentID`、`knowledgeID`、`source`、`index_version`；**字段名统一，不再混用 knowledge_name/knowledgeID**；
   - 将"写入 Chroma"和"生成 BM25 语料"拆开：DataProcessAgent 只产出 ChunkRecord，IndexManager 负责写不同索引；
   - 摘要与分类保留但升级为 **PaperCard**（摘要、研究问题、方法、贡献、数据集、指标、主要结果、局限、标签），初版可新增 JSON 字段逐步填充；
   - 处理完成后把 `index_version` 写入 Document 表，避免旧索引被误认为已完成。

```python
# dataprocessAgent.py（改造后的关键逻辑示意）
records = []
for page_num in range(len(doc)):
    page_text = doc.load_page(page_num).get_text("text")
    for ch in split_text(page_text):
        records.append({
            "id": f"{file_hash}:p{page_num+1}:c{ch.index}",
            "text": ch.text,
            "metadata": {
                "documentID": file_hash,
                "knowledgeID": knowledgeID,
                "page_number": page_num + 1,
                "chunk_index": ch.index,
                "source": filepath,
                "index_version": settings.INDEX_VERSION,
            }
        })
index_manager.add_document(records)
```

4. **向量重建策略**（从 ONNXMiniLM_L6_V2 切换到 BGE-M3 后，旧 Chroma 向量不能复用，必须显式迁移）：
   - 新增 `CHROMA_LAYER1_V2_DIR`，不覆盖旧 layer1；开发期保留旧索引用于 Basic RAG baseline；
   - 新增 `scripts/reindex_v2.py`：遍历数据库中 documentStatus=2 的 PDF，重新分块并写入 V2 Chroma 与 BM25 corpus；
   - 只有当 V2 向量数与 chunk 记录数一致、抽样检索正常后，才把默认 `RETRIEVAL_VERSION` 切到 v2；
   - 比赛实验必须保留 v1 baseline 配置，便于实验一直接比较"Basic RAG vs PaperAgent Full"。

### 6.2 阶段二：BGE-M3 + BM25 + RRF + Reranker Hybrid Retrieval

先实现稳定的固定 Hybrid Pipeline，再接 Adaptive Top-K；不要一次把所有动态逻辑混在一起。

1. **依赖调整**（`requirement.txt` 新增，版本以最终环境锁定为准）：

```
FlagEmbedding
rank-bm25
sentence-transformers      # 如 reranker 采用 CrossEncoder 路径
pydantic-settings
alembic                     # 推荐
orjson                      # 当前已有，可用于 SSE/日志
```

> BGE-M3 与 reranker 模型体积较大。比赛演示机若无法稳定联网下载，应提前将模型下载到固定目录，并通过环境变量 `BGE_M3_MODEL_PATH` / `RERANKER_MODEL_PATH` 指向本地缓存。

2. **Dense Retriever**：

```python
# core/retrieval/dense.py
class DenseRetriever:
    def __init__(self, chroma_db):
        self.db = chroma_db

    def search(self, query: str, document_ids: list[str], k: int) -> list[EvidenceChunk]:
        where = build_document_filter(document_ids)
        docs_scores = self.db.similarity_search_with_relevance_scores(
            query, k=k, filter=where
        )
        return [to_evidence(doc, score, kind="dense") for doc, score in docs_scores]
```

现有 AcadeChroma 继续作为存储层，但不再让它直接决定"最终检索策略"。建议增加 `raw_search()` 或暴露底层 Chroma 方法，由 DenseRetriever 做 EvidenceChunk 转换。

3. **Sparse BM25 Retriever**：

```python
# core/retrieval/sparse.py
class BM25Retriever:
    def __init__(self, corpus_store):
        self.store = corpus_store

    def search(self, query: str, document_ids: list[str], k: int):
        corpus = self.store.get_scope(document_ids)
        # 中文建议 jieba/字符n-gram；英文使用正则词法切分
        tokenized = [tokenize(x.text) for x in corpus]
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(tokenize(query))
        top = top_indices(scores, k)
        return [corpus[i].model_copy(update={"sparse_score": float(scores[i])}) for i in top]
```

> 说明：BM25 必须使用与 documentID 对应的 chunk corpus；不要在每次请求时从 Chroma 全量读取再构建 BM25，应在索引阶段同步生成可持久化 BM25 corpus。首版比赛规模可用 pickle/JSONL + 内存 BM25，后续替换 Elasticsearch/OpenSearch。主测试论文以英文为主时首版可用英文 tokenization；若要强调中文科研问答，建议中文 query 先做 query translation/keyword extraction。

4. **RRF 融合**（不比较原始分数，比较排名，避免两个检索器分数尺度不一致，常数 c=60）：

```python
# core/retrieval/fusion.py
from collections import defaultdict

def reciprocal_rank_fusion(rank_lists: list[list[EvidenceChunk]], c: int = 60):
    score = defaultdict(float)
    item = {}
    for ranked in rank_lists:
        for rank, e in enumerate(ranked, start=1):
            score[e.chunk_id] += 1.0 / (c + rank)
            item[e.chunk_id] = e
    merged = []
    for cid, s in sorted(score.items(), key=lambda x: x[1], reverse=True):
        merged.append(item[cid].model_copy(update={"fusion_score": s}))
    return merged
```

5. **Reranker**：

```python
# core/retrieval/reranker.py
class BGEReranker:
    def __init__(self, model):
        self.model = model

    def rerank(self, query: str, candidates: list[EvidenceChunk], top_n: int = 8):
        pairs = [[query, x.text] for x in candidates]
        scores = self.model.compute_score(pairs, normalize=True)
        rescored = [x.model_copy(update={"rerank_score": float(s)})
                    for x, s in zip(candidates, scores)]
        return sorted(rescored, key=lambda x: x.rerank_score or 0, reverse=True)[:top_n]
```

6. **RetrievalPipeline 与推荐初始参数**：

```python
# core/retrieval/pipeline.py
class RetrievalPipeline:
    def search(self, query, document_ids, cfg):
        dense = self.dense.search(query, document_ids, cfg.dense_k)
        sparse = self.sparse.search(query, document_ids, cfg.sparse_k)
        fused = reciprocal_rank_fusion([dense, sparse], c=cfg.rrf_c)
        reranked = self.reranker.rerank(query, fused[:cfg.rerank_candidates], cfg.final_k)
        return reranked
```

| 参数 | 建议初始值 | 用途 | 备注 |
|---|---|---|---|
| dense_k | 20 | Dense 候选召回 | 比最终 top-k 大，保证融合空间 |
| sparse_k | 20 | BM25 候选召回 | 同上 |
| RRF c | 60 | 排名融合平滑常数 | 常用稳健默认值；非核心调参点 |
| rerank_candidates | 24 | 送入 Cross-Encoder 的候选数 | 控制延迟 |
| final_k | 8 | 最终提供给 Evidence Judge/LLM 的证据数 | Ask Mode 6~8，Research 可更大 |
| max_context_chars | 约 18k~28k | 证据文本预算 | 按具体模型上下文调整 |

7. **Adaptive Top-K 落地顺序**：
   - V2.1：先固定 final_k=8，跑通 Hybrid 与实验一；
   - V2.2：Evidence Judge 输出 evidence_score/confidence；若低于阈值，扩大 dense_k/sparse_k 或执行 query rewrite；
   - V2.3：最多扩展 1～2 次，防止无限检索；每次扩展记录在 trace 中；
   - V2.4：Research Mode 允许更高 context budget；Ask Mode 保持低延迟。

### 6.3 阶段三：把 Relatedness Judge 升级为 Research Decision Engine

当前 `chat_judge_relate()` 已证明"先判断再路由"的方向，但职责混在 ChatAgent，Schema 仅 is_relevant/is_professional/arxiv_query_keyword，且失败默认相关。V2 应抽成独立 Decision Plane，保留兼容层。

1. **Typed Decision Schema**：

```python
# core/decision/schemas.py
from enum import Enum
from pydantic import BaseModel, Field

class IntentType(str, Enum):
    PAPER_QA = "PAPER_QA"
    MULTI_PAPER_QA = "MULTI_PAPER_QA"
    RESEARCH_TASK = "RESEARCH_TASK"
    EXPERIMENT_TASK = "EXPERIMENT_TASK"
    GENERAL_CHAT = "GENERAL_CHAT"

class IntentDecision(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0, le=1)
    reason_code: str

class EvidenceDecision(BaseModel):
    decision: str  # ANSWER / EXPAND_LOCAL / SEARCH_EXTERNAL / ABSTAIN
    confidence: float = Field(ge=0, le=1)
    evidence_score: float = Field(ge=0, le=1)
    missing_aspects: list[str] = []
    search_keywords: list[str] = []

class GroundingDecision(BaseModel):
    passed: bool
    confidence: float = Field(ge=0, le=1)
    unsupported_claims: list[str] = []
```

2. **DecisionEngine 实现原则**：
   - 优先使用模型结构化输出（Pydantic/JSON Schema），不要继续把 `clean_markdown_json_blocks + json.loads` 作为唯一方案；
   - 每个 decision 都有 fallback 规则；结构化模型不可用时用 JSON prompt，解析失败时采取保守策略（Fail-closed）；
   - Decision Engine 不负责生成最终回答，只返回 typed decision；
   - 所有 decision 输出写入 trace，便于评测 Routing Accuracy，也便于前端显示"为什么继续检索"；
   - 不把 Jev 作为运行必需依赖；当前版本由 LLM Judge 实现相同 typed decision contract，未来替换专用模型时不改业务层。

```python
# core/decision/engine.py
class DecisionEngine:
    def __init__(self, llm):
        self.llm = llm

    def decide_intent(self, query, context_meta) -> IntentDecision:
        try:
            return self.structured_invoke(IntentDecision, build_intent_prompt(query, context_meta))
        except Exception:
            # fail-safe：复杂请求宁可进入 PAPER_QA/RESEARCH_TASK 检查，也不直接胡答
            return IntentDecision(intent="PAPER_QA", confidence=0.0,
                                  reason_code="PARSER_FALLBACK")

    def decide_evidence(self, query, evidence) -> EvidenceDecision:
        if not evidence:
            return EvidenceDecision(decision="SEARCH_EXTERNAL", confidence=1.0,
                                    evidence_score=0.0)
        try:
            return self.structured_invoke(EvidenceDecision,
                                           build_evidence_prompt(query, evidence))
        except Exception:
            return EvidenceDecision(decision="EXPAND_LOCAL", confidence=0.0,
                                    evidence_score=0.0)
```

3. **兼容现有 `chat_judge_relate()`**：
   - 第一步：不删除 ChatAgent.chat_judge_relate()，先改成调用 DecisionEngine.relatedness()；保持 router_llm.py 原接口可用；
   - 第二步：新增 router_qa.py，新的 Ask Mode 前端改走 /qa/stream；旧 /chat/* 在一个版本周期内作为兼容接口；
   - 第三步：前端全部迁移后，把 Relatedness prompt 从 myprompts.py 移到 decision/prompts.py；ChatAgent 只保留生成、摘要等能力。

4. **建议路由规则**：

| 条件 | 动作 | 原因 |
|---|---|---|
| 用户未绑定论文 + 普通科研问答 | GENERAL_CHAT 或外部搜索（按产品策略） | 避免把空知识库误当本地证据 |
| 绑定论文 + 高相关 + 证据充分 | LOCAL_ANSWER | 低延迟主路径 |
| 相关但证据不足 | EXPAND_LOCAL → QUERY_REWRITE | 先在用户论文范围内找齐 |
| 专业问题且本地明显不足 | SEARCH_EXTERNAL | 调用 arXiv/PaperSearchSkill |
| 非专业闲聊 | GENERAL_CHAT | 不做昂贵检索 |
| Judge 异常或置信度很低 | 保守扩检/提示证据不足 | 反幻觉优先，不默认"相关可答" |

### 6.4 阶段四：Evidence、Citation 与 Grounding Verify

1. **不再把 docs 转成字符串**：保持证据对象直到最后一步。LLM 上下文只在 `evidence/formatter.py` 中生成，同时保留 Citation 映射表。

```python
# core/evidence/formatter.py
def format_evidence(chunks: list[EvidenceChunk]):
    parts, citation_map = [], {}
    for i, e in enumerate(chunks, 1):
        cid = f"C{i}"
        parts.append(
            f"[{cid}] document={e.document_id} page={e.page_number} chunk={e.chunk_id}\n{e.text}"
        )
        citation_map[cid] = e
    return "\n".join(parts), citation_map
```

2. **生成回答必须强制引用 Citation ID**。生成 prompt 要求事实性结论后使用 [C1]、[C2]，且禁止生成未提供的 Citation ID。前端最终不直接把模型 Citation 当真，由后端根据 citation_map 转换为 documentID/page/chunk。

```
SYSTEM RULES（示意）
1. 只使用提供的 Evidence 回答可验证事实。
2. 每个关键事实必须引用 [C#]。
3. Evidence 不足时明确写"当前证据不足"，不得补写具体数字/实验结论。
4. 不得生成 Evidence 列表中不存在的 Citation ID。
```

3. **Grounding Verify 两阶段方案**：

| 阶段 | 实现 | 优点 | 缺点 |
|---|---|---|---|
| 比赛首版 | 生成完整 AnswerPackage → Grounding Judge → 再 SSE 分片输出 | 最稳，易做实验和引用核验 | 首 token 延迟变高 |
| 后续优化 | 正文 token 边生成边展示，完成后发送 grounding/citation 事件 | 交互更快 | 可能出现先展示后标警告的复杂 UX |

> 为省赛稳定性，建议采用第一种：内部非流式生成结构化 AnswerPackage，验证后再通过 SSE 模拟分片输出。用户仍看到流式效果，但最终内容先经过 Grounding。

```python
# core/evidence/grounding.py
class GroundingVerifier:
    def verify(self, answer: str, citations: list[Citation], evidence_map):
        # 首版：LLM Judge + 规则校验组合
        # 规则1：Citation ID 必须存在
        # 规则2：具体数字/数据集名等高风险 claim 必须有 citation
        # 规则3：Judge 输出 unsupported_claims
        ...
```

4. **SSE 事件协议统一**：

```
event: meta
data: {"trace_id":"...","route":"LOCAL_RAG"}

event: delta
data: {"text":"..."}

event: citations
data: {"items":[{"id":"C1","documentID":"...","page":4,"chunk_id":"..."}]}

event: grounding
data: {"passed":true,"confidence":0.91}

event: done
data: {"usage": {...}}

event: error
data: {"code":"MODEL_TIMEOUT","message":"..."}
```

前端不再只把 SSE 当纯字符串。`src/api/sse.ts` 负责解析 event 类型，messageList.ts 根据类型分别更新正文、citation 和状态。

### 6.5 阶段五：实现 Research Mode（Planner → Executor → Verifier → Artifact）

Research Mode 是 V2 最大的产品升级。实现时先做**可持久化的任务状态机**：任务有 task_id、step_id、状态和重试记录，前端才能展示真实进度，实验二才能测 Task Completion。

1. **数据 Schema**：

```python
# core/research/schemas.py
class PlanStep(BaseModel):
    step_id: str
    title: str
    skill: str
    depends_on: list[str] = []
    input: dict = {}
    success_criteria: list[str] = []

class TaskPlan(BaseModel):
    task_id: str
    goal: str
    steps: list[PlanStep]
    expected_artifacts: list[str]

class StepResult(BaseModel):
    step_id: str
    status: Literal["SUCCESS","FAILED","NEED_MORE_EVIDENCE"]
    output: dict = {}
    evidence_ids: list[str] = []
    error: str | None = None
```

2. **Planner**：只生成"有限技能集合"中的计划，不允许凭空生成工具名。Prompt 注入 SkillRegistry 的 name/description/input_schema，输出 TaskPlan。计划生成后先做静态校验：skill 是否存在、依赖是否循环、必需输入是否可由已有上下文或前置步骤产生。

3. **Executor**：首版顺序执行即可，不要为了"多 Agent"先做复杂并行；只有互不依赖的 Paper Reader/Extract 步骤后续再并行；优先保证可观测和可重试。每个 SkillRun 设置 timeout、retry_limit、idempotency_key，防止网络失败重复创建 Artifact。

4. **Verifier 与 Completion Decision**：检查"任务是否满足成功条件"，而不是再生成一段总结。例如比较 5 篇论文的方法/数据集/指标，成功条件结构化为 paper_count>=5、required_columns 全部存在、citation_coverage>=阈值。

```python
def verify_compare_artifact(artifact, criteria):
    checks = {
        "paper_count": len(artifact.rows) >= criteria.min_papers,
        "columns": all(c in artifact.columns for c in criteria.required_columns),
        "citations": artifact.citation_coverage >= criteria.min_citation_coverage,
    }
    return all(checks.values()), checks
```

5. **Artifact Builder**：

| Artifact 类型 | 结构 | 前端展示 | 文件导出 |
|---|---|---|---|
| PaperList | 论文元数据 + relevance | 卡片列表 | CSV/JSON |
| ComparisonTable | 列定义 + rows + citations | 表格 | CSV/XLSX（后续） |
| ResearchReport | Markdown sections + citations | Markdown | MD/PDF（后续） |
| EvidenceTable | claim/evidence/page | Evidence Panel | CSV |
| ExperimentReport | config/results/logs | 实验结果卡 | JSON/MD/PDF |

### 6.6 阶段六：Skill Framework 与 Quantum Experiment Skill

1. **SkillContract**：所有工具遵守同一生命周期：Schema 校验 → 权限判断 → execute → 结果标准化 → 记录 SkillRun。

```python
# core/skills/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel

class SkillResult(BaseModel):
    ok: bool
    output: dict = {}
    evidence: list[str] = []
    artifacts: list[dict] = []
    error_code: str | None = None
    error_message: str | None = None

class BaseSkill(ABC):
    name: str
    description: str
    input_model: type[BaseModel]
    permission: str = "read"
    timeout_s: int = 60

    def validate(self, raw: dict):
        return self.input_model.model_validate(raw)

    @abstractmethod
    async def execute(self, data: BaseModel, ctx) -> SkillResult:
        ...

    async def run(self, raw: dict, ctx):
        data = self.validate(raw)
        return await self.execute(data, ctx)
```

2. **SkillRegistry**：

```python
# core/skills/registry.py
class SkillRegistry:
    def __init__(self):
        self._skills = {}

    def register(self, skill: BaseSkill):
        if skill.name in self._skills:
            raise ValueError(f"duplicated skill: {skill.name}")
        self._skills[skill.name] = skill

    def get(self, name: str) -> BaseSkill:
        return self._skills[name]

    def describe(self):
        return [{"name": s.name,
                 "description": s.description,
                 "input_schema": s.input_model.model_json_schema()}
                for s in self._skills.values()]
```

3. **首批内置 Research Skills**：

| Skill | 复用当前代码 | 新增内容 | 验收 |
|---|---|---|---|
| paper_search | arxiv_client.py | 包装成 BaseSkill；返回结构化 paper list，不只 Markdown 链接 | 关键词→≥N 个元数据结果；异常可恢复 |
| local_retrieval | AcadeChroma | 调用 RetrievalPipeline | 返回 EvidenceChunk |
| paper_reader | DataProcessAgent/PDF | 按 documentID/page/section 读取原文 | 能够按 Citation 精确回读 |
| method_extract | LLM | 结构化 MethodCard | 字段完整率满足测试 |
| experiment_extract | LLM | 结构化 ExperimentConfig | 可供 Quantum Skill |
| paper_compare | LLM + Artifact | 表格 Schema + citation | 字段/citation 可验证 |
| citation_verify | GroundingVerifier | 批量校验 claim-evidence | 输出 pass/unsupported |
| report_generate | LLM + Artifact | Markdown 报告生成器 | 结构固定、引用可追踪 |

4. **Quantum Skill Adapter（必须以实际量子软件接口为准）**：

> ⚠️ 重要事实约束：当前仅有"量子算法模拟性能优化工具软件 V1.0"的软件著作权证书，**未提供其源代码、CLI 参数或 HTTP API**。适配边界可设计到可直接实施，但**不能凭空声称该工具当前支持哪些具体算法/参数**。开发时必须先确认真实调用接口，再完成 adapter.py。

```python
# core/skills/quantum/schemas.py（字段需按真实工具调整）
class QuantumExperimentInput(BaseModel):
    algorithm: str
    parameters: dict
    shots: int | None = None
    backend: str | None = "simulator"
    timeout_s: int = 120

class QuantumExperimentOutput(BaseModel):
    status: str
    normalized_metrics: dict
    raw_result_path: str | None = None
    stdout_tail: str | None = None
```

```python
# adapter.py：CLI 模式示意
class QuantumToolAdapter:
    async def run(self, data: QuantumExperimentInput):
        cmd = build_whitelisted_command(data)  # 不允许直接拼接用户原始字符串
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=data.timeout_s)
        if proc.returncode != 0:
            raise QuantumToolError(stderr.decode(errors="ignore"))
        return parse_quantum_output(stdout)
```

- 如果量子软件本身是 Python 包：优先直接 import 调用，避免 subprocess；
- 如果是桌面软件且没有 API：不要让 Agent 直接"点 GUI"；优先给原软件增加一个 CLI/HTTP wrapper；
- 算法名、参数名必须白名单；文件路径只能落在 task sandbox；**禁止 Shell=True**；
- 每次运行保存 config.json、stdout/stderr、raw result 和 normalized result，实验三直接复用这些原始记录。

### 6.7 阶段七：前端从 Chat UI 升级为 Research Workspace

1. **模式切换**：在 HeaderArea.vue 的 ModelBox 旁增加 Ask / Research / Experiment 三段式切换，而不是另起独立产品。

```typescript
// stores/workspaceMode.ts
export type WorkspaceMode = 'ask' | 'research' | 'experiment'
export const useWorkspaceModeStore = defineStore('workspaceMode', () => {
  const mode = ref<WorkspaceMode>('ask')
  return { mode }
})
```

- HeaderArea.vue：增加 ModeSwitch + decision status；
- InputBox.vue：根据 mode 改 placeholder；Research Mode 允许显示"生成计划后确认/执行"按钮；
- MainArea.vue：Ask 继续显示 MessageBox；Research 显示 StepTimeline + ArtifactPanel；Experiment 显示参数卡和执行结果；
- SideBar.vue：Research 模式显示任务历史，不再只显示 localStorage 聊天。

2. **Evidence Panel 与 Citation 点击跳页**：

```typescript
// Message 类型扩展
export type Citation = {
  id: string
  documentID: string
  page: number
  chunkId: string
  quote: string
}

export type Message = {
  ...
  citations?: Citation[]
  groundingPassed?: boolean
  traceId?: string
}
```

- 新增 CitationChip.vue：显示 [C1]，点击触发 router.push 到 `/home/pdfInfo/{knowledgeID}/{documentID}?page=4&chunk=C1`；
- pdfViewer.vue 初始化 page 时读取 route.query.page；若包含 quote/chunk，可在 text layer 中做临时高亮；首版至少实现准确跳页；
- 新增 EvidencePanel.vue：右侧展示 Citation 列表、论文名、页码、证据片段和 support score；
- Grounding 未通过时，在答案顶部显示"部分结论未通过证据核验"，不要静默展示。

3. **Research Mode UI**：

| 组件 | 状态来源 | 主要展示 |
|---|---|---|
| PlanPanel.vue | TaskPlan | 任务目标、steps、依赖关系 |
| StepTimeline.vue | ResearchStep[] | PENDING/RUNNING/SUCCESS/FAILED、耗时 |
| DecisionBadge.vue | SSE decision event | 本地证据不足/扩展检索/验证通过等 |
| ArtifactPanel.vue | Artifact[] | Comparison Table、Report、Evidence Table、Experiment Report |
| ResearchHistory.vue | /research/tasks | 历史任务、状态、重新打开 |

4. **前端 SSE 解析器统一**（替换 chat.ts 中"每个网络 chunk 直接 parsePack2"的模式，避免 SSE 半包/多事件合并造成解析异常）：

```typescript
// api/sse.ts（伪代码）
export async function consumeSSE(response: Response, onEvent: (evt:SSEEvent)=>void) {
  const reader = response.body!.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const { events, rest } = parseSSEFrames(buffer)
    buffer = rest
    events.forEach(onEvent)
  }
}
```

### 6.8 阶段八：数据库与持久化改造

1. **新增数据库表**：

| 表 | 关键字段 | 用途 |
|---|---|---|
| research_tasks | task_id,lid,goal,mode,status,plan_json,created_at,updated_at | Research Mode 主任务 |
| research_steps | step_id,task_id,skill_name,status,input_json,output_json,error | 任务步骤与重试 |
| skill_runs | run_id,task_id,step_id,duration_ms,status,error,trace_json | 工具调用审计/实验原始数据 |
| artifacts | artifact_id,task_id,type,title,content/path,metadata_json | 最终研究成果 |
| evidence_records | evidence_id,task/session,documentID,page,chunk_id,scores,text_hash | 证据追踪 |
| chat_sessions（可选） | session_id,lid,title,model,memory,created_at | 把重要会话从 localStorage 持久化到服务端 |

2. **models.py 增量示意**：

```python
class ResearchTask(Base):
    __tablename__ = "research_tasks"
    id = Column(Integer, primary_key=True)
    task_id = Column(String(64), unique=True, index=True, nullable=False)
    lid = Column(String(255), index=True, nullable=False)
    goal = Column(Text, nullable=False)
    mode = Column(String(32), default="research")
    status = Column(String(32), index=True, nullable=False)
    plan_json = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
```

3. **字段命名统一**：当前数据库字段是 `uid`，前端称 `documentID`，Chroma metadata 也使用 `documentID`。数据库暂不改列名以避免迁移风险，但**代码层统一暴露 document_id**；Repository/CRUD 负责把 Document.uid 映射为 document_id。`knowledge_name` 停止新增，统一 `knowledgeID`。

4. **迁移方式**：引入 Alembic（`alembic init migrations`，把现有 Base metadata 接入 env.py）；生成 migration 001_research_tables；SQLite 开发环境先验证升级/降级；生产/比赛演示数据库升级前备份 acadeagent.db。**禁止继续只依赖 Base.metadata.create_all 作为结构升级手段**。

### 6.9 阶段九：API 与路由重构

1. **保留旧 API，新增 V2 API**：

| 方法 | 路径 | 输入 | 输出 |
|---|---|---|---|
| POST | /qa/stream | question, document_ids, model?, context? | typed SSE：meta/delta/citations/grounding/done |
| POST | /research/tasks | goal, document_ids, options | task_id + 初始状态 |
| GET | /research/tasks/{task_id} | - | Task + Plan + Steps + Artifacts |
| GET | /research/tasks/{task_id}/events | - | SSE progress/decision/skill/artifact |
| POST | /research/tasks/{task_id}/cancel | - | cancel state |
| POST | /skills/quantum/validate | QuantumExperimentInput | validated params / errors |
| GET | /evidence/{trace_id} | - | Evidence records + citations |

2. **router_llm.py 具体拆分**：
   - 把 get_chat_agent() 保留到 services/llm_service.py，避免每个 router 自己找 model；
   - 把 chat_multi_file_generate_flow 的"翻译→检索→judge→arxiv→生成"拆为 QAService.answer()；Router 只验证请求并返回 StreamingResponse；
   - 原 `/chat/mulit_file_chat_generate_flow`（拼写错误）保留 deprecated wrapper，内部调用新 /qa 服务；前端迁移后再移除；
   - 新增 get_current_user 鉴权并校验 document_ids 是否属于当前用户/允许的临时会话。

```python
# router_qa.py
@router.post("/qa/stream")
async def qa_stream(req: QARequest,
                    request: Request,
                    user=Depends(get_current_user)):
    service: QAService = request.app.container.qa_service
    verify_document_scope(user, req.document_ids)
    return StreamingResponse(
        service.stream(req, user=user),
        media_type="text/event-stream"
    )
```

### 6.10 阶段十：配置、模型路由、安全与可观测性

1. **Settings 集中化**：

```python
# core/common/config.py
class Settings(BaseSettings):
    INDEX_VERSION: str = "v2-bge-m3-001"
    BGE_M3_MODEL_PATH: str
    RERANKER_MODEL_PATH: str
    DENSE_K: int = 20
    SPARSE_K: int = 20
    RRF_C: int = 60
    FINAL_K: int = 8
    EVIDENCE_THRESHOLD: float = 0.65
    MAX_RETRIEVAL_ROUNDS: int = 2
    FRONTEND_ORIGINS: list[str] = ["http://127.0.0.1:8080"]
    SKILL_SANDBOX_DIR: str = "./res/tasks"
    class Config:
        env_file = ".env"
```

2. **Model Router 首版不要复杂化**（"规则 + 配置"实现，不需要训练模型）：

| 任务 | 默认模型策略 | 理由 |
|---|---|---|
| Intent/Evidence/Grounding Judge | 低温度、支持结构化输出的稳定模型 | 输出短、格式敏感 |
| 普通 Ask QA | DeepSeek/Kimi 中低成本模型 | 响应速度 |
| Research planning/综合报告 | 长上下文/推理较强模型 | 复杂度更高 |
| 摘要/标签 | 固定模型 | 保证 PaperCard 稳定 |

3. **安全加固清单（必须全部落实）**：
   - 移除浏览器直连模型服务的 apiKey 路径（src/api/gpt.ts）；
   - 所有上传接口检查 MIME、扩展名、文件大小；文件名使用安全重命名，避免路径穿越；
   - 临时文件设置 TTL 和清理任务；
   - 所有 Research Skill 输入经过 Pydantic Schema；执行器禁用任意 Shell 字符串；
   - 高风险 Skill（未来代码执行、外部写操作）支持 permission=confirm 并由前端人工确认；
   - CORS 使用环境变量白名单；
   - 日志不得记录完整 API Key、密码、敏感论文全文；Evidence 日志可存 hash/截断文本。

4. **Trace 与日志**：每次 QA/Research 请求生成 trace_id，至少记录：user/task/session（匿名内部ID）、query / intent decision、retrieval config + candidate chunk ids + scores、evidence decision / query rewrite / external search、model name + latency + token usage、citations / grounding result、skill run args（敏感字段脱敏）/ status / duration / error、git commit hash / INDEX_VERSION。

---

## 七、三组核心实验（必须嵌入工程，可脚本重算）

### 7.1 eval 目录结构

```
eval/
├─ datasets/
│  ├─ qa_200.jsonl
│  ├─ research_30.jsonl
│  └─ quantum_20.jsonl
├─ scripts/
│  ├─ run_qa_eval.py
│  ├─ score_grounding.py
│  ├─ run_research_eval.py
│  └─ run_quantum_eval.py
├─ configs/
│  ├─ basic_rag.yaml
│  └─ paperagent_full.yaml
└─ results/
   └─ <run_id>/
      ├─ config.json
      ├─ raw.jsonl
      ├─ summary.csv
      └─ environment.json
```

每次评测至少记录 input、expected、retrieved evidence、route、model output、citations、tool args、score、timestamp 和代码 commit hash。

### 7.2 实验一：可信论文问答与反幻觉

- **目的**：验证 Decision Engine + Evidence-Adaptive Hybrid RAG 是否能在保持正确性的同时减少无证据事实陈述。
- **测试集**：30 篇公开论文 + 200 个问题（120 个单论文可答、40 个跨论文、40 个本地证据不足），预标注 Gold Evidence 与预期检索范围。
- **对比系统**：

| 对比系统 | 检索/控制策略 | 主要作用 | 评价指标 |
|---|---|---|---|
| LLM Only | 不提供论文证据 | 观察无检索约束下的生成表现 | Answer Accuracy / Unsupported Claim Rate |
| Basic RAG | 固定 Top-K Dense Retrieval | 作为现有论文问答基线 | Accuracy / UCR / Citation Accuracy |
| PaperAgent Full | Hybrid Retrieval + Evidence Decision + Grounding | 验证可信检索与结构化决策的增益 | Accuracy / UCR / Citation Accuracy |

- **评价方法**：Answer Accuracy（按 Gold Evidence 与答案要点人工核验）；Unsupported Claim Rate（回答拆为事实性 Claim，标 Supported/Unsupported/Contradicted）；Citation Accuracy（引用片段是否真正支撑对应 Claim）。
- **有效性判定**：三项指标形成一致改善，重点观察相对 Basic RAG 的正确率提升、无证据陈述下降、引用可验证性。
- **代码路径**：Basic RAG 配置用旧 Dense Store/final_k 固定，不调用 Decision/External/Grounding；PaperAgent Full 走新 QAService，保存 EvidenceChunk、Decision、AnswerPackage；人工标注用 CSV/JSONL（每条 factual claim 标 Supported/Unsupported/Contradicted）；脚本自动计算三项指标。

### 7.3 实验二：Research Mode 复杂科研任务

- **测试集**：30 个端到端任务（10 个文献调研、10 个多论文比较、10 个科研整理/Related Work），预定义必需字段、引用要求、完成条件和合格成果标准。
- **对比系统**：

| 对比系统 | 任务规划 | 工具/Skill 调用 | 交付形式 | 核心指标 |
|---|---|---|---|---|
| Basic Multi-Paper RAG | 无显式任务图 | 以多文档检索+生成回答为主 | 聊天回答 | Task Completion / Citation Correctness / Time |
| PaperAgent Research Mode | Planner 定义步骤与完成条件 | Search / Read / Extract / Compare / Verify | Comparison Table / Report / Citations | Task Completion / Artifact Completeness / Citation Correctness / Time |

- **指标解释**：Task Completion（关键子任务全部完成）；Artifact Completeness（预定义字段/表格/报告结构完成比例）；Citation Correctness（引用能否支撑对应结论）；Time-to-Qualified-Artifact（提交任务到获得满足验收标准成果的总时间，含必要人工补问/修正）。
- **典型用例**："比较给定 5 篇 RAG 论文的检索策略、Reranker、数据集、评价指标和主要实验结果，输出比较表，并生成带引用的 Related Work 框架。"验收字段：5 篇论文均覆盖；方法/数据集/指标完整；关键结果有证据；引用可追溯。
- **代码路径**：30 个任务预定义 required_fields / min_papers / citation_requirement / success criteria；Basic 直接调用 QAService 一次生成；Research Mode 调用 ResearchOrchestrator；Artifact Builder 输出结构化 JSON 同时渲染 Markdown，**评价优先从 JSON 读取**，不从自然语言报告重新解析；Time-to-Qualified-Artifact 从 task create 时间到 verifier passed 时间计算。

### 7.4 实验三：Quantum Experiment Skill 专业工具执行

- **测试集**：20 个量子科研任务，全部限定在量子算法模拟性能优化工具实际支持的算法与参数范围内，为每个任务预定义正确参数和预期执行状态。
- **对比系统**：

| 对比系统 | 参数抽取方式 | 参数校验 | 工具调用 | 核心指标 |
|---|---|---|---|---|
| Prompt-based Tool Calling | 模型直接生成工具参数 | 仅依赖提示词约束 | 直接调用 | Parameter Extraction / Valid Tool Input / Execution Success |
| PaperAgent Quantum Skill | 结构化 Schema 抽取 | 类型、必填项与范围 Validator | Skill Adapter 调用并标准化返回 | Parameter Extraction / Valid Tool Input / Execution Success / Report Completeness |

- **执行链路**：论文解析 → 算法识别 → 参数抽取 → Schema 类型/范围校验 → Skill Routing → 调用量子模拟工具 → 标准化结果 → 实验报告。
- **代码路径**：20 个 Quantum Task 只能选真实工具支持的算法/参数；每条 gold 保存 expected algorithm/parameters/expected executable state；Prompt Tool Calling baseline 跳过 Schema/Validator 直接让模型生成工具参数后执行（必须在隔离环境）；自动计算四项指标。

### 7.5 三组实验的证明关系

| 验证目标 | 关键技术 | 对应测试 | 有效性判定 |
|---|---|---|---|
| 可信 | Decision Engine + Evidence-Adaptive RAG | 实验一 | 正确率、无证据陈述和引用正确性形成一致改善 |
| 可执行 | Planner + Research Skills + Verifier | 实验二 | 复杂任务完成度和成果完整度稳定优于基础 RAG |
| 可扩展 | Skill Framework + Quantum Tool | 实验三 | 参数合法性、工具执行成功率和报告完整度达到稳定可用水平 |

---

## 八、实施顺序、分支策略与验收门槛（实施方案第 14 章）

### 8.1 M0~M8 阶段（不要先做最炫的 Research UI，先把可追溯证据打通）

| 阶段 | 建议分支 | 预计工作量 | 完成门槛 |
|---|---|---|---|
| M0 基线冻结 | release/v1-baseline | 0.5 天 | 打 tag；现有问答可运行；保存 baseline demo |
| M1 Evidence 数据结构 + BGE-M3 | feature/retrieval-v2 | 2~3 天 | V2 索引可重建；EvidenceChunk 保留页码/score |
| M2 BM25+RRF+Reranker | feature/hybrid-rag | 2~3 天 | HybridPipeline 单元测试通过；QA 可返回结构化 evidence |
| M3 Decision + Grounding | feature/decision-evidence | 2~3 天 | 证据不足可扩检/拒答；Citation 可点击跳页 |
| M4 Research 状态机 | feature/research-mode | 3~5 天 | 30 个任务中可稳定跑 Search/Extract/Compare/Report 链路 |
| M5 Skill Framework | feature/skills | 2 天 | Registry/SkillRun/timeout/retry 完成 |
| M6 Quantum Adapter | feature/quantum-skill | 2~4 天 | 真实工具至少完成一类算法端到端调用 |
| M7 UI polish + Artifact | feature/research-ui | 2~3 天 | Plan/Timeline/Evidence/Artifact UI 完整 |
| M8 Eval & freeze | release/v2-competition | 3~5 天 | 三组实验可复现；A1/A2/A3 可生成 |

### 8.2 每个阶段的回滚点（必须保留）

- 始终保留 v1-baseline tag 与旧 Chroma 路径，任何新索引问题都可切回 Basic RAG；
- 新 /qa/stream 与旧 /chat/* 并存至少一个迭代，前端迁移失败可回退；
- Research Mode 与 Ask Mode 解耦；Research 出问题不能影响普通论文问答；
- Quantum Skill 以插件注册，工具不可用时只隐藏 Experiment Mode，不影响主系统。

### 8.3 "能提交比赛"的最小完成定义（Definition of Done）

1. Ask Mode：单/多论文问答，答案带可点击 Citation，Evidence Judge 在证据不足时能扩检/提示不足；
2. Hybrid Retrieval：BGE-M3 + BM25 + RRF + Reranker 真实运行，非 PPT 概念；
3. Research Mode：至少覆盖"文献调研 / 多论文比较 / Related Work 整理"三类任务，Plan 和 Artifact 可见；
4. Skill Framework：至少注册 6 个 Research Skills，日志可查；
5. Quantum Skill：真实调用量子工具完成至少一个完整可重复流程；
6. 三组实验：脚本、原始数据、config、结果表完整保留；
7. 所有最终技术方案中的"已实现"表述都能在代码、Demo 或 A3 数据中找到对应证据。

### 8.4 开发流程与阶段验收（P0/P1/P2）

| 阶段 | 关键任务 | 验收标准 |
|---|---|---|
| P0 可信检索 | BGE-M3+BM25+RRF+Reranker、Evidence Judge、引用元数据 | 实验一可重跑；证据可追溯 |
| P1 科研执行 | Research Planner、Skill Registry、Artifact、Quantum Skill | 实验二/三端到端跑通 |
| P2 工程打磨 | 模型路由、错误恢复、部署脚本、UI 状态与测试报告 | 演示稳定、安装部署可复现 |

---

## 九、最终验收清单（实施方案附录 D，逐项通过才可交付）

- [ ] 旧版单论文/多论文 Ask 能力无回归；DeepSeek/Kimi/OpenAI-compatible 均能正常调用；
- [ ] BGE-M3、BM25、RRF、Reranker 在实际运行日志中可见，并有独立配置；
- [ ] 每个 EvidenceChunk 都能追踪 documentID、page_number、chunk_id；
- [ ] 证据不足问题不会直接强答，Decision trace 能显示扩检/外部搜索/证据不足；
- [ ] 最终答案 Citation 点击能打开正确 PDF 页码；
- [ ] Grounding Verify 输出可记录，可在失败时标记或触发重试；
- [ ] Research Task 有 task_id、plan、steps、status、artifacts，刷新页面后状态仍存在；
- [ ] SkillRegistry 能列出内置 skills，Planner 不会调用未注册技能；
- [ ] Quantum Skill 使用真实工具接口，参数经过 Schema/Validator，执行日志可保存；
- [ ] Ask、Research、Experiment 三种 UI 模式互不干扰；
- [ ] /chat/mulit_file_chat_generate_flow 等旧接口有兼容或已完成迁移；新接口全部鉴权；
- [ ] 前端不存在可暴露真实模型 API Key 的直连路径；
- [ ] 三组实验全部有 dataset/raw/config/summary，结果可通过脚本重算；
- [ ] A1 架构图/字段/参数与 release 分支完全一致；
- [ ] A2 所选 8 个代码片段均来自 release 分支且可解释输入/输出/异常/作用。

---

## 十、代码改造硬性规则

1. **公共类型先行**：先统一 `EvidenceChunk / Citation / AnswerPackage`，再写 Planner/UI；检索结果和回答结果全程保持结构化对象，不得转字符串后再解析；
2. **Fail-closed 优先**：所有 Judge 异常时采取保守策略（扩检/拒答/提示证据不足），禁止默认"相关可答"；
3. **兼容优先**：新 /qa/stream 与旧 /chat/* 并存至少一个迭代；不删除可运行能力；
4. **安全底线**：删除 src/api/gpt.ts 直连路径；上传鉴权 + MIME/大小限制 + TTL；CORS 白名单；Skill 执行禁用任意 Shell 字符串；禁止 Shell=True；
5. **安全执行**：BGE-M3/Reranker 模型用本地缓存路径（BGE_M3_MODEL_PATH / RERANKER_MODEL_PATH）；执行命令用参数数组 subprocess，不用 shell 字符串；
6. **量子工具事实约束**：不得编造量子工具支持的能力；必须先确认真实接口再实现 adapter；
7. **命名约定**：代码层统一 document_id（DB 列 uid 暂不改名，由 CRUD 映射）；停止新增 knowledge_name；
8. **可复现**：三组实验的 dataset/raw/config/summary 全部落盘，指标由脚本重算，禁止手工 Excel 结论；
9. **写码规范**：Python 用 Pydantic 做输入校验；前端 SSE 统一走 sse.ts 解析器；类型定义放公共位置；
10. **文档同步**：每完成一个阶段同步更新 README、A1 设计草稿和 eval config；最终 release 冻结后统一生成附件 A1/A2/A3。

---

## 十一、推荐请求/响应 Schema（附录 B）

```json
# QARequest
{
  "question": "比较这两篇论文的主要方法",
  "document_ids": ["docA", "docB"],
  "model": "deepseek",
  "mode": "ask",
  "conversation_context": "..."
}

# research task create
{
  "goal": "比较5篇RAG论文的检索策略、数据集和指标，并形成Related Work草稿",
  "document_ids": ["..."],
  "options": {
    "allow_external_search": true,
    "max_papers": 10,
    "output_artifacts": ["comparison_table", "report"]
  }
}

# Quantum Skill validate
{
  "algorithm": "<来自真实工具白名单>",
  "parameters": {"...": "..."},
  "backend": "simulator"
}
```

---

## 十二、.env.example / Settings 建议项（附录 C）

```env
# Models
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE=
KIMI_API_KEY=
KIMI_API_BASE=
OPENAI_API_KEY=
OPENAI_API_BASE=

# Retrieval
INDEX_VERSION=v2-bge-m3-001
BGE_M3_MODEL_PATH=./models/bge-m3
RERANKER_MODEL_PATH=./models/bge-reranker-v2-m3
CHROMA_LAYER1_V2_DIR=./res/layer1_v2
BM25_INDEX_DIR=./res/bm25
DENSE_K=20
SPARSE_K=20
RRF_C=60
RERANK_CANDIDATES=24
FINAL_K=8
EVIDENCE_THRESHOLD=0.65
MAX_RETRIEVAL_ROUNDS=2

# Research / Skill
SKILL_SANDBOX_DIR=./res/tasks
SKILL_DEFAULT_TIMEOUT=120
RESEARCH_MAX_STEPS=12
RESEARCH_MAX_RETRIES=2

# Security / Web
FRONTEND_ORIGINS=http://127.0.0.1:8080
MAX_UPLOAD_MB=50
TMP_FILE_TTL_HOURS=24

# Quantum（按实际工具补齐）
QUANTUM_TOOL_MODE=cli
QUANTUM_TOOL_PATH=
QUANTUM_TOOL_URL=
```

---

## 十三、现有文件逐项修改清单（附录 A，共 20 项）

| 文件 | 动作 | 具体目标 |
|---|---|---|
| PaperQuery_Backend/main.py | 修改 | 引入 Settings/AppContainer；初始化 RetrievalPipeline、DecisionEngine、SkillRegistry、ResearchOrchestrator；CORS 白名单 |
| PaperQuery_Backend/vector.py | 修改 | BGE-M3 初始化、index_version、重建策略、失败原因记录；保留 worker |
| core/agent/chatAgent.py | 瘦身 | 移出 Relatedness；保留生成/摘要/LLM 适配，最终可并入 QAService |
| core/agent/dataprocessAgent.py | 修改 | 结构化 ChunkRecord、PaperCard、IndexManager；统一 metadata |
| core/vectordb/chromadb.py | 修改 | 变成 Dense Store Adapter；返回结构化 Doc+score，不再 str(docs) |
| core/llm/LLM.py | 修改 | 模型注册配置化；结构化输出/模型能力元数据；修正 token count 实现 |
| core/llm/myprompts.py | 拆分 | Judge prompt→decision/prompts.py；Answer prompt→evidence/prompts.py；Research prompt→research/prompts.py |
| core/backend/router/router_llm.py | 兼容/拆分 | 保留 deprecated endpoint；新增 router_qa.py 与 service |
| core/backend/router/router_document.py | 修改 | 鉴权、文件安全、临时文件 TTL；上传完成后使用统一 IndexManager |
| core/backend/db/models.py | 修改 | 新增 ResearchTask/Step/SkillRun/Artifact/EvidenceRecord |
| core/backend/router/req_res_schema.py | 修改 | QARequest、ResearchTaskCreate、QuantumValidate 等 Schema |
| arxiv_client.py | 保留+封装 | 被 PaperSearchSkill 调用；返回结构化结果 |
| Frontend src/api/chat.ts | 拆分 | qa.ts + sse.ts；旧接口兼容 |
| Frontend stores/messageList.ts | 修改 | typed SSE；citations/grounding/trace |
| Frontend stores/chatHistory.ts | 保留 | Ask 本地缓存；Research 历史改服务端 |
| Frontend views/chat/HeaderArea.vue | 修改 | ModeSwitch + decision status |
| Frontend views/chat/MainArea.vue | 修改 | 按 mode 显示 Chat/Plan/Artifact |
| Frontend views/pdf/pdfViewer.vue | 修改 | citation 跳页与 Evidence 高亮 |
| Frontend src/api/gpt.ts | 删除/停用 | 避免浏览器直连模型服务 |
| requirement.txt | 修改 | 加入 BGE-M3/BM25/Reranker/Settings/Alembic 依赖 |

---

## 十四、A1/A2 附件生成指引（实施方案第 15 章）

### 14.1 附件 A1《PaperAgent 软件设计资料》（15~25 页，图多于长段文字，字段/参数必须来自最终 release/v2-competition 版本）

| A1 小节 | 直接从哪里生成/整理 | 必须包含 |
|---|---|---|
| A1-1 总体架构 | 六层架构 + 最终目录 | 六层架构、依赖方向、部署边界 |
| A1-2 模块设计 | core/decision,retrieval,research,skills,evidence,artifact | 每模块职责、输入/输出、依赖、异常 |
| A1-3 Ask 流程 | QAService + Decision/Retrieval/Grounding | Query→Retrieve→Judge→Answer→Citation |
| A1-4 Research 流程 | ResearchOrchestrator | 状态机、Plan/Step/Skill/Artifact |
| A1-5 Quantum 流程 | quantum/skill.py + adapter.py | Schema、Validator、真实工具接口、Result Parser |
| A1-6 数据设计 | models.py + EvidenceChunk Schema | documentID/page/chunk/task_id/step_id/artifact_id |
| A1-7 参数表 | Settings + eval config | Top-K、RRF c、Reranker、Judge 阈值、timeout/retry |
| A1-8 API 设计 | OpenAPI / router 文件 | 核心 endpoint + request/response + SSE events |
| A1-9 部署设计 | docker/README/.env.example | 本地/服务器部署、目录、模型缓存、安全 |

### 14.2 附件 A2《PaperAgent 核心代码说明》推荐 8 段

| 序号 | 代码片段 | 建议文件 | 展示重点 |
|---|---|---|---|
| 1 | Hybrid Retriever | core/retrieval/pipeline.py | Dense+BM25→RRF→Reranker 的主链路 |
| 2 | Evidence Decision | core/decision/engine.py | Evidence insufficiency → expand/search/abstain |
| 3 | Grounding Verify | core/evidence/grounding.py | Claim/Citation 核验与 fail-safe |
| 4 | Research Planner | core/research/planner.py | 受限技能集合生成 TaskPlan |
| 5 | Research Executor | core/research/executor.py | 状态机、Step 执行、重试、持久化 |
| 6 | Skill Registry | core/skills/registry.py | 插件注册与 input schema 暴露 |
| 7 | Quantum Skill Adapter | core/skills/quantum/skill.py + adapter.py | Schema/Validator/真实工具调用 |
| 8 | SSE/Error Handling | router_qa.py + api/sse.ts | typed events、半包解析、错误可观测 |

每段代码固定说明模板：【代码名称】【所在文件】【输入】【输出】【前置依赖】【核心逻辑】【异常处理】【关键参数】【技术作用】【与现有工程关系】。

A2 禁止事项：不选登录/普通 CRUD；不整段贴 200 行文件；不用未合并到 release 分支的实验代码截图；不放密钥、绝对服务器路径、个人信息。

### 14.3 A1 图的绘制时机

开发中可用方案图占位；功能冻结后根据 release/v2-competition 目录和真实接口重画最终图；架构图中每个模块都必须在代码中找到对应包/类，不出现只在 PPT 中存在的模块；关键参数从最终 .env.example/settings.py 自动抄录，避免文档与代码数值不一致。

---

## 十五、部署与安全（技术方案第四节）

### 15.1 部署形态

| 形态 | 适用对象 | 部署说明 |
|---|---|---|
| 个人本地版 | 学生/个人科研 | 前端+FastAPI+ChromaDB 本地运行；LLM 可调用授权 API |
| 实验室服务器版 | 课题组/研发团队 | 统一用户、知识库和文件存储；私有资料保留在内网服务器 |
| 云端演示版 | 比赛评审/试用 | Docker 化部署；配置演示账号与限流，便于评委验证 |

### 15.2 安全与稳定性设计

- 密钥与配置：API Key 通过 .env/密钥服务注入，仓库禁止硬编码；
- 权限边界：documentID / knowledgeID 作为检索隔离条件；Lab 版增加用户与知识库权限控制；
- 失败恢复：文档向量化任务异常时回滚状态；LLM/SSE 异常返回可读错误而非空白响应；
- 工具安全：Research Skill 定义权限、参数 Schema 和 validator；高风险工具要求人工确认；
- 可观测性：记录检索、决策、Skill 调用和错误事件，便于测试与演示复盘。

### 15.3 软件工程测试

| 测试项 | 最小测试场景 | 提交材料中给出的证据 |
|---|---|---|
| 兼容性 | Chrome / Edge；Windows / Linux | 测试用例与截图 |
| 异常恢复 | API 超时、arXiv 失败、PDF 损坏、向量任务中断 | 错误日志+恢复结果 |
| 性能 | 1/5/10 并发、10/30/50 篇知识库 | P50/P95 响应与处理时间 |
| 安装部署 | 全新环境按 README / Docker Compose 启动 | 部署录像或日志 |

---

## 十六、最终交付物清单

改造完成后，执行者应交付：

1. 改造后的完整代码（release/v2-competition 分支）；
2. `eval/` 下三组实验的 datasets / scripts / configs / results（raw 数据齐全）；
3. 逐项通过的最终验收清单（第九节）；
4. 可运行的演示环境（本地或 Docker）；
5. 生成的附件 A1（软件设计资料）与 A2（核心代码说明）素材；
6. 更新后的 README、.env.example、migrations。

---

## 结束语

PaperAgent V2 的正确改造顺序：**先建立可追溯 Evidence 数据结构 → 升级检索与结构化决策 → 构建 Research Task 状态机和 Skill Framework → Quantum Skill 最后接入**。每一层由下一层复用，直接对应最终技术方案和三组实验。现有工程不需要推倒重做：PDF/知识库、Chroma、ChatAgent、多模型、arXiv、SSE、Vue 页面继续利用；主要工作是把现有"Router + ChatAgent + 单路 RAG"拆成明确的 Retrieval、Decision、Evidence、Research、Skills、Artifact 层，并把前端从单一聊天视图升级为可观察科研任务执行过程的 Workspace。
