from app.services.preset_parser import classify_presets, extract_preset_ids


def test_classify_presets_applies_catalog_limits():
    base, sub = classify_presets([
        "with_elder",
        "walk_10m",
        "sinbong",
        "dongcheon",
        "flat_path",
        "shady_path",
        "green_path",
    ])

    assert [item["id"] for item in base] == ["with_elder", "walk_10m", "sinbong"]
    assert [item["id"] for item in sub] == ["flat_path", "shady_path"]


def test_classify_presets_deduplicates_ids():
    base, sub = classify_presets([
        "sinbong",
        "sinbong",
        "walk_30m",
        "shady_path",
        "shady_path",
    ])

    assert [item["id"] for item in base] == ["sinbong", "walk_30m"]
    assert [item["id"] for item in sub] == ["shady_path"]


def test_extract_preset_ids_filters_invalid_ids():
    valid, dropped = extract_preset_ids("`id:sinbong` `id:cool_path` `id:ghost_id`")

    assert valid == ["sinbong"]
    assert dropped == ["cool_path", "ghost_id"]
