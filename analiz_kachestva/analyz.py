# -*- coding: utf-8 -*-
"""
Анализатор качества поступающей информации с рейтингом A/B/C/D.

Подаёшь текст (файл .txt/.md) или вставку — получаешь рейтинг качества
A (≥80) / B (60–79) / C (40–59) / D (<40) + breakdown по 5 критериям.
Полностью локально, чистая stdlib, без LLM API.

Использование:
    python analyz.py путь\к\файлу.md      # анализ файла → отчёт + JSON в reports/
    python analyz.py --demo               # прогон на 3 встроенных демо-текстах
    python analyz.py                      # текст читается из stdin

Импорт:
    from analyz import analyze, rate
    result = analyze("текст документа...")
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime

# ── Общий логгер Ильи (правило «логи → D:\Логи») ──────────────────────────
sys.path.insert(0, r"D:\Логи")
from logger import get_logger  # noqa: E402  (файл D:\Логи\logger.py существует)

LOG = get_logger("analiz_kachestva", "analizator")

# ── Папки проекта ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# ── Словари маркеров ──────────────────────────────────────────────────────

# Вода / пустые обороты (критерий «Конкретность», штраф за каждое вхождение)
VODA_PATTERNS = [
    r"в современном мире", r"в современном обществе", r"играет ключевую роль",
    r"играет важную роль", r"играет огромную роль", r"революционн\w+",
    r"уникальн\w+", r"синерги\w+", r"на сегодняшний день", r"как известно",
    r"не вызывает сомнений", r"общепризнанно", r"многим известно",
    r"как все мы знаем", r"в наше время", r"без преувеличения",
    r"поистине", r"бесспорно", r"актуальность \w+ обусловлена",
]

# Шаблонные обороты ИИ-текста (критерий «ИИ-шаблонность», инверсия).
# Взято эхом из skill ai-detector Ильи (.claude/skills/ai-detector/).
AI_PATTERNS = [
    r"важно отметить", r"стоит подчеркнуть", r"стоит отметить",
    r"необходимо подчеркнуть", r"необходимо отметить", r"подводя итог",
    r"в заключение\b", r"в заключение можно сказать", r"подытоживая",
    r"давайте рассмотрим", r"давайте разберём", r"давайте разберем",
    r"стоит понимать", r"важно понимать", r"нельзя не отметить",
    r"в первую очередь стоит", r"ключевым моментом является",
    r"особое внимание стоит уделить", r"резюмируя", r"итак,?[ \n]",
    r"однако стоит отметить", r"при этом важно",
]

# Фразы «очевидности» без источника (критерий «Доказательность», минус)
NEDOKAZANNOST = [
    r"\bговорят\b", r"\bходят слухи\b", r"\bизвестно,? что\b",
    r"\bочевидно\b", r"\bвсе знают\b", r"\bпо слухам\b",
    r"\bэксперты (?:считают|утверждают)\b", r"\bнекоторые считают\b",
]

# Маркеры выводов/резюме (критерий «Согласованность структуры»)
VYVOD_PATTERNS = [
    r"#{1,6}\s*(?:вывод\w*|резюме|итог\w*|заключение|summary)",
    r"\b(?:итак|итог|выводы?|резюме|в заключение|подведём итог|подведем итог)\b",
    r"\bTL;?DR\b",
]

# ── Регэкспы фактов ────────────────────────────────────────────────────────
RE_NUM_PROC = re.compile(r"\d+(?:[.,]\d+)?\s*%")                     # проценты
RE_NUM_MONEY = re.compile(r"\d+(?:[.,]\d+)?\s*(?:₽|\brub\b|\bруб\b|\$|€|тыс\.?|млн|млрд)", re.IGNORECASE)  # деньги
RE_URL = re.compile(r"https?://[^\s)>\]]+")
RE_MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
RE_N_SAMPLE = re.compile(r"\bN\s*=\s*\d+")

RE_DATE_ISO = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")
RE_DATE_RU = re.compile(
    r"\b(\d{1,2})\.(0[1-9]|1[0-2])\.(20\d{2})\b"                    # 30.09.2026
)
RE_DATE_MONTH = re.compile(
    r"\b(?:январ[ьяуе]|феврал[ьяуе]|март[ае]|апрел[ьяуе]|ма[ейя]|июн[ьяуе]|"
    r"июл[ьяуе]|август[ае]|сентябр[ьяуе]|октябр[ьяуе]|ноябр[ьяуе]|декабр[ьяуе])"
    r"\s*(\d{1,4})?", re.IGNORECASE
)                                                                    # «в мае», «январь 2026»
RE_YEAR = re.compile(r"\b(19\d{2}|20\d{2})\s*г(?:\.|од)?\b")         # «2026 г.» / «год 2026»

MESES = {
    "январ": 1, "феврал": 2, "март": 3, "апрел": 4, "мае": 5, "мая": 5,
    "май": 5, "июн": 6, "июл": 7, "август": 8, "сентябр": 9, "октябр": 10,
    "ноябр": 11, "декабр": 12,
}

# Возраст даты: <1 года = 20, до 3 лет = 12, до 7 = 6, старше = 3
NOW = datetime(2026, 9, 30)


def _norm(text: str) -> str:
    """Нормализация: NFC, единый перенос строк, нижний регистр для словарей."""
    text = unicodedata.normalize("NFC", text)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _words(text: str):
    """Слова для подсчёта плотности (буквенные последовательности + числа)."""
    return re.findall(r"[а-яёa-z]+|\d+(?:[.,]\d+)?", text.lower(), re.IGNORECASE)


def _count_matches(patterns, text):
    """Число вхождений списка регэкспов в тексте."""
    total = 0
    for pat in patterns:
        total += len(re.findall(pat, text, re.IGNORECASE))
    return total


def _extract_dates(text: str):
    """Извлечь все найденные даты как (год, месяц) для расчёта возраста."""
    dts = []
    for m in RE_DATE_ISO.finditer(text):
        dts.append((int(m.group(1)), int(m.group(2))))
    for m in RE_YEAR.finditer(text):
        dts.append((int(m.group(1)), None))
    for m in RE_DATE_RU.finditer(text):
        dts.append((int(m.group(3)), int(m.group(2))))
    for m in re.finditer(r"\b(19\d{2}|20\d{2})\b", text):  # голый год («к 2026 году»)
        dts.append((int(m.group(1)), None))
    for m in RE_DATE_MONTH.finditer(text):
        stem = m.group(0).strip().lower()
        month = None
        for key, mm in MESES.items():
            if key in stem:
                month = mm
                break
        year = int(m.group(1)) if m.group(1) and len(m.group(1)) == 4 else (
            NOW.year if month else int(m.group(1) or NOW.year)
        )
        dts.append((year, month))
    # уникальные, без дублей («2026 г.» и голый «2026»); None-месяц в конец
    return sorted(set(dts), key=lambda d: (d[0], d[1] if d[1] is not None else 0))


def score_dokazatelnost(text: str, words_n: int):
    """Критерий 1. Доказательность: числа/даты/имёна фактов, источники, ссылки."""
    score = 0
    n_pct = len(RE_NUM_PROC.findall(text))
    n_money = len(RE_NUM_MONEY.findall(text))
    n_urls = len(RE_URL.findall(text))
    n_md_links = len(RE_MD_LINK.findall(text))
    n_n = len(RE_N_SAMPLE.findall(text))
    n_dates = len(_extract_dates(text))
    n_slova = len(re.findall(r"\b(?:п|г)\.\s+[А-ЯЁA-Z]|им\.|по данным\b|со слов\b", text, re.IGNORECASE))

    # Позитив: каждый вид факта добавляет баллы (с насыщением)
    score += min(6, n_pct * 2)            # проценты — до 6
    score += min(4, n_money * 2)          # деньги — до 4
    score += min(4, (n_md_links * 3) + min(n_urls, 2))  # ссылки: markdown сильно вверх
    score += min(2, n_n)                  # «N=…»
    score += min(3, n_dates)              # даты как факты
    score += min(1, n_slova)              # «по данным …»

    # Негатив: «говорят/очевидно» без ссылки = вниз
    n_bad = _count_matches(NEDOKAZANNOST, text)
    score -= min(8, n_bad * 2)

    # Если в тексте вообще нет ссылок — лёгкий штраф (источника нигде нет)
    if n_urls == 0 and n_md_links == 0 and words_n > 150:
        score -= 2

    return max(0, min(20, score)), {
        "проценты": n_pct, "денежные_числа": n_money, "ссылки": n_urls + n_md_links,
        "N_выборки": n_n, "даты": n_dates, "обороноты_без_источника": n_bad,
    }


def score_konkretnost(text: str, words_n: int):
    """Критерий 2. Конкретность: плотность цифр на 100 слов, примеры, штраф за воду."""
    score = 0
    digits_all = len(re.findall(r"\d", text))
    num_groups = len(re.findall(r"\b\d+(?:[.,]\d+)?\b", text))
    per100 = (num_groups / words_n * 100) if words_n else 0

    # Плотность цифр на 100 слов: 0 -> 0; >=5 -> максимум 10
    score += round(min(10, per100 * 2))

    # Примеры/кейсы: слова-маркеры («например», «кейс», «на примере», «случай»)
    primery = len(re.findall(
        r"\b(?:например|кейс\b|на примере|частный случай|практический пример|"
        r"история (?:клиента|проекта)|конкретный пример)\b", text, re.IGNORECASE))
    score += min(5, primery * 3) if primery else 0

    # Вода — штраф за каждое вхождение
    voda = _count_matches(VODA_PATTERNS, text)
    score -= min(10, voda * 2)

    return max(0, min(20, score)), {
        "цифр_на_100_слов": round(per100, 1), "примеры": primery, "вода": voda,
    }


def score_svezhest(text: str):
    """Критерий 3. Свежесть: возраст самой новой найденной даты."""
    dates = _extract_dates(text)
    details = {"дата_новейшая": None, "найдено_дат": len(dates)}
    if not dates:
        return 3, details  # дат нет вовсе

    # Самая новая дата: год+месяц (без месяца считаем как июнь — середина года)
    best = None
    for year, month in dates:
        if year > 2100:
            continue
        m = month if month else 6
        dt = datetime(year, min(12, max(1, m)), 1)
        if best is None or dt > best:
            best = dt
    age_years = (NOW - best).days / 365.25
    details["дата_новейшая"] = best.strftime("%Y-%m")
    details["возраст_лет"] = round(age_years, 1)

    if age_years < 1:
        return 20, details
    if age_years < 3:
        return 12, details
    if age_years < 7:
        return 6, details
    return 3, details


def score_struktura(text: str):
    """Критерий 4. Согласованность структуры: заголовки, списки, абзацы, выводы."""
    score = 0
    lines = text.split("\n")

    headers = [l for l in lines if re.match(r"\s*#{1,6}\s+\S", l) or
               re.match(r"^\s*={2,}\s*$", l)]
    n_headers = len(headers)
    score += min(6, n_headers * 2)        # заголовки — до 6

    bullets = len([l for l in lines if re.match(r"\s*(?:[-*•]|\d+[.)])\s+\S", l)])
    score += min(5, 3 if bullets >= 3 else (1 if bullets > 0 else 0))

    # Абзацы: штраф за гигантские (>2000 символов без разрыва)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    huge = [p for p in paragraphs if len(p) > 2000]
    score -= min(4, len(huge) * 2)
    if not paragraphs:
        score -= 4  # полностью пустая структура
    else:
        # все абзацы читаемой длины — структура не «простыня», небольшой плюс
        score += 2

    # Выводы/резюме
    vyvody = _count_matches(VYVOD_PATTERNS, text)
    score += min(5, 5 if vyvody else 0)

    return max(0, min(20, score)), {
        "заголовков": n_headers, "списочных_строк": bullets,
        "гигантских_абзацев": len(huge), "выводов": vyvody,
    }


def score_ai(text: str):
    """Критерий 5. ИИ-шаблонность (инверсия): чем больше штампов, тем ниже балл."""
    matched = []
    for pat in AI_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            matched.append(m.group(0).strip().lower())
    n = len(matched)
    details = {"ии_шаблонов": n, "совпадения": sorted(set(matched))[:10]}
    if n == 0:
        return 20, details
    if n <= 2:
        return 14, details
    if n <= 5:
        return 9, details
    if n <= 10:
        return 4, details
    return 0, details


def rate(score: float) -> str:
    """Рейтинг по сумме: A ≥80, B 60–79, C 40–59, D <40."""
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    return "D"


def _empty_report() -> dict:
    """Отчёт для пустого/пробельного текста: D, 0 баллов — без падения."""
    LOG.info("пустой текст: вердикт D (0/100)")
    return {
        "рейтинг": "D",
        "сумма": 0,
        "breakdown": {name: {"балл": 0, "детали": {}}
                      for name in ("доказательность", "конкретность", "свежесть",
                                   "согласованность_структуры", "маркеры_ии_шаблонности")},
        "топ_3_проблемы": [],
        "найденные_даты": [],
        "найденные_ссылки": [],
        "статистика": {"символов": 0, "слов": 0},
        "дата_анализа": NOW.strftime("%Y-%m-%d"),
    }


def analyze(text: str) -> dict:
    """Анализ текста → отчёт dict. Не падает на пустом тексте (D, 0 баллов)."""
    text = _norm(text or "")
    words = _words(text)
    words_n = len(words)
    if words_n == 0:  # пустой или пробельный текст — ранний выход
        return _empty_report()
    LOG.info("старт анализа: длина=%d симв, %d слов, sha1=%s…",
             len(text), words_n,
             __import__("hashlib").sha1(text.encode()).hexdigest()[:8])

    s1, d1 = score_dokazatelnost(text, words_n)
    s2, d2 = score_konkretnost(text, words_n)
    s3, d3 = score_svezhest(text)
    s4, d4 = score_struktura(text)
    s5, d5 = score_ai(text)
    total = s1 + s2 + s3 + s4 + s5
    verdict = rate(total)

    breakdown = {
        "доказательность": {"балл": s1, "детали": d1},
        "конкретность": {"балл": s2, "детали": d2},
        "свежесть": {"балл": s3, "детали": d3},
        "согласованность_структуры": {"балл": s4, "детали": d4},
        "маркеры_ии_шаблонности": {"балл": s5, "детали": d5},
    }

    # Топ-3 проблемы: критерии с наименьшим баллом
    pairs = sorted(breakdown.items(), key=lambda kv: kv[1]["балл"])
    problemy = [
        {"критерий": name, "балл": data["балл"],
         "суть": _problem_hint(name, data)}
        for name, data in pairs[:3]
    ]

    urls = RE_URL.findall(text) or [m.group(2) for m in RE_MD_LINK.finditer(text)]

    LOG.info("вердикт: %s (сумма %d/100) | док=%d конкр=%d свеж=%d структура=%d ии=%d",
             verdict, total, s1, s2, s3, s4, s5)

    return {
        "рейтинг": verdict,
        "сумма": total,
        "breakdown": breakdown,
        "топ_3_проблемы": problemy,
        "найденные_даты": sorted({f"{y}" if m is None else f"{y}-{m:02d}"
                                  for y, m in _extract_dates(text)}, reverse=True)[:10],
        "найденные_ссылки": urls[:10],
        "статистика": {"символов": len(text), "слов": words_n},
        "дата_анализа": NOW.strftime("%Y-%m-%d"),
    }


def _problem_hint(name: str, data: dict) -> str:
    """Коротко по-русски, что не так с критерием (для «топ-3 проблем»)."""
    dt = data.get("детали", {})
    hints = {
        "доказательность": "мало фактов/источников: " +
            ", ".join(f"{k}={v}" for k, v in dt.items()) if dt else "",
        "конкретность": "мало цифр на 100 слов или много воды: " +
            ", ".join(f"{k}={v}" for k, v in dt.items()) if dt else "",
        "свежесть": "дат нет или они старые: " +
            ", ".join(f"{k}={v}" for k, v in dt.items()) if dt else "",
        "согласованность_структуры": "проблемы структуры: " +
            ", ".join(f"{k}={v}" for k, v in dt.items()) if dt else "",
        "маркеры_ии_шаблонности": "шаблонные ИИ-обороты (" + str(dt.get("ии_шаблонов", 0)) + "): " +
            ", ".join(dt.get("совпадения", [])) if dt.get("ии_шаблонов") else "",
    }
    return hints.get(name, "")


def _format_report(res: dict) -> str:
    """Человекочитаемый отчёт для консоли."""
    lines = ["=" * 60, f"РЕЙТИНГ КАЧЕСТВА: {res['рейтинг']}  (сумма {res['сумма']}/100)",
             "=" * 60]
    for name, data in res["breakdown"].items():
        lines.append(f"  {name:<28} {data['балл']:>3}/20")
    lines.append("-" * 60)
    lines.append("Топ-3 проблемы:")
    for p in res["топ_3_проблемы"]:
        lines.append(f"  · {p['критерий']} ({p['балл']}/20): {p['суть']}")
    if res["найденные_даты"]:
        lines.append(f"Даты: {', '.join(res['найденные_даты'][:5])}")
    if res["найденные_ссылки"]:
        lines.append(f"Ссылки: {len(res['найденные_ссылки'])} шт.")
    return "\n".join(lines)


# ── Демо-тексты ────────────────────────────────────────────────────────────

DEMO_A = """# Отчёт по рынку ИИ: итоги 2026 года
По данным аналитики Cloud.ru, российский AI-рынок вырос до 58 млрд руб в 2026,
что на 450% больше показателя 2025 года ([источник](https://example.com/report)).
N = 1200 компаний участвовало в опросе; 72% внедрили хотя бы одного агента.
Например, ВТБ снизил стоимость обработки заявок на 34% (12.05.2026).
Выводы: рынок продолжает расти, консервативная оценка на 2027 год — 90 млрд руб.
"""

DEMO_C = """В современном мире, особенно к 2026 году, технологии играют ключевую роль. Многие говорят,
что наступила уникальная эпоха. Как известно, синергия процессов неизбежно
приведёт к революционным изменениям. Если говорить о будущем, то очевидно, важно
быть готовым к переменам и развитию.
"""

DEMO_D = """Важно отметить, что данный вопрос требует комплексного подхода.
Стоит подчеркнуть, что давайте рассмотрим основные аспекты подробнее.
Подводя итог, можно сказать, что в заключение важно понимать контекст.
Однако стоит отметить, что при этом важно соблюдать баланс. Итак, важным
моментом является системный взгляд. Резюмируя вышесказанное, нельзя не
отметить стратегическую ценность данного направления. Важно понимать,
что стоит отметить также необходимость синергии. Подытоживая, ключевым
моментом является гибкость."""

DEMO = {"A": DEMO_A, "C": DEMO_C, "D": DEMO_D}


def run_demo():
    """--demo: прогон на трёх встроенных текстах + JSON в reports/."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    results = {}
    for tag, text in DEMO.items():
        LOG.info("демо-прогон: текст %s (длина=%d)", tag, len(text))
        res = analyze(text)
        results[tag] = res
        path = os.path.join(REPORTS_DIR, f"demo_{tag}_анализ.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print(f"\n--- Демо-{tag} ---")
        print(_format_report(res))
        print(f"JSON: {path}")
    ok = results["A"]["сумма"] >= 80 and results["D"]["сумма"] < 40
    LOG.info("демо завершено: A=%d D=%d, ожидание А>=80/D<40: %s",
             results["A"]["сумма"], results["D"]["сумма"], "выполнено" if ok else "НЕ выполнено")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Анализатор качества информации с рейтингом A/B/C/D")
    ap.add_argument("path", nargs="?", help="путь к файлу .txt/.md (или stdin)")
    ap.add_argument("--demo", action="store_true", help="прогон на демо-текстах")
    args = ap.parse_args(argv)

    if args.demo:
        return run_demo()

    if args.path:
        if not os.path.isfile(args.path):
            print(f"Файл не найден: {args.path}", file=sys.stderr)
            return 2
        with open(args.path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        name = os.path.splitext(os.path.basename(args.path))[0]
        LOG.info("файл принят: %s (длина=%d)", os.path.basename(args.path), len(text))
    else:
        text = sys.stdin.read()
        name = "stdin"
        LOG.info("текст из stdin (длина=%d)", len(text))

    res = analyze(text)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_json = os.path.join(REPORTS_DIR, f"{name}_анализ.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    print(_format_report(res))
    print(f"JSON сохранён: {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())