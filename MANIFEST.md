# MANIFEST — деплой-пакет портфолио Ильи AI

**Дата сборки:** 2026-08-17

## Содержимое

| Папка/файл | Назначение | Размер |
|---|---|---|
| `index.html` | Корневая навигация — ссылки на ilya-vizitka и nova | 0.4 КБ |
| `ilya-vizitka/` | Сайт-визитка (главная + 4 проекта) — готов к деплою | 142 КБ |
| `ilya-vizitka.zip` | То же, в одном архиве для деплоя | 40 КБ |
| `nova/` | Сайт салона красоты NOVA — демо с реальными фото | 45 КБ |
| `nova.zip` | NOVA-салон, в архиве | 13 КБ |
| `pdf/` | PDF-превью всех 6 страниц для офлайн-показа | 38 МБ |

## Запуск

### Локально
```bash
cd portfolio/deploy
python -m http.server 8080
# http://localhost:8080 — навигация
# http://localhost:8080/ilya-vizitka/ — сайт-визитка
# http://localhost:8080/nova/ — NOVA
```

### Деплой ilya-vizitka.zip

**Cloudflare Pages:**
1. Cloudflare Dashboard → Pages → Upload → zip → загрузить `ilya-vizitka.zip`
2. Получить URL вида `ilya-vizitka.pages.dev`
3. Custom domain → прописать

**Netlify (drag-and-drop):**
1. Открыть [app.netlify.com/drop](https://app.netlify.com/drop)
2. Перетащить всю папку `ilya-vizitka/`
3. Получить URL вида `ilya-vizitka.netlify.app`

**Vercel:**
```bash
cd ilya-vizitka
vercel --prod
```

### Деплой nova.zip — аналогично

## PDF-превью (`pdf/`)

- `ilya-vizitka.pdf` — сайт-визитка, ~35 МБ (полный)
- `nova.pdf` — NOVA, ~650 КБ
- `project-website.pdf` — проект «Сайт», ~390 КБ
- `project-chatbot.pdf` — проект «Чат-бот», ~230 КБ
- `project-content.pdf` — проект «Контент», ~2 МБ
- `project-automation.pdf` — проект «Автоматизация», ~290 КБ
- `project-vpn.pdf` — проект «VPN через Telegram», ~110 КБ (B2C SaaS-концепция)
- `project-elevenmusic.pdf` — проект «AI-музыка ElevenMusic», ~105 КБ (3 гипотезы монетизации, юнит-экономика, риски)

PDF — векторный (для печати) + растровый (для экрана), A4, фон сохранён. Открыть в Adobe Reader / Preview / любом современном браузере.

## Структура ilya-vizitka

```
ilya-vizitka/
├── index.html              # главная
├── assets/                 # (резерв)
├── projects/
│   ├── website/index.html  # премиум-лендинг кофейни
│   ├── chatbot/index.html  # живой AI-агент
│   ├── content/index.html  # галерея AI-контента
│   ├── automation/index.html # flow-редактор
│   ├── vpn/index.html      # B2C SaaS VPN через Telegram
│   └── elevenmusic/index.html # AI-музыка ElevenMusic — 3 гипотезы
└── README.md
```

## Что нужно сделать перед прод-запуском

- Заменить плейсхолдеры (контакты, цены, имена) на реальные
- Добавить Schema.org JSON-LD на все страницы
- Подключить Яндекс.Метрику + GA4
- Добавить Open Graph image (`assets/og.png` 1200×630)
- Настроить YCLIENTS/Dikidi для формы записи в NOVA

## Что НЕ сделано

- Реальные интеграции (формы сабмитят в alert)
- Деплой (только локально + zip)
- Отправка ссылок клиентам
- Публикация в каталогах / индексация в поиске

Всё перечисленное — **красная зона**, только по явному «делаем».
