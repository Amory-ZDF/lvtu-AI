#!/usr/bin/env python3
"""旅图 Lvtu-AI 产品评测脚本。

默认离线读取 test_cases.json 中的 sample_response 做评测；如果传入
--base-url，则会请求本地后端接口，并用真实响应评分。

用法：
    python3 评测/run_evaluation.py
    python3 评测/run_evaluation.py --base-url http://127.0.0.1:8000/api/v1
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_CASES = ROOT / "test_cases.json"
RESULT_DIR = ROOT / "results"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def response_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False).lower()


def non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def get_values(data: Any, path: str) -> list[Any]:
    """支持类似 options[].days[].spots[].name 的简单路径。"""
    current = [data]
    for raw_part in path.split("."):
        is_array = raw_part.endswith("[]")
        part = raw_part[:-2] if is_array else raw_part
        next_values: list[Any] = []
        for item in current:
            if isinstance(item, dict) and part in item:
                value = item[part]
                if is_array:
                    if isinstance(value, list):
                        next_values.extend(value)
                else:
                    next_values.append(value)
            elif isinstance(item, list) and part == "":
                next_values.extend(item)
        current = next_values
    return current


def count_path(data: Any, path: str) -> int:
    values = get_values(data, path)
    total = 0
    for value in values:
        if isinstance(value, list):
            total += len(value)
        elif non_empty(value):
            total += 1
    return total


def score_required_paths(data: Any, check: dict[str, Any]) -> tuple[float, str]:
    paths = check.get("paths", [])
    if not paths:
        return 0.0, "未配置 paths"
    passed = []
    failed = []
    for path in paths:
        values = get_values(data, path)
        if any(non_empty(v) for v in values):
            passed.append(path)
        else:
            failed.append(path)
    ratio = len(passed) / len(paths)
    detail = f"通过 {len(passed)}/{len(paths)}；缺失: {', '.join(failed) if failed else '无'}"
    return ratio, detail


def score_keyword_any(data: Any, check: dict[str, Any]) -> tuple[float, str]:
    text = response_text(data)
    keywords = check.get("keywords", [])
    min_hits = max(int(check.get("min_hits", 1)), 1)
    hits = [kw for kw in keywords if str(kw).lower() in text]
    ratio = min(len(hits) / min_hits, 1.0)
    detail = f"命中 {len(hits)}/{min_hits}: {', '.join(hits) if hits else '无'}"
    return ratio, detail


def score_avoid_keywords(data: Any, check: dict[str, Any]) -> tuple[float, str]:
    text = response_text(data)
    keywords = check.get("keywords", [])
    hits = [kw for kw in keywords if str(kw).lower() in text]
    ratio = 1.0 if not hits else 0.0
    detail = f"冲突词: {', '.join(hits) if hits else '无'}"
    return ratio, detail


def score_min_count(data: Any, check: dict[str, Any]) -> tuple[float, str]:
    path = check.get("path")
    minimum = max(int(check.get("min", 1)), 1)
    if not path:
        return 0.0, "未配置 path"
    count = count_path(data, path)
    ratio = min(count / minimum, 1.0)
    detail = f"{path} 数量 {count}/{minimum}"
    return ratio, detail


def score_numeric_range(data: Any, check: dict[str, Any]) -> tuple[float, str]:
    path = check.get("path")
    min_value = float(check.get("min", float("-inf")))
    max_value = float(check.get("max", float("inf")))
    values = get_values(data, path) if path else []
    numbers: list[float] = []
    for value in values:
        if isinstance(value, (int, float)):
            numbers.append(float(value))
        elif isinstance(value, str):
            match = re.search(r"-?\d+(?:\.\d+)?", value)
            if match:
                numbers.append(float(match.group()))
    if not numbers:
        return 0.0, f"{path} 未找到数字"
    valid = [n for n in numbers if min_value <= n <= max_value]
    ratio = len(valid) / len(numbers)
    detail = f"有效 {len(valid)}/{len(numbers)}，范围 [{min_value}, {max_value}]，值={numbers}"
    return ratio, detail


SCORERS = {
    "required_paths": score_required_paths,
    "keyword_any": score_keyword_any,
    "avoid_keywords": score_avoid_keywords,
    "min_count": score_min_count,
    "numeric_range": score_numeric_range,
}


def call_api(base_url: str, endpoint: str, payload: dict[str, Any], timeout: int) -> Any:
    url = base_url.rstrip("/") + endpoint
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 local/dev use
        raw = response.read().decode("utf-8")
    parsed = json.loads(raw)
    if isinstance(parsed, dict) and "data" in parsed:
        return parsed["data"]
    return parsed


def evaluate_case(case: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    source = "sample_response"
    response = case.get("sample_response")
    error = None
    if args.base_url and case.get("endpoint"):
        try:
            response = call_api(args.base_url, case["endpoint"], case.get("payload", {}), args.timeout)
            source = "api"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            error = f"API 调用失败，回退到 sample_response: {exc}"
            response = case.get("sample_response")
            source = "sample_response_fallback"

    checks_result = []
    total_weight = 0.0
    weighted_score = 0.0
    for check in case.get("checks", []):
        weight = float(check.get("weight", 0))
        total_weight += weight
        scorer = SCORERS.get(check.get("type"))
        if not scorer:
            ratio, detail = 0.0, f"未知检查类型: {check.get('type')}"
        else:
            ratio, detail = scorer(response, check)
        score = round(ratio * weight, 2)
        weighted_score += score
        checks_result.append(
            {
                "name": check.get("name"),
                "type": check.get("type"),
                "weight": weight,
                "score": score,
                "detail": detail,
                "reason": check.get("reason", ""),
            }
        )

    final_score = round((weighted_score / total_weight) * 100, 2) if total_weight else 0.0
    if final_score >= 90:
        level = "可上线重点路径"
    elif final_score >= 80:
        level = "可灰度验证"
    elif final_score >= 70:
        level = "可 Demo，不建议上线"
    elif final_score >= 60:
        level = "需要修复"
    else:
        level = "阻塞问题"

    return {
        "id": case.get("id"),
        "name": case.get("name"),
        "scenario": case.get("scenario"),
        "source": source,
        "score": final_score,
        "level": level,
        "error": error,
        "checks": checks_result,
    }


def write_markdown_report(path: Path, results: list[dict[str, Any]]) -> None:
    average = round(sum(r["score"] for r in results) / len(results), 2) if results else 0.0
    lines = [
        "# 旅图 AI 产品评测报告",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"测试用例数：{len(results)}",
        f"平均分：{average}",
        "",
        "## 总览",
        "",
        "| Case | 场景 | 分数 | 等级 | 数据源 |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for result in results:
        lines.append(
            f"| {result['id']} {result['name']} | {result['scenario']} | "
            f"{result['score']} | {result['level']} | {result['source']} |"
        )
    lines.extend(["", "## 明细", ""])
    for result in results:
        lines.extend(
            [
                f"### {result['id']}｜{result['name']}",
                "",
                f"- 场景：{result['scenario']}",
                f"- 分数：{result['score']}",
                f"- 等级：{result['level']}",
                f"- 数据源：{result['source']}",
            ]
        )
        if result.get("error"):
            lines.append(f"- 备注：{result['error']}")
        lines.extend(["", "| 检查项 | 得分/权重 | 结果 | 产品原因 |", "| --- | ---: | --- | --- |"])
        for check in result["checks"]:
            lines.append(
                f"| {check['name']} | {check['score']}/{check['weight']} | "
                f"{check['detail']} | {check['reason']} |"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="旅图 AI 产品评测脚本")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="测试用例 JSON 路径")
    parser.add_argument("--base-url", default=None, help="本地后端 API base url，例如 http://127.0.0.1:8000/api/v1")
    parser.add_argument("--timeout", type=int, default=10, help="API 请求超时时间，秒")
    args = parser.parse_args()

    cases_path = Path(args.cases)
    cases = load_json(cases_path)
    if not isinstance(cases, list):
        print("测试用例文件必须是 JSON 数组", file=sys.stderr)
        return 2

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    results = [evaluate_case(case, args) for case in cases]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = RESULT_DIR / f"evaluation_report_{timestamp}.json"
    md_path = RESULT_DIR / f"evaluation_report_{timestamp}.md"
    dump_json(json_path, {"results": results},)
    write_markdown_report(md_path, results)

    average = round(sum(r["score"] for r in results) / len(results), 2) if results else 0.0
    print(f"评测完成：{len(results)} 个 case，平均分 {average}")
    print(f"JSON 报告：{json_path}")
    print(f"Markdown 报告：{md_path}")
    return 0 if average >= 70 else 1


if __name__ == "__main__":
    raise SystemExit(main())
