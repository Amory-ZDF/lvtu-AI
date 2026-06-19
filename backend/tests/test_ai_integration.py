from __future__ import annotations

from types import SimpleNamespace

from app.core.exceptions import AppException
from app.core.safety import filter_sensitive_words, sanitize_content, validate_ai_output
from app.integrations.cache import ResponseCache
from app.integrations.factory import (
    get_media_asset_integration,
    get_recommender_integration,
    get_route_planner_integration,
)
from app.integrations.placeholders import (
    MockMediaAssetIntegration,
    MockRecommendationIntegration,
    MockRoutePlannerIntegration,
)
from app.integrations.prompts.destination import build_destination_prompt
from app.integrations.rag.store import InMemoryVectorStore
from app.schemas.planning import DestinationRecommendationRequest

# -----------------------------
# Factory 降级测试
# -----------------------------


def _make_settings(
    *,
    ai_provider: str = "mock",
    ai_api_key: str | None = None,
    ai_base_url: str | None = None,
    ai_model_name: str | None = None,
    agent_provider: str = "mock",
    agent_api_key: str | None = None,
    agent_base_url: str | None = None,
    agent_workflow_name: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        ai_provider=ai_provider,
        ai_api_key=ai_api_key,
        ai_base_url=ai_base_url,
        ai_model_name=ai_model_name,
        agent_provider=agent_provider,
        agent_api_key=agent_api_key,
        agent_base_url=agent_base_url,
        agent_workflow_name=agent_workflow_name,
    )


def test_factory_recommender_mock_when_provider_is_mock() -> None:
    settings = _make_settings(ai_provider="mock", ai_api_key="key", ai_base_url="url")
    integration = get_recommender_integration(settings)
    assert isinstance(integration, MockRecommendationIntegration)


def test_factory_recommender_mock_when_no_api_key() -> None:
    settings = _make_settings(
        ai_provider="openai",
        ai_api_key=None,
        ai_base_url="https://api.example.com",
        ai_model_name="gpt-4",
    )
    integration = get_recommender_integration(settings)
    assert isinstance(integration, MockRecommendationIntegration)


def test_factory_recommender_mock_when_no_base_url() -> None:
    settings = _make_settings(
        ai_provider="openai",
        ai_api_key="key",
        ai_base_url=None,
        ai_model_name="gpt-4",
    )
    integration = get_recommender_integration(settings)
    assert isinstance(integration, MockRecommendationIntegration)


def test_factory_route_planner_mock_when_provider_is_mock() -> None:
    settings = _make_settings(agent_provider="mock")
    integration = get_route_planner_integration(settings)
    assert isinstance(integration, MockRoutePlannerIntegration)


def test_factory_route_planner_mock_when_no_api_key() -> None:
    settings = _make_settings(
        agent_provider="langgenie",
        agent_api_key=None,
        agent_base_url="https://api.example.com",
        agent_workflow_name="wf",
    )
    integration = get_route_planner_integration(settings)
    assert isinstance(integration, MockRoutePlannerIntegration)


def test_factory_media_asset_always_mock() -> None:
    settings = _make_settings()
    integration = get_media_asset_integration(settings)
    assert isinstance(integration, MockMediaAssetIntegration)


# -----------------------------
# Prompt 模板测试
# -----------------------------


def test_build_destination_prompt_returns_messages_list() -> None:
    request = DestinationRecommendationRequest(
        departure_city="上海",
        duration_days=4,
        season="11月",
        travel_style=["慢游", "出片"],
        interests=["寺院", "咖啡"],
        budget_min=3000,
        budget_max=6000,
    )
    messages = build_destination_prompt(request)

    assert isinstance(messages, list)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "上海" in messages[1]["content"]
    assert "4" in messages[1]["content"]
    assert "11月" in messages[1]["content"]
    assert "慢游/出片" in messages[1]["content"]
    assert "寺院/咖啡" in messages[1]["content"]
    assert "3000-6000 RMB" in messages[1]["content"]


def test_build_destination_prompt_handles_missing_fields() -> None:
    request = DestinationRecommendationRequest()
    messages = build_destination_prompt(request)

    assert len(messages) == 2
    user_content = messages[1]["content"]
    assert "未指定" in user_content  # departure_city 默认值
    assert "不限" in user_content  # season 默认值


def test_build_destination_prompt_budget_only_max() -> None:
    request = DestinationRecommendationRequest(
        departure_city="北京",
        duration_days=3,
        budget_max=5000,
    )
    messages = build_destination_prompt(request)
    assert "≤5000 RMB" in messages[1]["content"]


def test_build_destination_prompt_no_budget() -> None:
    request = DestinationRecommendationRequest(
        departure_city="北京",
        duration_days=3,
    )
    messages = build_destination_prompt(request)
    assert "不限" in messages[1]["content"]


# -----------------------------
# Safety 测试
# -----------------------------


def test_filter_sensitive_words_replaces_banned_words() -> None:
    text = "this is fuck and shit content"
    result = filter_sensitive_words(text)
    assert "fuck" not in result.lower()
    assert "shit" not in result.lower()
    assert "***" in result


def test_filter_sensitive_words_case_insensitive() -> None:
    text = "What The FUCK"
    result = filter_sensitive_words(text)
    assert "fuck" not in result.lower()
    assert "***" in result


def test_filter_sensitive_words_empty_string() -> None:
    assert filter_sensitive_words("") == ""
    assert filter_sensitive_words(None) is None  # type: ignore[arg-type]


def test_filter_sensitive_words_no_match() -> None:
    text = "this is clean content"
    assert filter_sensitive_words(text) == text


def test_sanitize_content_removes_script_tags() -> None:
    text = "<script>alert('xss')</script>hello"
    result = sanitize_content(text)
    assert "<script>" not in result.lower()
    assert "hello" in result


def test_sanitize_content_escapes_html() -> None:
    text = "<b>bold</b>"
    result = sanitize_content(text)
    assert "&lt;b&gt;" in result


def test_sanitize_content_filters_sensitive_words() -> None:
    text = "fuck <script>alert(1)</script>"
    result = sanitize_content(text)
    assert "fuck" not in result.lower()
    assert "<script>" not in result.lower()


def test_validate_ai_output_success() -> None:
    output = {"destinations": [], "query_summary": "test"}
    result = validate_ai_output(output, ["destinations", "query_summary"])
    assert result == output


def test_validate_ai_output_missing_field() -> None:
    output = {"destinations": []}
    try:
        validate_ai_output(output, ["destinations", "query_summary"])
        raise AssertionError("Expected AppException")
    except AppException as exc:
        assert exc.status_code == 502
        assert "query_summary" in exc.message


def test_validate_ai_output_not_dict() -> None:
    try:
        validate_ai_output("not a dict", ["field"])  # type: ignore[arg-type]
        raise AssertionError("Expected AppException")
    except AppException as exc:
        assert exc.status_code == 502


# -----------------------------
# ResponseCache 测试
# -----------------------------


def test_response_cache_set_and_get() -> None:
    cache = ResponseCache()
    cache.set("key1", {"data": "value"}, ttl=60)
    result = cache.get("key1")
    assert result == {"data": "value"}


def test_response_cache_get_missing_key() -> None:
    cache = ResponseCache()
    assert cache.get("nonexistent") is None


def test_response_cache_expired() -> None:
    cache = ResponseCache()
    cache.set("key1", {"data": "value"}, ttl=-1)  # 已过期
    assert cache.get("key1") is None


def test_response_cache_make_key_stable() -> None:
    """相同 request_data 生成相同 key。"""
    data1 = {"a": 1, "b": 2}
    data2 = {"b": 2, "a": 1}  # 顺序不同
    key1 = ResponseCache.make_key(data1)
    key2 = ResponseCache.make_key(data2)
    assert key1 == key2


def test_response_cache_make_key_different_data() -> None:
    key1 = ResponseCache.make_key({"a": 1})
    key2 = ResponseCache.make_key({"a": 2})
    assert key1 != key2


def test_response_cache_clear() -> None:
    cache = ResponseCache()
    cache.set("key1", {"data": "value"}, ttl=60)
    cache.clear()
    assert cache.get("key1") is None


def test_response_cache_cleanup_expired() -> None:
    cache = ResponseCache()
    cache.set("expired1", {"data": 1}, ttl=-1)
    cache.set("expired2", {"data": 2}, ttl=-1)
    cache.set("valid", {"data": 3}, ttl=60)

    count = cache.cleanup_expired()
    assert count == 2
    assert cache.get("valid") == {"data": 3}


# -----------------------------
# RAG InMemoryVectorStore 测试
# -----------------------------


def test_inmemory_vector_store_add_and_search() -> None:
    store = InMemoryVectorStore()
    docs = [
        {"content": "京都的红叶很美，秋天是最佳季节", "id": "1"},
        {"content": "东京塔是著名的夜景拍摄地", "id": "2"},
        {"content": "大阪的美食以章鱼烧和大阪烧闻名", "id": "3"},
    ]
    store.add_documents(docs)

    results = store.search("京都红叶", top_k=2)
    assert len(results) > 0
    assert results[0]["id"] == "1"
    assert "score" in results[0]


def test_inmemory_vector_store_search_empty_store() -> None:
    store = InMemoryVectorStore()
    results = store.search("anything", top_k=5)
    assert results == []


def test_inmemory_vector_store_search_no_match() -> None:
    store = InMemoryVectorStore()
    store.add_documents([{"content": "京都红叶", "id": "1"}])
    results = store.search("zzzzzzz", top_k=5)
    assert results == []


def test_inmemory_vector_store_top_k_limit() -> None:
    store = InMemoryVectorStore()
    store.add_documents(
        [
            {"content": "京都 京都 京都", "id": "1"},
            {"content": "京都 东京", "id": "2"},
            {"content": "京都 大阪", "id": "3"},
        ]
    )
    results = store.search("京都", top_k=2)
    assert len(results) == 2


def test_inmemory_vector_store_search_empty_query() -> None:
    store = InMemoryVectorStore()
    store.add_documents([{"content": "京都红叶", "id": "1"}])
    results = store.search("", top_k=5)
    assert results == []


def test_inmemory_vector_store_preserves_document_fields() -> None:
    store = InMemoryVectorStore()
    store.add_documents(
        [
            {
                "content": "京都红叶",
                "id": "1",
                "title": "京都攻略",
                "metadata": {"source": "wiki"},
            }
        ]
    )
    results = store.search("京都", top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == "1"
    assert results[0]["title"] == "京都攻略"
    assert results[0]["metadata"] == {"source": "wiki"}
