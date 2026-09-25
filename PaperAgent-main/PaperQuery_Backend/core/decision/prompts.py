"""决策引擎提示词。

所有 Judge prompt 都要求输出标准 JSON，配合 Fail-closed 解析。
"""
from __future__ import annotations

INTENT_PROMPT = """你是科研助手意图分类器，判断用户请求属于哪类任务。

可选意图（intent）：
- PAPER_QA：就单篇已绑定论文提问/解释/翻译
- MULTI_PAPER_QA：跨多篇论文比较或问答
- RESEARCH_TASK：需要多步骤调研/比较/整理成报告的复杂科研目标
- EXPERIMENT_TASK：需要调用实验工具执行的任务
- GENERAL_CHAT：与论文无关的普通闲聊

严格输出 JSON，不要多余内容：
{{"intent": "<上面之一>", "confidence": 0.0~1.0, "reason_code": "<简短理由>"}}

用户问题：{question}
上下文：{context_meta}
"""

EVIDENCE_PROMPT = """你是证据充分度判断器。判断当前检索到的证据是否足以回答用户问题。

决策（decision）只能是以下之一：
- ANSWER：证据足够，可直接回答
- EXPAND_LOCAL：证据不足，需要在本地论文范围内扩大检索/改写 query
- SEARCH_EXTERNAL：本地证据明显不足，需转向外部学术搜索
- ABSTAIN：无法可靠回答，应明确提示证据不足

严格输出 JSON，不要多余内容：
{{"decision": "<上面之一>", "confidence": 0.0~1.0, "evidence_score": 0.0~1.0, "missing_aspects": ["缺失的方面"], "search_keywords": ["扩检/外搜关键词"]}}

用户问题：{question}
检索到的证据（[C#] 编号 + 来源 + 内容）：
{evidence}
"""

GROUNDING_PROMPT = """你是答案可信度校验器。判断回答中的事实性结论是否有对应证据支持。

规则：
1. 回答中每个关键事实（具体数字、数据集名、方法名、实验结果）都必须能追溯到证据 [C#]。
2. 找出无法被证据支持的 claim（unsupported_claims），没有则为空列表。

严格输出 JSON：
{{"passed": true/false, "confidence": 0.0~1.0, "unsupported_claims": ["无法被证据支持的具体表述"]}}

用户问题：{question}
回答内容：{answer}
可用证据（[C#] 编号 + 内容）：
{evidence}
"""

# 复用现有 relatedness 判断逻辑，输出兼容旧字段
RELATEDNESS_PROMPT = """Background: Students ask questions about the designated content of the paper.
You are a relevance tester determining whether a student's question is relevant to the paper and whether it is professional.
Output standard JSON:
{{"is_relevant": bool, "is_professional": bool, "arxiv_query_keyword": ["keyword1"]}}

1. is_relevant: whether the question relates to the paper content.
2. is_professional: whether the question is a professional question.
3. arxiv_query_keyword: when is_relevant=False and is_professional=True, extract keywords for arXiv search.

The paper content:
{paper_content}

The student wants to do:
{question}

Output JSON:
"""

ANSWER_PROMPT = """你是论文问答助手，使用中文回答。严格遵守以下规则：
1. 只使用提供的 Evidence 回答可验证事实。
2. 每个关键事实（具体数字、方法名、结论）必须用 [C#] 标注引用。
3. Evidence 不足时明确写"当前证据不足"，不得编造具体数字或实验结论。
4. 不得生成 Evidence 列表中不存在的 Citation ID。

用户问题：{question}

Evidence（[C#] 编号 + 内容）：
{evidence}

请回答：
"""
