from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import ensure_parent, first_sentence, normalize_whitespace, write_json


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

    def as_dict(self) -> dict[str, Any]:
        return {field: getattr(self, field) for field in self.__dataclass_fields__}


def _date_value(value: Any) -> str:
    if isinstance(value, dict):
        parts = value.get("date-parts", [[]])[0]
    elif isinstance(value, list) and value and isinstance(value[0], dict):
        parts = value[0].get("date-parts", [[]])[0]
    else:
        return ""
    if parts:
        try:
            return "-".join(f"{int(part):02d}" if i else str(int(part)) for i, part in enumerate(parts))
        except (TypeError, ValueError):
            pass
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    records: list[PaperRecord] = []
    for item in payload.get("message", {}).get("items", []):
        doi = normalize_whitespace(str(item.get("DOI", ""))).lower()
        title = first_sentence(normalize_whitespace(str(item.get("title", [""])[0] if item.get("title") else "")))
        if not doi or not title:
            continue
        abstract = normalize_whitespace(str(item.get("abstract", "")))
        authors = []
        for author in item.get("author", []):
            name = normalize_whitespace(" ".join(str(author.get(key, "")) for key in ("given", "family")))
            if name:
                authors.append(name)
        categories = [normalize_whitespace(str(x)) for x in item.get("subject", []) if normalize_whitespace(str(x))]
        published = _date_value(item.get("published")) or _date_value(item.get("created"))
        records.append(PaperRecord(
            paper_id=doi, title=title, summary=abstract, authors=authors,
            categories=categories, primary_category=categories[0] if categories else "",
            published=published, updated=_date_value(item.get("updated")) or published,
            abs_url=str(item.get("URL", f"https://doi.org/{doi}")),
            pdf_url="", comment=normalize_whitespace(str(item.get("comment", ""))),
        ))
    return records


def _load_snapshot(settings: Settings) -> list[PaperRecord]:
    response = json.loads(settings.paths.raw_api_response.read_text(encoding="utf-8"))
    records = parse_crossref_payload(response)
    if not records:
        records = [PaperRecord(**item) for item in json.loads(settings.paths.raw_records_json.read_text(encoding="utf-8"))]
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    ensure_parent(settings.paths.raw_api_response)
    try:
        response = requests.get(
            "https://api.crossref.org/works", params={"query": settings.source_query, "filter": settings.source_filter, "rows": settings.max_results}, timeout=15,
        )
        for attempt in range(3):
            if response.status_code not in {429, 503}:
                response.raise_for_status()
                break
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                response.raise_for_status()
        write_json(settings.paths.raw_api_response, response.json())
        records = parse_crossref_payload(response.json())
    except (requests.RequestException, OSError, ValueError):
        records = _load_snapshot(settings)
    if not records:
        raise RuntimeError("Không thể lấy dữ liệu Crossref và không có snapshot offline hợp lệ.")
    write_json(settings.paths.raw_records_json, [record.as_dict() for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [PaperRecord(**item) for item in payload]

