#!/usr/bin/env python3
"""LuckyPilot AutoFinder.

Imports only explicitly approved RSS/Atom or JSON feeds. It does not crawl HTML,
copy full descriptions, download images, or automate sweepstakes participation.
"""
from __future__ import annotations
import datetime as dt
import email.utils
import hashlib
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "site" / "data" / "sources.json"
OUTPUT = ROOT / "site" / "gewinnspiele.json"
USER_AGENT = "LuckyPilot-AutoFinder/1.0 (+https://luckypilot.de)"


def today() -> str:
    return dt.date.today().isoformat()


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/rss+xml, application/atom+xml, text/xml"})
    with urllib.request.urlopen(req, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {url}")
        return response.read()


def clean(value: object, limit: int = 240) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def iso_date(value: object) -> str:
    text = clean(value, 80)
    if not text:
        return ""
    try:
        return dt.date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        pass
    try:
        parsed = email.utils.parsedate_to_datetime(text)
        return parsed.date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return ""


def stable_id(organizer: str, link: str, title: str) -> str:
    digest = hashlib.sha256(f"{organizer}|{link}|{title}".encode("utf-8")).hexdigest()[:16]
    return f"auto-{digest}"


def same_domain(url: str, allowed_domains: list[str]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d.lower() or host.endswith("." + d.lower()) for d in allowed_domains)


def make_item(raw: dict, source: dict) -> dict | None:
    fields = source.get("fields", {})
    get = lambda name, default="": raw.get(fields.get(name, name), default)
    title = clean(get("title"), 140)
    link = clean(get("url"), 500)
    organizer = clean(source.get("organizer") or get("organizer"), 100)
    if not title or not link or not organizer:
        return None
    allowed_domains = source.get("allowed_domains", [])
    if allowed_domains and not same_domain(link, allowed_domains):
        return None
    prize = clean(get("prize") or title, 160)
    deadline = iso_date(get("deadline"))
    category = clean(get("category") or source.get("category") or "Sonstiges", 40)
    frequency = clean(get("participationFrequency") or "einmalig", 30)
    # Deliberately creates a neutral original template instead of copying feed text.
    description = f"{organizer} informiert über die Aktion „{title}“. Details und verbindliche Teilnahmebedingungen stehen auf der offiziellen Aktionsseite."
    return {
        "id": stable_id(organizer, link, title),
        "title": title,
        "prize": prize,
        "organizer": organizer,
        "description": description,
        "sourceUrl": link,
        "deadline": deadline,
        "category": category,
        "participationFrequency": frequency,
        "verified": False,
        "lastChecked": today(),
        "added": iso_date(get("published")) or today(),
        "imageUrl": "",
        "imageRightsConfirmed": False,
        "sourceName": clean(source.get("name"), 100),
        "importMode": source.get("type", "")
    }


def parse_json(payload: bytes, source: dict) -> list[dict]:
    data = json.loads(payload.decode("utf-8"))
    path = source.get("items_path", "items")
    items = data
    for key in path.split(".") if path else []:
        items = items.get(key, []) if isinstance(items, dict) else []
    return items if isinstance(items, list) else []


def child_text(node: ET.Element, names: tuple[str, ...]) -> str:
    for child in node.iter():
        tag = child.tag.split("}")[-1].lower()
        if tag in names and child.text:
            return child.text.strip()
    return ""


def parse_feed(payload: bytes, source: dict) -> list[dict]:
    root = ET.fromstring(payload)
    entries = [n for n in root.iter() if n.tag.split("}")[-1].lower() in {"item", "entry"}]
    result = []
    for node in entries:
        link = ""
        for child in node.iter():
            if child.tag.split("}")[-1].lower() == "link":
                link = child.attrib.get("href") or (child.text or "")
                if link:
                    break
        result.append({
            "title": child_text(node, ("title",)),
            "url": link,
            "published": child_text(node, ("published", "updated", "pubdate")),
            "prize": child_text(node, ("prize",)),
            "deadline": child_text(node, ("deadline", "enddate", "validthrough")),
            "category": child_text(node, ("category",)),
        })
    return result


def load_existing() -> list[dict]:
    try:
        value = json.loads(OUTPUT.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def main() -> int:
    config = json.loads(SOURCES.read_text(encoding="utf-8"))
    if config.get("policy", {}).get("allow_html_scraping"):
        raise RuntimeError("HTML scraping is disabled by LuckyPilot policy.")
    imported: list[dict] = []
    errors: list[str] = []
    for source in config.get("sources", []):
        if not source.get("enabled") or source.get("permission_status") != "approved":
            continue
        try:
            payload = fetch(source["url"])
            rows = parse_json(payload, source) if source.get("type") == "json" else parse_feed(payload, source)
            for raw in rows:
                item = make_item(raw, source)
                if item:
                    imported.append(item)
        except Exception as exc:  # one broken source must not stop all others
            errors.append(f"{source.get('name', source.get('url'))}: {exc}")

    existing = {x.get("id"): x for x in load_existing() if isinstance(x, dict) and x.get("id")}
    for item in imported:
        previous = existing.get(item["id"], {})
        item["verified"] = bool(previous.get("verified", False))
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
    print(f"LuckyPilot: {len(imported)} importiert, {len(active)} aktiv, {len(errors)} Fehler")
    for error in errors:
        print("WARN:", error, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
