# jobs.py
import re
from typing import List, Tuple

# Канонический список, 1-в-1 с вашим GLOBAL_LIST_INIT
WHITEJOBS = [
    "Captain",
    "Head of Provisioning",
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
    "hop": "Head of Provisioning",
    "head of provisioning": "Head of Provisioning",
    "head of personnel": "Head of Provisioning",
    "ce": "Chief Engineer",
    "chief engineer": "Chief Engineer",
    "cmo": "Chief Medical Officer",
    "chief medical officer": "Chief Medical Officer",
    "rd": "Research Director",
    "research director": "Research Director",
    "ai": "AI",
}

# Разбор текста заявки: извлекаем блоки в квадратных скобках, после ключевых слов и из markdown-заголовков
JOB_PATTERNS = [
    # jobs/job: ...
    re.compile(r"\bjobs?\s*[:\-]\s*(?P<body>.+)$", re.IGNORECASE | re.MULTILINE),

    # [Captain, AI]
    re.compile(r"^\s*\[(?P<body>[^\]]+)\]\s*$", re.IGNORECASE | re.MULTILINE),

    # ## Job: Head of Personnel.
    re.compile(r"^\s*#{1,6}\s*job\s*[:\-]\s*(?P<body>.+)$", re.IGNORECASE | re.MULTILINE),

    # "Job: ..." (в т.ч. с точкой в конце)
    re.compile(r"^\s*job\s*[:\-]\s*(?P<body>.+?)(?:\.\s*)?$", re.IGNORECASE | re.MULTILINE),
]

SEPARATORS = re.compile(r"[,;/\|\u2013\u2014\-]+")  # запятая, точка с запятой, /, |, тире

# Предочистка "ошибочного" ввода
_STRIKE = re.compile(r"~~.*?~~")               # Mythrix Edorand~~
_PARENS = re.compile(r"\([^)]*\)")             # (Mythrix Edorand, ...)
_TRAIL_PUNCT = re.compile(r"[.\s]+$")          # завершающие точки/пробелы
_SPACES = re.compile(r"\s+")                   # нормализация пробелов

def _clean_body(s: str) -> str:
    s = _STRIKE.sub("", s)
    s = _PARENS.sub("", s)
    s = _TRAIL_PUNCT.sub("", s)
    s = _SPACES.sub(" ", s).strip()
    return s

def _canonize(token: str) -> str | None:
    t = _SPACES.sub(" ", token).strip()
    if not t:
        return None

    # Сопоставление с каноном без учёта регистра и завершающей пунктуации
    t2 = _TRAIL_PUNCT.sub("", t)
    for w in WHITEJOBS:
        if w.lower() == t2.lower():
            return w

    # По алиасам
    key = t2.lower()
    return ALIASES.get(key)

def normalize_jobs_from_text(text: str) -> Tuple[List[str], List[str]]:
    """
    Возвращает (валидные_канонические_роли, нераспознанные_токены).
    """
    candidates: list[str] = []

    # 1) По явным паттернам
    for pat in JOB_PATTERNS:
        for m in pat.finditer(text):
            body = _clean_body(m.group("body"))
            if body:
                candidates.extend(SEPARATORS.split(body))

    # 2) Если явных паттернов нет, пытаемся выделить из всей строки
    if not candidates:
        cleaned = _clean_body(text)
        candidates = SEPARATORS.split(cleaned)

    # Чистим и нормализуем
    valid: list[str] = []
    unknown: list[str] = []
    seen = set()

    for raw in candidates:
        t = _clean_body(raw)
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

