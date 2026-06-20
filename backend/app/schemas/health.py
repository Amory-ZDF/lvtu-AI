from pydantic import BaseModel


class ReadinessDetails(BaseModel):
    database: str
    redis: str | None = None


class HealthPayload(BaseModel):
    status: str
    service: str
    environment: str
    details: ReadinessDetails
