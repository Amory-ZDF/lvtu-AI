"""Agent 集成模块。

提供基于 LangGraph 的旅行规划 Agent 和基于工作流 API 的路线规划集成。
"""

from app.integrations.agent.real_agent import RealRoutePlannerIntegration

__all__ = ["RealRoutePlannerIntegration"]

# LangGraph Agent 是可选的（需要 langgraph 依赖，且相关文件可能不在仓库中）
try:
    from app.integrations.agent.langgraph_agent import LangGraphTravelAgent
    from app.integrations.agent.router import router

    __all__ += ["LangGraphTravelAgent", "router"]
except ImportError:
    pass
