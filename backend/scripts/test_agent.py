#!/usr/bin/env python3
"""
旅图AI LangGraph Agent 测试脚本

测试账号：
  Email: test@lvtest.com
  Password: Test12345678
  User ID: c6487690-3e47-42f5-a754-4d07a0add669

用法：
  cd backend && source .venv/bin/activate
  python -m scripts.test_agent              # 运行全部测试
  python -m scripts.test_agent --scenario 1  # 只运行场景1
  python -m scripts.test_agent --scenario 2  # 只运行场景2

结果保存到：backend/test_agent_results/
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# ── 配置 ──────────────────────────────────────────────
BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"
AGENT_CHAT_URL = f"{BASE_URL}{API_PREFIX}/agent/chat"
AUTH_LOGIN_URL = f"{BASE_URL}{API_PREFIX}/auth/login"

TEST_USER = {
    "email": "test@lvtest.com",
    "password": "Test12345678",
}
TEST_USER_ID = "c6487690-3e47-42f5-a754-4d07a0add669"

# 结果输出目录
RESULTS_DIR = Path(__file__).resolve().parent.parent / "test_agent_results"


# ── 工具函数 ──────────────────────────────────────────
def login() -> str:
    """登录获取 access_token。"""
    resp = requests.post(
        AUTH_LOGIN_URL,
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]},
    )
    resp.raise_for_status()
    return resp.json()["data"]["token"]["access_token"]


def chat_with_agent(
    token: str,
    message: str,
    conversation_id: str | None = None,
    timeout: int = 120,
) -> dict:
    """调用 Agent Chat 端点。"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "message": message,
        "conversation_id": conversation_id,
        "user_id": TEST_USER_ID,
    }
    resp = requests.post(
        AGENT_CHAT_URL, json=payload, headers=headers, timeout=timeout
    )
    if resp.status_code != 200:
        return {
            "error": True,
            "status_code": resp.status_code,
            "detail": resp.text,
        }
    return resp.json()["data"]


def save_result(scenario_name: str, turn: int, message: str, result: dict, elapsed: float):
    """保存测试结果到文件。"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    entry = {
        "timestamp": timestamp,
        "scenario": scenario_name,
        "turn": turn,
        "user_message": message,
        "elapsed_seconds": round(elapsed, 2),
        "agent_reply": result.get("reply", ""),
        "conversation_id": result.get("conversation_id", ""),
        "structured_output": result.get("output"),
        "error": result.get("error", False),
        "error_detail": result.get("detail") if result.get("error") else None,
    }

    # 追加到会话日志
    log_file = RESULTS_DIR / f"test_log_{timestamp[:8]}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, indent=2) + "\n")

    # 也保存单次结果
    result_file = RESULTS_DIR / f"{scenario_name}_turn{turn}_{timestamp}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)

    return entry


def print_result(entry: dict):
    """格式化打印测试结果。"""
    print("\n" + "=" * 70)
    print(f"  场景: {entry['scenario']} | 轮次: {entry['turn']} | "
          f"耗时: {entry['elapsed_seconds']}s")
    print("=" * 70)
    print(f"\n📝 用户消息:\n  {entry['user_message']}")

    if entry.get("error"):
        print(f"\n❌ 错误 (HTTP {entry.get('status_code', '?')}):")
        print(f"  {entry.get('error_detail', '未知错误')}")
        return

    reply = entry.get("agent_reply", "")
    # 截断过长的回复
    if len(reply) > 2000:
        reply = reply[:2000] + "\n  ... (已截断)"
    print(f"\n🤖 Agent 回复:\n{reply}")

    output = entry.get("structured_output")
    if output:
        print("\n📊 结构化输出 (JSON):")
        print(json.dumps(output, ensure_ascii=False, indent=2))

    print(f"\n🔗 Conversation ID: {entry.get('conversation_id', 'N/A')}")


# ── 测试场景 ──────────────────────────────────────────
def scenario_1_destination_recommendation(token: str) -> str | None:
    """场景1: 目的地推荐（单轮）"""
    print("\n" + "─" * 70)
    print("  场景 1: 目的地推荐")
    print("─" * 70)

    message = "我想去日本旅行，预算5000元左右，大概5天，喜欢摄影和美食，有什么推荐？"
    start = time.time()
    result = chat_with_agent(token, message)
    elapsed = time.time() - start

    entry = save_result("destination_recommendation", 1, message, result, elapsed)
    print_result(entry)
    return entry.get("conversation_id")


def scenario_2_route_planning(token: str, conversation_id: str | None = None):
    """场景2: 路线规划（多轮，接续场景1的对话）"""
    print("\n" + "─" * 70)
    print("  场景 2: 路线规划（多轮对话）")
    print("─" * 70)

    # 第1轮：选定目的地，请求规划
    message = "我选京都，帮我规划一个5天的行程，节奏适中"
    start = time.time()
    result = chat_with_agent(token, message, conversation_id)
    elapsed = time.time() - start

    entry = save_result("route_planning", 1, message, result, elapsed)
    print_result(entry)
    conv_id = entry.get("conversation_id") or conversation_id

    # 第2轮：调整行程（测试多轮上下文）
    message2 = "第二天太赶了，能安排宽松一点吗？"
    start = time.time()
    result2 = chat_with_agent(token, message2, conv_id)
    elapsed2 = time.time() - start

    entry2 = save_result("route_planning", 2, message2, result2, elapsed2)
    print_result(entry2)


def scenario_3_knowledge_search(token: str):
    """场景3: 知识库搜索 + 机位推荐"""
    print("\n" + "─" * 70)
    print("  场景 3: 知识库搜索 + 机位推荐")
    print("─" * 70)

    message = "帮我查查北京有哪些好的拍照机位，最好是故宫附近的"
    start = time.time()
    result = chat_with_agent(token, message)
    elapsed = time.time() - start

    entry = save_result("knowledge_search", 1, message, result, elapsed)
    print_result(entry)


def scenario_4_outfit_recommendation(token: str):
    """场景4: 穿搭推荐"""
    print("\n" + "─" * 70)
    print("  场景 4: 穿搭推荐")
    print("─" * 70)

    message = "我秋天去京都，寺庙游览场景，穿什么比较合适？"
    start = time.time()
    result = chat_with_agent(token, message)
    elapsed = time.time() - start

    entry = save_result("outfit_recommendation", 1, message, result, elapsed)
    print_result(entry)


def scenario_5_multi_turn_context(token: str):
    """场景5: 多轮上下文记忆测试"""
    print("\n" + "─" * 70)
    print("  场景 5: 多轮上下文记忆测试")
    print("─" * 70)

    # 第1轮
    msg1 = "我想去东南亚旅行"
    start = time.time()
    r1 = chat_with_agent(token, msg1)
    e1 = time.time() - start
    entry1 = save_result("multi_turn_context", 1, msg1, r1, e1)
    print_result(entry1)
    conv_id = entry1.get("conversation_id")

    # 第2轮（不带目的地，测试是否记住"东南亚"）
    msg2 = "预算3000，大概4天"
    start = time.time()
    r2 = chat_with_agent(token, msg2, conv_id)
    e2 = time.time() - start
    entry2 = save_result("multi_turn_context", 2, msg2, r2, e2)
    print_result(entry2)

    # 第3轮（测试是否记住前两轮）
    msg3 = "帮我推荐最合适的那个"
    start = time.time()
    r3 = chat_with_agent(token, msg3, conv_id)
    e3 = time.time() - start
    entry3 = save_result("multi_turn_context", 3, msg3, r3, e3)
    print_result(entry3)


# ── 主函数 ────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="旅图AI Agent 测试脚本")
    parser.add_argument(
        "--scenario", type=int, choices=[1, 2, 3, 4, 5],
        help="只运行指定场景（1-5），不指定则运行全部",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  旅图AI LangGraph Agent 测试")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  测试账号: {TEST_USER['email']}")
    print(f"  结果目录: {RESULTS_DIR}")
    print("=" * 70)

    # 登录
    print("\n🔐 登录中...")
    try:
        token = login()
        print(f"  ✅ 登录成功，Token: {token[:30]}...")
    except Exception as e:
        print(f"  ❌ 登录失败: {e}")
        sys.exit(1)

    # 运行测试场景
    scenarios = {
        1: lambda: scenario_1_destination_recommendation(token),
        2: lambda: scenario_2_route_planning(token),
        3: lambda: scenario_3_knowledge_search(token),
        4: lambda: scenario_4_outfit_recommendation(token),
        5: lambda: scenario_5_multi_turn_context(token),
    }

    if args.scenario:
        scenarios[args.scenario]()
    else:
        # 场景1和2是连续的（场景2接续场景1的对话）
        conv_id = None
        if not args.scenario or args.scenario == 1:
            conv_id = scenario_1_destination_recommendation(token)
        if not args.scenario or args.scenario == 2:
            scenario_2_route_planning(token, conv_id)
        if not args.scenario or args.scenario == 3:
            scenario_3_knowledge_search(token)
        if not args.scenario or args.scenario == 4:
            scenario_4_outfit_recommendation(token)
        if not args.scenario or args.scenario == 5:
            scenario_5_multi_turn_context(token)

    print("\n" + "=" * 70)
    print(f"  测试完成！结果已保存到: {RESULTS_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
