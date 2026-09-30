# Telegram-бот модератор (каркас)

Каркас бота-модератора для Telegram-группы: локальные правила без LLM, учёт предупреждений в SQLite.

## Установка

```
pip install "python-telegram-bot>=21.0" python-dotenv
```

## Как получить токен

1. В Telegram найди @BotFather → команда `/newbot`.
2. Дай боту имя и username (должно заканчиваться на `bot`).
3. BotFather выдаст токен вида `123456789:AAH...` — он секрет, никому не показывай.
4. Скопируй `.env.example` → `.env`, впиши токен в `TG_MODERATOR_TOKEN`.

## Запуск

```
python bot.py            # обычный запуск (нужен токен в .env)
python bot.py --check    # проверка схемы БД и логгера БЕЗ подключения к Telegram
python tests/test_rules_engine.py   # тесты движка правил
```

## Что внутри

- `bot.py` — async-бот (python-telegram-bot v21): /start, /rules, /warn, /list, автопроверка каждого сообщения.
- `rules_engine.py` — чистый движок правил: капс (>70% заглавных при длине >30), стоп-ссылки, повторы.
- `db.py` — SQLite `data/moderator.db`: таблицы users / messages / violations, создаётся автоматически.
- `rules.md` — текст правил для команды /rules.
- Логи: `D:\Логи\tg_moderator\bot\<дата>.log` — только user_id и действие, БЕЗ текстов и имён (ПДн).

## Команды

| Команда | Что делает |
|---|---|
| /start | приветствие + регистрация в БД |
| /rules | правила группы (из rules.md) |
| /warn @user причина | вручную +1 предупреждение (TODO: только админы) |
| /list | последние 10 нарушений |

## Логика модерации

Каждое сообщение проверяется `check_text()` → (verdict, score, rule). Нарушение = запись в violations + warnings_count++. При 3 предупреждениях — action `mute_1h`.

## TODO

- **Mute/бан** — `mute_1h` сейчас только записывается; реальный мьют требует прав админа у бота в чате ( restrict_chat_member, см. TODO в bot.py).
- **/warn по username** — разрешение @username в user_id требует кэша участников чата (get_chat_administrators / кэш при сообщениях).
- **Проверка прав админа** для /warn (сейчас команду может вызвать любой).
- **Интеграция анализатора качества** — отдельный проект `projects/analiz_kachestva` (пишется субагентом отдельно), свяжем позже.