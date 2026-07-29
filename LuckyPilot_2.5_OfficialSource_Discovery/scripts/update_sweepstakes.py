#!/usr/bin/env python3
"""LuckyPilot Official Source Discovery 2.5.

Discovers sweepstakes on explicitly allow-listed organiser domains through their
robots.txt and XML sitemaps. It only stores minimal factual metadata and links
back to the official organiser page. It does not copy article text, images,
logos or terms, and it never automates participation.
"""
from __future__ import annotations

import datetime as dt
import email.utils
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "site" / "data" / "sources.json"
OUTPUT = ROOT / "site" / "gewinnspiele.json"
REPORT = ROOT / "site" / "data" / "autofinder-report.json"
USER_AGENT = "LuckyPilot-AutoFinder/2.5 (+https://luckypilot.de)"
KEYWORDS = ("gewinnspiel", "verlosung", "win", "contest", "aktion")
DEADLINE_PATTERNS = [
    re.compile(r"(?:teilnahmeschluss|aktionsende|einsendeschluss|gültig\s+bis|bis zum)\D{0,35}(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})", re.I),
    re.compile(r'"(?:endDate|validThrough)"\s*:\s*"(\d{4}-\d{2}-\d{2})', re.I),
]
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
CANONICAL_RE = re.compile(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', re.I)


def today() -> str:
    return dt.date.today().isoformat()


def fetch(url: str, accept: str = "*/*", max_bytes: int = 2_500_000) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {url}")
        return response.read(max_bytes + 1)[:max_bytes]


def clean(value: object, limit: int = 240) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def iso_date(value: object) -> str:
    text = clean(value, 80)
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%y"):
        try:
            return dt.datetime.strptime(text[:10], fmt).date().isoformat()
        except ValueError:
            pass
    try:
        return email.utils.parsedate_to_datetime(text).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return ""


def stable_id(organizer: str, link: str) -> str:
    digest = hashlib.sha256(f"{organizer}|{link}".encode()).hexdigest()[:16]
    return f"auto-{digest}"


def host_of(url: str) -> str:
    return (urllib.parse.urlparse(url).hostname or "").lower().removeprefix("www.")


def same_domain(url: str, domain: str) -> bool:
    host = host_of(url)
    domain = domain.lower().removeprefix("www.")
    return host == domain or host.endswith("." + domain)


def robots_allows(base_url: str, url: str) -> tuple[bool, list[str]]:
    robots_url = urllib.parse.urljoin(base_url, "/robots.txt")
    rp = urllib.robotparser.RobotFileParser()
    try:
        text = fetch(robots_url, "text/plain", 500_000).decode("utf-8", "ignore")
        rp.set_url(robots_url)
        rp.parse(text.splitlines())
        sitemaps = [line.split(":", 1)[1].strip() for line in text.splitlines() if line.lower().startswith("sitemap:")]
        return rp.can_fetch(USER_AGENT, url), sitemaps
    except Exception:
        # Fail closed for page crawling; sitemap discovery may use configured URLs.
        return False, []


def parse_sitemap(payload: bytes) -> tuple[list[str], list[str]]:
    root = ET.fromstring(payload)
    tag = root.tag.split("}")[-1].lower()
    locs = [clean(n.text, 1000) for n in root.iter() if n.tag.split("}")[-1].lower() == "loc" and n.text]
    return (locs, []) if tag == "urlset" else ([], locs)


def sitemap_candidates(source: dict) -> list[str]:
    base = source["base_url"]
    domain = source["domain"]
    configured = list(source.get("sitemaps", []))
    _, robots_maps = robots_allows(base, base)
    queue = list(dict.fromkeys(robots_maps + configured + [urllib.parse.urljoin(base, "/sitemap.xml")]))
    seen_maps: set[str] = set()
    urls: list[str] = []
    max_maps = int(source.get("max_sitemaps", 20))
    max_urls = int(source.get("max_urls", 3000))
    while queue and len(seen_maps) < max_maps and len(urls) < max_urls:
        sm = queue.pop(0)
        if sm in seen_maps or not same_domain(sm, domain):
            continue
        seen_maps.add(sm)
        try:
            page_urls, child_maps = parse_sitemap(fetch(sm, "application/xml,text/xml"))
            urls.extend(u for u in page_urls if same_domain(u, domain))
            queue.extend(m for m in child_maps if same_domain(m, domain))
        except Exception:
            continue
    unique = list(dict.fromkeys(urls))[:max_urls]
    return [u for u in unique if any(k in urllib.parse.unquote(u).lower() for k in source.get("keywords", KEYWORDS))]


def extract_deadline(body: str) -> str:
    for pattern in DEADLINE_PATTERNS:
        match = pattern.search(body)
        if match:
            return iso_date(match.group(1))
    return ""


def extract_title(body: str) -> str:
    for pattern in (H1_RE, TITLE_RE):
        match = pattern.search(body)
        if match:
            title = clean(match.group(1), 150)
            title = re.sub(r"\s+[|–—-]\s+[^|–—]{2,60}$", "", title).strip()
            if title:
                return title
    return ""


def make_official_item(url: str, source: dict) -> dict | None:
    allowed, _ = robots_allows(source["base_url"], url)
    if not allowed:
        return None
    payload = fetch(url, "text/html,application/xhtml+xml", int(source.get("max_page_bytes", 1_500_000)))
    body = payload.decode("utf-8", "ignore")
    low = clean(body, 20_000).lower()
    if not any(k in low for k in source.get("page_keywords", ("gewinnspiel", "verlosung"))):
        return None
    canonical = CANONICAL_RE.search(body)
    link = urllib.parse.urljoin(url, canonical.group(1)) if canonical else url
    if not same_domain(link, source["domain"]):
        link = url
    title = extract_title(body)
    if not title:
        return None
    organizer = clean(source["organizer"], 100)
    deadline = extract_deadline(body)
    description = f"{organizer} informiert auf der offiziellen Website über die Aktion „{title}“. Verbindliche Angaben stehen ausschließlich auf der verlinkten Veranstalterseite."
    return {
        "id": stable_id(organizer, link),
        "title": title,
        "prize": title,
        "organizer": organizer,
        "description": description,
        "sourceUrl": link,
        "deadline": deadline,
        "category": clean(source.get("category", "Sonstiges"), 40),
        "participationFrequency": "einmalig",
        "verified": False,
        "lastChecked": today(),
        "added": today(),
        "imageUrl": "",
        "imageRightsConfirmed": False,
        "sourceName": clean(source.get("name", organizer), 100),
        "importMode": "official-sitemap",
        "officialSource": True,
    }


def load_existing() -> list[dict]:
    try:
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def main() -> int:
    config = json.loads(SOURCES.read_text(encoding="utf-8"))
    imported: list[dict] = []
    source_report: list[dict] = []
    for source in config.get("sources", []):
        if not source.get("enabled") or source.get("type") != "official_sitemap":
            continue
        found = accepted = 0
        errors: list[str] = []
        try:
            candidates = sitemap_candidates(source)
            found = len(candidates)
            for url in candidates[: int(source.get("max_pages_per_run", 25))]:
                try:
                    item = make_official_item(url, source)
                    if item:
                        imported.append(item)
                        accepted += 1
                    time.sleep(float(source.get("delay_seconds", 0.8)))
                except Exception as exc:
                    errors.append(f"{url}: {type(exc).__name__}")
        except Exception as exc:
            errors.append(str(exc))
        source_report.append({"source": source.get("name"), "candidates": found, "accepted": accepted, "errors": errors[:10]})

    existing = {x.get("id"): x for x in load_existing() if isinstance(x, dict) and x.get("id")}
    for item in imported:
        previous = existing.get(item["id"], {})
        item["added"] = previous.get("added") or item["added"]
        existing[item["id"]] = item

    cutoff = dt.date.today() - dt.timedelta(days=2)
    active = []
    for item in existing.values():
        deadline = iso_date(item.get("deadline"))
        if deadline and dt.date.fromisoformat(deadline) < cutoff:
            continue
        active.append(item)
    active.sort(key=lambda x: (x.get("deadline") or "9999-12-31", x.get("title") or ""))
    OUTPUT.write_text(json.dumps(active, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps({"runDate": today(), "imported": len(imported), "active": len(active), "sources": source_report}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"LuckyPilot: {len(imported)} offizielle Fundstellen, {len(active)} aktive Einträge")
    for row in source_report:
        print(f"- {row['source']}: {row['candidates']} Kandidaten, {row['accepted']} übernommen, {len(row['errors'])} Fehler")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        raise
