from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from core.utils import compact_join, write_json

DROP_COUNT = 5
BLANK_POSITIONS = (5, 6)
NOISE_POSITIONS = (8, 9)
TRUNCATE_POSITIONS = (11, 12)
STALE_POSITIONS = (13, 14, 15)
DUPLICATE_POSITIONS = (18, 19)
STALE_SHIFT_DAYS = 365
NOISE_MARKER = "@@@###$$$ %%%^^^ &&&*** CORRUPTION-NOISE"


def _refresh_derived_fields(corrupted: pd.DataFrame) -> pd.DataFrame:
    refreshed = corrupted.copy()
    refreshed["authors_joined"] = refreshed["authors"].map(
        lambda values: compact_join(values) if isinstance(values, list) else ""
    )
    refreshed["categories_joined"] = refreshed["categories"].map(
        lambda values: compact_join(values) if isinstance(values, list) else ""
    )
    refreshed["summary_chars"] = refreshed["summary"].map(lambda value: len(str(value)))
    refreshed["text_for_embedding"] = refreshed.apply(
        lambda row: (
            f"Title: {row['title']}\n"
            f"Authors: {row['authors_joined']}\n"
            f"Published: {row['published']}\n"
            f"Categories: {row['categories_joined']}\n"
            f"Summary: {row['summary']}"
        ),
        axis=1,
    )
    return refreshed


def _paper_ids(frame: pd.DataFrame, positions: tuple[int, ...]) -> list[str]:
    return [str(frame.iloc[position]["paper_id"]) for position in positions]


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    if len(df) < 21:
        raise ValueError(f"Corruption flow requires at least 21 cleaned documents, found {len(df)}.")

    ordered = df.sort_values(
        by=["published", "paper_id"], ascending=[False, True], kind="mergesort"
    ).reset_index(drop=True)
    log_path = Path(output_log_path)
    total_before = int(len(ordered))
    log: list[dict[str, object]] = []

    retained = ordered.iloc[DROP_COUNT:].copy().reset_index(drop=True)
    dropped_ids = [str(ordered.iloc[position]["paper_id"]) for position in range(DROP_COUNT)]
    log.append(
        {
            "corruption": "drop_latest_records",
            "description": "Removed the newest records to simulate missing fresh data.",
            "paper_ids": dropped_ids,
            "rows_before": total_before,
            "rows_after": int(len(retained)),
        }
    )

    blank_positions = tuple(position - DROP_COUNT for position in BLANK_POSITIONS)
    for position in blank_positions:
        retained.at[position, "summary"] = ""
    log.append(
        {
            "corruption": "blank_summary",
            "description": "Cleared summaries to simulate empty crawl/extraction results.",
            "paper_ids": _paper_ids(retained, blank_positions),
            "rows_affected": len(blank_positions),
        }
    )

    noise_positions = tuple(position - DROP_COUNT for position in NOISE_POSITIONS)
    for position in noise_positions:
        original = str(retained.at[position, "summary"])
        retained.at[position, "summary"] = f"{NOISE_MARKER} {original} {NOISE_MARKER}"
    log.append(
        {
            "corruption": "inject_noise",
            "description": "Inserted deterministic noise markers into summaries.",
            "paper_ids": _paper_ids(retained, noise_positions),
            "rows_affected": len(noise_positions),
        }
    )

    truncate_positions = tuple(position - DROP_COUNT for position in TRUNCATE_POSITIONS)
    for position in truncate_positions:
        retained.at[position, "title"] = str(retained.at[position, "title"])[:5]
    log.append(
        {
            "corruption": "truncate_title",
            "description": "Cut titles below eight characters to simulate malformed metadata.",
            "paper_ids": _paper_ids(retained, truncate_positions),
            "rows_affected": len(truncate_positions),
            "max_title_chars": 5,
        }
    )

    stale_positions = tuple(position - DROP_COUNT for position in STALE_POSITIONS)
    stale_dates: list[str] = []
    for position in stale_positions:
        original = date.fromisoformat(str(retained.at[position, "published"]))
        stale = (original - timedelta(days=STALE_SHIFT_DAYS)).isoformat()
        retained.at[position, "published"] = stale
        retained.at[position, "updated"] = stale
        stale_dates.append(stale)
    retained["age_days"] = (date.today() - pd.to_datetime(retained["published"]).dt.date).map(
        lambda value: value.days
    )
    log.append(
        {
            "corruption": "stale_date",
            "description": "Moved publication dates one year into the past to simulate stale data.",
            "paper_ids": _paper_ids(retained, stale_positions),
            "rows_affected": len(stale_positions),
            "shift_days": STALE_SHIFT_DAYS,
            "stale_dates": stale_dates,
        }
    )

    duplicate_positions = tuple(position - DROP_COUNT for position in DUPLICATE_POSITIONS)
    duplicates = retained.iloc[list(duplicate_positions)].copy()
    corrupted = pd.concat([retained, duplicates], ignore_index=True)
    log.append(
        {
            "corruption": "duplicate_rows",
            "description": "Appended exact duplicate rows to simulate repeated ingestion.",
            "paper_ids": _paper_ids(retained, duplicate_positions),
            "rows_affected": len(duplicate_positions),
        }
    )

    corrupted = _refresh_derived_fields(corrupted).reset_index(drop=True)
    log.append(
        {
            "corruption": "summary",
            "description": "Completed all six controlled corruption scenarios.",
            "total_rows_before": total_before,
            "total_rows_after": int(len(corrupted)),
            "scenario_count": 6,
        }
    )
    write_json(log_path, log)
    return corrupted
