from __future__ import annotations

from typing import Any
from pathlib import Path

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    checks = {
        "row_count": {"success": 1 <= len(df), "observed": len(df), "expected": ">= 1"},
        "paper_id_not_null": {"success": bool(df["paper_id"].notna().all()) if "paper_id" in df else False},
        "paper_id_unique": {"success": bool(df["paper_id"].is_unique) if "paper_id" in df else False},
        "title_not_null": {"success": bool(df["title"].notna().all()) if "title" in df else False},
        "summary_length": {"success": bool(df["summary_chars"].between(20, 100000).all()) if "summary_chars" in df else False},
        "text_for_embedding_not_null": {"success": bool(df["text_for_embedding"].fillna("").ne("").all()) if "text_for_embedding" in df else False},
    }
    result = {"report_name": report_name, "success": all(item["success"] for item in checks.values()), "checks": checks}
    output = {
        "baseline": settings.paths.baseline_quality_report,
        "corrupted": settings.paths.corrupted_quality_report,
        "repaired": settings.paths.repaired_quality_report,
    }.get(report_name, settings.paths.corrupted_quality_report)
    write_json(output, result)
    return result


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path) -> dict[str, Any]:
    total = len(df)
    stale_rows = int((pd.to_numeric(df.get("age_days", pd.Series(dtype=float)), errors="coerce") > settings.freshness_threshold_days).sum())
    dates = pd.to_datetime(df.get("published", pd.Series(dtype=str)), errors="coerce")
    result = {
        "latest_published": None if dates.empty or dates.isna().all() else dates.max().date().isoformat(),
        "oldest_published": None if dates.empty or dates.isna().all() else dates.min().date().isoformat(),
        "stale_rows": stale_rows, "total_rows": total,
        "stale_ratio": stale_rows / total if total else 0.0,
        "threshold_days": settings.freshness_threshold_days,
        "stale_threshold_ratio": 0.25,
        "is_fresh": total > 0 and stale_rows / total <= 0.25,
    }
    write_json(report_path, result)
    return result

