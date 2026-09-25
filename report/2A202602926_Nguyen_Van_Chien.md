# Member Role Report — Nguyễn Văn Chiến

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Văn Chiến             |
| MSSV               | 2A202602926                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | MultiPerson     |
| Vai trò chính    | Raw Ingestion & Data Lineage                 |
| Repository         | https://github.com/nvchien19/K4-L3A-Day10-MultiPerson-DataPipeline.git |
| Ngày hoàn thành | 2026-09-25               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Raw ingestion từ Crossref | `src/ingestion/crossref.py`: `parse_crossref_payload`, `fetch_source_records`, `load_raw_records` | Crossref response/snapshot, query/filter, `max_results=24` | `data/raw/crossref_response.json` có 24 items; `data/raw/crossref_records.json` có 24 records | Hoàn thành |
| Nguồn dữ liệu cho Repair | `load_raw_records` dùng trong `src/pipelines/corruption_flow.py` | Raw records đã bảo toàn | Repair rebuild từ raw, tạo 22 repaired rows | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Kiểm tra contract raw → clean | Vũ Văn Hà / `src/ingestion/cleaning.py` | Xác định 2 raw records bị loại do ngày thiếu ngày, clean còn 22 rows |
| Kiểm tra nguồn repair | Nguyễn Hồ Nam, Nguyễn Trọng Huy / `src/pipelines/corruption_flow.py` | Repair dùng raw records, không dùng corrupted dataframe |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Parse payload Crossref và chuẩn hóa `PaperRecord` | `src/ingestion/crossref.py`, `data/raw/crossref_records.json` | 24 records có `paper_id`, title, summary, authors, categories, published/updated, URL | Đếm JSON và kiểm tra schema |
| Fetch có retry và fallback snapshot | `src/ingestion/crossref.py`, `data/raw/crossref_response.json` | Giữ nguyên response 24 items, không phụ thuộc mạng khi đã có snapshot | Chạy Baseline ở chế độ snapshot |
| Bảo toàn lineage cho repair | `data/raw/crossref_records.json`, `data/clean/papers_clean_repaired.json` | Repaired rows được rebuild từ raw, khớp Baseline | So sánh clean/repaired rows và metrics |

Output cụ thể nhất của tôi là cặp raw artifact: response gốc 24 items và 24 `PaperRecord`, làm đầu vào tin cậy cho cleaning, indexing, corruption và repair.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline cần một nguồn raw ổn định dù Crossref API có thể lỗi, giới hạn request hoặc trả dữ liệu thiếu trường. Nếu ingestion không bảo toàn raw, các bước cleaning, corruption và repair sẽ không còn căn cứ tin cậy để đối chiếu.

### Cách triển khai

Tôi triển khai ingestion theo nguyên tắc raw-first:

- Đọc `payload["message"]["items"]`.
- Lấy DOI, title, abstract, authors, subject, ngày, URL.
- Loại thẻ HTML/JATS trong title/abstract.
- Chuẩn hóa tác giả từ `given` + `family`.
- Ưu tiên ngày từ `published`, `published-online`, `published-print`, rồi `created`.
- Lấy PDF từ `link` nếu có `content-type=application/pdf`, nếu không dùng URL DOI.
- Bỏ record thiếu DOI, title, summary hoặc ngày hợp lệ.
- Gọi Crossref có retry cho `429/500/502/503/504`.
- Nếu đã có snapshot và không yêu cầu refresh, dùng snapshot để tái hiện.
- Nếu Live API lỗi nhưng snapshot tồn tại, fallback về snapshot.
- Luôn ghi response gốc trước khi ghi records đã parse.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Crossref JSON hoặc snapshot, query/filter, `max_results=24` |
| Output                         | `list[PaperRecord]` và 2 raw JSON |
| Module phụ thuộc             | `src/core/config.py`, `src/core/utils.py`                    |
| Module sử dụng output        | `src/ingestion/cleaning.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Mất mạng, HTTP 429/5xx, thiếu DOI/title/summary/ngày, abstract chứa JATS |

### Cách xác minh

```powershell
$env:LLM_PROVIDER='mock'
.\.venv\Scripts\python.exe script/run_phase1.py
.\.venv\Scripts\python.exe script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Raw 24 records, clean hợp lệ, Baseline pass, Corrupted suy giảm, Repaired phục hồi.
- **Kết quả thực tế:** Raw 24 records, clean 22 rows, Baseline/Repaired hit rate `1.0`, Corrupted hit rate `0.6`.
- **Artifact/log:** `data/raw/`, `data/clean/`, `data/results/`, `data/quality/`, `data/reports/`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Nên ưu tiên Live API hay snapshot khi chạy pipeline trong phòng lab.
- **Các phương án đã cân nhắc:** Luôn gọi Live API để lấy dữ liệu mới nhất; hoặc snapshot-first và chỉ refresh khi được yêu cầu.
- **Phương án đã chọn:** Snapshot-first, có retry và fallback.
- **Lý do:** Live API có thể bị `429`, mất mạng hoặc đổi dữ liệu giữa các lần chạy, làm Baseline/Corrupted/Repaired mất tính so sánh. Snapshot-first giữ reproducibility, còn refresh vẫn khả dụng khi cần dữ liệu mới.
- **Bằng chứng quyết định phù hợp:** Pipeline chạy ở requested mode snapshot, raw response/items được giữ nguyên, Baseline và Repaired cho cùng metrics.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Raw có 24 records nhưng clean chỉ còn 22 rows.
- **Lệnh hoặc bước tái hiện:** So sánh `data/raw/crossref_records.json` với `data/clean/papers_clean.json`.
- **Nguyên nhân gốc:** Hai record chỉ có ngày dạng `YYYY-MM`, không đủ ngày-tháng-ngày nên cleaning không parse được và loại khỏi index theo contract dữ liệu hợp lệ.
- **Cách xử lý:** Giữ nguyên raw để bảo toàn lineage, không cố sửa tay ngày thiếu; chỉ đưa 22 rows hợp lệ vào cleaning/index; ghi nhận chênh lệch trong báo cáo.
- **Cách xác minh sau khi sửa:** Raw 24, clean 22, Baseline Quality Gate pass, Repaired rebuild đúng 22 rows.
- **Điều học được:** Ingestion phải tách rõ bảo toàn nguồn và validation đầu vào; dữ liệu thiếu vẫn có giá trị lineage nhưng không nên vào serving/index.

## 7. Hiểu biết về luồng end-to-end

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Crossref response được parse thành `PaperRecord`, lưu raw, cleaning chuẩn hóa schema và tạo `text_for_embedding`, MiniLM tạo embedding, ChromaDB lưu collection Baseline.
2. Mỗi câu hỏi có đáp án chuẩn và `ground_truth_doc_ids`; retrieval đúng nếu ID chuẩn xuất hiện trong kết quả, câu trả lời được chấm bằng Token F1 và LLM Judge.
3. Quality checks kiểm tra tính toàn vẹn/schema hiện tại như null, unique, độ dài summary; freshness kiểm tra độ cũ theo `age_days` và tỷ lệ stale.
4. Cùng test set giúp chênh lệch metrics phản ánh đúng tác động của corruption/repair, không phải do đổi đề.
5. Repair thành công khi clean/repaired rows khớp Baseline, Quality Gate pass, freshness fresh và metrics trở lại mức Baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      1.0 |       0.6 |      1.0 | Mất 5 record mới làm 4 câu hỏi mất ground truth |
| `mean_token_f1`      |      0.8 |    0.1923 |      0.8 | Blank/noise/stale date làm đáp án sai nghiêm trọng |
| `judge_accuracy`     |      0.8 |       0.2 |      0.8 | Judge phản ánh suy giảm rõ hơn hit rate |
| `mean_judge_score`   |      4.2 |       1.6 |      4.2 | Repair khôi phục hoàn toàn điểm judge |
| Quality checks         |     Pass |      Fail |     Pass | Corrupted fail unique và summary length |
| Freshness status       |    Fresh |     Fresh |    Fresh | Corrupted có stale nhưng tỷ lệ chưa vượt ngưỡng |

### Kết luận từ số liệu

1. Drop latest records và blank/noise/stale date → Quality Gate fail unique/summary length và Freshness ghi stale rows → hit rate giảm còn `0.6`, Token F1 còn `0.1923`.
2. Repair rebuild từ raw records → Quality Gate pass, freshness fresh, metrics trở lại Baseline `1.0` hit rate và `0.8` Token F1.

Corruption ảnh hưởng rõ nhất là drop latest records vì nó xóa hẳn ground-truth documents của 4 câu hỏi, khiến retrieval không thể trúng dù embedding tốt.

Kết quả khác kỳ vọng ban đầu là corrupted freshness vẫn `Fresh` vì stale ratio chỉ khoảng `15.79%`, dưới ngưỡng `25%`. Tôi đã kiểm tra `repaired_freshness_report.json` và báo cáo đối chiếu trước khi kết luận.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Raw preservation là nền tảng của data lineage và repair đáng tin cậy.
2. Retry/fallback giúp pipeline tái hiện trong môi trường API không ổn định.
3. Dữ liệu xấu có thể làm agent trả lời sai mà không báo lỗi, nên Quality Gate phải chặn trước index.

### Nếu có thêm thời gian

Tôi sẽ bổ sung kiểm tra schema raw ngay sau ingestion, ví dụ cảnh báo record thiếu ngày đầy đủ trước khi cleaning loại bỏ. Cách đo là đếm raw invalid theo loại lỗi và kiểm tra Baseline không còn chênh lệch raw/clean ngoài dự kiến.

## 10. Cam kết của thành viên

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [ ] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Văn Chiến
**Ngày xác nhận:** 2026-09-25
