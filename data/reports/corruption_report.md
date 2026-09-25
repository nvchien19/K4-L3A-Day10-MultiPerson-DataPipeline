# Corruption and Repair Comparison

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| `retrieval_hit_rate` | 1.0 | 0.6 | 1.0 |
| `mean_token_f1` | 0.8 | 0.1923076923076923 | 0.8 |
| `judge_accuracy` | 0.8 | 0.2 | 0.8 |
| `mean_judge_score` | 4.2 | 1.6 | 4.2 |

## Quality
| State | Success | Freshness |
|---|---:|---|
| Corrupted | False | True |
| Repaired | True | True |

The repaired state is rebuilt from the preserved raw records before re-indexing and re-evaluation.
