from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[2]
PRESET_CATALOG_PATH = BASE_DIR / "data" / "preset_catalog.json"


class PresetValidationError(ValueError):
    pass


def load_preset_catalog(path: Path = PRESET_CATALOG_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_preset_index(catalog: dict[str, Any]) -> dict[str, Any]:
    categories = catalog.get("categories", {})
    selection_rules = catalog.get("selection_rules", {})

    id_index: dict[str, dict[str, Any]] = {}
    label_index: dict[str, str] = {}
    alias_index: dict[str, str] = {}

    for category_name, items in categories.items():
        for item in items:
            preset_id = item["id"]
            id_index[preset_id] = {
                "category": category_name,
                "label": item["label"],
                "type": item["type"],
                "aliases": list(item.get("aliases", [])),
                "enabled": bool(item.get("enabled", False)),
            }
            label_index[item["label"]] = preset_id
            for alias in item.get("aliases", []):
                alias_index[alias] = preset_id

    return {
        "id_index": id_index,
        "label_index": label_index,
        "alias_index": alias_index,
        "selection_rules": selection_rules,
    }


def validate_preset_output(
    payload: dict[str, Any],
    catalog: dict[str, Any] | None = None,
    *,
    allow_alias_label: bool = False,
) -> list[str]:
    errors: list[str] = []

    if not isinstance(payload, dict):
        return ["output must be a JSON object"]

    catalog = catalog or load_preset_catalog()
    index = build_preset_index(catalog)
    selection_rules = index["selection_rules"]
    id_index = index["id_index"]
    label_index = index["label_index"]
    alias_index = index["alias_index"]

    allowed_top_level_fields = {
        "intent",
        "base_presets",
        "sub_presets",
        "confidence",
        "needs_confirmation",
        "reasons",
        "unmatched_tokens",
    }
    for key in payload:
        if key not in allowed_top_level_fields:
            errors.append(f"unexpected top-level field: {key}")

    required_fields = ["intent", "base_presets", "sub_presets", "confidence", "needs_confirmation"]
    for field in required_fields:
        if field not in payload:
            errors.append(f"missing required field: {field}")

    if not isinstance(payload.get("intent"), str) or not payload.get("intent", "").strip():
        errors.append("intent must be a non-empty string")

    base_presets = payload.get("base_presets")
    sub_presets = payload.get("sub_presets")
    if not isinstance(base_presets, list):
        errors.append("base_presets must be an array")
        base_presets = []
    if not isinstance(sub_presets, list):
        errors.append("sub_presets must be an array")
        sub_presets = []

    if len(base_presets) > int(selection_rules.get("max_base_presets", 3)):
        errors.append("base_presets exceeds the allowed maximum")
    if len(sub_presets) > int(selection_rules.get("max_sub_presets", 2)):
        errors.append("sub_presets exceeds the allowed maximum")

    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        errors.append("confidence must be a number between 0 and 1")

    if not isinstance(payload.get("needs_confirmation"), bool):
        errors.append("needs_confirmation must be a boolean")

    selected_ids: set[str] = set()
    selected_labels: set[str] = set()

    def validate_item(item: Any, role: str, index_in_list: int) -> None:
        if not isinstance(item, dict):
            errors.append(f"{role}[{index_in_list}] must be an object")
            return

        required_item_fields = ["id", "label", "category"]
        for field in required_item_fields:
            if field not in item:
                errors.append(f"{role}[{index_in_list}] missing field: {field}")

        allowed_item_fields = {"id", "label", "category", "source", "score"}
        for field in item:
            if field not in allowed_item_fields:
                errors.append(f"{role}[{index_in_list}] unexpected field: {field}")

        preset_id = item.get("id")
        label = item.get("label")
        category = item.get("category")

        if not isinstance(preset_id, str) or not preset_id:
            errors.append(f"{role}[{index_in_list}].id must be a non-empty string")
            return

        catalog_item = id_index.get(preset_id)
        if catalog_item is None:
            errors.append(f"{role}[{index_in_list}].id is not in preset catalog: {preset_id}")
            return

        if not catalog_item["enabled"]:
            errors.append(f"{role}[{index_in_list}].id is disabled in preset catalog: {preset_id}")

        if not isinstance(label, str) or not label:
            errors.append(f"{role}[{index_in_list}].label must be a non-empty string")
        else:
            canonical_label = catalog_item["label"]
            if label != canonical_label:
                if allow_alias_label and label in catalog_item["aliases"]:
                    pass
                else:
                    errors.append(
                        f"{role}[{index_in_list}].label does not match catalog label for {preset_id}: {label}"
                    )

        if not isinstance(category, str) or not category:
            errors.append(f"{role}[{index_in_list}].category must be a non-empty string")
        elif category != catalog_item["category"]:
            errors.append(
                f"{role}[{index_in_list}].category does not match catalog category for {preset_id}: {category}"
            )

        source = item.get("source")
        if source is not None and source not in {"stt", "manual", "ai"}:
            errors.append(f"{role}[{index_in_list}].source is invalid: {source}")

        score = item.get("score")
        if score is not None and (not isinstance(score, (int, float)) or not 0 <= float(score) <= 1):
            errors.append(f"{role}[{index_in_list}].score must be a number between 0 and 1")

        if catalog_item["type"] != ("base" if role == "base_presets" else "sub"):
            errors.append(f"{role}[{index_in_list}].type does not match selected role for {preset_id}")

        if preset_id in selected_ids:
            errors.append(f"duplicate preset id detected: {preset_id}")
        selected_ids.add(preset_id)

        if isinstance(label, str):
            if label in selected_labels and not selection_rules.get("allow_duplicate_labels", False):
                errors.append(f"duplicate preset label detected: {label}")
            selected_labels.add(label)

        if label and label not in label_index and label not in alias_index:
            errors.append(f"{role}[{index_in_list}].label is not in preset catalog: {label}")

    for idx, item in enumerate(base_presets):
        validate_item(item, "base_presets", idx)
    for idx, item in enumerate(sub_presets):
        validate_item(item, "sub_presets", idx)

    reasons = payload.get("reasons")
    if reasons is not None:
        if not isinstance(reasons, list):
            errors.append("reasons must be an array when provided")
        else:
            selected_reason_ids = {item.get("id") for item in base_presets + sub_presets if isinstance(item, dict)}
            for idx, reason in enumerate(reasons):
                if not isinstance(reason, dict):
                    errors.append(f"reasons[{idx}] must be an object")
                    continue

                allowed_reason_fields = {"preset_id", "reason"}
                for field in reason:
                    if field not in allowed_reason_fields:
                        errors.append(f"reasons[{idx}] unexpected field: {field}")

                if not isinstance(reason.get("preset_id"), str) or not reason.get("preset_id", ""):
                    errors.append(f"reasons[{idx}].preset_id must be a non-empty string")
                    continue
                if reason["preset_id"] not in selected_reason_ids:
                    errors.append(f"reasons[{idx}].preset_id is not present in selected presets: {reason['preset_id']}")
                if not isinstance(reason.get("reason"), str) or not reason.get("reason", "").strip():
                    errors.append(f"reasons[{idx}].reason must be a non-empty string")

    unmatched_tokens = payload.get("unmatched_tokens")
    if unmatched_tokens is not None:
        if not isinstance(unmatched_tokens, list) or any(not isinstance(token, str) for token in unmatched_tokens):
            errors.append("unmatched_tokens must be an array of strings when provided")

    return errors


def assert_valid_preset_output(
    payload: dict[str, Any],
    catalog: dict[str, Any] | None = None,
    *,
    allow_alias_label: bool = False,
) -> None:
    errors = validate_preset_output(payload, catalog, allow_alias_label=allow_alias_label)
    if errors:
        raise PresetValidationError("; ".join(errors))
