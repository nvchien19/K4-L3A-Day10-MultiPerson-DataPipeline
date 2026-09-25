import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    settings = load_settings()
    run_date = now_utc()

    if not settings.paths.baseline_metrics.exists():
        raise RuntimeError("Run script/run_phase1.py before the corruption flow.")
    baseline_metrics = read_json(settings.paths.baseline_metrics)

    if settings.paths.clean_json.exists():
        clean_df = pd.read_json(settings.paths.clean_json)
    else:
        clean_df = build_clean_dataframe(load_raw_records(settings.paths.raw_records_json), run_date)
    
    if not settings.paths.eval_testset.exists():
        build_test_set(clean_df, settings.paths.eval_testset)

    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))

    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df, settings, settings.paths.corrupted_embeddings_json
    )
    corrupted_bundle = evaluate_pipeline(
        settings,
        corrupted_index,
        settings.paths.eval_testset,
        settings.paths.corrupted_metrics,
        settings.paths.corrupted_answers,
    )
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, settings.paths.freshness_report
    )

    repair_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(repair_records, run_date)
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))

    repaired_index = LocalEmbeddingIndex.build(
        repaired_df, settings, settings.paths.repaired_embeddings_json
    )
    repaired_bundle = evaluate_pipeline(
        settings,
        repaired_index,
        settings.paths.eval_testset,
        settings.paths.repaired_metrics,
        settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness = build_freshness_report(
        repaired_df, settings, settings.paths.repaired_freshness_report
    )

    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics,
        corrupted_bundle.summary,
        repaired_bundle.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    print("Metric | Baseline | Corrupted | Repaired")
    for label, key in (
        ("retrieval_hit_rate", "retrieval_hit_rate"),
        ("mean_token_f1", "mean_token_f1"),
        ("judge_accuracy", "judge_accuracy"),
        ("mean_judge_score", "mean_judge_score"),
    ):
        print(
            f"{label} | {baseline_metrics[key]:.4f} | "
            f"{corrupted_bundle.summary[key]:.4f} | {repaired_bundle.summary[key]:.4f}"
        )
    print(
        f"Corrupted quality success={corrupted_quality['success']}; "
        f"repaired quality success={repaired_quality['success']}"
    )
    print(f"Corruption flow hoàn tất: corrupted={len(corrupted_df)}, repaired={len(repaired_df)}")
