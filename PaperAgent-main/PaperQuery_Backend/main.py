from contextlib import asynccontextmanager

import dotenv

dotenv.load_dotenv()

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from langchain_core.embeddings import Embeddings

from core.agent.chatAgent import *
from core.agent.dataprocessAgent import *
from core.backend.crud.crud_document import *
from core.backend.crud.crud_knowledge import *
from core.backend.crud.crud_user import *
from core.backend.db.database import SessionLocal, engine
from core.backend.db.models import Base
from core.backend.router import (
    router_document,
    router_knowledge,
    router_llm,
    router_translate,
    router_user,
    router_note,
    router_post,
    router_commit,
    router_qa,
    router_research,
)
from core.backend.schema.schema import *
from core.common.config import settings
from core.decision.engine import DecisionEngine
from core.llm.LLM import LLM
from core.vectordb.chromadb import *


Base.metadata.create_all(bind=engine)


def _build_retrieval_pipeline():
    """构建 Hybrid Retrieval Pipeline（BGE-M3 + BM25 + RRF + Reranker）。加载失败抛异常。"""
    import pickle

    from langchain_chroma import Chroma

    from core.retrieval.dense import BGE3Embeddings, DenseRetriever
    from core.retrieval.pipeline import RetrievalPipeline
    from core.retrieval.reranker import BGEReranker
    from core.retrieval.sparse import BM25Retriever

    embedding = BGE3Embeddings(settings.BGE_M3_MODEL_PATH)
    chroma_v2 = Chroma(
        persist_directory=settings.CHROMA_LAYER1_V2_DIR,
        embedding_function=embedding,
    )
    corpus_path = os.path.join(settings.BM25_INDEX_DIR, "corpus.pkl")
    with open(corpus_path, "rb") as f:
        corpus = pickle.load(f)
    dense = DenseRetriever(chroma_v2)
    sparse = BM25Retriever(corpus)
    reranker = BGEReranker(settings.RERANKER_MODEL_PATH)
    return RetrievalPipeline(dense, sparse, reranker, cfg=settings)


def _build_skill_registry():
    """注册全部内置 Research Skills。"""
    from core.skills.builtin import (
        LocalRetrievalSkill,
        PaperCompareSkill,
        ReportGenerateSkill,
    )
    from core.skills.citation_verify import CitationVerifySkill
    from core.skills.extract import ExperimentExtractSkill, MethodExtractSkill
    from core.skills.paper_reader import PaperReaderSkill
    from core.skills.paper_search import PaperSearchSkill
    from core.skills.registry import SkillRegistry

    registry = SkillRegistry()
    registry.register(LocalRetrievalSkill())
    registry.register(ReportGenerateSkill())
    registry.register(PaperCompareSkill())
    registry.register(PaperSearchSkill())
    registry.register(PaperReaderSkill())
    registry.register(MethodExtractSkill())
    registry.register(ExperimentExtractSkill())
    registry.register(CitationVerifySkill())
    return registry


def _build_research_orchestrator(registry, llm, ctx):
    """构建 Research Planner → Executor → Verifier → Orchestrator。"""
    from core.research.executor import Executor
    from core.research.orchestrator import ResearchOrchestrator
    from core.research.planner import Planner
    from core.research.verifier import Verifier

    planner = Planner(llm, registry)
    executor = Executor(registry, ctx)
    return ResearchOrchestrator(planner, executor, Verifier())


class ONNXEmbeddings(Embeddings):
    """使用 ChromaDB 内置 ONNX 模型，无需 API key，不依赖 sentence-transformers"""
    def __init__(self):
        cache_dir = os.getenv("CHROMA_ONNX_CACHE_DIR")
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            ONNXMiniLM_L6_V2.DOWNLOAD_PATH = cache_dir
        self._ef = ONNXMiniLM_L6_V2()

    def embed_documents(self, texts):
        return self._ef(texts)

    def embed_query(self, text):
        return self._ef([text])[0]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.llm = LLM()
    app.chroma_db = AcadeChroma(
        os.getenv("CHROMA_LAYER1_DIR"),
        os.getenv("CHROMA_LAYER2_DIR"),
        ONNXEmbeddings(),
        app.llm
    )

    # 为每个模型创建 ChatAgent
    # 非流式 LLM 使用 deepseek 作为默认
    app.chat_agent = ChatAgent(
        app.llm.get_llm('deepseek'),
        app.llm.get_stream_llm('deepseek'),
        app.chroma_db
    )

    # 存储各模型的流式 chat agent
    app.chat_agents = {
        'deepseek': app.chat_agent,
        'kimi': ChatAgent(
            app.llm.get_llm('kimi'),
            app.llm.get_stream_llm('kimi'),
            app.chroma_db
        ),
        'openai': ChatAgent(
            app.llm.get_llm('openai'),
            app.llm.get_stream_llm('openai'),
            app.chroma_db
        ),
    }

    # V2: DecisionEngine（轻量，基于 LLM Judge）
    app.decision_engine = DecisionEngine(app.llm.get_llm('deepseek'))

    # V2: Hybrid Retrieval Pipeline（容错加载，失败则降级为基础检索）
    app.retrieval_pipeline = None
    try:
        app.retrieval_pipeline = _build_retrieval_pipeline()
        print("[V2] Hybrid Retrieval Pipeline 初始化完成")
    except Exception as e:
        print(f"[V2] Hybrid Retrieval 初始化失败，降级为基础检索: {e}")

    # V2: SkillRegistry + ResearchOrchestrator
    app.skill_registry = _build_skill_registry()
    research_ctx = {
        "retrieval_pipeline": app.retrieval_pipeline,
        "llm": app.llm.get_llm('deepseek'),
        "decision_engine": app.decision_engine,
        "db": SessionLocal(),
    }
    app.research_orchestrator = _build_research_orchestrator(
        app.skill_registry, app.llm.get_llm('deepseek'), research_ctx
    )
    print(f"[V2] Research Orchestrator 初始化完成（{len(app.skill_registry.names())} 个 Skills）")

    yield
    # Clean up the ML models and release resources
    print("shoutdown!")


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router_user.router, tags=["router_user"])
app.include_router(router_knowledge.router, tags=["knowledge"])
app.include_router(router_document.router, tags=["router_document"])
app.include_router(router_llm.router, tags=["router_llm"])
app.include_router(router_translate.router, tags=["router_translate"])
app.include_router(router_note.router, tags=["router_note"])
app.include_router(router_post.router, tags=["router_post"])
app.include_router(router_commit.router, tags=["router_commit"])
app.include_router(router_qa.router, tags=["router_qa"])
app.include_router(router_research.router, tags=["router_research"])
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
