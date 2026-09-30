# -*- coding: utf-8 -*-
r"""ДОСЬЕ ПО URL — автомат по памятке Манье (раздел 4).

    python dosye_url.py <URL> [--llm ollama] [--pdf]

Делает: читает сайт (главная + до 8 внутренних страниц) → извлекает факты
(юрлицо, телефоны, email, ИНН/ОГРН, цены, услуги) → сверяет сайт с реквизитами
→ генерирует черновик досье на 1 страницу по шаблону Манье.
LLM (ollama) дорабатывает гипотезы/цифру; без ключа работает детерминированная
часть — все факты с сайта достоверны, гипотезы помечаются как «проверить».
Результат: md рядом с проектом в out\ + опция PDF на стол.
Логи: D:\Логи\dosye\dosye_url\
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
from datetime import date

sys.path.insert(0, r"D:\Логи")
from logger import get_logger

log = get_logger("dosye", "dosye_url")
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "1"

ROOT = pathlib = None
import pathlib
ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
MAX_TEXT = 3000


def fetch(url):
    import requests
    log.info("GET %s", url[:100])
    r = requests.get(url, timeout=25, headers=H)
    r.raise_for_status()
    return r.text


def strip_html(html_text):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_text, "html.parser")
    return soup


def собрать_тексты(url):
    """Главная + внутренние ссылки того же домена (не файлы). Возвращает [(url, title, text)]."""
    from bs4 import BeautifulSoup
    base = urllib.parse.urlparse(url)
    домен = base.netloc
    html_main = fetch(url)
    soup = strip_html(html_main)
    title_main = (soup.title.string or "").strip() if soup.title else ""
    страница = [(url, title_main, soup.get_text(" ", strip=True))]

    ссылки = []
    for a in soup.find_all("a"):
        href = a.get("href") or ""
        full = urllib.parse.urljoin(url, href)
        p = urllib.parse.urlparse(full)
        if p.netloc == домен and p.path not in ("", "/") and not p.path.startswith("#"):
            if not re.search(r"\.(pdf|docx?|xlsx?|zip|jpg|png|mp4)$", p.path.lower()):
                if full not in ссылки:
                    ссылки.append(full)
    log.info("найдено %d внутренних ссылок, беру первые 15", len(ссылки))
    for u in ссылки[:15]:
        try:
            t = strip_html(fetch(u))
            ttl = (t.title.string or "").strip() if t.title else ""
            страница.append((u, ttl, t.get_text(" ", strip=True)))
        except Exception as e:
            log.error("страница упала %s: %s", u, e)
    return страница


def факты(страницы):
    """Детерминированное извлечение фактов из текста страниц."""
    text_all = " \n".join(f"{ttl} {txt}" for _, ttl, txt in страницы)
    ф = {"юрлица": [], "title_юрлица": None, "телефоны": [], "emails": [],
         "инн": [], "огрн": [], "цены": [], "фрагменты": {}}

    for m in re.finditer(r"(?:ООО|АО|ЗАО|ОП|ИП)\s*[«\"]?([А-ЯЁA-Z][А-ЯЁа-яёA-Za-z\- ]{2,40})[»\"]?",
                         text_all):
        if m.group(0) not in ф["юрлица"]:
            ф["юрлица"].append(m.group(0).strip()[:60])

    titles = {ttl for _, ttl, _ in страницы if ttl}
    for ttl in titles:
        m = re.search(r"(ООО|ИП|АО)\s*[«\"]?([А-ЯЁ][А-ЯЁа-яё\- ]{1,30})", ttl)
        if m:
            ф["title_юрлица"] = f"{m.group(1)} «{m.group(2).strip()}»"

    for m in re.finditer(r"(\+7|8)\s?[\(\-]?\s?(\d{3,4})\)?[\s\-]?(\d{3})[\s\-]?(?:(\d{2})[\s\-]?(\d{2})|(\d{3}))",
                         text_all):
        код, n1 = m.group(2), m.group(3)
        if m.group(4):
            т = f"+7 ({код}) {n1}-{m.group(4)}-{m.group(5)}"
        else:
            т = f"+7 ({код}) {n1}-{m.group(6)}"
        if т not in ф["телефоны"]:
            ф["телефоны"].append(т)

    for m in re.finditer(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text_all):
        if m.group(0) not in ф["emails"]:
            ф["emails"].append(m.group(0).lower())
    ф["emails"] = [e for e in ф["emails"] if not e.endswith((".png", ".jpg"))][:4]

    for m in re.finditer(r"ИНН/КПП\s*[:\s]*((\d{10,12})(?:/\d{9})?)", text_all, re.I):
        ф["инн"].append(m.group(1))
    for m in re.finditer(r"ИНН\s*[:\s]?(\d{10,12})", text_all, re.I):
        ф["инн"].append(m.group(1))
    ф["инн"] = list(dict.fromkeys(ф["инн"]))[:3]
    for m in re.finditer(r"ОГРН\s*[:\s]?(\d{13})", text_all, re.I):
        ф["огрн"].append(m.group(1))

    for m in re.finditer(r"(\d[\d\s ]{2,})\s?(?:₽|руб)", text_all):
        n = m.group(1).replace(" ", "").replace(" ", "")
        if len(n) >= 4:
            ф["цены"].append(n)
    # цены прайсов: «7 800,00» (тысячи через пробел, копейки через запятую/точку)
    for m in re.finditer(r"\b(\d{1,3})\s(\d{3})[.,](\d{2})\b", text_all):
        v = f"{m.group(1)}{m.group(2)}.{m.group(3)}"
        if v not in ф["цены"]:
            ф["цены"].append(v)

    for _, u, txt in страницы:
        ф["фрагменты"][u] = txt[:MAX_TEXT]
    тл = [t for _, _, t in страницы[1:]]
    ф["страниц_всего"] = len(тл)
    ф["мёртвых_страниц"] = sum(1 for t in тл if re.search(r"(Страница 404|Ошибка 404)", t))
    return ф


def сверка(ф):
    """Что сайт говорит сам про себя: юрлицо в title vs в футере, ИНН на сайте."""
    строки = []
    v = ф["title_юрлица"]
    others = [у for у in ф["юрлица"] if v and у.replace("«", "\"").replace("«", "") != v.replace("«", "\"").replace("«", "")]
    if v and others:
        строки.append(f"❌ Расхождение: title страниц = {v}, в тексте встречаются: {', '.join(others[:3])}")
    elif v:
        строки.append(f"✅ Юрлицо постоянно: {v}")
    else:
        строки.append("⚠ Юрлицо в title не найдено — проверить вручную")
    if ф["инн"]:
        строки.append(f"✅ ИНН на сайте: {', '.join(ф['инн'])} (сверить с egrul.nalog.ru)")
    else:
        строки.append("⚠ ИНН на сайте не найден — поискать по агрегаторам (Т-Банк/Xfirm) вручную")
    if ф["огрн"]:
        строки.append(f"✅ ОГРН на сайте: {ф['огрн'][0]}")
    строки.append(f"Контакты: {', '.join(ф['телефоны'][:2]) or '—'}; email: {', '.join(ф['emails'][:2]) or '—'}")
    if ф.get("мёртвых_страниц"):
        строки.append(f"❌ Сайт мёртв изнутри: {ф['мёртвых_страниц']} из {ф['страниц_всего']} внутренних страниц = 404 (ИТ-обслуживание слабое — аргумент за нас)")
    return строки


def гипотезы_llm(страницы, провайдер="ollama"):
    """LLM-слой: 3 гипотезы + цифра. Работает на локальной модели или ProxyAPI."""
    text = "\n---\n".join(f"{u}\n{txt[:1500]}" for u, _, txt in страницы)[:6000]
    промпт = f"""Ты готовишь переговорщика к звонку в компанию по памятке А. Манье.
Ниже текст страниц сайта компании. Найди (по-русски, конкретно, без воды):
1. Чем компания зарабатывает (2-3 строки)
2. 3 проверяемые гипотезы боли (каждая: проблема — как проверить на звонке)
3. Цифра «на этот звонок»: какая экономия возможна и вилка цены (обследование 300 тыс. / пилот 1,5-3 млн ₽)
4. Следующий шаг после звонка.
Формат: короткие пункты. Факты только из текста ниже, придуманное помечай «?».

ТЕКСТ САЙТА:
{text}
"""
    from crewai import LLM
    if провайдер == "ollama":
        llm = LLM(model="ollama/qwen3:1.7b", base_url="http://localhost:11434")
    else:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
        llm = LLM(model="openai/gpt-4o-mini",
                  base_url="https://api.proxyapi.ru/openai/v1",
                  api_key=os.getenv("PROXYAPI_KEY") or os.getenv("OPENAI_API_KEY"))
    log.info("LLM-слой: %s", провайдер)
    ans = llm.call([{"role": "user", "content": промпт}])
    return str(ans).strip()


def собрать_досье(url, факт_д, сверка_д, гип_текст, страницы):
    today = date.today().strftime("%d.%m.%Y")
    md = [f"# ДОСЬЕ (черновик автомата): {url} — на {today}",
          "",
          f"*Автоматический сбор с сайта ({len(факт_д['фрагменты'])} страниц). "
          "Проверять руками перед звонком: egrul.nalog.ru + агрегаторы. "
          "Структура — раздел 4 памятки Манье.*",
          "", "## 1. Чем компания зарабатывает (черновик)"]
    md.append(гип_текст if гип_текст else "*LLM недоступен — факты ниже, гипотезы составить за час руками.*")

    md += ["", "## 2. Факты с сайта (детерминированные, правда)"]
    md.append(f"- Названия юрлиц в тексте: {', '.join(факт_д['юрлица'][:5]) or '—'}")
    md.append(f"- Title страниц: {факт_д['title_юрлица'] or '—'}")
    md.append(f"- Телефоны: {', '.join(факт_д['телефоны'][:3]) or '—'}")
    md.append(f"- Email: {', '.join(факт_д['emails'][:3]) or '—'}")
    md.append(f"- ИНН/ОГРН упоминания: {', '.join(факт_д['инн']) or 'инн не найден'}; {', '.join(факт_д['огрн']) or 'огрн не найден'}")
    if факт_д["цены"]:
        md.append(f"- Числа с ₽ (возможные цены, тыс/шт): {', '.join(факт_д['цены'][:6])}")

    md += ["", "## 3. Сверка сайта с реквизитами"]
    md += [f"- {s}" for s in сверка_д]

    md += ["", "## 4. Страницы — фрагменты для речевой подготовки"]
    for u, ttl, txt in страницы:
        md.append(f"### {ttl or u}\n<источник {u}>\n{txt[:700]}…\n")

    md += ["", "## 5. Цифра НА ЭТОТ ЗВОНОК / следующий шаг",
           "*Заполнить вручную по памятке: вилка обследование 300 тыс. / пилот от 1,5 до 3 млн ₽; "
           "письмо-саммари в день звонка; предоплата 40–50%.*",
           "",
           f"**Источники:** сайт {url} (снят {today}; {len(факт_д['фрагменты'])} страниц), "
           "сверка реквизитов — egrul.nalog.ru вручную.",
           ]
    return "\n".join(md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Досье по URL (памятка Манье)")
    ap.add_argument("url")
    ap.add_argument("--llm", choices=["ollama", "proxyapi", "нет"], default="нет",
                    help="слой анализа: нет (только факты) / ollama / proxyapi (ключ в .env)")
    ap.add_argument("--pdf", action="store_true", help="сгенерировать PDF рядом с md")
    args = ap.parse_args()

    log.info("=== СТАРТ ДОСЬЕ: %s llm=%s ===", args.url, args.llm)
    страницы = собрать_тексты(args.url)
    log.info("страниц собрано: %d", len(страницы))
    ф = факты(страницы)
    св = сверка(ф)
    г = гипотезы_llm(страницы, args.llm) if args.llm != "нет" else None
    md_text = собрать_досье(args.url, ф, св, г, страницы)

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", urllib.parse.urlparse(args.url).netloc)
    out_md = OUT / f"досье_{slug}_{date.today().strftime('%Y-%m-%d')}.md"
    out_md.write_text(md_text, encoding="utf-8")
    log.info("досье: %s (%d символов)", out_md, len(md_text))
    print("MD:", out_md)

    if args.pdf:
        import subprocess
        pdf = str(out_md.with_suffix(".pdf"))
        r = subprocess.run([sys.executable,
                            r"C:\Users\Илья\Documents\ilya-claude\data\tmp\md2pdf_универсальный.py",
                            str(out_md), pdf], capture_output=True, text=True)
        print(r.stdout.strip())
        log.info("pdf: %s", pdf if os.path.exists(pdf) else "НЕ УДАЛСЯ")