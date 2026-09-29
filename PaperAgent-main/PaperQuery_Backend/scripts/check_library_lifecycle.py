"""End-to-end Library test using only a newly created synthetic PDF.

The script creates uniquely named test data and removes that exact library in
finally. Set PAPERAGENT_TEST_USER and PAPERAGENT_TEST_PASSWORD before running.
"""

import io
import os
import time
import uuid

import fitz
import requests


base = os.getenv("PAPERAGENT_TEST_BASE", "http://127.0.0.1:8001")
username = os.environ["PAPERAGENT_TEST_USER"]
password = os.environ["PAPERAGENT_TEST_PASSWORD"]
session = requests.Session()
token = session.post(f"{base}/login", json={"username": username, "password": password}, timeout=20).json()["data"]["access_token"]
session.headers["Authorization"] = f"Bearer {token}"
knowledge_id = None


def require(name, response):
    result = response.json()
    print(f"{name}: HTTP {response.status_code}, status {result.get('status_code')}")
    if response.status_code != 200 or result.get("status_code") != 200:
        raise RuntimeError(f"{name} failed: {response.text[:300]}")
    return result


try:
    name = f"PaperAgent 自动回归 {uuid.uuid4().hex[:8]}"
    knowledge = require("create library", session.post(f"{base}/knowledges/createKnowledge", json={
        "knowledgeName": name, "knowledgeDescription": "Synthetic lifecycle check"}, timeout=20))
    knowledge_id = knowledge["data"]["knowledgeID"]
    require("edit library", session.post(f"{base}/knowledges/updateKnowledge", json={
        "knowledgeID": knowledge_id, "knowledgeName": name, "knowledgeDescription": "Edited synthetic lifecycle check"}, timeout=20))

    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "PaperAgent synthetic PDF for Library upload, index, reader, and notes regression.")
    pdf_bytes = document.tobytes()
    document.close()
    uploaded = require("upload PDF", session.post(f"{base}/document/upload", data={"knowledgeID": knowledge_id},
        files={"documentFile": ("paperagent_synthetic_check.pdf", io.BytesIO(pdf_bytes), "application/pdf")}, timeout=30))
    document_id = uploaded["data"]["documentID"]
    params = {"knowledgeID": knowledge_id, "documentID": document_id}
    require("list document", session.get(f"{base}/document/getDocumentList", params={"knowledgeID": knowledge_id}, timeout=20))
    pdf = session.get(f"{base}/document/getFile", params=params, timeout=20)
    if pdf.status_code != 200 or not pdf.content.startswith(b"%PDF-"):
        raise RuntimeError("PDF reader endpoint failed")
    print(f"read PDF: {len(pdf.content)} bytes")
    require("save note", session.post(f"{base}/note/updatenote", json={**params, "note": "# Synthetic note"}, timeout=20))
    notes = require("notes collection", session.get(f"{base}/notes/collection", timeout=20))["data"]
    if not any(item["documentID"] == document_id for item in notes):
        raise RuntimeError("Saved note missing from collection")

    status = None
    for _ in range(24):
        status = require("index status", session.get(f"{base}/document/Info", params=params, timeout=20))["data"]["documentStatus"]
        if status == 2:
            break
        time.sleep(5)
    if status != 2:
        raise RuntimeError("PDF indexing did not finish within 120 seconds")
    print("synthetic PDF indexed and ready")
finally:
    if knowledge_id:
        response = session.post(f"{base}/knowledges/deleteKnowledge", json={"knowledgeIDs": [knowledge_id]}, timeout=30)
        print(f"cleanup library: HTTP {response.status_code}, body {response.text[:180]}")
