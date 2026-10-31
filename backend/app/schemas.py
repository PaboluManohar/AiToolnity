from datetime import datetime
from typing import Any

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=1, max_length=255)
    api_key: str | None = Field(default=None, min_length=20, max_length=500)

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,254}", value):
            raise ValueError("Enter a valid OpenRouter model identifier.")
        return value

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value or any(character.isspace() for character in value):
                raise ValueError("Enter a valid OpenRouter API key.")
        return value


class ExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_id: str = Field(min_length=1, max_length=255)
    inputs: dict[str, Any] = Field(max_length=32)
    tone: str = Field(min_length=1, max_length=80)


class RefinementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tone: str | None = None
    instructions: str | None = Field(default=None, max_length=4000)

    @field_validator("instructions")
    @classmethod
    def trim_instructions(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


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
