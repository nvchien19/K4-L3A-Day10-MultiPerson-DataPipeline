from __future__ import annotations

from datetime import datetime
import re
from html import unescape

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def _clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", unescape(value or ""))
    return normalize_whitespace(value)


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    rows: list[dict] = []
    for record in records:
        title = _clean_text(record.title)
        summary = _clean_text(record.summary)
        authors = [_clean_text(author) for author in record.authors if _clean_text(author)]
        categories = [_clean_text(category) for category in record.categories if _clean_text(category)]
        if not title or not record.paper_id:
            continue
        published = pd.to_datetime(record.published, errors="coerce")
        if pd.isna(published):
            published = pd.to_datetime(record.updated, errors="coerce")
        if pd.isna(published):
            continue
        published_timestamp = published.tz_localize(None) if published.tzinfo is not None else published
        run_timestamp = pd.Timestamp(run_date)
        run_timestamp = run_timestamp.tz_localize(None) if run_timestamp.tzinfo is not None else run_timestamp
        age_days = max(0, (run_timestamp.normalize() - published_timestamp.normalize()).days)
        authors_joined = compact_join(authors)
        categories_joined = compact_join(categories)
        text_for_embedding = " ".join((title, authors_joined, summary, categories_joined)).strip()
        rows.append({
            "paper_id": record.paper_id, "title": title, "summary": summary,
            "authors": authors, "categories": categories,
            "authors_joined": authors_joined, "categories_joined": categories_joined,
            "primary_category": record.primary_category or (categories[0] if categories else ""),
            "published": published.date().isoformat(), "updated": record.updated or published.date().isoformat(),
            "age_days": age_days, "summary_chars": len(summary), "text_for_embedding": text_for_embedding,
            "abs_url": record.abs_url, "pdf_url": record.pdf_url, "comment": record.comment,
        })
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.drop_duplicates("paper_id", keep="first").sort_values("paper_id").reset_index(drop=True)

