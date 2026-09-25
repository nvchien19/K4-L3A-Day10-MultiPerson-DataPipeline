from __future__ import annotations

from datetime import datetime, UTC
import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    settings = load_settings()
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    clean = pd.read_json(settings.paths.clean_json)
    corrupted = corrupt_clean_dataframe(clean, settings.paths.corruption_log)
    write_csv(corrupted, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted.to_dict(orient="records"))
    corrupted_quality = run_data_quality_checks(corrupted, settings, "corrupted")
    corrupted_freshness = build_freshness_report(corrupted, settings, settings.paths.freshness_report)
    corrupted_index = LocalEmbeddingIndex.build(corrupted, settings, settings.paths.corrupted_embeddings_json)
    corrupted_metrics = evaluate_pipeline(settings, corrupted_index, settings.paths.eval_testset, settings.paths.corrupted_metrics, settings.paths.corrupted_answers).summary

    repaired = build_clean_dataframe(load_raw_records(settings.paths.raw_records_json), datetime.now(UTC))
    write_csv(repaired, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired.to_dict(orient="records"))
    repaired_quality = run_data_quality_checks(repaired, settings, "repaired")
    repaired_freshness = build_freshness_report(repaired, settings, settings.paths.repaired_freshness_report)
    repaired_index = LocalEmbeddingIndex.build(repaired, settings, settings.paths.repaired_embeddings_json)
    repaired_metrics = evaluate_pipeline(settings, repaired_index, settings.paths.eval_testset, settings.paths.repaired_metrics, settings.paths.repaired_answers).summary
    generate_corruption_report(settings.paths.comparison_report, baseline_metrics, corrupted_metrics, repaired_metrics, corrupted_quality, repaired_quality, corrupted_freshness, repaired_freshness)
    print(f"Corruption flow hoàn tất: corrupted={len(corrupted)}, repaired={len(repaired)}")

