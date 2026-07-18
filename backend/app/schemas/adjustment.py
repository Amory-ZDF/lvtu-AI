from __future__ import annotations

from datetime import time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AdjustmentChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: Literal["add", "update", "delete", "move"]
    day_id: UUID | None = None
    point_id: UUID | None = None
    target_day_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    point_type: str | None = Field(default=None, min_length=1, max_length=64)
    start_time: time | None = None
    end_time: time | None = None
    notes: str | None = Field(default=None, max_length=1000)
    position: int | None = Field(default=None, ge=1, le=100)

    @model_validator(mode="after")
    def validate_operation_fields(self) -> "AdjustmentChange":
        if self.operation == "add" and (self.day_id is None or not self.name):
            raise ValueError("add 操作必须包含 day_id 和 name")
        if self.operation in {"update", "delete", "move"} and self.point_id is None:
            raise ValueError(f"{self.operation} 操作必须包含 point_id")
        if self.operation == "move" and self.target_day_id is None:
            raise ValueError("move 操作必须包含 target_day_id")
        if self.operation == "update":
            editable = {"name", "point_type", "start_time", "end_time", "notes"}
            if not editable.intersection(self.model_fields_set):
                raise ValueError("update 操作没有可更新字段")
        return self


class AdjustmentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    changes: list[AdjustmentChange] = Field(min_length=1, max_length=30)
    summary: str = Field(min_length=1, max_length=500)
