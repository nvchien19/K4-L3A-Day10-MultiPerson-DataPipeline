from __future__ import annotations

from datetime import date, datetime, timezone
import re

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def _clean_text(value: object) -> str:
    text = "" if value is None else str(value)
    return normalize_whitespace(re.sub(r"<[^>]+>", " ", text))


def _clean_names(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [name for name in (normalize_whitespace(str(value)) for value in values) if name]


def _parse_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = normalize_whitespace(str(value))
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for pattern in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[:19], pattern).date()
        except ValueError:
            continue
    return None


def _run_date_value(run_date: datetime) -> date:
    if run_date.tzinfo is None:
        return run_date.replace(tzinfo=timezone.utc).date()
    return run_date.astimezone(timezone.utc).date()


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    current_date = _run_date_value(run_date)
    rows: list[dict[str, object]] = []

    for record in records:
        published = _parse_date(record.published)
        updated = _parse_date(record.updated) or published
        if published is None or updated is None:
            continue
        title = _clean_text(record.title)
        summary = _clean_text(record.summary)
        authors = _clean_names(record.authors)
        categories = _clean_names(record.categories)
        rows.append(
            {
                "paper_id": normalize_whitespace(record.paper_id),
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": normalize_whitespace(record.primary_category) or (categories[0] if categories else "Uncategorized"),
                "published": published.isoformat(),
                "updated": updated.isoformat(),
                "abs_url": normalize_whitespace(record.abs_url),
                "pdf_url": normalize_whitespace(record.pdf_url),
                "comment": normalize_whitespace(record.comment),
                "published_date": published,
                "age_days": (current_date - published).days,
            }
        )

    df = pd.DataFrame(
        rows,
        columns=[
            "paper_id",
            "title",
            "summary",
            "authors",
            "categories",
            "primary_category",
            "published",
            "updated",
            "abs_url",
            "pdf_url",
            "comment",
            "published_date",
            "age_days",
        ],
    )
    if df.empty:
        return df

    df["authors_joined"] = df["authors"].map(lambda values: compact_join(values))
    df["categories_joined"] = df["categories"].map(lambda values: compact_join(values))
    df["summary_chars"] = df["summary"].map(len)
    df["text_for_embedding"] = df.apply(
        lambda row: "\n".join(
            line.rstrip()
            for line in (
                f"Title: {row['title']}",
                f"Authors: {row['authors_joined']}",
                f"Published: {row['published']}",
                f"Categories: {row['categories_joined']}",
                f"Summary: {row['summary']}",
            )
        ),
        axis=1,
    )

    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df[
        (df["paper_id"] != "")
        & (df["title"] != "")
        & (df["summary_chars"] >= 30)
        & (df["text_for_embedding"] != "")
        & (df["age_days"] >= 0)
    ]
    df = df.sort_values(by=["published_date", "paper_id"], ascending=[False, True], kind="mergesort")
    return df.reset_index(drop=True).drop(columns=["published_date"])
