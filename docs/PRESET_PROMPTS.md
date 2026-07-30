# STT to Preset Prompts

This document defines the prompt set for the flow:

`STT text -> GPT preset extraction -> JSON validation -> user edit -> route recommendation`

The model must not recommend routes. It only extracts presets from the approved catalog.

## Shared Inputs

Use these files as the source of truth:

- `data/preset_catalog.json`
- `data/preset_output_schema.json`
- `data/route_tags.json`

## 1. System Prompt

```text
You are a preset extraction assistant for a climate-based walking route service.

Your only job is to convert user speech text into presets.
Do not recommend routes.
Do not invent new presets.
Only select presets that exist in the provided preset catalog.

Rules:
- Output JSON only. No markdown, no explanation, no code fences.
- Return at most 3 base presets and at most 2 sub presets.
- Use only labels and ids that exist in the provided catalog.
- If a user phrase does not match any preset, leave it in unmatched_tokens.
- If the request is ambiguous, lower confidence and set needs_confirmation to true.
- Prefer direct, observable user intent over guessing.
- Keep reasons short and tied to the user wording.

Output must match the provided JSON schema.
```

## 2. User Prompt Template

```text
User speech text:
{{stt_text}}

Available preset catalog:
{{preset_catalog_json}}

Selection rules:
- Max base presets: 3
- Max sub presets: 2
- Only use presets from the catalog
- If there is a conflict, prefer the most specific preset for the user intent

Current context:
- Mode: {{mode_or_none}}
- Optional location context: {{location_or_none}}
- Optional time context: {{time_or_none}}

Return JSON that matches the schema exactly.
```

## 3. Validation / Retry Prompt

Use this when the model response is invalid JSON, violates the schema, or contains unknown presets.

```text
Your previous response was invalid.

Fix the output using only the provided preset catalog.

Required corrections:
- Output JSON only.
- Remove any preset that is not in the catalog.
- Enforce max 3 base presets and max 2 sub presets.
- Ensure the result matches the JSON schema exactly.
- If uncertainty remains, set needs_confirmation to true.

Do not add any new presets.
Do not explain the changes.
Return only corrected JSON.
```

## 4. Example Prompt Pairs

### Example A

Input:

```text
더운데 강아지랑 30분 정도 산책하고 싶어.
```

Expected output:

```json
{
  "intent": "더운 날 반려동물과 30분 정도 산책하고 싶음",
  "base_presets": [
    { "id": "cool_path", "label": "시원한길", "category": "experience", "source": "stt", "score": 0.98 },
    { "id": "walk_30m", "label": "30분", "category": "duration", "source": "stt", "score": 0.97 },
    { "id": "pet_friendly", "label": "반려동물", "category": "condition", "source": "stt", "score": 0.99 }
  ],
  "sub_presets": [
    { "id": "shelter_rich", "label": "쉼터많음", "category": "experience", "source": "ai", "score": 0.82 },
    { "id": "low_surface_temp", "label": "표면온도낮음", "category": "experience", "source": "ai", "score": 0.8 }
  ],
  "confidence": 0.95,
  "needs_confirmation": false,
  "reasons": [
    { "preset_id": "cool_path", "reason": "'더운데'에서 더위를 피하고 싶다는 의도가 강함" },
    { "preset_id": "walk_30m", "reason": "'30분 정도'가 명시됨" },
    { "preset_id": "pet_friendly", "reason": "'강아지랑'이 명시됨" },
    { "preset_id": "shelter_rich", "reason": "더운 날에는 쉴 곳이 있는 길이 적합함" },
    { "preset_id": "low_surface_temp", "reason": "표면이 덜 뜨거운 길을 선호하는 맥락과 일치함" }
  ],
  "unmatched_tokens": ["더운데", "강아지랑"]
}
```

### Example B

Input:

```text
조용하고 평지 위주로 15분만 걷고 싶어.
```

Expected output:

```json
{
  "intent": "조용하고 평지 위주의 짧은 산책을 원함",
  "base_presets": [
    { "id": "walk_15m", "label": "15분", "category": "duration", "source": "stt", "score": 0.98 }
  ],
  "sub_presets": [
    { "id": "quiet_path", "label": "조용한길", "category": "place", "source": "stt", "score": 0.96 },
    { "id": "flat_path", "label": "평지", "category": "experience", "source": "stt", "score": 0.94 }
  ],
  "confidence": 0.93,
  "needs_confirmation": false,
  "reasons": [
    { "preset_id": "walk_15m", "reason": "'15분만'이 명시됨" },
    { "preset_id": "quiet_path", "reason": "'조용하고'라는 표현과 일치함" },
    { "preset_id": "flat_path", "reason": "'평지 위주'가 명시됨" }
  ],
  "unmatched_tokens": ["걷고 싶어"]
}
```

### Example C

Input:

```text
오늘은 좀 시원한 데로 걸을래.
```

Expected output:

```json
{
  "intent": "시원한 경로를 짧게 탐색하고 싶음",
  "base_presets": [
    { "id": "cool_path", "label": "시원한길", "category": "experience", "source": "stt", "score": 0.97 }
  ],
  "sub_presets": [],
  "confidence": 0.81,
  "needs_confirmation": true,
  "reasons": [
    { "preset_id": "cool_path", "reason": "'시원한 데'라는 핵심 의도가 명확함" }
  ],
  "unmatched_tokens": ["오늘은", "좀", "걸을래"]
}
```

## Implementation Notes

- Keep this prompt set in sync with `data/preset_catalog.json`.
- Use the validation prompt whenever JSON parsing or schema validation fails.
- If you add or rename presets, update both the catalog and the examples.

## 5. OpenAI API Messages Example

Use this shape in backend code when calling the model.

```python
import json

def build_preset_messages(stt_text: str, preset_catalog: dict, mode: str | None = None, location: str | None = None, time_context: str | None = None) -> list[dict]:
  return [
    {
      "role": "system",
      "content": (
        "You are a preset extraction assistant for a climate-based walking route service. "
        "Your only job is to convert user speech text into presets. "
        "Do not recommend routes. Do not invent new presets. "
        "Only select presets that exist in the provided preset catalog. "
        "Output JSON only and match the provided schema exactly."
      ),
    },
    {
      "role": "user",
      "content": (
        f"User speech text:\n{stt_text}\n\n"
        f"Available preset catalog:\n{json.dumps(preset_catalog, ensure_ascii=False, indent=2)}\n\n"
        "Selection rules:\n"
        "- Max base presets: 3\n"
        "- Max sub presets: 2\n"
        "- Only use presets from the catalog\n"
        "- If there is a conflict, prefer the most specific preset for the user intent\n\n"
        f"Current context:\n- Mode: {mode or 'none'}\n- Optional location context: {location or 'none'}\n- Optional time context: {time_context or 'none'}\n\n"
        "Return JSON that matches the schema exactly."
      ),
    },
  ]


def build_retry_messages(previous_response: str) -> list[dict]:
  return [
    {
      "role": "system",
      "content": (
        "You are a preset extraction assistant for a climate-based walking route service. "
        "Fix invalid JSON or schema violations only. Return JSON only."
      ),
    },
    {
      "role": "user",
      "content": (
        "Your previous response was invalid.\n\n"
        "Fix the output using only the provided preset catalog.\n\n"
        "Required corrections:\n"
        "- Output JSON only.\n"
        "- Remove any preset that is not in the catalog.\n"
        "- Enforce max 3 base presets and max 2 sub presets.\n"
        "- Ensure the result matches the JSON schema exactly.\n"
        "- If uncertainty remains, set needs_confirmation to true.\n\n"
        "Do not add any new presets.\n"
        "Do not explain the changes.\n"
        f"Previous response:\n{previous_response}"
      ),
    },
  ]
```

If you are using structured outputs, you can also pass `data/preset_output_schema.json` as the JSON schema contract in the same call.
