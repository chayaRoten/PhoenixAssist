from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

SITE_BASE_URL = "https://www.fnx.co.il"
PUBLIC_HOSTS = {"www.fnx.co.il"}
HEBREW_STOPWORDS = {
    "אני", "אתה", "את", "הוא", "היא", "אנחנו", "הם", "הן", "של", "על",
    "עם", "מה", "איך", "איפה", "האם", "אפשר", "יש", "אין", "לא", "אתר", "באתר",
    "מידע", "לגבי", "עבור", "כדי", "שלי", "שלך", "הזה", "הזאת", "יותר", "כולל",
}


def normalize_url(url: str, base_url: str = SITE_BASE_URL) -> str:
    """Return a fully qualified public URL for a page under the public Phoenix site."""
    if not url or url.startswith("#") or url.startswith("javascript:"):
        return base_url + "/"

    if url.startswith("/"):
        return urljoin(base_url, url)

    parsed = urlparse(url)
    if not parsed.netloc:
        return url.rstrip("#")
    if parsed.netloc in PUBLIC_HOSTS:
        return url.rstrip("#")
    if parsed.netloc.endswith("fnx.co.il") and parsed.netloc not in PUBLIC_HOSTS:
        return base_url + "/"
    if parsed.netloc and not parsed.netloc.endswith("fnx.co.il"):
        return base_url + "/"
    return url.rstrip("#")


def extract_public_links(html: str, base_url: str = SITE_BASE_URL) -> list[str]:
    """Extract only public Phoenix URLs from HTML and remove duplicates."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    seen: set[str] = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        normalized = normalize_url(href, base_url)
        parsed = urlparse(normalized)

        if normalized in seen or normalized == base_url + "/":
            continue
        if parsed.netloc and parsed.netloc not in PUBLIC_HOSTS:
            continue
        seen.add(normalized)
        links.append(normalized)

    return links


def extract_page_text(html: str) -> str:
    """Keep readable main content and drop navigation, footer, and boilerplate noise."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    for tag_name in ["nav", "header", "footer", "aside", "script", "style"]:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    main = soup.find("main") or soup.body or soup
    text_blocks: list[str] = []

    for element in main.find_all(["h1", "h2", "h3", "p", "li"]):
        if element.find_parent(["p", "li"]):
            continue
        content = " ".join(element.get_text(" ", strip=True).split())
        content = re.sub(r"לדעת עוד(?: על .*?)? עוד סגור", " ", content)
        content = re.sub(r"לקבלת הצעה|מידע נוסף", " ", content)
        content = re.sub(r"\s+", " ", content).strip()
        if content and len(content) > 2:
            text_blocks.append(content)

    return "\n".join(text_blocks)


def fetch_page_html(url: str, timeout: int = 20) -> str | None:
    """Fetch a public page and return raw HTML or None if unreachable."""
    try:
        import requests

        response = requests.get(url, timeout=timeout, headers={"User-Agent": "PhoenixAssist/1.0"})
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None


def crawl_public_pages(start_urls: list[str], max_pages: int = 15, max_depth: int = 1) -> list[dict[str, str]]:
    """Fetch a bounded set of public Phoenix pages and return cleaned text blocks with source URLs."""
    from bs4 import BeautifulSoup

    queue: list[tuple[str, int]] = [(url, 0) for url in start_urls]
    visited: set[str] = set()
    docs: list[dict[str, str]] = []

    while queue and len(visited) < max_pages:
        url, depth = queue.pop(0)
        normalized = normalize_url(url)
        if normalized in visited:
            continue
        if normalized.startswith(SITE_BASE_URL) and normalized.split("//")[-1].split("/")[0] not in {"www.fnx.co.il"}:
            continue

        html = fetch_page_html(normalized)
        if not html:
            continue

        visited.add(normalized)
        page_text = extract_page_text(html)
        if page_text:
            title = BeautifulSoup(html, "html.parser").title.get_text(" ", strip=True) if BeautifulSoup(html, "html.parser").title else normalized
            docs.append({"source_url": normalized, "title": title, "text": page_text})

        if depth >= max_depth:
            continue

        for link in extract_public_links(html, SITE_BASE_URL):
            if link not in visited:
                queue.append((link, depth + 1))

    return docs


def answer_from_documents(question: str, docs: list[dict[str, str]], limit: int = 3) -> tuple[str, list[str]]:
    """Return concise source excerpts ranked by query relevance, without inventing facts."""
    if not docs:
        return (
            "כרגע לא הצלחתי לאסוף מידע מהאתר הציבורי, ולכן אין לי מקור אמין שעליו אוכל לבסס תשובה. כדאי לנסות שוב בעוד כמה דקות.",
            [],
        )

    if re.search(r"לא הבנתי|לא ברור לי|לא הבנתי את התשובה|אפשר להסביר", question.strip().lower()):
        return (
            "בשמחה. איזו נקודה תרצי שאסביר מחדש? אפשר גם לכתוב את השאלה במילים אחרות, למשל: «מה מכסה ביטוח מקיף?».",
            [],
        )

    normalized_question = question.strip().lower()
    if "ביטוח מקיף" in normalized_question:
        keywords = ["מקיף", "נזקי רכוש", "צד ג", "רכב"]
    elif "ביטוח חובה" in normalized_question:
        keywords = ["חובה", "מחיר", "נהג", "רכב"]
    elif "ביטוח צד ג" in normalized_question or "צד שלישי" in normalized_question:
        keywords = ["צד ג", "צד שלישי", "נזקי רכוש"]
    else:
        keywords = [
            token for token in re.findall(r"[א-תA-Za-z0-9]+", normalized_question)
            if len(token) > 1 and token not in HEBREW_STOPWORDS
        ]
    if not keywords:
        return (
            "כדי שאוכל לחפש במידע שבאתר, כתבי שאלה ממוקדת יותר — למשל: «מה כולל ביטוח מקיף?».",
            [],
        )

    ranked: list[tuple[float, str, dict[str, str]]] = []
    for doc in docs:
        title = doc.get("title", "")
        text = doc.get("text", "")
        fragments = [
            sentence.strip()
            for block in text.splitlines()
            for sentence in re.split(r"(?<=[.!?؟])\s+", block)
            if len(sentence.strip()) >= 24
            and len(sentence.split()) >= 5
            and len(sentence.split()) <= 40
        ]
        if not fragments and text.strip():
            fragments = [text.strip()]

        for fragment in fragments:
            lowered = fragment.lower()
            if "ביטוח מקיף" in normalized_question and "מקיף" in lowered:
                matched = {"מקיף"}
                if "רכב" in lowered or "רכוש" in lowered:
                    matched.add("נזקי רכוש")
                if "צד ג" in lowered or "צד שלישי" in lowered:
                    matched.add("צד ג")
                if "רכב חשמלי" in lowered:
                    matched.discard("נזקי רכוש")
                    matched.discard("צד ג")
            else:
                matched = {
                    keyword
                    for keyword in keywords
                    if keyword in lowered
                    or (len(keyword) > 3 and keyword[1:] in lowered)
                }
            minimum_matches = 1 if "ביטוח מקיף" in normalized_question else max(1, (len(set(keywords)) + 1) // 2)
            if len(matched) < minimum_matches:
                continue
            if len(keywords) > 1 and len(matched) == 1 and len(fragment.split()) < 10:
                continue
            title_matches = sum(
                keyword in title.lower() or (len(keyword) > 3 and keyword[1:] in title.lower())
                for keyword in keywords
            )
            ui_penalty = 0.4 if re.search(r"לדעת עוד|עוד סגור|לקבלת הצעה", fragment) else 0
            length_penalty = max(0, len(fragment.split()) - 20) * 0.01
            score = len(matched) / len(set(keywords)) + title_matches * 0.05 - ui_penalty - length_penalty
            ranked.append((score, fragment, doc))

    if not ranked:
        return (
            "לא מצאתי בעמודים הציבוריים שאספתי מידע שמתייחס ישירות לשאלה. כדי לא להטעות, לא אנחש תשובה. אפשר לנסח את השאלה מחדש או לעיין בעמודי המקור שבאתר.",
            [],
        )

    ranked.sort(key=lambda item: item[0], reverse=True)
    selected: list[tuple[float, str, dict[str, str]]] = []
    sources: list[str] = []
    seen_fragments: set[str] = set()
    max_results = min(limit, 2)
    for item in ranked:
        _, fragment, doc = item
        normalized_fragment = re.sub(r"\s+", " ", fragment).strip()
        if normalized_fragment in seen_fragments:
            continue
        seen_fragments.add(normalized_fragment)
        selected.append((item[0], normalized_fragment, doc))
        source = doc["source_url"]
        if source not in sources:
            sources.append(source)
        if len(selected) >= max_results:
            break

    bullets = []
    for _, fragment, _ in selected:
        fragment = re.sub(r"\s*\([^)]{0,100}כרוכ[^)]*\)", "", fragment)
        fragment = re.sub(r"\s+", " ", fragment).strip()
        if len(fragment) > 280:
            fragment = fragment[:277].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
        bullets.append(f"- {fragment}")
    answer = "מצאתי באתר את הפרטים הבאים שעשויים לענות על השאלה:\n\n" + "\n\n".join(bullets)
    return answer, sources
