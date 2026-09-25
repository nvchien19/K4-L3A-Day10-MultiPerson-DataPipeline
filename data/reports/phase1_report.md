# Phase 1 Baseline Report

## Source
- Records: 24
- Source: Crossref REST API

## Metrics
| Metric | Value |
|---|---:|
| `samples` | 10 |
| `retrieval_hit_rate` | 1.0 |
| `mean_token_f1` | 0.6724815894587873 |
| `judge_accuracy` | 0.7 |
| `mean_judge_score` | 3.6 |

## Quality Gate
- Success: **True**
- Checks: {'row_count': {'success': True, 'observed': 24, 'expected': '>= 1'}, 'paper_id_not_null': {'success': True}, 'paper_id_unique': {'success': True}, 'title_not_null': {'success': True}, 'summary_length': {'success': True}, 'text_for_embedding_not_null': {'success': True}}

## Freshness
- Status: **Fresh**
- Stale rows: 0/24
- Threshold: 180 days
