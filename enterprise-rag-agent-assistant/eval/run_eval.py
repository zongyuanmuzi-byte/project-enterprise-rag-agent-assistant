import argparse
import json
from pathlib import Path
from typing import Any

import requests


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_DATASET_PATH = Path(__file__).with_name("eval_dataset.json")
NO_ANSWER_TEXT = "根据当前知识库资料，无法回答该问题。"
EMPTY_KB_TEXT = "当前知识库还没有可检索内容，请先上传文档后再提问。"


def load_dataset(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def call_agent_chat(base_url: str, question: str) -> dict[str, Any]:
    response = requests.post(
        f"{base_url.rstrip('/')}/agent/chat",
        json={"question": question},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def evaluate_case(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
    failures = []

    expected_tool = case.get("expected_tool")
    actual_tool = result.get("tool_used")

    if actual_tool != expected_tool:
        failures.append(f"tool_used expected={expected_tool!r}, got={actual_tool!r}")

    answer = result.get("answer") or ""
    sources = result.get("sources") or []
    expected_behavior = case.get("expected_behavior")
    expected_keywords = case.get("expected_keywords") or []

    if expected_behavior == "answer_with_sources":
        if not sources:
            failures.append("expected non-empty sources")

        for keyword in expected_keywords:
            if keyword not in answer:
                failures.append(f"missing keyword in answer: {keyword}")

    elif expected_behavior == "no_answer":
        if sources:
            failures.append("expected empty sources for no_answer")

        if NO_ANSWER_TEXT not in answer and EMPTY_KB_TEXT not in answer:
            failures.append("expected no-answer text")

    elif expected_behavior == "no_sources":
        if sources:
            failures.append("expected empty sources")

        if not answer:
            failures.append("expected non-empty answer")

    else:
        failures.append(f"unknown expected_behavior: {expected_behavior}")

    return len(failures) == 0, failures


def run_eval(base_url: str, dataset_path: Path) -> int:
    dataset = load_dataset(dataset_path)
    passed = 0
    failed = 0

    for case in dataset:
        case_id = case.get("id", "<unknown>")
        question = case["question"]

        try:
            result = call_agent_chat(base_url, question)
            ok, failures = evaluate_case(case, result)

        except Exception as exc:
            ok = False
            failures = [f"request failed: {type(exc).__name__}: {exc}"]

        if ok:
            passed += 1
            print(f"[PASS] {case_id}")
        else:
            failed += 1
            print(f"[FAIL] {case_id}")
            for failure in failures:
                print(f"  - {failure}")

    total = len(dataset)
    print("")
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return 0 if failed == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run manual API eval for Enterprise RAG Agent Assistant.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET_PATH))
    args = parser.parse_args()

    raise SystemExit(run_eval(args.base_url, Path(args.dataset)))


if __name__ == "__main__":
    main()
