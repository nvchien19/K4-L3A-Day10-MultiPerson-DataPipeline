from __future__ import annotations

from datetime import datetime, UTC
import pandas as pd

from core.config import load_settings
from core.utils import write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    settings = load_settings()
    records = fetch_source_records(settings)
    clean = build_clean_dataframe(records, datetime.now(UTC))
    write_csv(clean, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean.to_dict(orient="records"))
    quality = run_data_quality_checks(clean, settings, "baseline")
    freshness = build_freshness_report(clean, settings, settings.paths.freshness_report)
    if not quality["success"]:
        raise RuntimeError("Baseline Quality Gate failed; vector index was not built.")
    build_test_set(clean, settings.paths.eval_testset)
    index = LocalEmbeddingIndex.build(clean, settings, settings.paths.embeddings_json)
    bundle = evaluate_pipeline(settings, index, settings.paths.eval_testset, settings.paths.baseline_metrics, settings.paths.baseline_answers)
    write_json(settings.paths.demo_answers, [{"question": item["question"], "answer": item["answer"]} for item in bundle.answers[:2]])
    generate_phase1_report(settings.paths.baseline_report, {"source": settings.source_api, "records": len(clean)}, bundle.summary, quality, freshness)
    print(f"Baseline hoàn tất: {len(clean)} records, quality={quality['success']}, hit_rate={bundle.summary['retrieval_hit_rate']:.3f}")

