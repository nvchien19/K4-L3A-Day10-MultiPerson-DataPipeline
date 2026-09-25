from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

from core.utils import write_json


def _rebuild_text(row: pd.Series) -> str:
    summary = str(row.get("summary", ""))
    return " ".join(str(row.get(field, "")) for field in ("title", "authors_joined", summary, "categories_joined")).strip()


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path) -> pd.DataFrame:
    corrupted = df.copy().reset_index(drop=True)
    events: list[dict] = []
    if len(corrupted) > 6:
        removed = corrupted.tail(2).copy()
        corrupted = corrupted.iloc[:-2].copy()
        events.append({"type": "missing_recent_records", "records": removed["paper_id"].tolist()})
    if not corrupted.empty:
        blank_id = corrupted.iloc[1]["paper_id"]
        corrupted.loc[1, "summary"] = ""
        events.append({"type": "blank_summary", "paper_ids": [blank_id]})
    if len(corrupted) > 3:
        noise_id = corrupted.iloc[2]["paper_id"]
        corrupted.loc[2, "text_for_embedding"] = str(corrupted.loc[2, "text_for_embedding"]) + " NOISE !!! corrupted"
        events.append({"type": "inject_noise", "paper_ids": [noise_id]})
    if len(corrupted) > 4:
        title_id = corrupted.iloc[3]["paper_id"]
        corrupted.loc[3, "title"] = str(corrupted.loc[3, "title"])[:12]
        events.append({"type": "truncate_title", "paper_ids": [title_id]})
    if not corrupted.empty:
        stale_id = corrupted.iloc[0]["paper_id"]
        corrupted.loc[0, "published"] = (datetime.now() - timedelta(days=365)).date().isoformat()
        corrupted.loc[0, "age_days"] = 365
        events.append({"type": "stale_date", "paper_ids": [stale_id]})
    duplicate = corrupted.iloc[[0]].copy()
    duplicate["paper_id"] = duplicate["paper_id"].astype(str) + "-duplicate"
    corrupted = pd.concat([corrupted, duplicate], ignore_index=True)
    events.append({"type": "duplicate_rows", "paper_ids": duplicate["paper_id"].tolist()})
    corrupted["text_for_embedding"] = corrupted.apply(_rebuild_text, axis=1)
    write_json(output_log_path, {"scenarios": events, "rows_before": len(df), "rows_after": len(corrupted)})
    return corrupted

