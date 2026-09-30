# -*- coding: utf-8 -*-
"""
db.py — работа с SQLite-БД модератора.

БД: data/moderator.db (создаётся автоматически при старте).
Логируем только user_id и действие — без текстов сообщений и имён (ПДн).
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, r"D:\Логи")
from logger import get_logger  # noqa: E402

log = get_logger("tg_moderator", "db")

DB_PATH = BASE_DIR / "data" / "moderator.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY,
    username       TEXT,
    first_seen     TEXT NOT NULL,
    warnings_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS messages (
    msg_id    INTEGER PRIMARY KEY,
    user_id   INTEGER NOT NULL,
    chat_id   INTEGER NOT NULL,
    date      TEXT NOT NULL,
    text_hash TEXT,
    verdict   TEXT
);
CREATE TABLE IF NOT EXISTS violations (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    date    TEXT NOT NULL,
    rule    TEXT,
    score   INTEGER NOT NULL,
    action  TEXT,
    msg_id  INTEGER
);
"""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def init_db(db_path=DB_PATH) -> None:
    """Создать таблицы, если их ещё нет."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()
    log.info("Схема БД готова: %s", db_path)


def register_user(user_id: int, username: str | None, db_path=DB_PATH) -> None:
    """Регистрация пользователя (или обновление username)."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO users (user_id, username, first_seen) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username",
            (user_id, username, _now()),
        )
        conn.commit()
    finally:
        conn.close()
    log.info("Регистрация пользователя user_id=%s", user_id)


def log_message(msg_id: int, user_id: int, chat_id: int,
                text_hash: str, verdict: str, db_path=DB_PATH) -> None:
    """Запись факта сообщения (текст НЕ пишем — только хеш и вердикт)."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO messages (msg_id, user_id, chat_id, date, text_hash, verdict) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, user_id, chat_id, _now(), text_hash, verdict),
        )
        conn.commit()
    finally:
        conn.close()
    log.info("Сообщение зафиксировано user_id=%s chat_id=%s вердикт=%s",
             user_id, chat_id, verdict)


def add_violation(user_id: int, chat_id: int, rule: str, score: int,
                  action: str, msg_id: int, db_path=DB_PATH) -> None:
    """Записать нарушение и повысить warnings_count пользователя."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO violations (user_id, chat_id, date, rule, score, action, msg_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, chat_id, _now(), rule, score, action, msg_id),
        )
        conn.execute(
            "UPDATE users SET warnings_count = warnings_count + 1 WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
        warnings = get_warnings(user_id, conn=conn)
    finally:
        conn.close()
    log.info("Нарушение user_id=%s chat_id=%s правило=%s score=%s действие=%s",
             user_id, chat_id, rule, score, action)


def get_warnings(user_id: int, db_path=DB_PATH, conn: sqlite3.Connection | None = None) -> int:
    """Текущий счётчик предупреждений пользователя."""
    own = False
    if conn is None:
        conn = sqlite3.connect(db_path)
        own = True
    try:
        row = conn.execute(
            "SELECT warnings_count FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row[0] if row else 0
    finally:
        if own:
            conn.close()


def increment_warnings(user_id: int, username: str | None, db_path=DB_PATH) -> int:
    """Ручной /warn: +1 к предупреждениям (пользователь регистрируется при необходимости)."""
    register_user(user_id, username, db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE users SET warnings_count = warnings_count + 1 WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
        warnings = conn.execute(
            "SELECT warnings_count FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
    finally:
        conn.close()
    log.info("Ручной warn user_id=%s → счётчик=%s", user_id, warnings)
    return warnings


def last_violations(limit: int = 10, db_path=DB_PATH) -> list:
    """Последние нарушения: [(date, user_id, chat_id, rule, score, action), ...]"""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT date, user_id, chat_id, rule, score, action FROM violations "
            "ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return rows
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("OK: БД инициализирована:", DB_PATH)