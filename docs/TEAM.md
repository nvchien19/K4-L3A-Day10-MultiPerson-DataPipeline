# Danh Sách Thành Viên & Phân Công Công Việc

- Tên Nhóm: `[Điền tên nhóm]`
- Mã Nhóm / Lớp: `K4-L3-DAY10`
- Tên Repository Nộp Bài: `K4-L3-DAY10-TenNhom-DataPipeline`
- Ngày cập nhật phân công: `[Điền ngày]`

> Mỗi người sở hữu một phần deliverable chính, có input/output và cách xác minh rõ ràng. Các phần liên quan vẫn được review chéo trước khi tích hợp. Phần việc dưới đây là phạm vi được giao; chỉ đánh dấu hoàn thành sau khi có code và artifact thực tế.

---

## 1. Danh sách thành viên

| STT | Họ và tên        | MSSV          | Email          | Vai trò chính                               | Báo cáo cá nhân                          |
| --: | ---------------- | ------------- | -------------- | ------------------------------------------- | ---------------------------------------- |
|   1 | Nguyễn Hồ Nam    | `2A202602788` | `[Điền email]` | Trưởng nhóm & Pipeline Integration/Evidence | `report/2A202602788_Nguyen_Ho_Nam.md`    |
|   2 | Nguyễn Văn Chiến | `2A202602926` | `[Điền email]` | Raw Ingestion & Data Lineage                | `report/2A202602926_Nguyen_Van_Chien.md` |
|   3 | Vũ Văn Hà        | `2A202602589` | `[Điền email]` | Data Modeling & Vector Index                | `report/2A202602589_Vu_Van_Ha.md`        |
|   4 | Nguyễn Cảnh Duy  | `2A202602815` | `[Điền email]` | Data Observability & Evaluation             | `report/2A202602815_Nguyen_Canh_Duy.md`  |
|   5 | Nguyễn Trọng Huy | `2A202602379` | `[Điền email]` | Corruption, RAG Agent & Repair              | `report/2A202602379_Nguyen_Trong_Huy.md` |

---

## 2. Quy tắc phối hợp

- Owner chịu trách nhiệm chính cho file/deliverable được giao; người hỗ trợ review nhưng không tự ý thay đổi contract mà không thông báo.
- Không hard-code đường dẫn, tên collection, model hoặc secret. Dùng `src/core/config.py` và `src/core/utils.py`.
- Không sửa cùng một hàm song song. Trước khi đổi chữ ký hàm hoặc schema, thống nhết trong nhóm và cập nhật các module phụ thuộc.
- Mỗi thay đổi phải kèm lệnh kiểm tra hoặc artifact có thể tái hiện.
- Mỗi thành viên tự tạo báo cáo cá nhân theo mẫu `report/individual_report.md`; không sao chép nguyên văn báo cáo của nhau.
- Không commit `.env`, API key, token hoặc log chứa secret.
- Mỗi thành viên cần có commit thực tế trên nhánh `main`; kiểm tra Contributors trước khi nộp.

---

## 3. Ma trận phân công theo deliverable

| Deliverable               | Owner chính      | Hỗ trợ/review                      | Input                         | Output bắt buộc                                            | Cách xác minh                                        |
| ------------------------- | ---------------- | ---------------------------------- | ----------------------------- | ---------------------------------------------------------- | ---------------------------------------------------- |
| Raw ingestion và lineage  | Nguyễn Văn Chiến | Nguyễn Hồ Nam                      | Crossref response/snapshot    | `data/raw/crossref_response.json`, `crossref_records.json` | Đếm record, kiểm tra fallback offline                |
| Cleaning và data model    | Vũ Văn Hà        | Nguyễn Văn Chiến, Nguyễn Cảnh Duy  | `PaperRecord`                 | Clean CSV/JSON, schema, `text_for_embedding`               | Chạy cleaning, kiểm tra 24 dòng và `paper_id` unique |
| Embedding và ChromaDB     | Vũ Văn Hà        | Nguyễn Trọng Huy, Nguyễn Hồ Nam    | Clean dataframe               | Index `papers-baseline`, manifest embeddings               | Kiểm tra collection và số document                   |
| Quality Gate và Freshness | Nguyễn Cảnh Duy  | Vũ Văn Hà, Nguyễn Hồ Nam           | Clean/corrupted dataframe     | Quality/freshness JSON                                     | Kiểm tra `success`, expectation và ngưỡng stale      |
| Test set và metrics       | Nguyễn Cảnh Duy  | Vũ Văn Hà, Nguyễn Trọng Huy        | Clean dataframe, index        | `test_set.json`, metrics JSON                              | Kiểm tra 10 câu, đủ 4 loại, đánh giá cùng test set   |
| RAG Agent và QA           | Nguyễn Trọng Huy | Vũ Văn Hà                          | Collection, câu hỏi           | Smoke-test answers, agent demo                             | Chạy retrieval/QA trên từng collection               |
| Reporting                 | Nguyễn Cảnh Duy  | Nguyễn Hồ Nam, Nguyễn Trọng Huy    | Metrics, quality, freshness   | `phase1_report.md`, `corruption_report.md`                 | Đối chiếu report với JSON artifact                   |
| Baseline orchestration    | Nguyễn Hồ Nam    | Tất cả thành viên                  | Raw, clean, test set, modules | Baseline metrics và toàn bộ artifact Phase 1               | `python script/run_phase1.py`                        |
| Corruption suite          | Nguyễn Trọng Huy | Vũ Văn Hà, Nguyễn Cảnh Duy         | Clean dataframe               | Corruption log, corrupted data/index                       | Kiểm tra đủ 6 loại lỗi                               |
| Repair và comparison flow | Nguyễn Hồ Nam    | Nguyễn Trọng Huy, Nguyễn Văn Chiến | Raw, corrupted flow           | Repaired metrics, comparison report                        | `python script/run_corruption_flow.py` và chạy lặp   |

---

## 4. Kế hoạch triển khai theo checkpoint

| Checkpoint | Phụ trách chính                              | Việc cần hoàn thành                                                   | Đầu ra kiểm tra                                                      |
| ---------- | -------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------- |
| CP0        | Nguyễn Văn Chiến; Nguyễn Hồ Nam              | Môi trường, `.env` local, ingestion, retry và offline fallback        | Hai raw JSON, import smoke test thành công, đủ 24 record             |
| CP1        | Vũ Văn Hà; Nguyễn Cảnh Duy                   | Cleaning, schema, `age_days`, `text_for_embedding`, GX 1.x, freshness | Clean CSV/JSON và `success=True`                                     |
| CP2        | Vũ Văn Hà; Nguyễn Cảnh Duy; Nguyễn Trọng Huy | Test set, MiniLM, Chroma baseline, QA smoke test                      | 10 câu hỏi, collection `papers-baseline` có 24 document              |
| CP3        | Nguyễn Hồ Nam                                | Nối baseline end-to-end, lưu metrics và báo cáo                       | `baseline_metrics.json`, `phase1_report.md`, exit code `0`           |
| CP4        | Nguyễn Trọng Huy; Nguyễn Cảnh Duy            | Corruption, quality signal, re-index, evaluation trên dữ liệu lỗi     | Log đủ 6 lỗi, corrupted metrics, quality/freshness cảnh báo          |
| CP5        | Nguyễn Hồ Nam; Nguyễn Trọng Huy              | Repair từ raw, đánh giá lại, so sánh ba trạng thái                    | Repaired metrics và `corruption_report.md`                           |
| CP6        | Tất cả                                       | Demo, Q&A, kiểm tra contributors, nộp LMS                             | Demo thành công, mọi thành viên có commit trên `main` và tự nộp link |

---

## 5. Phần việc chi tiết

### Nguyễn Hồ Nam — `2A202602788`

- Vai trò: Trưởng nhóm, điều phối tích hợp và kiểm chứng end-to-end.
- File/deliverable sở hữu: `src/core/config.py`, `src/core/utils.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`.
- Nhiệm vụ:
  - Thống nhất path, settings, collection name và data contract trước khi các nhánh module được giao.
  - Nối baseline flow từ raw đến report và không nạp index khi Quality Gate fail.
  - Nối corruption flow, đảm bảo repair luôn bắt đầu từ raw và tạo lại collection có kiểm soát.
  - Chạy lại toàn bộ flow, đối chiếu metrics/report và lập bằng chứng cho nhóm.
  - Tổng hợp lịch trình, merge, xử lý conflict và chuẩn bị bản nộp cuối.
- Kiểm tra được giao:
  - [ ] `python -m compileall src`.
  - [ ] `python script/run_phase1.py` chạy thành công.
  - [ ] `python script/run_corruption_flow.py` chạy thành công.
  - [ ] Baseline/Corrupted/Repaired dùng cùng test set.
  - [ ] Không có path tuyệt đối và không có secret.
- Đóng góp cần ghi trong báo cáo cá nhân: Quyết định thiết kế orchestration, idempotency, cách xử lý blocker tích hợp và kết quả chạy thực tế.

### Nguyễn Văn Chiến — `2A202602926`

- Vai trò: Raw Ingestion, Data Lineage và nguồn dữ liệu cho Repair.
- File/deliverable sở hữu: `src/ingestion/crossref.py`; các raw artifact trong `data/raw/`.
- Nhiệm vụ:
  - Hoàn thiện `parse_crossref_payload()` và `load_raw_records()`.
  - Hoàn thiện `fetch_source_records()` với query/filter, retry `429/503`, timeout và lưu raw response.
  - Bảo toàn raw response trước khi biến đổi; bảo đảm snapshot offline được dùng khi Live API lỗi.
  - Chuẩn hóa `PaperRecord`, loại bỏ record không hợp lệ và kiểm tra đủ 24 record.
  - Hỗ trợ Huy/Nam xác minh repair luôn dùng raw artifact.
- Kiểm tra được giao:
  - [ ] Chạy lệnh fetch và nhận `Đã tải 24 bài báo`.
  - [ ] Hai file raw tồn tại, đọc được và không bị sửa sau khi lưu.
  - [ ] Tắt mạng/snapshot giả lập vẫn load được dữ liệu qua fallback.
  - [ ] Record có `paper_id` ổn định và đủ trường cần cho cleaning.
- Đóng góp cần ghi trong báo cáo cá nhân: Cách bảo toàn lineage, xử lý retry/fallback và lý do repair phải lấy từ raw.

### Vũ Văn Hà — `2A202602589`

- Vai trò: Data Modeling, Embedding và Vector Store.
- File/deliverable sở hữu: `src/ingestion/cleaning.py`, `src/retrieval/embeddings.py`, `src/retrieval/index.py`.
- Nhiệm vụ:
  - Chuẩn hóa text, loại HTML/XML/JATS, parse ngày và tính `age_days`.
  - Tạo `authors_joined`, `categories_joined`, `summary_chars` và `text_for_embedding` đúng format.
  - Lọc record lỗi, khử trùng lặp theo `paper_id` và lưu CSV/JSON ổn định.
  - Tích hợp MiniLM `all-MiniLM-L6-v2` và metadata cần thiết.
  - Quản lý collection `papers-baseline`; hỗ trợ tạo lại collection corrupted/repaired.
- Kiểm tra được giao:
  - [ ] Clean dataframe đạt 24 dòng trong bộ dữ liệu chuẩn.
  - [ ] `paper_id`, `age_days`, `text_for_embedding` hợp lệ.
  - [ ] Không có `paper_id` trùng và embedding manifest được tạo.
  - [ ] Collection có đúng tên và đúng số document.
- Đóng góp cần ghi trong báo cáo cá nhân: Quy tắc cleaning, data contract, lựa chọn metadata và cách tái tạo index.

### Nguyễn Cảnh Duy — `2A202602815`

- Vai trò: Data Observability, Benchmark Evaluation và Reporting.
- File/deliverable sở hữu: `src/observability/quality.py`, `src/evaluation/testset.py`, `src/evaluation/metrics.py`, `src/observability/reporting.py`.
- Nhiệm vụ:
  - Dùng đúng API Great Expectations 1.x và bốn expectation bắt buộc.
  - Tính Freshness SLA theo `age_days > 180` và ngưỡng stale 25%.
  - Sinh 10 câu hỏi deterministic, đủ bốn `question_type` và có `ground_truth_doc_ids`.
  - Tổng hợp Hit Rate, Token F1 và metrics hợp lệ cho ba trạng thái.
  - Sinh báo cáo Baseline và bảng đối chiếu Baseline/Corrupted/Repaired từ artifact thật.
- Kiểm tra được giao:
  - [ ] Baseline Quality Gate trả `success=True`.
  - [ ] Corrupted quality/freshness phát hiện lỗi dự kiến.
  - [ ] Test set có đúng 10 câu và đủ 4 loại.
  - [ ] Mọi metric trong report khớp file JSON.
- Đóng góp cần ghi trong báo cáo cá nhân: Cách chọn quality dimensions, xây evaluation set và diễn giải sự suy giảm/phục hồi.

### Nguyễn Trọng Huy — `2A202602379`

- Vai trò: Data Corruption, RAG Agent và kiểm chứng Repair.
- File/deliverable sở hữu: `src/ingestion/corruption.py`; hỗ trợ trực tiếp `src/retrieval/qa.py`, `src/retrieval/agent.py`, `src/retrieval/llm.py`.
- Nhiệm vụ:
  - Tiêm đủ sáu corruption: mất record mới, blank summary, noise, truncate title, stale date và duplicate rows.
  - Rebuild `text_for_embedding` và `age_days`, ghi log chi tiết từng thay đổi.
  - Kiểm tra retrieval/QA trên collection baseline, corrupted và repaired.
  - Phối hợp với Chiến/Nam để repair từ raw, không lấy corrupted data làm nguồn.
  - Smoke-test agent bằng câu hỏi thuộc cả bốn loại.
- Kiểm tra được giao:
  - [ ] `corruption_log.json` có đủ sáu loại lỗi.
  - [ ] Corrupted metrics thể hiện suy giảm thực tế.
  - [ ] Repaired index không chứa dữ liệu lỗi ngoài dữ liệu hợp lệ từ raw.
  - [ ] Agent không trả lời sai một cách không có kiểm soát khi context bị hỏng.
- Đóng góp cần ghi trong báo cáo cá nhân: Thiết kế corruption, ảnh hưởng đến retrieval/answer, bằng chứng repair và blocker đã xử lý.

---

## 6. Lịch handoff nội bộ

1. Trước khi code song song: Nam công bố data contract, path và tên collection; tất cả xác nhận đầu vào/đầu ra.
2. Sau CP0: Chiến bàn giao raw schema cho Hà; Hà chốt clean schema cho Duy và Huy.
3. Sau CP1: Duy bàn giao quality contract; Hà bàn giao text/metadata contract cho retrieval.
4. Sau CP2: Duy cung cấp test set cố định; Huy và Hà dùng đúng test set này cho mọi metrics.
5. Trước CP3: Mỗi owner tự kiểm tra output; Nam chỉ merge khi các artifact tương ứng đã tồn tại.
6. Trước CP5: Chiến xác nhận raw còn nguyên; Huy xác nhận repair chỉ dùng raw; Duy xác nhận report có số liệu khớp JSON.
7. Trước CP6: Tất cả cập nhật báo cáo cá nhân, commit lên `main`, kiểm tra Contributors và tự nộp link LMS.

---

## 7. Definition of Done

- [ ] Mỗi thành viên có commit thực tế và báo cáo cá nhân đúng vai trò.
- [ ] Hai entrypoint chạy với exit code `0`.
- [ ] Raw, clean, eval, index, quality, metrics và report artifacts tồn tại.
- [ ] Baseline quality pass; Corrupted quality/freshness có tín hiệu lỗi; Repaired phục hồi hợp lệ.
- [ ] Báo cáo không bịa số liệu và số liệu khớp artifact.
- [ ] Không có `.env`, API key, token, path tuyệt đối hoặc log secret.
- [ ] Tất cả thành viên xuất hiện trong Contributors của nhánh `main`.
- [ ] Từng thành viên tự nộp link repository lên VLearn LMS.

## 8. Báo cáo cá nhân

Mỗi người tạo file theo tên trong bảng thành viên, dựa trên `report/individual_report.md`. Báo cáo phải nêu rõ:

- phần đã hoàn thành và phần đang thử nghiệm;
- input/output của module mình sở hữu;
- artifact hoặc metric chứng minh kết luận;
- một lỗi/blocker đã xử lý;
- khả năng giải thích luồng end-to-end;
- phần hỗ trợ các thành viên khác.
