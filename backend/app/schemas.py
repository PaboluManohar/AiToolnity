from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=1, max_length=255)
    api_key: str | None = Field(default=None, min_length=20, max_length=500)


class ExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_id: str
    inputs: dict[str, Any]
    tone: str


class RefinementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tone: str | None = None
    instructions: str | None = Field(default=None, max_length=4000)


class ExecutionResponse(BaseModel):
    id: int
    tool_id: str
    input_data: dict[str, Any]
    result: str
    model: str
    tone: str
    created_at: datetime


class SettingsResponse(BaseModel):
    model: str
    has_api_key: bool


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
