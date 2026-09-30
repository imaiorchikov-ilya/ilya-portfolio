# -*- coding: utf-8 -*-
"""
rules_engine.py — чистый движок проверки сообщений модератором.

Без LLM на этом этапе: детерминированные локальные правила.
Функция check_text возвращает (verdict, score, rule):
    verdict — 'ok' | 'spam' | 'links' | 'repeat'
    score   — насколько плохо (0 = чисто, выше = хуже)
    rule    — человекочитаемое название сработавшего правила или None

Функция чистая: никакого ввода-вывода, легко покрывается тестами.
"""

# Стоп-список доменов/паттернов ссылок (расширяемый)
STOP_LINKS = (
    "bit.ly", "tinyurl.com", "t.me/+",
    "cutt.ly", "shorturl.at", "is.gd",
    "casino", "1xbet", "mostbet", "pin-up",
)

# Пороги
CAPS_MIN_LEN = 30          # длина, с которой капс считается спамом
CAPS_RATIO = 0.70          # доля заглавных букв в буквах
REPEAT_MIN_LEN = 20        # минимальная длина сообщения, чтобы учитывать повторы


def _caps_ratio(text: str) -> float:
    """Доля заглавных букв среди букв текста (0..1)."""
    letters = [c for c in text if c.isalpha() and c.isascii() or c.isalpha()]
    if not letters:
        return 0.0
    upper = sum(1 for c in letters if c.isupper())
    return upper / len(letters)


def check_text(text: str, prev_text: str = "") -> tuple:
    """Проверка текста сообщения.

    :param text: текст текущего сообщения
    :param prev_text: предыдущее сообщение того же пользователя (для повтора)
    :return: (verdict: str, score: int, rule: str | None)
    """
    if not text or not text.strip():
        return ("ok", 0, None)

    stripped = text.strip()

    # 1. Стоп-ссылки
    low = stripped.lower()
    for pattern in STOP_LINKS:
        if pattern in low:
            return ("spam", 3, f"стоп-ссылка: {pattern}")

    # 2. Капс
    if len(stripped) > CAPS_MIN_LEN and _caps_ratio(stripped) > CAPS_RATIO:
        return ("spam", 2, "капс/крик")

    # 3. Повтор предыдущего сообщения
    if (
        prev_text
        and stripped.lower() == prev_text.strip().lower()
        and len(stripped) >= REPEAT_MIN_LEN
    ):
        return ("repeat", 2, "повтор сообщения")

    return ("ok", 0, None)


def warnings_to_action(warnings: int) -> str | None:
    """Что делать при данном числе предупреждений.

    3 предупреждения → mute_1h (сам mute требует прав админа — TODO).
    """
    if warnings >= 3:
        return "mute_1h"
    return None