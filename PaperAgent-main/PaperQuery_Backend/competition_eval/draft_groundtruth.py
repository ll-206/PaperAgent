"""Prepare evidence-linked QA candidates for independent human review."""
from __future__ import annotations

import csv
import argparse
import re
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
PAPERS = {row["paper_id"]: row for row in csv.DictReader((HERE / "datasets" / "paper_corpus.csv").open(encoding="utf-8"))}

# Each question and search phrase was selected against the paper's method,
# experiment, or result sections. The generated quote remains a DRAFT until a
# person verifies that it fully supports the answer on the indicated page.
NORMAL = [
    ("P01", "What two kinds of memory are combined in the original RAG model?", 1, "parametric memory"),
    ("P01", "Which open-domain QA datasets are used to evaluate RAG?", 4, "Natural Questions (NQ)"),
    ("P01", "On how many open-domain QA tasks does RAG set a new state of the art?", 1, "three open domain QA tasks"),
    ("P02", "What special tokens support Self-RAG's retrieval and reflection?", 1, "reflection tokens"),
    ("P02", "Which model sizes are evaluated for Self-RAG?", 1, "7B and 13B parameters"),
    ("P02", "Which baseline systems does Self-RAG outperform in the paper's summary?", 1, "outperforms ChatGPT"),
    ("P03", "What component assesses the quality of retrieved documents in CRAG?", 1, "retrieval evaluator"),
    ("P03", "Which external source extends CRAG's limited static corpus?", 1, "large-scale web searches"),
    ("P03", "How many datasets are used in CRAG's reported experiments?", 1, "four datasets"),
    ("P04", "What does FLARE use to anticipate future content for retrieval?", 1, "prediction of the upcoming sentence"),
    ("P04", "Which multihop QA task is included in FLARE's evaluation?", 3, "multihop QA ("),
    ("P04", "How does FLARE perform relative to the tested baselines?", 7, "outperforms all base"),
    ("P05", "How does REPLUG treat the language model it augments?", 1, "black box"),
    ("P05", "Which open-domain QA benchmark is used to evaluate REPLUG?", 6, "Natural Questions"),
    ("P05", "By what percentage does REPLUG improve GPT-3 language modeling?", 1, "6.3%"),
    ("P06", "Which attention mechanism computes association discrepancy in Anomaly Transformer?", 1, "Anomaly-Attention"),
    ("P06", "Which server-machine anomaly dataset is used in the evaluation?", 6, "SMD (Server Machine Dataset"),
    ("P06", "What average improvement does the association criterion bring over reconstruction?", 7, "18.76%"),
    ("P07", "What self-conditioning technique does TranAD use?", 1, "focus score-based self-conditioning"),
    ("P07", "Which water-treatment dataset is included in TranAD's evaluation?", 8, "Secure Water Treatment (SWaT)"),
    ("P07", "What is TranAD's reported maximum F1 improvement over baselines?", 8, "17.06%"),
    ("P08", "What design enables DCdetector's contrastive representation learning?", 1, "dual attention asymmetric design"),
    ("P08", "Which server-machine benchmark appears in DCdetector's experiments?", 7, "SMD"),
    ("P08", "What broad performance claim is made for DCdetector on benchmark datasets?", 1, "state-of-the-art results"),
    ("P09", "How many graph attention layers does MTAD-GAT use?", 1, "two graph attention layers"),
    ("P09", "Which spacecraft dataset appears in MTAD-GAT's evaluation?", 7, "SMAP"),
    ("P09", "On how many real-world datasets does MTAD-GAT claim to outperform prior models?", 1, "three real-world datasets"),
    ("P10", "Which block is the task-general backbone of TimesNet?", 1, "TimesBlock"),
    ("P10", "Which anomaly-detection metric is reported in TimesNet's result table?", 9, "F1-score"),
    ("P10", "Across how many mainstream time-series tasks does TimesNet claim state-of-the-art results?", 1, "mainstream time series analysis tasks"),
]
UNANSWERABLE = [
    ("P01", "What was the exact electricity cost in USD of training the RAG model?"),
    ("P02", "What was the exact carbon footprint in kg CO2 of Self-RAG training?"),
    ("P03", "What was the retrieval evaluator's exact peak memory usage in MB?"),
    ("P04", "What was the exact GPU-hour cost of all FLARE experiments?"),
    ("P05", "What was the exact monetary API cost per REPLUG evaluation query?"),
    ("P06", "How many joules did Anomaly Transformer consume per detected anomaly?"),
    ("P07", "What was the precise CO2 emission of the TranAD experiments?"),
    ("P08", "What was the exact cloud-hosting cost of DCdetector's benchmark run?"),
    ("P09", "What was the exact power draw in watts during MTAD-GAT training?"),
    ("P10", "What was the exact dollar cost of each TimesNet training run?"),
]

def clean(text: str) -> str:
    return " ".join(text.split())

def evidence_window(page_text: str, needle: str) -> str:
    lowered = page_text.lower()
    idx = lowered.find(needle.lower())
    if idx < 0:
        raise ValueError(f"Evidence phrase absent: {needle}")
    words = list(re.finditer(r"\S+", page_text))
    matching = next(i for i, word in enumerate(words) if word.start() <= idx < word.end() or word.start() >= idx)
    left = max(0, matching - 12)
    right = min(len(words), matching + 52)
    return page_text[words[left].start():words[right-1].end()]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--force",action="store_true",help="Overwrite existing annotations")
    args=parser.parse_args()
    path=HERE / "datasets" / "qa_groundtruth.csv"
    if path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite reviewable annotations: {path}; pass --force explicitly")
    out=[]
    normal_rows=[]
    for index, (paper_id, query, page, needle) in enumerate(NORMAL, 1):
        with fitz.open(HERE / PAPERS[paper_id]["pdf_path"]) as pdf:
            text=clean(pdf[page-1].get_text())
        quote=evidence_window(text,needle)
        row={"question_id":f"Q{index:03}","question_type":"normal","query":query,"selected_doc":paper_id,
             "gold_page":page,"gold_evidence":quote,"answerable":1,"distractor_doc":"","review_status":"pending"}
        out.append(row)
        normal_rows.append(row)
    for index,(paper_id,query) in enumerate(UNANSWERABLE,31):
        out.append({"question_id":f"Q{index:03}","question_type":"unanswerable","query":query,"selected_doc":paper_id,
                    "gold_page":"","gold_evidence":"","answerable":0,"distractor_doc":"","review_status":"pending"})
    for index,base in enumerate(normal_rows[::3],41):
        paper_id=base["selected_doc"]
        distractor_number=((int(paper_id[1:])-1)//5)*5 + (int(paper_id[1:])%5)+1
        distractor=f"P{distractor_number:02}"
        out.append({**base,"question_id":f"Q{index:03}","question_type":"scope",
                    "query":"In the selected paper only, " + base["query"][0].lower() + base["query"][1:],
                    "distractor_doc":distractor,"review_status":"pending"})
    assert len(out)==50
    with path.open("w",encoding="utf-8",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    print(f"Wrote {len(out)} draft questions to {path}")

if __name__ == "__main__":
    main()
