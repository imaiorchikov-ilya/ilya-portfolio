# -*- coding: utf-8 -*-
"""
bot.py — каркас Telegram-бота модератора (python-telegram-bot v21+, async).

Токен: только через переменную окружения TG_MODERATOR_TOKEN (файл .env).
Без токена бот не стартует, но `python bot.py --check` проверяет схему БД
и логирование без подключения к Telegram.

Логи: D:\\Логи\\tg_moderator\\bot\\<дата>.log — БЕЗ текстов сообщений и имён
(только user_id и действие, ПДн не логируем).
"""
import argparse
import hashlib
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, r"D:\Логи")

from logger import get_logger  # noqa: E402

# .env ищем в папке проекта
load_dotenv(BASE_DIR / ".env")

import os  # noqa: E402

import db  # noqa: E402
import rules_engine  # noqa: E402

log = get_logger("tg_moderator", "bot")

TOKEN = os.getenv("TG_MODERATOR_TOKEN")

# Последнее сообщение каждого пользователя — для правила «повтор»
_last_user_text: dict[int, str] = {}

# Права админа (для /warn) — TODO: заполнять из конфига
ADMIN_IDS: set[int] = set()


def _token_ok(token):
    """Токен присутствует и похоже на Telegram-токен."""
    if not token:
        return False
    parts = token.split(":")
    return len(parts) == 2 and parts[0].isdigit() and len(parts[1]) >= 30


def run_check() -> int:
    """--check: проверка схемы БД и логирования без Telegram."""
    print("[1/2] Схема БД...")
    db.init_db()
    print(f"      OK: {db.DB_PATH}")
    print("[2/2] Логгер...")
    log.info("--check пройден: БД и логгер работают")
    print(f"      OK: D:\\Логи\\tg_moderator\\bot\\")
    print("CHECK PASSED")
    return 0


async def cmd_start(update, context) -> None:
    """/start — приветствие + регистрация."""
    user = update.effective_user
    if not user:
        return
    db.register_user(user.id, user.username)
    log.info("/start user_id=%s", user.id)
    await update.message.reply_text(
        "Привет! Я бот-модератор этой группы.\n"
        "Я слежу за правилами: за спам, капс и ссылки — предупреждения.\n"
        "3 предупреждения — мьют на час.\n"
        "Команды: /rules — правила, /list — последние нарушения."
    )


async def cmd_rules(update, context) -> None:
    """/rules — правила из rules.md."""
    rules_path = BASE_DIR / "rules.md"
    text = rules_path.read_text(encoding="utf-8") if rules_path.exists() else \
        "Правила пока не заполнены (файл rules.md отсутствует)."
    log.info("/rules user_id=%s", update.effective_user.id if update.effective_user else "?")
    await update.message.reply_text(text)


async def cmd_warn(update, context) -> None:
    """/warn @user причина — вручную повысить счётчик (только админы, TODO)."""
    caller = update.effective_user
    if not caller or not context.args:
        return
    # TODO: проверка прав админа через context.bot.get_chat_member + ADMIN_IDS
    target = context.args[0].lstrip("@")
    reason = " ".join(context.args[1:]) or "без причины"
    log.info("/warn инициатор=%s цель=@%s причина-длина=%s",
             caller.id, target, len(reason))
    # TODO: разрешение @username в user_id требует кэша участников чата —
    #       сейчас каркасная заготовка: ищем пользователя по username в БД
    conn = __import__("sqlite3").connect(db.DB_PATH)
    try:
        row = conn.execute(
            "SELECT user_id FROM users WHERE username = ?", (target,)
        ).fetchone()
    finally:
        conn.close()
    if not row:
        await update.message.reply_text(
            f"Пользователь @{target} не найден в базе (он должен написать в чат хотя бы раз)."
        )
        return
    user_id = row[0]
    warnings = db.increment_warnings(user_id, target)
    db.add_violation(user_id, update.effective_chat.id, f"ручной warn: {reason}", 1,
                     rules_engine.warnings_to_action(warnings) or "warn", msg_id=0)
    await update.message.reply_text(
        f"@{target}: предупреждение #{warnings}. {reason}"
    )


async def cmd_list(update, context) -> None:
    """/list — последние нарушения."""
    rows = db.last_violations()
    log.info("/list user_id=%s", update.effective_user.id if update.effective_user else "?")
    if not rows:
        await update.message.reply_text("Нарушений пока нет. Тишина и порядок.")
        return
    lines = [
        f"{d} | user {u} | {r} | score {s} | {a}"
        for (d, u, c, r, s, a) in rows
    ]
    await update.message.reply_text("Последние нарушения:\n" + "\n".join(lines))


async def on_message(update, context) -> None:
    """Автопроверка КАЖДОГО сообщения по простым правилам."""
    msg = update.effective_message
    user = update.effective_user
    if not msg or not user or not msg.text:
        return

    text = msg.text
    prev = _last_user_text.get(user.id, "")
    verdict, score, rule = rules_engine.check_text(text, prev)
    _last_user_text[user.id] = text

    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    db.register_user(user.id, user.username)
    db.log_message(msg.message_id, user.id, msg.chat_id, text_hash, verdict)

    if verdict == "ok":
        log.info("Сообщение чистое user_id=%s chat_id=%s", user.id, msg.chat_id)
        return

    action = rules_engine.warnings_to_action(db.get_warnings(user.id) + 1)
    db.add_violation(user.id, msg.chat_id, rule, score, action or "warn", msg.message_id)
    warnings = db.get_warnings(user.id)
    log.info("Нарушение user_id=%s chat_id=%s правило=%s действие=%s",
             user.id, msg.chat_id, rule, action or "warn")

    await msg.reply_text(
        f"Предупреждение #{warnings} (правило: {rule}). "
        f"3 предупреждения — мьют на час."
    )

    if action == "mute_1h":
        # TODO: реализация mute — требует прав админа бота в чате:
        #   until_date = msg.date + timedelta(hours=1)
        #   await context.bot.restrict_chat_member(msg.chat_id, user.id, permissions=..., until_date=...)
        log.info("MUTE-заготовка user_id=%s — реальный mute требует прав админа (TODO)", user.id)
        await msg.reply_text("Порог 3 предупреждений достигнут. Мьют на час (реализация — TODO).")


def main() -> int:
    parser = argparse.ArgumentParser(description="Telegram-бот модератор")
    parser.add_argument("--check", action="store_true",
                        help="проверить схему БД и логирование без Telegram")
    args = parser.parse_args()

    log.info("Старт бота-модератора (режим: %s)",
             "check" if args.check else "telegram")

    if args.check:
        return run_check()

    if not _token_ok(TOKEN):
        log.error("Токен TG_MODERATOR_TOKEN отсутствует или невалиден — старт невозможен")
        print("Ошибка: нет токена. Заполни .env (см. .env.example) или запусти "
              "python bot.py --check для проверки без Telegram.")
        return 1

    # Насквозь async-фреймворк — импорт здесь, чтобы --check работал без библиотеки
    from telegram.ext import Application, CommandHandler, MessageHandler, filters

    db.init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("rules", cmd_rules))
    app.add_handler(CommandHandler("warn", cmd_warn))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    log.info("Бот запускается (polling)")
    app.run_polling()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())