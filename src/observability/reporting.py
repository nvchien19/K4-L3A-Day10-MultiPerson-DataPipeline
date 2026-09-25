from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import write_text


def _metric_rows(metrics: dict[str, Any]) -> str:
    return "\n".join(f"| `{key}` | {value} |" for key, value in metrics.items() if isinstance(value, (int, float)))


def generate_phase1_report(report_path: Path, source_summary: dict[str, Any], metrics: dict[str, Any], quality: dict[str, Any], freshness: dict[str, Any]) -> None:
    text = f"""# Phase 1 Baseline Report

## Source
- Records: {source_summary.get('records', 'N/A')}
- Source: {source_summary.get('source', 'Crossref')}

## Metrics
| Metric | Value |
|---|---:|
{_metric_rows(metrics)}

## Quality Gate
- Success: **{quality.get('success')}**
- Checks: {quality.get('checks', {})}

## Freshness
- Status: **{'Fresh' if freshness.get('is_fresh') else 'Stale'}**
- Stale rows: {freshness.get('stale_rows', 'N/A')}/{freshness.get('total_rows', 'N/A')}
- Threshold: {freshness.get('threshold_days', 'N/A')} days
"""
    write_text(report_path, text)


def generate_corruption_report(report_path: Path, baseline_metrics: dict[str, Any], corrupted_metrics: dict[str, Any], repaired_metrics: dict[str, Any], corrupted_quality: dict[str, Any], repaired_quality: dict[str, Any], corrupted_freshness: dict[str, Any], repaired_freshness: dict[str, Any]) -> None:
    metrics = ["retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"]
    rows = "\n".join(f"| `{key}` | {baseline_metrics.get(key, 'N/A')} | {corrupted_metrics.get(key, 'N/A')} | {repaired_metrics.get(key, 'N/A')} |" for key in metrics)
    text = f"""# Corruption and Repair Comparison

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
{rows}

## Quality
| State | Success | Freshness |
|---|---:|---|
| Corrupted | {corrupted_quality.get('success')} | {corrupted_freshness.get('is_fresh')} |
| Repaired | {repaired_quality.get('success')} | {repaired_freshness.get('is_fresh')} |

The repaired state is rebuilt from the preserved raw records before re-indexing and re-evaluation.
"""
    write_text(report_path, text)

