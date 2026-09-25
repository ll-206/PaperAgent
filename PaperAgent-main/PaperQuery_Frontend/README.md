# PaperAgent 前端

PaperAgent 论文查询 AI Agent 的前端工作台。基于 Vue3，围绕论文知识库提供
**Chat 可信问答**、**Research 研究编排**、**知识库/文档管理** 与 **Dashboard 概览**，
支持 PDF 阅读、划线翻译、结构化引用（`[C#]`）点击跳转到原文对应页。

## 主要功能页面

- **Chat（问答）**：接入后端 V2 `/qa/stream`（SSE），流式回答 + 反幻觉 + 可点击引用
- **Research（研究模式）**：任务编排（Planner→Executor→Verifier），步骤耗时时间线、产物查看
- **Knowledge / Library**：知识库统计、文档列表、上传与向量化状态
- **Dashboard**：系统/知识库概览
- **PDF 阅读**：翻页、翻译、引用定位

## 技术栈

- Vue3 + TypeScript + Vite
- UI：Element Plus + Tailwind CSS + UnoCSS
- 状态管理：Pinia + Vuex
- 路由：Vue Router
- 请求：Axios / Fetch（SSE）

## 安装和运行

> 需先启动后端（见 `../PaperQuery_Backend/README.md` 或项目根 `快速启动.md`）。

```bash
cd PaperQuery_Frontend
npm install
npm run dev
```

打开浏览器访问 `http://127.0.0.1:8080`（端口见 `vite.config.ts` 的 `server.port`）。
后端地址在 `config/.env.dev` 中配置（默认 `http://127.0.0.1:8001`）。

## 目录速览

```
src/
├── views/           页面（chat / research / dashboard / library / pdf ...）
├── components/      通用组件（PDF 阅读、时间线、气泡等）
├── api/             后端接口封装（chat / qa / research / ...）
├── stores/          状态（messageList / chatHistory / documentList / ...）
├── router/          路由（含各页 document.title 设置）
└── config/          环境变量
```

## License

MIT