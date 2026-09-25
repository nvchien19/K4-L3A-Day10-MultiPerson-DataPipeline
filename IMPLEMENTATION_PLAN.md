# Kế hoạch triển khai Day 10 — Data Pipeline & Data Observability

Kế hoạch này chuyển yêu cầu trong `README.md`, `docs/Guide.md` và `docs/CHECKPOINTS.md` thành các bước có thể kiểm tra. Thực hiện theo thứ tự từ trên xuống dưới; không chuyển checkpoint nếu chưa đạt tín hiệu hoàn thành.

## 1. Mục tiêu

Xây dựng pipeline RAG bảy tầng:

```text
Crossref API hoặc snapshot offline
    -> raw preservation
    -> cleaning và chuẩn hóa
    -> Great Expectations Quality Gate và Freshness
    -> MiniLM embedding và ChromaDB
    -> test set và baseline metrics
    -> corruption và đo suy giảm
    -> repair từ raw và đối chiếu ba trạng thái
```

Các trạng thái cần chứng minh:

1. **Baseline:** dữ liệu sạch, Quality Gate pass, RAG có metrics thật.
2. **Corrupted:** dữ liệu bị tiêm đủ sáu lỗi, Quality Gate hoặc Freshness cảnh báo, metrics suy giảm.
3. **Repaired:** phục hồi từ raw, metrics và chất lượng trở lại gần hoặc bằng Baseline.

## 2. Nguyên tắc bắt buộc

- Bảo toàn response gốc Crossref trước khi parse hoặc làm sạch.
- Luôn có đường fallback về `data/raw/crossref_response.json` khi API lỗi, không mạng hoặc gặp `429`.
- Quality Gate phải chạy trước khi nạp dữ liệu vào Vector Store.
- Repair phải đọc lại raw, không sửa trực tiếp trên corrupted dataframe.
- Dùng `paper_id` làm khóa định danh và làm khóa khử trùng lặp.
- Dùng `run_date` nhất quán cho Baseline, Corrupted và Repaired khi so sánh `age_days`.
- Sinh test set theo cách deterministic để chạy lại cho cùng kết quả.
- Chỉ ghi số liệu thực tế đọc từ JSON; không tự đặt số liệu trong báo cáo.
- Không commit `.env`, API key hoặc token.
- Không thêm phần thư viện hoặc API mới nếu chưa có trong `pyproject.toml`.

## 3. Definition of Done

- Các hàm đang chứa `TODO(student)`/`NotImplementedError` đã được triển khai.
- `python script/run_phase1.py` chạy với exit code `0`.
- `python script/run_corruption_flow.py` chạy với exit code `0`.
- Raw snapshot và raw records được tạo hoặc được tải đúng định dạng.
- Clean dataframe có 24 dòng trong bộ dữ liệu chuẩn và không có `paper_id` trùng.
- Baseline Quality Gate trả `success = True`.
- Corrupted quality report thể hiện lỗi; `corruption_log.json` có đủ sáu loại lỗi.
- Freshness report có các trường bắt buộc và cảnh báo đúng ngưỡng.
- Test set có 10 câu hỏi, phủ đủ `summary`, `authors`, `date`, `categories`.
- Có metrics Baseline, Corrupted và Repaired; các số liệu trong báo cáo khớp JSON.
- `corruption_report.md` có bảng Baseline vs Corrupted vs Repaired.
- Chạy lại flow không tạo thêm dữ liệu hoặc collection ngoài trạng thái được dự kiến.
- Không có secret trong Git.

## 4. Bản đồ triển khai

| Thứ tự | File | Phạm vi |
|---:|---|---|
| 1 | `src/ingestion/crossref.py` | Parse payload, gọi API, retry, lưu raw, fallback offline, load records |
| 2 | `src/ingestion/cleaning.py` | Chuẩn hóa record thành dataframe sẵn sàng embedding |
| 3 | `src/observability/quality.py` | GX 1.x Quality Gate và Freshness SLA |
| 4 | `src/evaluation/testset.py` | Sinh benchmark 10 câu hỏi |
| 5 | `src/observability/reporting.py` | Sinh báo cáo Markdown cho Baseline và đối chiếu |
| 6 | `src/pipelines/phase1.py` | Điều phối toàn bộ Baseline flow |
| 7 | `src/ingestion/corruption.py` | Tiêm sáu dạng lỗi có kiểm soát |
| 8 | `src/pipelines/corruption_flow.py` | Điều phối Corruption, Repair và Evaluation |

Các module `src/core/`, `src/retrieval/` và `src/evaluation/metrics.py` cần được tích hợp đúng contract của pipeline; không tạo lại logic nếu module đã cung cấp chức năng.

## 5. Kế hoạch thực hiện theo checkpoint

### CP0 — Môi trường và Raw Ingestion

- [ ] Kiểm tra Python `3.11`, `3.12` hoặc `3.13`.
- [ ] Cài dependencies bằng `uv sync` hoặc `python -m pip install -e .`.
- [ ] Tạo `.env` từ `.env.example` nếu cần gọi LLM; không commit file này.
- [ ] Kiểm tra import `chromadb`, `great_expectations`, `sentence_transformers`.
- [ ] Hoàn thiện `parse_crossref_payload()`.
- [ ] Hoàn thiện `fetch_source_records()` với request, retry `429/503`, lưu raw response và fallback snapshot.
- [ ] Hoàn thiện `load_raw_records()`.
- [ ] Xác nhận `PaperRecord` có đủ `paper_id`, `title`, `summary`, `authors`, `categories`, ngày và URL.
- [ ] Bảo đảm lấy đủ 24 bài báo trong snapshot chuẩn.

Tín hiệu đạt:

```powershell
python -c "import chromadb, great_expectations, sentence_transformers; print('Môi trường sẵn sàng')"
python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); r=fetch_source_records(s); print(f'Tín hiệu hoàn thành: Đã tải {len(r)} bài báo')"
```

Artifact bắt buộc:

- `data/raw/crossref_response.json`
- `data/raw/crossref_records.json`

### CP1 — Cleaning, Data Model và Quality Gate

- [ ] Hoàn thiện `build_clean_dataframe()`.
- [ ] Chuẩn hóa title, summary, authors, categories và loại HTML/XML/JATS.
- [ ] Parse `published` và `updated` thành dữ liệu nhất quán.
- [ ] Tính `age_days = (run_date - published).days`.
- [ ] Tạo các cột `authors_joined`, `categories_joined`, `summary_chars`, `text_for_embedding`.
- [ ] Tạo `text_for_embedding` đúng thứ tự: Title, Authors, Published, Categories, Summary.
- [ ] Loại record không hợp lệ và khử trùng lặp theo `paper_id`.
- [ ] Sắp xếp dataframe ổn định trước khi lưu.
- [ ] Lưu cả `papers_clean.csv` và `papers_clean.json`.
- [ ] Hoàn thiện `run_data_quality_checks()` bằng API GX 1.x hiện hành.
- [ ] Chạy đủ bốn expectation bắt buộc.
- [ ] Hoàn thiện `build_freshness_report()`.
- [ ] Quy định stale khi `age_days > 180`.
- [ ] Đặt `is_fresh = False` khi tỷ lệ stale vượt 25%.

Quality Gate phải kiểm tra:

1. Số dòng nằm trong khoảng `5..5000`.
2. `paper_id`, `title`, `text_for_embedding` không null.
3. `paper_id` là duy nhất.
4. `summary` có độ dài tối thiểu 30 ký tự.

Kết quả phải trả về dict có key `success` và ghi report dưới `data/quality/`.

Tín hiệu đạt:

```powershell
python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); print(f'Tín hiệu hoàn thành: Clean thành công {len(df)} dòng')"
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print(f'Tín hiệu hoàn thành: Quality check status = {res[\"success\"]}')"
```

### CP2 — Test Set và RAG Index

- [ ] Hoàn thiện `build_test_set()`.
- [ ] Chọn dữ liệu đại diện đủ số lượng để sinh 10 câu hỏi.
- [ ] Bảo đảm có đủ bốn `question_type`: `summary`, `authors`, `date`, `categories`.
- [ ] Mỗi câu có `id`, `question`, `ground_truth`, `ground_truth_doc_ids`.
- [ ] Lưu `data/eval/test_set.json`.
- [ ] Tích hợp MiniLM `all-MiniLM-L6-v2`.
- [ ] Tạo collection `papers-baseline` và nạp đủ 24 tài liệu.
- [ ] Lưu metadata cần thiết cho truy vấn.
- [ ] Kiểm tra `top_k`, `max_results` và các path theo `core.config`.

Tín hiệu đạt:

```powershell
python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); ts=build_test_set(df, s.paths.eval_testset); print(f'Tín hiệu hoàn thành: Sinh được {len(ts)} câu hỏi test')"
```

### CP3 — Baseline End-to-End

- [ ] Hoàn thiện `src/pipelines/phase1.py` theo thứ tự:
  1. Load settings.
  2. Load hoặc fetch raw records.
  3. Clean và lưu CSV/JSON.
  4. Chạy quality gate và freshness.
  5. Tạo test set.
  6. Dựng Chroma baseline index.
  7. Chạy retrieval/QA/evaluation.
  8. Lưu metrics và answers.
  9. Sinh `phase1_report.md`.
  10. Chạy agent demo tùy chọn.
- [ ] Không nạp index nếu Quality Gate thất bại.
- [ ] Bảo đảm metrics lấy từ kết quả chạy thực tế.
- [ ] Chạy `python script/run_phase1.py`.
- [ ] Kiểm tra exit code và toàn bộ artifact Baseline.

Tín hiệu đạt:

```powershell
python script/run_phase1.py
```

### CP4 — Corruption và đo suy giảm

- [ ] Hoàn thiện `corrupt_clean_dataframe()` trên bản sao dataframe.
- [ ] Không mutate trực tiếp Baseline.
- [ ] Tiêm đủ sáu loại lỗi:
  1. Drop khoảng 20% bản ghi mới nhất.
  2. Blank summary ở một số dòng.
  3. Inject noise vào summary.
  4. Truncate title xuống dưới 8 ký tự.
  5. Lùi ngày xuất bản về quá khứ.
  6. Duplicate rows.
- [ ] Rebuild `text_for_embedding` sau mỗi thay đổi liên quan.
- [ ] Cập nhật lại `age_days` sau khi sửa ngày.
- [ ] Ghi log có số lượng, vị trí hoặc mô tả thay đổi cho cả sáu trường hợp.
- [ ] Lưu `data/results/corruption_log.json`.
- [ ] Lưu corrupted clean artifacts và corrupted Chroma collection.
- [ ] Chạy evaluation trên collection `papers-corrupted`.
- [ ] Chạy quality/freshness; lỗi ở đây là kết quả dự kiến, không làm dừng flow trước khi ghi bằng chứng.
- [ ] Xác nhận metrics Corrupted thấp hơn Baseline rõ rệt.

Tín hiệu đạt:

```powershell
python -c "from core.config import load_settings; from ingestion.corruption import corrupt_clean_dataframe; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); c=corrupt_clean_dataframe(df, s.paths.corruption_log); print(f'Tín hiệu hoàn thành: Corrupted {len(c)} dòng')"
```

### CP5 — Idempotent Repair và báo cáo đối chiếu

- [ ] Hoàn thiện `src/pipelines/corruption_flow.py`.
- [ ] Load Baseline artifacts và metrics.
- [ ] Tạo và lưu Corrupted artifacts.
- [ ] Dựng lại `papers-corrupted` từ dữ liệu bị nhiễm.
- [ ] Đánh giá và lưu `corrupted_metrics.json`.
- [ ] Chạy Quality Gate và Freshness cho Corrupted.
- [ ] Repair bắt buộc bắt đầu từ `data/raw/crossref_records.json` hoặc raw response.
- [ ] Clean lại dữ liệu từ raw, không dùng corrupted data làm nguồn.
- [ ] Lưu Repaired clean artifacts.
- [ ] Dựng lại `papers-repaired` từ dữ liệu đã repair.
- [ ] Đánh giá và lưu `repaired_metrics.json`.
- [ ] Kiểm tra chất lượng và Freshness của Repaired.
- [ ] Sinh `corruption_report.md` có đủ ba cột Baseline, Corrupted, Repaired.
- [ ] Xác nhận chạy lặp lại không nhân thêm collection hoặc dữ liệu ngoài duplicate có chủ ý.

Tín hiệu đạt:

```powershell
python script/run_corruption_flow.py
```

### CP6 — Demo, nghiệm thu và nộp bài

- [ ] Chạy lại flow từ đầu sau khi sửa lần cuối.
- [ ] Kiểm tra cả hai entrypoint với exit code `0`.
- [ ] Kiểm tra bảng so sánh có số liệu khớp với các file JSON.
- [ ] Kiểm tra sáu mục corruption log.
- [ ] Kiểm tra `TEAM.md` đã ghi đầy đủ thành viên và đóng góp.
- [ ] Kiểm tra `.env` không được theo dõi hoặc commit.
- [ ] Kiểm tra tất cả thành viên xuất hiện trong Contributors của nhánh `main`.
- [ ] Chuẩn bị demo Baseline, Corrupted, Repaired và giải thích Silent Failure.
- [ ] Tự nộp link repository lên VLearn LMS trước deadline.

## 6. Artifact cần kiểm tra

```text
data/raw/crossref_response.json
data/raw/crossref_records.json
data/clean/papers_clean.csv
data/clean/papers_clean.json
data/eval/test_set.json
data/chroma/
data/quality/baseline_quality_report.json
data/quality/corrupted_quality_report.json
data/quality/freshness_report.json
data/results/baseline_metrics.json
data/results/corruption_log.json
data/results/corrupted_metrics.json
data/results/repaired_metrics.json
data/reports/phase1_report.md
data/reports/corruption_report.md
```

Các artifact phụ được pipeline tạo thêm cũng phải tồn tại nếu chạy end-to-end: answers, embedding manifests, quality report cho từng trạng thái và Chroma collections `papers-baseline`, `papers-corrupted`, `papers-repaired`.

## 7. Báo cáo và số liệu

`phase1_report.md` phải nêu:

- nguồn dữ liệu và số lượng record;
- cấu hình test/evaluation;
- retrieval hit rate, token F1 và các metrics có thật;
- kết quả Quality Gate;
- kết quả Freshness.

`corruption_report.md` phải có bảng tối thiểu:

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|

Báo cáo cũng nên giải thích:

- lỗi nào đã được tiêm;
- Quality Gate phát hiện lỗi gì;
- Freshness có báo stale hay không;
- vì sao Agent có thể trả lời sai trước khi phục hồi;
- vì sao metrics hồi phục gần hoặc bằng Baseline.

## 8. Kiểm tra cuối

Chạy theo thứ tự:

```powershell
python -m compileall src
python script/run_phase1.py
python script/run_corruption_flow.py
```

Nếu project có thêm test hoặc cấu hình lint/typecheck trong lúc triển khai, chạy các lệnh đó sau khi cài dependency. Repository hiện chưa cấu hình sẵn lệnh lint/typecheck bắt buộc; không tự thêm tool mới nếu chưa có yêu cầu.

## 9. Checklist tiến độ nhanh

- [ ] CP0 môi trường và raw ingestion
- [ ] CP1 cleaning, GX 1.x và freshness
- [ ] CP2 test set và Chroma baseline
- [ ] CP3 baseline pipeline và report
- [ ] CP4 corruption suite và degraded metrics
- [ ] CP5 repair, idempotency và comparison report
- [ ] CP6 demo, contributors và LMS submission
- [ ] Không có secret trong repository
- [ ] Tất cả số liệu báo cáo khớp artifact thực tế
- [ ] Chạy lại thành công ít nhất hai lần
