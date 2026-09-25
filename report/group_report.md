# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4              |
| Tên nhóm         | MultiPerson     |
| Repository         | https://github.com/nvchien19/K4-L3A-Day10-MultiPerson-DataPipeline.git |
| Ngày hoàn thành | 2026-09-25               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Hồ Nam | 2A202602788 | Pipeline Integration & Evidence | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, metrics và comparison report |
| 2 | Nguyễn Văn Chiến | 2A202602926 | Raw Ingestion & Data Lineage | `src/ingestion/crossref.py`, raw response/records, nguồn repair |
| 3 | Vũ Văn Hà | 2A202602589 | Data Modeling & Vector Index | `src/ingestion/cleaning.py`, `src/retrieval/embeddings.py`, `src/retrieval/index.py` |
| 4 | Nguyễn Cảnh Duy | 2A202602815 | Data Observability & Evaluation | `src/observability/quality.py`, `src/evaluation/testset.py`, `src/evaluation/metrics.py`, `src/observability/reporting.py` |
| 5 | Nguyễn Trọng Huy | 2A202602379 | Corruption, RAG Agent & Repair | `src/ingestion/corruption.py`, kiểm chứng QA/agent, dữ liệu corrupted/repaired |

Báo cáo cá nhân đã tạo: `report/2A202602788_NguyenHoNam.md`, `report/2A202602926_Nguyen_Van_Chien.md`, `report/2A202602589_VuVanHa.md`, `report/2A202602815_NguyenCanhDuy.md`, `report/2A202602379_Nguyen_Trong_Huy.md`.

## 2. Tóm tắt kết quả

**Tóm tắt của nhóm:**

Nhóm đã hoàn thành ingestion Crossref, cleaning, Quality Gate, test set, MiniLM/ChromaDB, Baseline, corruption có kiểm soát, repair từ raw và báo cáo đối chiếu ba trạng thái. Raw có 24 response items và 24 records; cleaning giữ lại 22 rows hợp lệ vì 2 record chỉ có ngày dạng năm-tháng. Baseline tạo test set 10 câu, collection `papers-baseline` 22 documents, hit rate `1.0`, Token F1 `0.8`, Quality Gate pass và freshness fresh. Corruption tạo 19 rows, hit rate còn `0.6`, Token F1 còn `0.1923`; Quality Gate fail ở unique và summary length vì trùng lặp và summary rỗng. Repair rebuild từ raw, tạo lại 22 rows, Quality Gate pass và metrics trở lại Baseline. Giới hạn chính là judge đang chạy ở chế độ tái hiện mock/fallback thay vì LLM production, và dữ liệu Crossref live có thể thay đổi giữa các lần chạy.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref response/snapshot, query/filter, `max_results=24` | Fetch, retry, parse, bảo toàn raw | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Nguyễn Văn Chiến |
| Cleaning          | `PaperRecord` | Chuẩn hóa text/ngày, dedupe, lọc invalid, tạo embedding text | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Vũ Văn Hà |
| Embedding/index   | Clean dataframe | MiniLM embedding, metadata, collection riêng theo trạng thái | `data/embeddings/`, `papers-baseline`, `papers-corrupted`, `papers-repaired` | Vũ Văn Hà |
| Evaluation        | Test set, index | Retrieval, Token F1, LLM Judge, Ragas tùy chọn | `data/eval/test_set.json`, metrics và answers trong `data/results/` | Nguyễn Cảnh Duy |
| Observability     | Clean/corrupted/repaired dataframe | GX checks, freshness SLA, sinh Markdown | `data/quality/`, `data/reports/` | Nguyễn Cảnh Duy |
| Corruption/repair | Clean dataframe, raw records | Tiêm 6 lỗi, re-index, repair từ raw | Corruption log, corrupted/repaired artifacts | Nguyễn Trọng Huy |
| Orchestration     | Raw, clean, test set, modules | Chạy Baseline rồi Corruption/Repair, kiểm tra artifact | Metrics và comparison report | Nguyễn Hồ Nam |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `mock`         |
| `LLM_MODEL`                | Giá trị cấu hình mặc định `gemini-2.5-flash`; provider `mock` dùng cho tái hiện |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2`         |
| Số lượng Crossref records | Raw 24, clean 22         |
| Retrieval`top_k`           | `4`         |
| Freshness threshold          | `180` ngày, stale ratio `0.25`         |
| Random seed, nếu có        | Không dùng seed ngẫu nhiên; corruption và test set deterministic |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

### Lệnh chạy

```powershell
$env:LLM_PROVIDER='mock'
.\.venv\Scripts\python.exe script/run_phase1.py
.\.venv\Scripts\python.exe script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-09-25                  | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| Corruption flow   | Thành công | 2026-09-25                  | `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API |
| Query/filter                | Query embedding/RAG/LLM và filter ngày/abstract theo `src/core/config.py` |
| Thời điểm lấy dữ liệu | Snapshot raw hiện có trong `data/raw/`; pipeline chạy 2026-09-25 |
| Số record nhận được    | 24 response items, 24 raw records |
| Cơ chế retry/backoff      | Retry `429/500/502/503/504`, fallback snapshot khi Live API lỗi |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | string | Có | DOI định danh document | Bỏ record |
| `title` | string | Có | Tiêu đề đã loại markup | Bỏ record |
| `summary` | string | Có | Abstract đã loại markup | Bỏ record hoặc fail quality nếu ngắn |
| `authors` | list[string] | Không | Danh sách tác giả | Chuẩn hóa, có thể rỗng |
| `categories` | list[string] | Không | Subject Crossref | Chuẩn hóa, fallback `primary_category` |
| `primary_category` | string | Không | Category chính | `Uncategorized` nếu thiếu |
| `published` | string ISO date | Có | Ngày xuất bản | Bỏ record nếu không parse được |
| `updated` | string ISO date | Có | Ngày cập nhật | Dùng published nếu thiếu |
| `abs_url` | string | Không | URL DOI | Dựng từ DOI nếu thiếu |
| `pdf_url` | string | Không | PDF nếu có | Dùng URL DOI nếu thiếu |
| `comment` | string | Không | Ghi chú lineage | Chuẩn hóa |
| `authors_joined` | string | Có ở clean | Tác giả nối chuỗi | Sinh từ `authors` |
| `categories_joined` | string | Có ở clean | Category nối chuỗi | Sinh từ `categories` |
| `summary_chars` | integer | Có ở clean | Độ dài summary | Tính lại sau corruption |
| `age_days` | integer | Có ở clean | Tuổi record | Tính từ `run_date - published` |
| `text_for_embedding` | string | Có ở clean | Context đưa vào embedding | Rebuild sau mọi thay đổi |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Loại record thiếu DOI/title/summary/ngày | Completeness/Validity  |              2 | Raw 24, clean 22 |
| Khử trùng lặp theo `paper_id` | Uniqueness  |              0 Baseline | Quality unique pass |
| Summary tối thiểu 30 ký tự | Completeness  |              0 Baseline | Quality summary pass |
| Chuẩn hóa whitespace và markup | Validity |              24 | Kiểm tra clean text |
| Sắp xếp published giảm dần và `paper_id` | Consistency |              22 | Thứ tự dataframe ổn định |

Nhóm tạo `text_for_embedding` theo đúng thứ tự Title, Authors, Published, Categories, Summary. Document ID là `paper_id`/DOI. Tuổi dữ liệu tính bằng `(run_date - published).days`.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | `10`                 |
| Các`question_type`                    | `summary`, `authors`, `date`, `categories`                  |
| Ground-truth document ID                 | DOI trong `ground_truth_doc_ids`     |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2`                  |
| Vector store/collection                  | ChromaDB: `papers-baseline`, `papers-corrupted`, `papers-repaired`                 |
| Retrieval`top_k`                       | `4`                   |
| LLM provider/model                       | `mock` cho tái hiện; Ragas skip                   |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Test set được giữ nguyên vì corruption/repair chỉ thay đổi corpus/index, không sinh đề mới. Nhờ đó chênh lệch metrics phản ánh đúng chất lượng dữ liệu.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | 24 items, 24 records |
| Cleaned dataset          | `data/clean/`                        | Có | 22 rows hợp lệ |
| Embedding manifest/index | `data/embeddings/`                   | Có | Manifest Baseline và 22 documents |
| Evaluation set           | `data/eval/`                         | Có | 10 câu, đủ 4 loại |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Hit rate `1.0` |
| Quality/freshness        | `data/quality/`                      | Có | Quality pass, freshness fresh |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Khớp metrics JSON |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     1.0 | Mọi ground-truth document đều được retrieval  |
| `mean_token_f1`      |     0.8 | Đáp án trích xuất đúng phần lớn nội dung chuẩn                           |
| `judge_accuracy`     |     0.8 | Judge chấp nhận 8/10 đáp án                           |
| `mean_judge_score`   |     4.2 | Điểm trung bình trên thang judge                           |
| Ragas, nếu có        | N/A | Chưa bật `RUN_RAGAS` vì vòng Ragas chậm |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| Row count | Completeness | `>= 1`         | Pass, 22 | `data/quality/baseline_quality_report.json`   |
| `paper_id` not null | Completeness | Không null | Pass | Baseline quality report |
| `paper_id` unique | Uniqueness | Duy nhất | Pass | Baseline quality report |
| `title` not null | Completeness | Không null | Pass | Baseline quality report |
| Summary length | Completeness | Đủ nội dung | Pass | Baseline quality report |
| `text_for_embedding` not null | Validity | Không null | Pass | Baseline quality report |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Clean/Baseline dataset            |
| Timestamp mới nhất       | `2026-09-15`                         |
| Ngưỡng freshness         | `180` ngày, stale ratio `0.25`                         |
| Trạng thái baseline      | Fresh               |
| Lý do                     | Stale `0/22`, stale ratio `0.0` |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Drop latest records | Bỏ 5 record mới nhất |          5 | Mất ground truth, hit giảm | Hit còn `0.6` | Rebuild từ raw |
| Blank summary | Xóa summary 2 rows |          2 | Summary length fail | Đáp án rỗng/sai | Rebuild từ raw |
| Inject noise | Chèn marker nhiễu 2 summaries |          2 | Token F1 giảm | Token F1 còn `0.1923` | Rebuild từ raw |
| Truncate title | Cắt title còn tối đa 5 ký tự |          2 | Metadata hỏng | Retrieval/answer suy giảm | Rebuild từ raw |
| Stale date | Lùi ngày 365 ngày cho 3 rows |          3 | Freshness stale rows tăng | Đáp án ngày sai | Rebuild từ raw |
| Duplicate rows | Nhân bản 2 rows |          2 | Unique fail | Quality fail | Rebuild từ raw |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log có đủ 6 scenario, paper ID, số rows trước/sau và tham số stale/noise/truncate.

Repair rebuild toàn bộ corpus từ `data/raw/crossref_records.json`, cleaning lại, tạo collection repaired riêng và đánh giá lại trên cùng test set. Nhờ đó repaired không kế thừa lỗi từ corrupted dataframe.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      1.0 |       0.6 |      1.0 |                      -0.4 |             +0.4 | Mất ground truth do drop records |
| `mean_token_f1`        |      0.8 |    0.1923 |      0.8 |                   -0.6077 |          +0.6077 | Blank/noise/stale date tác động mạnh |
| `judge_accuracy`       |      0.8 |       0.2 |      0.8 |                      -0.6 |             +0.6 | Judge suy giảm rõ |
| `mean_judge_score`     |      4.2 |       1.6 |      4.2 |                      -2.6 |             +2.6 | Repair khôi phục hoàn toàn |
| Quality checks pass/fail |     Pass |      Fail |     Pass |                 Pass→Fail |      Fail→Pass | Fail unique và summary length |
| Freshness status         |    Fresh |     Fresh |    Fresh |            Stale rows tăng |   Stale rows về 0 | Corrupted stale ratio chưa vượt ngưỡng |

Hai kết luận có quan hệ nhân quả:

1. Drop latest records, blank/noise/stale date và duplicate rows → Quality Gate fail unique/summary length và Freshness ghi stale rows → hit rate còn `0.6`, Token F1 còn `0.1923`.
2. Repair rebuild từ raw records → Quality Gate pass, freshness fresh, metrics trở lại Baseline `1.0` hit rate và `0.8` Token F1.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** `ValueError: Invalid test-set source row at position 4` khi chạy Baseline trên snapshot Crossref mới.
- **Nguyên nhân:** Record live không có subject nên `categories_joined` rỗng, test-set builder từ chối ground truth rỗng.
- **Cách xử lý:** Dùng `primary_category` làm đáp án dự phòng cho câu hỏi categories trong `src/evaluation/testset.py`.
- **Cách xác minh:** Chạy lại Baseline và Corruption/Repair thành công, test set 10 câu, metrics đầy đủ.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Judge chạy ở chế độ mock/fallback | Điểm judge có thể khác LLM production | Chạy lại với provider thật và so sánh metrics |
| Crossref live thay đổi theo thời gian | Raw/clean có thể khác snapshot hiện tại | Ghim snapshot và ghi hash/thời điểm fetch |
| Corrupted freshness vẫn Fresh | Tín hiệu stale chưa đủ mạnh trong demo | Tăng số stale rows hoặc hạ ngưỡng demo và đo lại |
| Báo cáo cá nhân mới hoàn thiện gần thời điểm nộp | Cần rà lại để tránh mâu thuẫn số liệu giữa báo cáo nhóm và báo cáo từng người | Đối chiếu từng báo cáo cá nhân với artifact và metrics chung trước khi nộp |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.

