# jobs.py
import re
from typing import List, Tuple

# Канонический список, 1-в-1 с вашим GLOBAL_LIST_INIT
WHITEJOBS = [
    "Captain",
    "Head of Personnel",
    "Head of Security",
    "Chief Engineer",
    "Chief Medical Officer",
    "Research Director",
    "AI",
]

# Нормализация: сюда добавляйте синонимы, сокращения, варианты написания
ALIASES = {
    "cap": "Captain",
    "captain": "Captain",
    "hos": "Head of Security",
    "head of security": "Head of Security",
    "hop": "Head of Personnel",
    "head of personnel": "Head of Personnel",
    "ce": "Chief Engineer",
    "chief engineer": "Chief Engineer",
    "cmo": "Chief Medical Officer",
    "chief medical officer": "Chief Medical Officer",
    "rd": "Research Director",
    "research director": "Research Director",
    "ai": "AI",
}

# Разбор текста заявки: извлекаем блоки в квадратных скобках, после ключевых слов, или просто через запятые
JOB_PATTERNS = [
    re.compile(r"\bjobs?\s*[:\-]\s*(?P<body>.+)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*\[(?P<body>[^\]]+)\]\s*$", re.IGNORECASE | re.MULTILINE),
]

SEPARATORS = re.compile(r"[,;/\|\u2013\u2014\-]+")  # запятая, точка с запятой, /, |, тире

def _canonize(token: str) -> str | None:
    key = token.strip().lower()
    if not key:
        return None
    # сначала прямое попадание в канон
    if token in WHITEJOBS:
        return token
    # потом по алиасам
    return ALIASES.get(key)

def normalize_jobs_from_text(text: str) -> Tuple[List[str], List[str]]:
    """
    Возвращает (валидные_канонические_роли, нераспознанные_токены).
    """
    candidates: list[str] = []

    # 1) По явным паттернам
    for pat in JOB_PATTERNS:
        for m in pat.finditer(text):
            body = m.group("body")
            candidates.extend(SEPARATORS.split(body))

    # 2) Если явных паттернов нет, пытаемся выделить из всей строки
    if not candidates:
        candidates = SEPARATORS.split(text)

    # Чистим и нормализуем
    valid: list[str] = []
    unknown: list[str] = []
    seen = set()

    for raw in candidates:
        t = raw.strip()
        if not t:
            continue
        canon = _canonize(t)
        if canon:
            if canon not in seen:
                valid.append(canon)
                seen.add(canon)
        else:
            unknown.append(t)

    return valid, unknown
