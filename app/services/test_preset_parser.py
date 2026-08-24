from preset_parser import extract_preset_ids

REAL_RESPONSE_1 = """유모차와 함께 그늘이 많은 길로 1시간 정도 산책할 경로를 찾고 있습니다.

## 이런 조건은 어떠세요? (5개)

1. **유아·유모차** `대상` `id:with_stroller` — 유모차 동반 산책이라고 하셨어요.
2. **평지 위주** `환경` `id:flat_path` — 유모차는 경사·단차가 적은 평지가 편해요.
3. **그늘 많은 길** `더위 대응` `id:shady_path` — 그늘진 길을 원하셨어요.
4. **1시간 안팎** `소요 시간` `id:walk_60m` — '한 시간쯤'이라 1시간 코스로 잡았어요.
5. **풍덕천1동** `장소` `id:pungdeokcheon_1` — 장소 언급이 없어 기본 지역으로 추정했어요.

> 말씀하신 내용이 조금 모호해서 우선 이렇게 골라봤어요. 맞는지 확인해 주시고, 다르면 편하게 말씀해 주세요.
"""

REAL_RESPONSE_2 = """유모차를 밀며 그늘 위주로 1시간가량 걷기 편한 평지 경로를 찾고 있습니다.
## 이런 조건은 어떠세요? (5개)
1. **유아·유모차** `대상` `id:with_stroller` — 유모차 동반 산책이라고 말씀하셨어요.
2. **평지 위주** `환경` `id:flat_path` — 유모차는 경사·단차가 적은 평지가 편해요.
3. **그늘 많은 길** `더위 대응` `id:shady_path` — 그늘 많은 길을 직접 요청하셨어요.
4. **1시간 안팎** `소요 시간` `id:walk_60m` — 1시간 정도 걷기를 원하셨어요.
5. **풍덕천1동** `장소` `id:pungdeokcheon_1` — 장소 언급이 없어 기본 지역으로 추정했어요.
> 말씀하신 내용이 조금 모호해서 우선 이렇게 골라봤어요. 맞는지 확인해 주시고, 다르면 편하게 말씀해 주세요."""


def test_extracts_all_five_ids():
    valid, dropped = extract_preset_ids(REAL_RESPONSE_1)
    assert valid == ["with_stroller", "flat_path", "shady_path", "walk_60m", "pungdeokcheon_1"]
    assert dropped == []


def test_works_without_blank_lines():
    valid, dropped = extract_preset_ids(REAL_RESPONSE_2)
    assert valid == ["with_stroller", "flat_path", "shady_path", "walk_60m", "pungdeokcheon_1"]


def test_filters_ai_selectable_false_ids():
    # cool_path(시원한길)는 ai_selectable=false라 걸러져야 함
    text = "추천 프리셋: `id:cool_path` `id:with_stroller`"
    valid, dropped = extract_preset_ids(text)
    assert "cool_path" not in valid
    assert "cool_path" in dropped
    assert valid == ["with_stroller"]


def test_filters_nonexistent_ids():
    # 카탈로그에 아예 없는 가짜 id
    text = "`id:with_stroller` `id:made_up_id_123`"
    valid, dropped = extract_preset_ids(text)
    assert valid == ["with_stroller"]
    assert dropped == ["made_up_id_123"]


def test_deduplicates_repeated_ids():
    text = "`id:with_stroller` 그리고 다시 `id:with_stroller`"
    valid, _ = extract_preset_ids(text)
    assert valid == ["with_stroller"]


def test_empty_text_returns_empty_lists():
    valid, dropped = extract_preset_ids("")
    assert valid == []
    assert dropped == []