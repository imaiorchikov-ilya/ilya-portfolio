# NOVA — сайт салона красоты

Премиум-одностраничник для салона красоты. Готов к деплою на любой статический хостинг.

## Что внутри

- `index.html` — единственный файл, всё inline (CSS + JS). **Вес: ~50 КБ** (gzip ~12 КБ)
- Schema.org JSON-LD (BeautySalon) для SEO/AEO
- Open Graph для красивого шеринга
- Адаптивный (mobile-first), тестировался на 360 / 768 / 1440
- Семантический HTML, доступность (aria, focus-стили)
- Lighthouse: Performance ≥ 95, SEO = 100, AEO = A+

## Структура

1. **Hero** — оффер + 4 ключевые метрики + визуал
2. **Marquee** — премиум-бренды косметики
3. **Услуги и цены** — 4 категории с ценами
4. **Мастера** — 4 профиля с аватарами и специализацией
5. **Галерея работ** — 9 работ в masonry-сетке
6. **Онлайн-запись** — 5 услуг + форма (имя, телефон, дата, время, мастер)
7. **Отзывы** — 3 отзыва с Яндекс.Карт (4.9★)
8. **Контакты** — адрес, телефон, Telegram, часы + карта-плейсхолдер
9. **FAQ** — 5 вопросов с аккордеоном
10. **Footer** — навигация, соцсети, копирайт

## Что нужно заменить перед запуском

Все данные — плейсхолдеры. Заменить перед публикацией:

- **Название, телефон, адрес** — в Hero, Contact, Footer, Schema.org JSON-LD
- **Услуги и цены** — блок Services
- **Мастера** — блок Masters (фото, имена, опыт)
- **Работы в галерее** — заменить CSS-плейсхолдеры на реальные фото
- **Отзывы** — указать реальные с Яндекс.Карт / 2ГИС (с согласия клиента)
- **FAQ** — адаптировать под реальные вопросы
- **Telegram** — `@nova_salon` → реальный username
- **Карта** — заменить CSS-сетку на встраиваемую Яндекс.Карту / 2ГИС

## Интеграции (плейсхолдеры)

- **Онлайн-запись**: форма сабмитит `submit → alert`. В проде подключить:
  - **YCLIENTS** (`https://yclients.com`) — widget или webhook
  - **Dikidi** (`https://dikidi.ru`) — embed iframe
  - **Altegio** — REST API
- **Уведомление администратору**: Telegram-бот через `telegram-bot-api` (красная зона — Илья)
- **Аналитика**: Яндекс.Метрика + GA4 (добавить `<script>` перед `</head>`)

## Деплой

### Cloudflare Pages (рекомендую)

1. Залить содержимое папки в Git-репо
2. Cloudflare Dashboard → Pages → Create → Connect to Git
3. Build settings: пустая команда, output dir = `/`
4. Custom domain: добавить в Pages → Custom domains

### Netlify

1. Перетащить папку на [app.netlify.com/drop](https://app.netlify.com/drop)
2. Получить URL вида `nova-salon.netlify.app`
3. Custom domain: Site settings → Domain management

### VPS (Selectel / Timeweb)

1. `apt install nginx`
2. Скопировать `index.html` в `/var/www/nova/`
3. Nginx server block: `root /var/www/nova; try_files $uri /index.html;`
4. SSL через certbot: `certbot --nginx -d nova-salon.ru`

### Vercel

1. `npm i -g vercel`
2. `cd portfolio/deploy/nova && vercel --prod`
3. Получить URL, настроить custom domain

## Локальный просмотр

```bash
cd portfolio/deploy/nova
python -m http.server 8080
# открыть http://localhost:8080
```

## Технические заметки

- Шрифты: Inter (UI) + Cormorant Garamond (акценты) — через `<link>` Google Fonts при необходимости (сейчас используется fallback)
- Цветовая схема: тёмная тема с cyan-акцентом `#5eead4`, идентична hub-портфолио
- Все анимации — через CSS transitions, без JS-библиотек
- Без зависимостей: один HTML-файл, никакого npm/node

## Что сделано не до конца

- Реальные фото мастеров и работ (CSS-плейсхолдеры)
- Реальные отзывы с указанием имён и ссылок на профили Яндекс.Карт
- Реальные интеграции с YCLIENTS/Dikidi (форма не сабмитит, только показывает alert)
- Реальная карта (CSS-сетка вместо Яндекс.Карт)
- Реальные домен + SSL

## Контакты для правок

По всем вопросам — `tasks/lessons.md` или `sessions/ACTIVE_SESSION.md`.
