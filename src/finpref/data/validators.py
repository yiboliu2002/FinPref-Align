"""Dataset validators."""

from __future__ import annotations

from typing import Any


def validate_messages(messages: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if not messages:
        return ["messages is empty"]
    roles = [m.get("role") for m in messages]
    if roles[0] != "system":
        errors.append("first message must be system")
    if "user" not in roles:
        errors.append("messages must contain user")
    if any("content" not in m or not m["content"] for m in messages):
        errors.append("each message must have non-empty content")
    return errors


def validate_sft_row(row: dict[str, Any]) -> list[str]:
    errors = []
    errors.extend(validate_messages(row.get("messages", [])))
    if not any(m.get("role") == "assistant" for m in row.get("messages", [])):
        errors.append("sft row must contain assistant response")
    return errors


def validate_dpo_row(row: dict[str, Any]) -> list[str]:
    errors = []
    for key in ["prompt", "chosen", "rejected"]:
        if key not in row:
            errors.append(f"missing {key}")
    if "prompt" in row:
        errors.extend(validate_messages(row["prompt"]))
    if not row.get("chosen") or not row.get("rejected"):
        errors.append("chosen and rejected must be non-empty")
    return errors


def validate_grpo_row(row: dict[str, Any]) -> list[str]:
    errors = []
    if "prompt" not in row:
        errors.append("missing prompt")
    else:
        errors.extend(validate_messages(row["prompt"]))
    if "meta" not in row:
        errors.append("missing meta")
    return errors


def validate_rows(kind: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    validators = {
        "sft": validate_sft_row,
        "dpo": validate_dpo_row,
        "grpo": validate_grpo_row,
        "eval": validate_grpo_row,
    }
    validate = validators[kind]
    failures = []
    for idx, row in enumerate(rows, start=1):
        errors = validate(row)
        if errors:
            failures.append({"line": idx, "id": row.get("id"), "errors": errors})
    return {"kind": kind, "total": len(rows), "failed": len(failures), "failures": failures[:50]}

