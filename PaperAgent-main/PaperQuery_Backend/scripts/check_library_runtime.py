"""Read-only Library smoke check, plus idempotent note-save verification.

Set PAPERAGENT_TEST_USER and PAPERAGENT_TEST_PASSWORD before running.
The note test writes the exact content it first read, so it does not change it.
"""

import os
import sys

import requests


BASE = os.environ.get("PAPERAGENT_TEST_BASE", "http://127.0.0.1:8001")
USER = os.environ.get("PAPERAGENT_TEST_USER")
PASSWORD = os.environ.get("PAPERAGENT_TEST_PASSWORD")
if not USER or not PASSWORD:
    raise SystemExit("Set PAPERAGENT_TEST_USER and PAPERAGENT_TEST_PASSWORD")

session = requests.Session()


def check(name, response, expected=200):
    print(f"{name}: HTTP {response.status_code}")
    if response.status_code != expected:
        print(response.text[:300])
        raise SystemExit(1)
    return response


login = check("login", session.post(f"{BASE}/login", json={"username": USER, "password": PASSWORD}))
session.headers["Authorization"] = f"Bearer {login.json()['data']['access_token']}"
check("auth", session.get(f"{BASE}/testlogin"))
libraries = check("libraries", session.get(f"{BASE}/knowledges/getKnowledgeList")).json()["data"]["knowledgeList"]
print(f"library count: {len(libraries)}")
if not libraries:
    raise SystemExit("No Library data to verify")

found = None
for library in libraries:
    documents = check("document list", session.get(f"{BASE}/document/getDocumentList", params={"knowledgeID": library["knowledgeID"]})).json()["data"]
    found = next((library, doc) for doc in documents if doc.get("documentStatus") == 2) if any(doc.get("documentStatus") == 2 for doc in documents) else None
    if found:
        break
if not found:
    raise SystemExit("No ready document to verify")

library, document = found
params = {"knowledgeID": library["knowledgeID"], "documentID": document["documentID"]}
check("document info", session.get(f"{BASE}/document/Info", params=params))
pdf = check("PDF", session.get(f"{BASE}/document/getFile", params=params))
if not pdf.content.startswith(b"%PDF-"):
    raise SystemExit("Reader endpoint did not return a PDF")
print(f"PDF bytes: {len(pdf.content)}")
check("summary", session.get(f"{BASE}/document/summarize", params=params))
note = check("read note", session.get(f"{BASE}/note/getnote", params=params)).json()["data"]["note"] or ""
check("save same note", session.post(f"{BASE}/note/updatenote", json={**params, "note": note}))
restored = check("read saved note", session.get(f"{BASE}/note/getnote", params=params)).json()["data"]["note"] or ""
if restored != note:
    raise SystemExit("Note content changed after save")

check("reject unauthenticated translation", requests.post(f"{BASE}/translate", json={"text": "Hello"}), 401)
translated = check("offline translation", session.post(f"{BASE}/translate", json={"text": "This paper proposes a new method for time series forecasting."}), 200).json()["data"]["text"]
print(f"translation contains Chinese: {any('一' <= character <= '龥' for character in translated)}")
if not any('一' <= character <= '龥' for character in translated):
    raise SystemExit("Offline translation was not Chinese")
print("Library smoke checks passed")
