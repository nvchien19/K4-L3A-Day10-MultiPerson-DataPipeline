from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
import re
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _first_text(value: Any) -> str:
    if isinstance(value, list):
        for item in value:
            text = _first_text(item)
            if text:
                return text
        return ""
    if isinstance(value, str):
        return normalize_whitespace(value)
    return ""


def _strip_markup(value: str) -> str:
    return normalize_whitespace(re.sub(r"<[^>]+>", " ", value))


def _author_name(author: Any) -> str:
    if isinstance(author, str):
        return normalize_whitespace(author)
    if not isinstance(author, dict):
        return ""
    given = normalize_whitespace(str(author.get("given", "")))
    family = normalize_whitespace(str(author.get("family", "")))
    full = normalize_whitespace(f"{given} {family}")
    if full:
        return full
    return normalize_whitespace(str(author.get("name", "")))


def _format_date_parts(parts: Any) -> str:
    if not parts:
        return ""
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 1
    day = int(parts[2]) if len(parts) > 2 else 1
    return date(year, month, day).isoformat()


def _format_crossref_date(value: Any) -> str:
    if isinstance(value, dict):
        date_parts = value.get("date-parts") or []
        if date_parts and isinstance(date_parts[0], list):
            return _format_date_parts(date_parts[0])
        timestamp = _first_text(value.get("date-time", ""))
        if timestamp:
            return _format_crossref_date(timestamp)
        return ""
    if isinstance(value, str):
        text = normalize_whitespace(value)
        if not text:
            return ""
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            return text[:10]
    return ""


def _published_date(item: dict[str, Any]) -> str:
    for key in ("published", "published-online", "published-print", "created"):
        formatted = _format_crossref_date(item.get(key))
        if formatted:
            return formatted
    return ""


def _updated_date(item: dict[str, Any], published: str) -> str:
    for key in ("indexed", "deposited", "created"):
        formatted = _format_crossref_date(item.get(key))
        if formatted:
            return formatted
    return published


def _pdf_url(item: dict[str, Any], fallback_url: str) -> str:
    links = item.get("link", [])
    if isinstance(links, list):
        for link in links:
            if isinstance(link, dict) and link.get("content-type") == "application/pdf":
                url = _first_text(link.get("URL", ""))
                if url:
                    return url
    return fallback_url


def record_to_dict(record: PaperRecord) -> dict[str, Any]:
    return asdict(record)


def record_from_dict(payload: dict[str, Any]) -> PaperRecord:
    return PaperRecord(
        paper_id=str(payload.get("paper_id", "")),
        title=str(payload.get("title", "")),
        summary=str(payload.get("summary", "")),
        authors=[str(author) for author in payload.get("authors", []) or []],
        categories=[str(category) for category in payload.get("categories", []) or []],
        primary_category=str(payload.get("primary_category", "")),
        published=str(payload.get("published", "")),
        updated=str(payload.get("updated", "")),
        abs_url=str(payload.get("abs_url", "")),
        pdf_url=str(payload.get("pdf_url", "")),
        comment=str(payload.get("comment", "")),
    )


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    message = payload.get("message", {}) if isinstance(payload, dict) else {}
    items = message.get("items", []) if isinstance(message, dict) else []
    records: list[PaperRecord] = []

    for item in items:
        if not isinstance(item, dict):
            continue
        doi = _first_text(item.get("DOI", ""))
        title = _strip_markup(_first_text(item.get("title", "")))
        summary = _strip_markup(_first_text(item.get("abstract", "")))
        if not doi or not title or not summary:
            continue

        authors = [name for name in (_author_name(author) for author in item.get("author", []) or []) if name]
        categories = [
            category
            for category in (_first_text(category) for category in item.get("subject", []) or [])
            if category
        ]
        published = _published_date(item)
        if not published:
            continue
        updated = _updated_date(item, published)
        abs_url = _first_text(item.get("URL", "")) or f"https://doi.org/{doi}"

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "Uncategorized",
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=_pdf_url(item, abs_url),
                comment=f"Crossref record {doi}",
            )
        )

    return records


def _request_works(settings: Settings, attempts: int = 4) -> dict[str, Any]:
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "select": "DOI,title,abstract,author,subject,published,created,indexed,URL,link",
    }
    headers = {"User-Agent": "Day10-Data-Pipeline-Lab/0.1 (educational use)"}
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            response = requests.get(
                "https://api.crossref.org/works",
                params=params,
                headers=headers,
                timeout=30,
            )
            if response.status_code == 200:
                payload = response.json()
                if isinstance(payload, dict):
                    return payload
                raise RuntimeError("Crossref returned an unexpected payload.")
            if response.status_code in {429, 500, 502, 503, 504}:
                last_error = RuntimeError(f"Crossref status {response.status_code}.")
            else:
                response.raise_for_status()
        except requests.RequestException as exc:
            last_error = exc
        time.sleep(2**attempt)

    raise RuntimeError(f"Crossref request failed after {attempts} attempts: {last_error}")


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    if (
        not settings.refresh_source
        and settings.paths.raw_api_response.exists()
        and settings.paths.raw_records_json.exists()
    ):
        return load_raw_records(settings.paths.raw_records_json)

    try:
        payload = _request_works(settings)
        write_json(settings.paths.raw_api_response, payload)
    except Exception:
        if settings.paths.raw_api_response.exists():
            payload = read_json(settings.paths.raw_api_response)
        else:
            raise

    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [record_to_dict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    payload = read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Raw records file must contain a list: {path}")
    return [record_from_dict(item) for item in payload if isinstance(item, dict)]
