import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "tools.yaml"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InputField(StrictModel):
    name: str
    label: str
    type: Literal["text", "textarea", "email", "url", "number", "select"] = "text"
    required: bool = False
    placeholder: str | None = None
    options: list[str] = Field(default_factory=list)
    min_length: int | None = Field(default=None, ge=0)
    max_length: int | None = Field(default=None, gt=0)
    min_value: float | None = None
    max_value: float | None = None

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        if not re.fullmatch(r"^[a-z][a-z0-9_-]*$", value):
            raise ValueError(
                "Field names must start with a lowercase letter and use lowercase letters, "
                "numbers, underscores, or hyphens."
            )
        return value

    @model_validator(mode="after")
    def validate_options(self) -> "InputField":
        if self.type == "select" and not self.options:
            raise ValueError("Select fields must define at least one option.")
        if self.type != "select" and self.options:
            raise ValueError("Only select fields may define options.")
        if (
            self.min_length is not None
            and self.max_length is not None
            and self.min_length > self.max_length
        ):
            raise ValueError("Minimum field length cannot exceed maximum field length.")
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            raise ValueError("Minimum field value cannot exceed maximum field value.")
        return self


class InputSchema(StrictModel):
    fields: list[InputField] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_fields(self) -> "InputSchema":
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("Input field names must be unique.")
        return self


class Tone(StrictModel):
    id: str
    name: str = Field(min_length=1)
    instructions: str = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        if not _SLUG.fullmatch(value):
            raise ValueError("Tone IDs must use lowercase letters, numbers, and hyphens.")
        return value


class ToolDefaults(StrictModel):
    description_template: str = Field(min_length=1)
    input_schema: InputSchema
    system_prompt: str = Field(min_length=1)
    tones: list[Tone]
    enabled: bool = True

    @model_validator(mode="after")
    def unique_tones(self) -> "ToolDefaults":
        ids = [tone.id for tone in self.tones]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("Tool tones must have unique IDs and include at least one tone.")
        return self


class ToolOverrides(StrictModel):
    id: str
    name: str = Field(min_length=1)
    description: str | None = Field(default=None, min_length=1)
    input_schema: InputSchema | None = None
    system_prompt: str | None = Field(default=None, min_length=1)
    tones: list[Tone] | None = None
    enabled: bool | None = None
    sub_items: list["ToolOverrides"] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        if not _SLUG.fullmatch(value):
            raise ValueError("IDs must use lowercase letters, numbers, and hyphens.")
        return value

    @model_validator(mode="after")
    def unique_tones(self) -> "ToolOverrides":
        if self.tones is not None:
            ids = [tone.id for tone in self.tones]
            if not ids or len(ids) != len(set(ids)):
                raise ValueError("Tool tones must have unique IDs and include at least one tone.")
        return self


class Item(ToolOverrides):
    pass


class Subcategory(StrictModel):
    id: str
    name: str
    items: list[Item] = Field(default_factory=list)


class Category(StrictModel):
    id: str
    name: str
    subcategories: list[Subcategory] = Field(default_factory=list)


class Catalogue(StrictModel):
    version: str
    description: str
    default_model: str = "openrouter/free"
    tool_defaults: ToolDefaults
    categories: list[Category]


def _read_catalogue(path: Path) -> Catalogue:
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        catalogue = Catalogue.model_validate(raw)
    except (OSError, yaml.YAMLError, ValidationError) as error:
        raise RuntimeError(f"Invalid tool catalogue at {path}: {error}") from error

    try:
        catalogue.tool_defaults.description_template.format(name="tool")
    except (IndexError, KeyError, ValueError) as error:
        raise RuntimeError(
            f"Invalid tool catalogue at {path}: description_template must use only "
            "the {name} placeholder."
        ) from error

    seen_tool_ids: set[str] = set()
    for category in catalogue.categories:
        for subcategory in category.subcategories:
            for item in subcategory.items:
                tools = item.sub_items or [item]
                for tool in tools:
                    if tool.id in seen_tool_ids:
                        raise RuntimeError(
                            f"Invalid tool catalogue at {path}: duplicate tool ID '{tool.id}'."
                        )
                    seen_tool_ids.add(tool.id)
    return catalogue


@lru_cache(maxsize=1)
def get_catalogue() -> Catalogue:
    return _read_catalogue(Path(os.getenv("TOOLS_CONFIG_PATH", str(_DEFAULT_CONFIG_PATH))))


def clear_catalogue_cache() -> None:
    get_catalogue.cache_clear()


def effective_tool(tool: ToolOverrides, defaults: ToolDefaults) -> dict[str, Any]:
    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description
        or defaults.description_template.format(name=tool.name),
        "input_schema": (tool.input_schema or defaults.input_schema).model_dump(),
        "system_prompt": tool.system_prompt or defaults.system_prompt,
        "tones": [
            tone.model_dump() for tone in (tool.tones or defaults.tones)
        ],
        "enabled": defaults.enabled if tool.enabled is None else tool.enabled,
    }


def get_tool(tool_id: str) -> dict[str, Any] | None:
    catalogue = get_catalogue()
    for category in catalogue.categories:
        for subcategory in category.subcategories:
            for item in subcategory.items:
                for tool in item.sub_items or [item]:
                    if tool.id == tool_id:
                        result = effective_tool(tool, catalogue.tool_defaults)
                        if not result["enabled"]:
                            return None
                        return result
    return None


def list_categories() -> list[dict[str, str]]:
    return [{"id": item.id, "name": item.name} for item in get_catalogue().categories]


def list_subcategories(category_id: str) -> list[dict[str, str]] | None:
    category = next(
        (item for item in get_catalogue().categories if item.id == category_id), None
    )
    if category is None:
        return None
    return [{"id": item.id, "name": item.name} for item in category.subcategories]


def list_items(category_id: str, subcategory_id: str) -> list[dict[str, Any]] | None:
    category = next(
        (item for item in get_catalogue().categories if item.id == category_id), None
    )
    if category is None:
        return None
    subcategory = next(
        (item for item in category.subcategories if item.id == subcategory_id), None
    )
    if subcategory is None:
        return None
    result = []
    for item in subcategory.items:
        tool_nodes = item.sub_items or [item]
        tools = [
            effective_tool(tool, get_catalogue().tool_defaults)
            for tool in tool_nodes
            if get_tool(tool.id) is not None
        ]
        result.append(
            {
                "id": item.id,
                "name": item.name,
                "tools": tools,
            }
        )
    return result
