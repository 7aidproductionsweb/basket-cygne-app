from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup, Tag

URL = "https://competitions.ffbb.com/ligues/guy/comites/0973/clubs/guy0973007/equipes/200000005178873/classement"
OUTPUT_FILE = Path("data.json")
REQUEST_TIMEOUT = 20


def log(message: str) -> None:
    print(f"[scraper] {message}")


def fetch_html() -> Tuple[Optional[str], Optional[str]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "fr,fr-FR;q=0.9,en;q=0.8",
    }
    try:
        response = requests.get(URL, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        response.encoding = response.encoding or "utf-8"
        return response.text, None
    except requests.RequestException as exc:
        return None, f"Network error: {exc}"


def clean_text(tag: Tag) -> str:
    return " ".join(tag.get_text(" ", strip=True).split())


def find_target_table(soup: BeautifulSoup) -> Optional[Tag]:
    for table in soup.find_all("table"):
        headers = [clean_text(th).lower() for th in table.find_all("th")]
        header_blob = " ".join(headers)
        if "pts" in header_blob and ("equipe" in header_blob or "rang" in header_blob or "classement" in header_blob):
            return table
    return None


def parse_standings(html: str) -> Tuple[List[dict], Optional[str]]:
    soup = BeautifulSoup(html, "html.parser")
    table = find_target_table(soup)
    if table is None:
        return [], "Standings table not found"

    standings: List[dict] = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue

        entry = {
            "rank": clean_text(cells[0]),
            "name": clean_text(cells[1]),
            "points": clean_text(cells[2]),
            "played": clean_text(cells[3]) if len(cells) > 3 else "",
            "won": clean_text(cells[4]) if len(cells) > 4 else "",
            "lost": clean_text(cells[5]) if len(cells) > 5 else "",
        }
        standings.append(entry)

    if not standings:
        return [], "No standings rows parsed"

    return standings, None


def build_payload(standings: List[dict], warning: Optional[str]) -> dict:
    now = datetime.now(timezone.utc).astimezone()
    return {
        "updated_at": now.isoformat(),
        "source": URL,
        "standings": standings,
        "standing_count": len(standings),
        "status": "ok" if warning is None else "degraded",
        "warning": warning,
    }


def save_payload(payload: dict) -> None:
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"Wrote {OUTPUT_FILE} ({payload['standing_count']} entries, status={payload['status']}).")


def main() -> None:
    log("Starting scrape")

    html, fetch_error = fetch_html()
    standings: List[dict] = []
    parse_error: Optional[str] = None

    if html:
        standings, parse_error = parse_standings(html)
    warning = fetch_error or parse_error

    payload = build_payload(standings, warning)
    save_payload(payload)

    if warning:
        log(f"Completed with warning: {warning}")
    else:
        log("Scrape completed successfully")


if __name__ == "__main__":
    main()
