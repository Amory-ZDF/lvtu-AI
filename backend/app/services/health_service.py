from app.schemas.health import HealthPayload, ReadinessDetails


def build_live_response(service: str, environment: str) -> HealthPayload:
    return HealthPayload(
        status="ok",
        service=service,
        environment=environment,
        details=ReadinessDetails(database="not_checked"),
    )
