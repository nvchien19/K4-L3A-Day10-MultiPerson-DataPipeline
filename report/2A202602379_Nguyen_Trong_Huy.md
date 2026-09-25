# Member Role Report — Nguyễn Trọng Huy

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Trọng Huy             |
| MSSV               | 2A202602379                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | MultiPerson     |
| Vai trò chính    | Corruption, RAG Agent & Repair                 |
| Repository         | https://github.com/nvchien19/K4-L3A-Day10-MultiPerson-DataPipeline.git |
| Ngày hoàn thành | 2026-09-25               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Tiêm lỗi dữ liệu có kiểm soát | `src/ingestion/corruption.py`: `corrupt_clean_dataframe`, `_refresh_derived_fields` | Clean dataframe sau baseline | Corrupted dataframe, `data/results/corruption_log.json` ghi đủ 6 scenario | Hoàn thành |
| Kiểm chứng QA/RAG agent trên dữ liệu lỗi | `src/retrieval/qa.py`, `src/retrieval/agent.py`, `src/pipelines/corruption_flow.py` | Test set cố định, index baseline/corrupted/repaired | Metrics và answers cho trạng thái corrupted/repaired | Hoàn thành |
| Repair và đối chiếu phục hồi | `src/pipelines/corruption_flow.py`: phần rebuild từ raw records | `data/raw/crossref_records.json`, test set chung | `data/clean/papers_clean_repaired.*`, `data/results/repaired_metrics.json`, quality/freshness repaired | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Làm rõ tác động của dữ liệu lỗi lên metrics | Nguyễn Hồ Nam / pipeline integration | Có bảng so sánh Baseline, Corrupted, Repaired trong báo cáo nhóm |
| Kiểm tra tín hiệu quality/freshness sau corruption | Nguyễn Cảnh Duy / observability | Corrupted fail quality ở unique và summary length; repaired pass lại |
| Giữ contract cho embedding sau khi sửa dữ liệu | Vũ Văn Hà / cleaning và vector index | `summary_chars`, `age_days`, `text_for_embedding` được tính lại trước khi re-index |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Thiết kế 6 corruption scenario deterministic | `src/ingestion/corruption.py`, `data/results/corruption_log.json` | Drop latest records, blank summary, inject noise, truncate title, stale date, duplicate rows | Đọc corruption log và kiểm tra số row trước/sau |
| Rebuild index và đánh giá corrupted state | `src/pipelines/corruption_flow.py`, `data/results/corrupted_metrics.json` | Hit rate giảm từ `1.0` xuống `0.6`, Token F1 giảm từ `0.8` xuống `0.1923` | Chạy `script/run_corruption_flow.py` sau baseline |
| Repair từ raw thay vì vá dataframe lỗi | `data/raw/crossref_records.json`, `data/clean/papers_clean_repaired.json` | Repaired có 22 rows, quality pass và metrics quay về baseline | So sánh `repaired_metrics.json` với `baseline_metrics.json` |
| Kiểm chứng hành vi QA/agent | `src/retrieval/qa.py`, `src/retrieval/agent.py`, `data/results/*_answers.json` | Agent/QA suy giảm khi index chứa dữ liệu lỗi và phục hồi sau repair | Đối chiếu answer, retrieved doc IDs và judge score |

Output cụ thể nhất của tôi là bộ corruption/repair artifacts: `data/results/corruption_log.json`, corrupted/repaired metrics và dữ liệu repaired được rebuild từ raw. Các artifact này chứng minh quan hệ nhân quả giữa dữ liệu hỏng, Quality Gate và chất lượng câu trả lời của RAG agent.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

RAG agent có thể vẫn trả lời bình thường khi dữ liệu trong index đã hỏng. Nếu chỉ nhìn vào việc pipeline chạy không lỗi thì rất dễ bỏ sót silent failure: mất ground-truth document, summary rỗng, metadata sai hoặc dữ liệu trùng. Phần của tôi tạo dữ liệu lỗi có kiểm soát, đo tác động lên retrieval/answer quality, rồi chứng minh repair từ raw có thể phục hồi kết quả.

### Cách triển khai

Tôi triển khai corruption theo hướng deterministic để các lần chạy có thể so sánh được:

- Sắp xếp dữ liệu theo `published` giảm dần và `paper_id` để chọn record ổn định.
- Xóa 5 record mới nhất nhằm mô phỏng mất dữ liệu tươi.
- Xóa summary của 2 record để mô phỏng crawl/extraction rỗng.
- Chèn noise marker vào 2 summary để kiểm tra khả năng phát hiện nội dung bẩn.
- Cắt title của 2 record còn tối đa 5 ký tự để làm hỏng metadata.
- Lùi ngày của 3 record đi 365 ngày để tạo tín hiệu stale.
- Nhân bản 2 rows để làm Quality Gate fail ở uniqueness.
- Tính lại các trường dẫn xuất như `summary_chars`, `age_days` và `text_for_embedding` trước khi build index corrupted.

Repair không vá trực tiếp corrupted dataframe. Luồng repair đọc lại `data/raw/crossref_records.json`, chạy cleaning, build collection `papers-repaired`, sau đó đánh giá lại trên cùng test set với baseline/corrupted.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Clean dataframe, raw records, `data/eval/test_set.json`, baseline metrics |
| Output                         | Corrupted dataframe, repaired dataframe, corruption log, metrics/answers của corrupted và repaired |
| Module phụ thuộc             | `src/ingestion/cleaning.py`, `src/retrieval/index.py`, `src/evaluation/metrics.py`, `src/observability/quality.py` |
| Module sử dụng output        | `src/pipelines/corruption_flow.py`, `src/observability/reporting.py`, báo cáo nhóm |
| Điều kiện lỗi cần xử lý | Thiếu baseline artifact, clean dataset quá ít row, trường derived không được refresh sau corruption, raw records không dùng được để repair |

### Cách xác minh

```powershell
$env:LLM_PROVIDER='mock'
.\.venv\Scripts\python.exe script/run_phase1.py
.\.venv\Scripts\python.exe script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Baseline pass; corrupted làm metrics giảm và Quality Gate fail; repaired pass và metrics quay về baseline.
- **Kết quả thực tế theo báo cáo nhóm:** Baseline/Repaired hit rate `1.0`, Corrupted hit rate `0.6`; Baseline/Repaired Token F1 `0.8`, Corrupted Token F1 `0.1923`.
- **Artifact/log:** `data/results/corruption_log.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/quality/`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi corrupted data đã được tạo, có thể repair bằng cách vá từng lỗi trong dataframe hoặc rebuild lại toàn bộ từ raw records.
- **Các phương án đã cân nhắc:** Vá trực tiếp từng lỗi trong corrupted dataframe; hoặc bỏ corrupted dataframe và chạy lại cleaning từ `data/raw/crossref_records.json`.
- **Phương án đã chọn:** Rebuild từ raw records.
- **Lý do:** Vá từng lỗi dễ bỏ sót trường dẫn xuất, duplicate hoặc lỗi metadata đã lan sang embedding. Rebuild từ raw giữ đúng data lineage, dễ tái hiện và không kế thừa trạng thái lỗi.
- **Bằng chứng quyết định phù hợp:** Repaired có 22 rows như baseline, Quality Gate pass, freshness fresh và metrics phục hồi về hit rate `1.0`, Token F1 `0.8`.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Sau khi chỉnh `summary`, `title` hoặc `published`, nếu không cập nhật lại `text_for_embedding` và các trường thống kê, corrupted index có thể vẫn phản ánh dữ liệu cũ hoặc quality report không thấy đúng mức lỗi.
- **Lệnh hoặc bước tái hiện:** Tạo corrupted dataframe rồi build index/evaluate ngay mà không refresh các trường derived.
- **Nguyên nhân gốc:** `summary_chars`, `age_days`, `authors_joined`, `categories_joined` và `text_for_embedding` được sinh từ clean dataframe ban đầu; các thao tác corruption chỉ sửa một số cột nguồn.
- **Cách xử lý:** Thêm bước `_refresh_derived_fields` sau tất cả scenario, đồng thời tính lại `age_days` sau khi lùi `published`.
- **Cách xác minh sau khi sửa:** Corruption log ghi đủ scenario, corrupted metrics giảm rõ, Quality Gate phát hiện lỗi summary/unique, còn repaired rebuild từ raw phục hồi kết quả.
- **Điều học được:** Trong data pipeline, sửa dữ liệu nguồn chưa đủ; mọi trường dẫn xuất dùng cho embedding và observability cũng phải được rebuild nhất quán.

## 7. Hiểu biết về luồng end-to-end

1. Crossref response được parse thành raw records, cleaning chuẩn hóa schema và tạo `text_for_embedding`; sau đó MiniLM tạo embedding và ChromaDB lưu collection để QA/RAG truy vấn.
2. Evaluation set gồm các câu hỏi có ground-truth answer và `ground_truth_doc_ids`; retrieval đúng khi DOI chuẩn xuất hiện trong top-k, còn answer quality được đo bằng Token F1 và judge.
3. Quality checks kiểm tra cấu trúc hiện tại của dataframe như null, duplicate và summary length; freshness kiểm tra độ mới theo `age_days` và stale ratio.
4. Phải dùng cùng test set cho baseline, corrupted và repaired để metric giảm/tăng là do dữ liệu thay đổi, không phải do câu hỏi thay đổi.
5. Repair thành công khi dữ liệu được clean lại từ raw, Quality Gate pass, freshness fresh và metrics quay về mức baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      1.0 |       0.6 |      1.0 | Drop latest records làm mất ground-truth document của một số câu hỏi |
| `mean_token_f1`      |      0.8 |    0.1923 |      0.8 | Blank/noise/truncate làm câu trả lời thiếu hoặc sai nội dung |
| `judge_accuracy`     |      0.8 |       0.2 |      0.8 | Judge phản ánh rõ việc agent trả lời sai sau corruption |
| `mean_judge_score`   |      4.2 |       1.6 |      4.2 | Repair phục hồi điểm judge về baseline |
| Quality checks         |     Pass |      Fail |     Pass | Corrupted fail ở duplicate `paper_id` và summary rỗng/ngắn |
| Freshness status       |    Fresh |     Fresh |    Fresh | Có stale rows tăng nhưng chưa vượt ngưỡng stale ratio `0.25` |

### Kết luận từ số liệu

1. Drop latest records, blank summary, truncate title và duplicate rows tạo dữ liệu thiếu/sai/trùng → Quality Gate fail unique/summary length và retrieval mất ground truth → hit rate giảm còn `0.6`, Token F1 còn `0.1923`.
2. Repair rebuild từ raw records → clean/repaired trở lại 22 rows hợp lệ, Quality Gate pass và freshness fresh → hit rate và Token F1 quay về mức baseline.

Corruption ảnh hưởng rõ nhất là `drop_latest_records` vì nó xóa hẳn document đúng khỏi corpus, làm retrieval không thể tìm thấy ground-truth dù câu hỏi không đổi. `blank_summary` cũng tác động mạnh đến answer quality vì agent có thể lấy đúng document nhưng không còn nội dung để trả lời.

Kết quả khác kỳ vọng là corrupted freshness vẫn `Fresh`. Nguyên nhân là stale rows có tăng nhưng stale ratio chưa vượt ngưỡng `0.25`; vì vậy freshness nên được đọc như tín hiệu vận hành, còn Quality Gate chịu trách nhiệm chặn lỗi cấu trúc rõ ràng.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Corruption phải deterministic thì mới so sánh baseline/corrupted/repaired một cách công bằng.
2. Quality Gate và metrics RAG bổ sung cho nhau: quality bắt lỗi dữ liệu, còn retrieval/Token F1/judge cho thấy tác động lên agent.
3. Repair đáng tin cậy nhất là rebuild từ raw source, không vá từng dòng đã hỏng.

### Nếu có thêm thời gian

Tôi sẽ bổ sung phân tích tác động riêng cho từng corruption scenario, ví dụ chạy ablation từng lỗi một rồi ghi metric delta. Cách đo là tạo 6 corrupted datasets riêng, đánh giá trên cùng test set và so sánh scenario nào làm giảm hit rate, Token F1 hoặc judge score nhiều nhất.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Trọng Huy
**Ngày xác nhận:** 2026-09-25
