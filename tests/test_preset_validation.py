from app.services.preset_validation import PresetValidationError, assert_valid_preset_output, load_preset_catalog, validate_preset_output


def test_validate_preset_output_accepts_known_presets():
    catalog = load_preset_catalog()
    payload = {
        "intent": "시원한 경로를 짧게 탐색하고 싶음",
        "base_presets": [
            {"id": "cool_path", "label": "시원한길", "category": "experience", "source": "stt", "score": 0.97},
            {"id": "walk_30m", "label": "30분", "category": "duration", "source": "stt", "score": 0.9},
        ],
        "sub_presets": [
            {"id": "shelter_rich", "label": "쉼터많음", "category": "experience", "source": "ai", "score": 0.81},
        ],
        "confidence": 0.88,
        "needs_confirmation": False,
        "reasons": [
            {"preset_id": "cool_path", "reason": "시원한 길을 원한다는 뜻임"},
            {"preset_id": "walk_30m", "reason": "30분 정도 걷고 싶다는 뜻임"},
        ],
        "unmatched_tokens": ["짧게"],
    }

    assert validate_preset_output(payload, catalog) == []
    assert_valid_preset_output(payload, catalog)


def test_validate_preset_output_rejects_unknown_and_over_limit_presets():
    catalog = load_preset_catalog()
    payload = {
        "intent": "검증 실패 예시",
        "base_presets": [
            {"id": "cool_path", "label": "시원한길", "category": "experience"},
            {"id": "walk_15m", "label": "15분", "category": "duration"},
            {"id": "walk_30m", "label": "30분", "category": "duration"},
            {"id": "ghost_preset", "label": "유령프리셋", "category": "experience"},
        ],
        "sub_presets": [
            {"id": "flat_path", "label": "평지", "category": "sub"},
            {"id": "unknown_sub", "label": "없는서브", "category": "place"},
            {"id": "shelter_rich", "label": "쉼터많음", "category": "experience"},
        ],
        "confidence": 1.2,
        "needs_confirmation": "nope",
    }

    errors = validate_preset_output(payload, catalog)

    assert any("base_presets exceeds the allowed maximum" in error for error in errors)
    assert any("sub_presets exceeds the allowed maximum" in error for error in errors)
    assert any("is not in preset catalog: ghost_preset" in error for error in errors)
    assert any("is not in preset catalog: unknown_sub" in error for error in errors)
    assert any("confidence must be a number between 0 and 1" in error for error in errors)
    assert any("needs_confirmation must be a boolean" in error for error in errors)

    try:
        assert_valid_preset_output(payload, catalog)
    except PresetValidationError as exc:
        assert "ghost_preset" in str(exc)
    else:
        raise AssertionError("Expected PresetValidationError")
