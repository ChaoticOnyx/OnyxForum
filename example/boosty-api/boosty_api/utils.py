from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlencode

def to_form_urlencoded(data: Dict[str, Any]) -> str:
    return urlencode({k: v for k, v in data.items() if v is not None}, doseq=True)

def build_editorjs_text_payload(text: str) -> str:
    """Boosty dialog messages use 'data' field that is JSON-encoded list of blocks, then URL-encoded."""
    blocks = [
        {"type": "text", "content": json.dumps([text, "unstyled", []], ensure_ascii=False), "modificator": ""},
        {"type": "text", "content": "", "modificator": "BLOCK_END"},
    ]
    return json.dumps(blocks, ensure_ascii=False)

def ensure_list(v: Any) -> List[Any]:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]
