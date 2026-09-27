"""PaperAgent 本地接口冒烟测试。

默认只运行无副作用、无模型费用的检查；传入 ``--with-model`` 时会额外执行一次
普通问候的 SSE 模型请求，用于验证真实模型切换。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass

import requests


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def expect_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    expected_status: int = 200,
    **kwargs,
) -> dict:
    response = session.request(method, url, timeout=30, **kwargs)
    if response.status_code != expected_status:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:240]}")
    return response.json()


def read_sse(response: requests.Response) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    event_name = "message"
    data_lines: list[str] = []
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            if data_lines:
                events.append((event_name, json.loads("\n".join(data_lines))))
            event_name, data_lines = "message", []
        elif line.startswith("event:"):
            event_name = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].strip())
    if data_lines:
        events.append((event_name, json.loads("\n".join(data_lines))))
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description="PaperAgent API 冒烟测试")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--username", default=os.getenv("PAPERAGENT_TEST_USER", "admin"))
    parser.add_argument("--password", default=os.getenv("PAPERAGENT_TEST_PASSWORD", "123456"))
    parser.add_argument("--with-model", choices=("deepseek", "kimi", "zhipu"))
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    session = requests.Session()
    checks: list[Check] = []

    def run(name, operation):
        try:
            detail = operation()
            checks.append(Check(name, True, str(detail)))
        except Exception as exc:  # 冒烟脚本需要继续展示全部失败项
            checks.append(Check(name, False, str(exc)))

    run("存活检查", lambda: expect_json(session, "GET", f"{base}/health/live")["status"])
    run("就绪检查", lambda: expect_json(session, "GET", f"{base}/health/ready")["status"])

    token_holder: dict[str, str] = {}

    def login():
        payload = expect_json(
            session,
            "POST",
            f"{base}/login",
            json={"username": args.username, "password": args.password},
        )
        token_holder["token"] = payload["data"]["access_token"]
        session.headers["Authorization"] = f"Bearer {token_holder['token']}"
        return "认证成功"

    run("用户登录", login)
    if token_holder:
        run(
            "能力清单",
            lambda: ", ".join(
                expect_json(session, "GET", f"{base}/test/capabilities")["data"]["models"]
            ),
        )
        run(
            "JSON 往返",
            lambda: expect_json(
                session, "POST", f"{base}/test/echo", json={"message": "PaperAgent"}
            )["data"]["message"],
        )

        def test_sse():
            response = session.get(f"{base}/test/sse", stream=True, timeout=30)
            response.raise_for_status()
            events = read_sse(response)
            text = "".join(data.get("text", "") for event, data in events if event == "delta")
            if text != "PaperAgent":
                raise RuntimeError(f"SSE 内容不完整: {text!r}")
            return f"{len(events)} events"

        run("SSE 通道", test_sse)
        run(
            "知识库读取",
            lambda: expect_json(session, "GET", f"{base}/knowledges/getLibraryInfo")["status_code"],
        )
        run(
            "研究任务读取",
            lambda: expect_json(session, "GET", f"{base}/research/tasks")["status_code"],
        )

        if args.with_model:
            def test_model():
                response = session.post(
                    f"{base}/qa/stream",
                    json={
                        "question": "hello",
                        "model": args.with_model,
                        "document_ids": [],
                        "conversation_context": "",
                    },
                    stream=True,
                    timeout=90,
                )
                response.raise_for_status()
                events = read_sse(response)
                models = expect_json(session, "GET", f"{base}/test/capabilities")["data"]["models"]
                if args.with_model not in models:
                    raise RuntimeError(f"模型未注册: {args.with_model}")
                if not any(event == "delta" and data.get("text") for event, data in events):
                    raise RuntimeError("模型 SSE 未返回文本")
                return f"{args.with_model}: {len(events)} events"

            run("真实模型流式问答", test_model)

    for check in checks:
        mark = "PASS" if check.ok else "FAIL"
        print(f"[{mark}] {check.name}: {check.detail}")
    failed = sum(not check.ok for check in checks)
    print(f"\n结果: {len(checks) - failed}/{len(checks)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
