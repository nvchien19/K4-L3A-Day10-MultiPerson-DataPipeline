# Phase 1 Baseline Report

## Source
- Records: 22
- Source: Crossref REST API

## Metrics
| Metric | Value |
|---|---:|
| `samples` | 10 |
| `retrieval_hit_rate` | 1.0 |
| `mean_token_f1` | 0.8 |
| `judge_accuracy` | 0.8 |
| `mean_judge_score` | 4.2 |

## Quality Gate
- Success: **True**
- Checks: {'row_count': {'success': True, 'observed': 22, 'expected': '>= 1'}, 'paper_id_not_null': {'success': True}, 'paper_id_unique': {'success': True}, 'title_not_null': {'success': True}, 'summary_length': {'success': True}, 'text_for_embedding_not_null': {'success': True}}

## Freshness
- Status: **Fresh**
- Stale rows: 0/22
- Threshold: 180 days
