"""Download and fingerprint the fixed ten-paper arXiv evaluation corpus."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import fitz
import requests

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "datasets" / "corpus"
PAPERS = [
    ("P01", "RAG", "2005.11401", "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"),
    ("P02", "RAG", "2310.11511", "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection"),
    ("P03", "RAG", "2401.15884", "Corrective Retrieval Augmented Generation"),
    ("P04", "RAG", "2305.06983", "Active Retrieval Augmented Generation"),
    ("P05", "RAG", "2301.12652", "REPLUG: Retrieval-Augmented Black-Box Language Models"),
    ("P06", "ANOMALY", "2110.02642", "Anomaly Transformer: Time Series Anomaly Detection with Association Discrepancy"),
    ("P07", "ANOMALY", "2201.07284", "TranAD: Deep Transformer Networks for Anomaly Detection in Multivariate Time Series Data"),
    ("P08", "ANOMALY", "2306.10347", "DCdetector: Dual Attention Contrastive Representation Learning for Time Series Anomaly Detection"),
    ("P09", "ANOMALY", "2009.02040", "Multivariate Time-series Anomaly Detection via Graph Attention Network"),
    ("P10", "ANOMALY", "2210.02186", "TimesNet: Temporal 2D-Variation Modeling for General Time Series Analysis"),
]

def main():
    CORPUS.mkdir(parents=True, exist_ok=True)
    rows=[]
    for paper_id, cluster, arxiv_id, title in PAPERS:
        path = CORPUS / f"{paper_id}.pdf"
        if not path.exists():
            response = requests.get(f"https://arxiv.org/pdf/{arxiv_id}", timeout=60)
            response.raise_for_status()
            if not response.content.startswith(b"%PDF-"):
                raise RuntimeError(f"{paper_id}: arXiv response is not a PDF")
            path.write_bytes(response.content)
        data=path.read_bytes()
        if not data.startswith(b"%PDF-"):
            raise RuntimeError(f"{paper_id}: invalid local PDF")
        with fitz.open(path) as pdf:
            pages=len(pdf)
            extractable=int(any(pdf[i].get_text().strip() for i in range(min(pages,3))))
        rows.append({"paper_id":paper_id,"cluster_id":cluster,"title":title,"arxiv_id":arxiv_id,
                     "source_url":f"https://arxiv.org/abs/{arxiv_id}","pdf_path":f"datasets/corpus/{paper_id}.pdf",
                     "page_count":pages,"text_extractable":extractable,"sha256":hashlib.sha256(data).hexdigest(),
                     "byte_size":len(data)})
        print(paper_id, arxiv_id, pages, len(data))
    path=HERE / "datasets" / "paper_corpus.csv"
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    main()
