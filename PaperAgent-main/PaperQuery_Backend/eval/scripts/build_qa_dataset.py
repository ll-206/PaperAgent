# -*- coding: utf-8 -*-
"""实验一数据集构建器。

功能：
1. 内置 48 条人工校验的种子问题（SEED），覆盖三类：
   - answerable_single : 单文档可答（gold evidence 标注页码与原文）
   - unanswerable      : 本地证据不足（PaperAgent 应 ABSTAIN，基线易幻觉）
   - cross_doc         : 跨文档对比（当前库仅 1 篇，系统应如实说明证据不足）
2. --expand N：调用 LLM 基于 PDF 真实内容自动追加问题，向 200 题目标扩充。
   自动生成的问题 source 标记为 "llm_generated"，建议人工抽检后再用于正式结果。

用法（在 PaperQuery_Backend 目录下）：
    python eval/scripts/build_qa_dataset.py                 # 写出种子 qa_200.jsonl
    python eval/scripts/build_qa_dataset.py --expand 152    # 种子 + LLM 扩充至约 200 条
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

# 文档与库的真实标识（来自数据库 documents 表）
DOC_ID = "70c1eaca0422998e00b2f77f01a985c2"
KID = "48f27d78-b753-11f1-bae9-a0d3656ab525"
PDF_REL = "/res/pdf/Day01-作业-2025.7.9-李贤烽_20250712001605.pdf"
# 一个不存在的第二文档 ID，用于跨文档类问题（测试系统是否如实说明而非编造）
DOC_ID_FAKE = "0000000000000000000000000000aaaa"


def _ev(page: int, quote: str) -> dict:
    return {"document_id": DOC_ID, "knowledge_id": KID, "page": page, "quote": quote}


def _q(qid: str, category: str, question: str, gold_answer: str,
       evidence: list, expected_route: str, difficulty: str,
       document_ids: list | None = None) -> dict:
    return {
        "id": qid,
        "category": category,
        "question": question,
        "document_ids": document_ids if document_ids is not None else [DOC_ID],
        "gold_answer": gold_answer,
        "gold_evidence": evidence,
        "expected_route": expected_route,
        "difficulty": difficulty,
        "source": "handcrafted",
    }


# ============================ 种子问题（48 条） ============================
SEED: list[dict] = [
    # ---------- answerable_single（28 条） ----------
    _q("qa-001", "answerable_single", "互联网的主要作用有哪些？",
       "信息传输和通信、云存储、让设备互通互联。",
       [_ev(1, "主要作用：信息传输和通信 云储存 让设备互通互联")], "LOCAL_RAG", "easy"),
    _q("qa-002", "answerable_single", "请用自己的话描述互联网的结构。",
       "个人/企业 → 终端 → 互联网 → 服务器。",
       [_ev(2, "个人/企业->终端->互联网->服务器")], "LOCAL_RAG", "easy"),
    _q("qa-003", "answerable_single", "学习这门网络课程，主要的学习对象是什么？",
       "网络协议、设备原理、地址管理。",
       [_ev(1, "网络协议、设备原理、地址管理")], "LOCAL_RAG", "easy"),
    _q("qa-004", "answerable_single", "为什么购买的 1TB 硬盘连接主机后，显示容量却不够 1TB？",
       "一是单位换算的差异，二是存在隐藏的分区。",
       [_ev(1, "具有单位换算的差异 隐藏的分区")], "LOCAL_RAG", "medium"),
    _q("qa-005", "answerable_single", "IP 地址的作用是什么？",
       "标识网络设备的地址，只有具有 IP 地址的设备才能上网。",
       [_ev(1, "只有具有ip 地址的设备才能上网，标识网络设备的地址")], "LOCAL_RAG", "easy"),
    _q("qa-006", "answerable_single", "网络掩码的作用是什么？",
       "区分 IP 地址的主机位和网络位。",
       [_ev(1, "网络掩码可以区分IP 地址的主机位和网络位")], "LOCAL_RAG", "easy"),
    _q("qa-007", "answerable_single", "网络掩码的原理是什么？",
       "转换为二进制格式时，网络位用 1 表示，主机位用 0 表示。",
       [_ev(1, "原理：转换位二进制的格式时，网络位对应的用1 表示，主机位用0 表示")], "LOCAL_RAG", "medium"),
    _q("qa-008", "answerable_single", "掩码 255.255.128.0 对应的反掩码是多少？",
       "0.0.127.255。",
       [_ev(1, "255.255.128.0 对应的反掩码 0.0.127.255")], "LOCAL_RAG", "medium"),
    _q("qa-009", "answerable_single", "网络掩码有哪些特点？",
       "长度与 IP 地址一致（32bit）；左边是 1、右边是 0，1 和 0 不会交叉出现。",
       [_ev(1, "掩码的长度与IP 地址长度一致，比如32bit 左边是1，右边是0，1 和0 不会交叉出现")], "LOCAL_RAG", "medium"),
    _q("qa-010", "answerable_single", "常用的在线进制转换网站有哪些？",
       "RapidTables、BinaryHex Converter、CalculatorSoup。",
       [_ev(1, "RapidTables、BinaryHex Converter、CalculatorSoup")], "LOCAL_RAG", "easy"),
    _q("qa-011", "answerable_single", "A 类 IP 地址的地址总数是多少？",
       "约 2,113,928,964（16777214 × 126）。",
       [_ev(2, "A 类地址：16777214*126=2,113,928,964")], "LOCAL_RAG", "hard"),
    _q("qa-012", "answerable_single", "针对 IP 地址空间不足，有哪些缓解方案？",
       "①提出私有地址与公有地址，用 NAT 缓解地址耗尽；②子网划分，按需分配含不同主机位的网段。",
       [_ev(2, "提出私有地址...然后用NAT 来缓解地址空间的耗尽 子网划分")], "LOCAL_RAG", "medium"),
    _q("qa-013", "answerable_single", "解决 IP 地址空间不足的根本方案是什么？",
       "IPv6，本质是增加 IP 地址空间数量，地址长度为 128bit。",
       [_ev(2, "解决方案：IPv6（本质是增加IP 地址空间的数量）128bit")], "LOCAL_RAG", "easy"),
    _q("qa-014", "answerable_single", "一个正规机房应该具备哪些功能模块？",
       "基础设施模块（供电、制冷、防雷接地）、IT 设备承载模块（机柜与布线、核心设备区）、运维管理模块（操作区、备件）、应急保障（消防）。",
       [_ev(2, "基础设施模块（供电、制冷、防雷接地）IT 设备承载模块...运维管理模块...应急保障（消防）")], "LOCAL_RAG", "medium"),
    _q("qa-015", "answerable_single", "请列举几个常见的网络机柜品牌。",
       "图腾、南诺信、华为服务器机柜、APC、三拓。",
       [_ev(2, "图腾...南诺信...华为服务器机柜...APC...三拓")], "LOCAL_RAG", "easy"),
    _q("qa-016", "answerable_single", "在华为官网上查找交换机产品文档的路径是什么？",
       "打开 https://support.huawei.com/enterprise/ → 产品与解决方案 → 企业网络 → 交换机 → 点击目标型号了解更多 → 相关资源 → 下载彩页。",
       [_ev(3, "路径：打开官网https://support.huawei.com/enterprise/——》产品与解决方案——》企业网络——》交换机——》点击目标型号了解更多——》相关资源——》下载彩页")], "LOCAL_RAG", "hard"),
    _q("qa-017", "answerable_single", "常见的私有 IP 地址空间分别是多少？",
       "A 类 10.0.0.0/8；B 类 172.16.0.0/12；C 类 192.168.0.0/16；D 类 239.0.0.0/8。",
       [_ev(3, "A 类：10.0.0.0/8 B 类172.16.0.0/12 C 类192.168.0.0/16 D 类：239.0.0.0/8")], "LOCAL_RAG", "medium"),
    _q("qa-018", "answerable_single", "常见的园区网络架构是怎样的？",
       "分为接入层、汇聚层、核心层。",
       [_ev(3, "接入层、汇聚层、核心层")], "LOCAL_RAG", "easy"),
    _q("qa-019", "answerable_single", "网络故障排查中，终端故障如何判断？",
       "同网段其他设备可以、但这一台不行，属于终端故障。",
       [_ev(3, "终端故障（同网段其他设备可以，但这一个不行）")], "LOCAL_RAG", "medium"),
    _q("qa-020", "answerable_single", "网络故障排查中，交换故障如何判断？",
       "同网段设备之间互不通（如 192.168.1.10 与 192.168.1.20），属于交换故障。",
       [_ev(3, "交换故障（同网段互不通（如192.168.1.10↔192.168.1.20））")], "LOCAL_RAG", "medium"),
    _q("qa-021", "answerable_single", "网络故障排查中，路由故障如何判断？",
       "跨网段设备之间互不通（如 192.168.1.10 与 10.1.1.1），属于路由故障。",
       [_ev(3, "路由故障（跨网段互不通（如192.168.1.10↔10.1.1.1））")], "LOCAL_RAG", "medium"),
    _q("qa-022", "answerable_single", "200.160.3.255/24 为什么不能正常使用？",
       "它是该网段的广播地址，不能使用。",
       [_ev(3, "200.160.3.255/24（广播地址不能使用）")], "LOCAL_RAG", "medium"),
    _q("qa-023", "answerable_single", "10.178.32.0/20 为什么不能正常使用？",
       "它是该网段的网络地址，不能使用。",
       [_ev(3, "10.178.32.0/20（网络地址不能使用）")], "LOCAL_RAG", "medium"),
    _q("qa-024", "answerable_single", "常见的网络拓扑图绘制工具有哪些？",
       "Microsoft Visio、draw.io、PowerPoint。",
       [_ev(4, "Microsoft Visio、draw.io、PowerPoint")], "LOCAL_RAG", "easy"),
    _q("qa-025", "answerable_single", "NAT 在缓解 IP 地址不足中起什么作用？",
       "配合私有地址重复利用，缓解公有地址空间的耗尽。",
       [_ev(2, "提出私有地址（重复利用，无法上网）和公有地址（收费，可联网）然后用NAT 来缓解地址空间的耗尽")], "LOCAL_RAG", "medium"),
    _q("qa-026", "answerable_single", "子网划分如何缓解 IP 地址空间不足？",
       "根据需要的主机位数量，分配含有不同主机位的网段。",
       [_ev(2, "子网划分，根据需要的主机位数量来分配含有不同主机位网段")], "LOCAL_RAG", "medium"),
    _q("qa-027", "answerable_single", "IPv6 的地址长度是多少 bit？",
       "128bit。",
       [_ev(2, "IPv6（本质是增加IP 地址空间的数量）128bit")], "LOCAL_RAG", "easy"),
    _q("qa-028", "answerable_single", "图腾 G2.6618 机柜的规格和价格是多少？",
       "18U，价格 700 元。",
       [_ev(2, "图腾 G2.6618 18U 700¥")], "LOCAL_RAG", "hard"),

    # ---------- unanswerable（14 条，本地证据不足） ----------
    _q("qa-029", "unanswerable", "Transformer 的自注意力机制计算公式是什么？请写出 Q、K、V 的运算。",
       "文档未涉及，应说明本地证据不足，不应编造公式。",
       [], "ABSTAIN", "hard"),
    _q("qa-030", "unanswerable", "BGP 协议的 OPEN 报文包含哪些字段？",
       "文档未涉及 BGP，应说明证据不足。",
       [], "ABSTAIN", "hard"),
    _q("qa-031", "unanswerable", "请详细对比 TCP 拥塞控制中 Reno 与 Cubic 算法的窗口增长函数。",
       "文档未涉及，应说明证据不足。",
       [], "ABSTAIN", "hard"),
    _q("qa-032", "unanswerable", "Shor 算法在量子计算机上分解大整数的时间复杂度是多少？",
       "文档未涉及量子计算，应说明证据不足。",
       [], "ABSTAIN", "hard"),
    _q("qa-033", "unanswerable", "ResNet-50 在 ImageNet 数据集上的 Top-1 准确率具体是多少？",
       "文档未涉及，应说明证据不足。",
       [], "ABSTAIN", "medium"),
    _q("qa-034", "unanswerable", "如何配置 OSPF 的区域认证？请给出完整的路由器命令。",
       "文档未涉及 OSPF 配置命令，应说明证据不足。",
       [], "ABSTAIN", "hard"),
    _q("qa-035", "unanswerable", "RFC 791 规定的 IP 头部 IHL 字段最小值是多少？",
       "文档未涉及该 RFC 细节，应说明证据不足。",
       [], "ABSTAIN", "hard"),
    _q("qa-036", "unanswerable", "这份文档里提到的实验使用了什么型号的 GPU、batch size 设为多少？",
       "文档为网络基础作业，无任何实验配置，应说明证据不足。",
       [], "ABSTAIN", "medium"),
    _q("qa-037", "unanswerable", "VLAN 和 VXLAN 封装带来的具体 overhead 分别是多少字节？",
       "文档未涉及，应说明证据不足。",
       [], "ABSTAIN", "hard"),
    _q("qa-038", "unanswerable", "文档中提到的 1TB 硬盘，其转速和缓存容量分别是多少？",
       "文档只解释容量显示差异，未给硬盘具体参数，应说明证据不足。",
       [], "ABSTAIN", "medium"),
    _q("qa-039", "unanswerable", "华为 S5735-L 交换机的具体功耗和包转发率是多少？",
       "文档只给查找文档的路径，无机型参数，应说明证据不足。",
       [], "ABSTAIN", "hard"),
    _q("qa-040", "unanswerable", "请给出生成树协议（STP）收敛时间的精确推导过程。",
       "文档未涉及 STP，应说明证据不足。",
       [], "ABSTAIN", "hard"),
    _q("qa-041", "unanswerable", "这份文档的作者列出了哪些参考文献？",
       "文档为练习题，无参考文献列表，应说明证据不足。",
       [], "ABSTAIN", "easy"),
    _q("qa-042", "unanswerable", "IPv6 邻居发现协议（NDP）的五种 ICMPv6 报文类型具体格式是什么？",
       "文档仅提到 IPv6 为 128bit，未涉及 NDP，应说明证据不足。",
       [], "ABSTAIN", "hard"),

    # ---------- cross_doc（6 条，需多篇文档，当前库不足） ----------
    _q("qa-043", "cross_doc", "请对比这两篇文档在园区网络架构设计上的异同。",
       "当前库仅有 1 篇文档，缺少第二篇，应如实说明无法完成跨文档对比，不应编造第二篇内容。",
       [], "SEARCH_EXTERNAL", "hard", document_ids=[DOC_ID, DOC_ID_FAKE]),
    _q("qa-044", "cross_doc", "综合多篇资料，它们关于私有 IP 地址范围的说法是否一致？",
       "需要至少两篇资料，当前仅 1 篇，应说明证据/资料不足。",
       [], "SEARCH_EXTERNAL", "medium", document_ids=[DOC_ID, DOC_ID_FAKE]),
    _q("qa-045", "cross_doc", "请比较至少两本教材对 IP 地址分类（A–E 类）的定义差异。",
       "当前库仅 1 份作业，无第二本教材，应说明资料不足。",
       [], "SEARCH_EXTERNAL", "medium", document_ids=[DOC_ID, DOC_ID_FAKE]),
    _q("qa-046", "cross_doc", "对比文档 A 和文档 B 中对正规机房功能模块的划分。",
       "缺少文档 B，应如实说明无法对比。",
       [], "SEARCH_EXTERNAL", "medium", document_ids=[DOC_ID, DOC_ID_FAKE]),
    _q("qa-047", "cross_doc", "请汇总多篇文档中的网络故障排查方法论，并指出它们之间的矛盾点。",
       "当前仅 1 篇，无法做多文档汇总与矛盾分析，应说明资料不足。",
       [], "SEARCH_EXTERNAL", "hard", document_ids=[DOC_ID, DOC_ID_FAKE]),
    _q("qa-048", "cross_doc", "跨文档统计各资料引用的网络机柜品牌与价格差异。",
       "当前仅 1 份资料，无法做跨文档价格对比，应说明资料不足。",
       [], "SEARCH_EXTERNAL", "hard", document_ids=[DOC_ID, DOC_ID_FAKE]),
]


# ============================ LLM 扩充 ============================
EXPAND_PROMPT = """你在为一个论文问答系统构造评测问题。下面是文档《{doc_name}》第 {page} 页的内容：

---
{page_text}
---

请基于该页【真实出现】的内容，生成 {n} 个互不重复的中文问题，并严格按 JSON 数组输出，每个元素含字段：
- question : 问题
- category : 只能是 answerable_single 或 unanswerable 之一；
  answerable_single 的答案必须能在本页找到，unanswerable 必须是本页及整篇文档明显没有、但容易被想当然回答的专业问题（约占 1/3）。
- gold_answer : 参考答案（unanswerable 写 "文档未涉及，应说明证据不足。"）
- page : 页码（整数）
- quote : answerable_single 时给出本页支撑答案的原文片段；unanswerable 给空字符串。
- difficulty : easy / medium / hard
只输出 JSON，不要解释。"""


def _read_pdf_pages(pdf_path: str) -> list[str]:
    import fitz
    doc = fitz.open(pdf_path)
    return [doc.load_page(i).get_text("text") for i in range(len(doc))]


def expand_with_llm(target_total: int) -> list[dict]:
    """调用 LLM 基于 PDF 各页生成补充问题。"""
    from core.llm.LLM import LLM

    need = target_total - len(SEED)
    if need <= 0:
        return []
    pdf_path = os.path.join(_backend_root(), PDF_REL.lstrip("/"))
    pages = _read_pdf_pages(pdf_path)
    llm = LLM().get_llm("deepseek")

    generated: list[dict] = []
    per_page = max(2, need // len(pages) + 1)
    for pno, text in enumerate(pages, 1):
        if len(generated) >= need:
            break
        prompt = EXPAND_PROMPT.format(
            doc_name="Day01 网络基础作业", page=pno,
            page_text=text.strip()[:2500], n=per_page,
        )
        try:
            resp = llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            import re
            content = re.sub(r"```(?:json)?", "", content).replace("```", "").strip()
            items = json.loads(content)
        except Exception as e:  # 单页失败不影响整体
            print(f"[warn] 第 {pno} 页生成失败: {e}")
            continue
        for it in items:
            if len(generated) >= need:
                break
            qid = f"qa-gen-{pno}-{len(generated)+1:03d}"
            ev = []
            if it.get("quote"):
                ev = [_ev(int(it.get("page", pno)), it["quote"])]
            cat = it.get("category", "answerable_single")
            generated.append({
                "id": qid,
                "category": cat,
                "question": it["question"],
                "document_ids": [DOC_ID],
                "gold_answer": it.get("gold_answer", ""),
                "gold_evidence": ev,
                "expected_route": "ABSTAIN" if cat == "unanswerable" else "LOCAL_RAG",
                "difficulty": it.get("difficulty", "medium"),
                "source": "llm_generated",
            })
        time.sleep(0.5)
    return generated


def _backend_root() -> str:
    # scripts/ -> eval/ -> backend root
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expand", type=int, default=0,
                        help="目标总题数；>48 时调用 LLM 扩充，如 --expand 200")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    # 保证后端根目录在 sys.path（可 import core），并切到该目录
    root = _backend_root()
    sys.path.insert(0, root)
    os.chdir(root)
    try:
        import dotenv
        dotenv.load_dotenv()
    except Exception:
        pass

    rows = list(SEED)
    if args.expand and args.expand > len(SEED):
        rows += expand_with_llm(args.expand)

    out = args.out or os.path.join(root, "eval", "datasets", "qa_200.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 统计
    from collections import Counter
    c = Counter(r["category"] for r in rows)
    s = Counter(r["source"] for r in rows)
    print(f"已写出 {len(rows)} 条 -> {out}")
    print("类别分布:", dict(c))
    print("来源分布:", dict(s))


if __name__ == "__main__":
    main()
