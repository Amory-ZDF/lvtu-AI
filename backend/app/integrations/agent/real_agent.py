"""基于工作流 API 的真实路线规划集成实现。

Agent API 格式：
POST {base_url}/workflows/{workflow_name}/run
Body: {"input": {...}, "api_key": ...}
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from app.core.exceptions import AppException
from app.core.safety import sanitize_content, validate_ai_output
from app.integrations.prompts.route import build_route_prompt
from app.schemas.planning import (
    ImageResource,
    RouteDayPlan,
    RouteGenerationPayload,
    RouteGenerationRequest,
    RouteOption,
    RouteSpot,
)

logger = logging.getLogger(__name__)


def _placeholder_image(description: str, category: str = "spot") -> ImageResource:
    """根据 Agent 返回的描述生成占位图资源。"""
    return ImageResource(
        category=category,
        url="",
        thumbnail_url="",
        alt=description,
        provider="real-agent",
        placeholder=True,
    )


class RealRoutePlannerIntegration:
    """基于工作流 API 的路线规划集成。

    调用格式：POST {base_url}/workflows/{workflow_name}/run
    请求体：{"input": {...}, "api_key": ...}
    """

    def __init__(self, base_url: str, api_key: str, workflow_name: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._workflow_name = workflow_name

    def generate_plan(
        self,
        request: RouteGenerationRequest,
    ) -> RouteGenerationPayload:
        messages = build_route_prompt(request)
        raw_content = self._call_workflow(messages)
        data = self._parse_json_response(raw_content)
        return self._build_payload(data, request)

    def _call_workflow(self, messages: list[dict]) -> str:
        """调用 Agent 工作流 API 并返回输出内容。"""
        url = f"{self._base_url}/workflows/{self._workflow_name}/run"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "input": {"messages": messages},
            "api_key": self._api_key,
        }

        prompt_length = sum(len(m.get("content", "")) for m in messages)
        start = time.perf_counter()
        success = False
        status_code: int | None = None
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, headers=headers, json=body)
                status_code = response.status_code
                response.raise_for_status()
                payload = response.json()
                content = self._extract_workflow_output(payload)
                success = True
                return content
        except httpx.HTTPStatusError as exc:
            logger.exception(
                "Agent API returned non-2xx status: %s, body=%s",
                exc.response.status_code,
                exc.response.text[:500],
            )
            raise AppException(
                status_code=502,
                code="agent_provider_error",
                message=f"Agent 服务返回错误状态：{exc.response.status_code}",
            ) from exc
        except httpx.RequestError as exc:
            logger.exception("Agent API request failed: %s", exc)
            raise AppException(
                status_code=502,
                code="agent_provider_unreachable",
                message="无法连接 Agent 服务",
            ) from exc
        except (KeyError, IndexError, TypeError) as exc:
            logger.exception("Agent API response missing expected fields: %s", exc)
            raise AppException(
                status_code=502,
                code="agent_response_invalid",
                message="Agent 服务返回结构异常",
            ) from exc
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "Agent call: prompt_length=%s response_status=%s success=%s elapsed_ms=%s",
                prompt_length,
                status_code,
                success,
                elapsed_ms,
            )

    @staticmethod
    def _extract_workflow_output(payload: dict) -> str:
        """从工作流响应中提取输出内容。

        兼容多种常见格式：
        - {"output": "..."}
        - {"output": {"content": "..."}}
        - {"result": "..."}
        - {"data": {...}}
        - 直接返回内容字符串
        """
        if "output" in payload:
            output = payload["output"]
            if isinstance(output, str):
                return output
            if isinstance(output, dict):
                if "content" in output:
                    return str(output["content"])
                return json.dumps(output, ensure_ascii=False)
        if "result" in payload:
            result = payload["result"]
            if isinstance(result, str):
                return result
            return json.dumps(result, ensure_ascii=False)
        if "data" in payload:
            data = payload["data"]
            if isinstance(data, str):
                return data
            return json.dumps(data, ensure_ascii=False)
        raise KeyError("workflow response missing output/result/data field")

    @staticmethod
    def _parse_json_response(content: str) -> dict:
        """解析 Agent 返回的 JSON 字符串。"""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.exception("Failed to parse Agent JSON response: %s", content[:500])
            raise AppException(
                status_code=502,
                code="agent_response_invalid",
                message="Agent 返回内容无法解析为 JSON",
            ) from exc
        if not isinstance(data, dict):
            raise AppException(
                status_code=502,
                code="agent_response_invalid",
                message="Agent 返回内容不是 JSON 对象",
            )
        return data

    def _build_payload(
        self,
        data: dict,
        request: RouteGenerationRequest,
    ) -> RouteGenerationPayload:
        """将 Agent 返回的 JSON 转换为 RouteGenerationPayload。"""
        validate_ai_output(data, ["options"])

        options_raw = data.get("options", [])
        if not isinstance(options_raw, list):
            raise AppException(
                status_code=502,
                code="agent_response_invalid",
                message="options 字段不是列表",
            )

        options: list[RouteOption] = []
        for idx, opt in enumerate(options_raw):
            if not isinstance(opt, dict):
                continue
            options.append(
                RouteOption(
                    id=str(opt.get("id", f"route-{idx}")),
                    title=sanitize_content(str(opt.get("title", ""))),
                    pace=sanitize_content(str(opt.get("pace", "balanced"))),
                    estimated_budget=sanitize_content(
                        str(opt.get("estimated_budget", "")),
                    ),
                    photo_score=float(opt.get("photo_score", 8.0)),
                    summary=sanitize_content(str(opt.get("summary", ""))),
                    days=self._build_days(opt.get("days", [])),
                ),
            )

        if not options:
            raise AppException(
                status_code=502,
                code="agent_response_invalid",
                message="Agent 未返回任何路线方案",
            )

        destination_name = sanitize_content(
            str(data.get("destination_name", request.destination_name)),
        )
        return RouteGenerationPayload(
            destination_name=destination_name,
            options=options,
        )

    @staticmethod
    def _build_days(days_raw: Any) -> list[RouteDayPlan]:
        """构建每日计划列表。"""
        if not isinstance(days_raw, list):
            return []
        days: list[RouteDayPlan] = []
        for day_item in days_raw:
            if not isinstance(day_item, dict):
                continue
            spots_raw = day_item.get("spots", [])
            spots: list[RouteSpot] = []
            if isinstance(spots_raw, list):
                for spot in spots_raw:
                    if not isinstance(spot, dict):
                        continue
                    spot_name = sanitize_content(str(spot.get("name", "")))
                    spots.append(
                        RouteSpot(
                            time_slot=sanitize_content(str(spot.get("time_slot", ""))),
                            name=spot_name,
                            description=sanitize_content(
                                str(spot.get("description", "")),
                            ),
                            suggested_duration_hours=float(
                                spot.get("suggested_duration_hours", 1.0),
                            ),
                            images=[_placeholder_image(spot_name, category="spot")],
                        ),
                    )
            days.append(
                RouteDayPlan(
                    day=int(day_item.get("day", len(days) + 1)),
                    theme=sanitize_content(str(day_item.get("theme", ""))),
                    commute_tip=sanitize_content(
                        str(day_item.get("commute_tip", "")),
                    ),
                    spots=spots,
                ),
            )
        return days
