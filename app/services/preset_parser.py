import json
import re
from pathlib import Path

_ID_PATTERN = re.compile(r"id:([A-Za-z0-9_]+)")
_CATALOG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "preset_catalog.json"

with open(_CATALOG_PATH, encoding="utf-8") as f:
    _CATALOG = json.load(f)

# ai_selectable=true 인 것만 "에이전트가 낼 수 있는 유효한 id"로 인정
_VALID_IDS = {
    item["id"]
    for items in _CATALOG["categories"].values()
    for item in items
    if item.get("ai_selectable", True)
}

# id -> 한글 라벨 매핑
_LABELS = {
    item["id"]: item["label"]
    for items in _CATALOG["categories"].values()
    for item in items
}

# id -> 카테고리명(condition/environment/heat/duration/place/experience) 매핑
_CATEGORY_OF = {
    item["id"]: cat_name
    for cat_name, items in _CATALOG["categories"].items()
    for item in items
}

# base로 보여줄 카테고리: 소요 시간 / 장소 / 대상. 나머지(환경/더위 대응)는 sub
_BASE_CATEGORIES = {"duration", "place", "condition"}


def extract_preset_ids(agent_text: str) -> tuple[list[str], list[str]]:
    """반환값: (검증 통과 id 목록, 검증 실패해 버려진 id 목록)"""
    raw_ids = _ID_PATTERN.findall(agent_text)

    seen, ordered = set(), []
    for pid in raw_ids:
        if pid not in seen:
            seen.add(pid)
            ordered.append(pid)

    valid = [pid for pid in ordered if pid in _VALID_IDS]
    dropped = [pid for pid in ordered if pid not in _VALID_IDS]
    return valid, dropped


def to_labels(preset_ids: list[str]) -> list[str]:
    """id 목록을 한글 라벨 목록으로 변환"""
    return [_LABELS[pid] for pid in preset_ids if pid in _LABELS]


def classify_presets(preset_ids: list[str]) -> tuple[list[dict], list[dict]]:
    """id 목록을 카테고리 기준으로 (base 목록, sub 목록) 두 그룹으로 분류.

    base: 소요 시간, 장소, 대상
    sub: 환경, 더위 대응
    """
    base, sub = [], []
    for pid in preset_ids:
        if pid not in _LABELS:
            continue
        item = {"id": pid, "label": _LABELS[pid]}
        category = _CATEGORY_OF.get(pid)
        if category in _BASE_CATEGORIES:
            base.append(item)
        else:
            sub.append(item)
    return base, sub