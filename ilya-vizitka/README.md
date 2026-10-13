# ilya-vizitka — сайт-визитка Ильи (AI-консультант)

Премиум-одностраничник + 4 проекта-образца (website/chatbot/content/automation). Полностью статический — открывается в браузере без сборки.

## Что внутри

```
ilya-vizitka/
├── index.html              # главная — 44 КБ
├── assets/                 # (резерв для будущих svg/png)
└── projects/
    ├── website/index.html  # премиум-лендинг кофейни — 16 КБ
    ├── chatbot/index.html  # живое демо AI-агента — 22 КБ
    ├── content/index.html  # галерея AI-контента — 31 КБ
    ├── automation/index.html # flow-редактор n8n — 27 КБ
    ├── vpn/index.html      # B2C SaaS: VPN через Telegram — 33 КБ
    └── elevenmusic/index.html # AI-музыка ElevenMusic — 8 КБ
```

**Суммарно ~140 КБ HTML, gzip ~35 КБ. Без npm/node, без зависимостей.**

## Стиль

Vercel/Linear family 2026, dark mode, cyan-акцент `#5eead4`. Кастомный курсор-glow, анимированная сетка, marquee, bento-сетка, серифные курсивные акценты.

## Деплой

### Cloudflare Pages (рекомендую)

1. Залить в Git-репо
2. Cloudflare Dashboard → Pages → Create → Connect to Git
3. Build settings: пустая команда, output dir = `/`
4. Custom domain → добавить

### Netlify (drag-and-drop, самый быстрый)

1. Перетащить всю папку `ilya-vizitka` на [app.netlify.com/drop](https://app.netlify.com/drop)
2. Получить URL вида `ilya-vizitka.netlify.app`

### Vercel

```bash
cd ilya-vizitka
npm i -g vercel
vercel --prod
```

### VPS (Selectel/Timeweb)

```bash
apt install nginx
cp -r ilya-vizitka/* /var/www/ilya-vizitka/
# nginx server block: root /var/www/ilya-vizitka;
certbot --nginx -d ilya-vizitka.ru
```

## Что нужно обновить перед прод-запуском

- **Контакты** в index.html (телефон, Telegram, email) — сейчас плейсхолдеры
- **Цены** в pricing-секции — три плана
- **Кейсы** в `cases` — ссылки на реальные проекты клиентов
- **Отзывы** — реальные имена и компании (с согласия)
- **Schema.org JSON-LD** в `index.html` — добавить Organization + Person + Service для AEO
- **Яндекс.Метрика + GA4** — добавить `<script>` перед `</head>` на всех страницах
- **Open Graph image** — `assets/og.png` 1200×630 (сейчас отсутствует)

## Локальный просмотр

```bash
cd ilya-vizitka
python -m http.server 8080
# http://localhost:8080 — главная
# http://localhost:8080/projects/website/ — проект 1
# http://localhost:8080/projects/chatbot/ — проект 2
# http://localhost:8080/projects/content/ — проект 3
# http://localhost:8080/projects/automation/ — проект 4
```

## Технические заметки

- `.reveal` класс использует IntersectionObserver для scroll-анимации — на скриншотах через Playwright нужно `document.querySelectorAll('.reveal').forEach(el => el.classList.add('in'))` (или просто скроллить)
- Все анимации через CSS transitions, без JS-библиотек
- Никаких внешних шрифтов (используется fallback на системные Inter/Cormorant Garamond)
- Каждая страница самодостаточна — можно деплоить только одну, без остальных
