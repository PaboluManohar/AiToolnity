from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from app.catalogue import _read_catalogue, clear_catalogue_cache, get_tool


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "tools.yaml"


def test_catalogue_loads_hierarchy_and_default_form(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TOOLS_CONFIG_PATH", str(CONFIG_PATH))
    clear_catalogue_cache()
    catalogue = _read_catalogue(CONFIG_PATH)
    assert len(catalogue.categories) == 29
    assert catalogue.default_model == "openrouter/free"
    tool = get_tool("career-path-finder")
    assert tool is not None
    assert tool["input_schema"]["fields"][0]["name"] == "context"
    assert tool["tones"][0]["id"] == "professional"


def test_new_yaml_tool_is_discovered_without_tool_specific_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    raw["categories"][0]["subcategories"][0]["items"].append(
        {
            "id": "test-added-tool",
            "name": "Test Added Tool",
            "description": "A test entry using the shared form and prompt.",
            "input_schema": {
                "fields": [
                    {
                        "name": "topic",
                        "label": "Topic",
                        "type": "text",
                        "required": True,
                        "options": [],
                    }
                ]
            },
            "system_prompt": "Write about the supplied topic.",
            "tones": [
                {
                    "id": "simple",
                    "name": "Simple",
                    "instructions": "Use plain language.",
                }
            ],
            "enabled": True,
        }
    )
    path = tmp_path / "tools.yaml"
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    monkeypatch.setenv("TOOLS_CONFIG_PATH", str(path))
    clear_catalogue_cache()

    tool = get_tool("test-added-tool")
    assert tool is not None
    assert tool["description"] == "A test entry using the shared form and prompt."
    assert tool["input_schema"]["fields"][0]["name"] == "topic"


def test_invalid_duplicate_tool_ids_are_reported(tmp_path: Path) -> None:
    raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    copy = deepcopy(raw["categories"][0]["subcategories"][0]["items"][0])
    raw["categories"][0]["subcategories"][0]["items"].append(copy)
    path = tmp_path / "duplicate-tools.yaml"
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    with pytest.raises(RuntimeError, match="duplicate tool ID"):
        _read_catalogue(path)


def test_invalid_input_schema_is_rejected(tmp_path: Path) -> None:
    raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    raw["tool_defaults"]["input_schema"]["fields"][0]["type"] = "unknown"
    path = tmp_path / "invalid-schema.yaml"
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid tool catalogue"):
        _read_catalogue(path)
