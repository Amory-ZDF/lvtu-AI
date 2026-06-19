from pydantic import BaseModel


class ReadinessDetails(BaseModel):
    database: str


class HealthPayload(BaseModel):
    status: str
    service: str
    environment: str
    details: ReadinessDetails
