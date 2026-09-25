# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Cảnh Duy |
| MSSV               | 2A202602815 |
| Khóa/Lớp         | K4 |
| Tên nhóm         | MultiPerson |
| Vai trò chính    | Pipeline end-to-end: ingestion, cleaning, evaluation set, observability, corruption/repair và tích hợp |
| Repository         | https://github.com/nvchien19/K4-L3A-Day10-MultiPerson-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ---------- |
| Raw ingestion | `src/ingestion/crossref.py`: `parse_crossref_payload`, `fetch_source_records`, `load_raw_records` | Crossref `/works` hoặc snapshot `data/raw/crossref_response.json` | `data/raw/crossref_records.json` (24 records) | Hoàn thành |
| Cleaning & data model | `src/ingestion/cleaning.py`: `build_clean_dataframe`, `build_text_for_embedding`, `save_clean_dataframe` | List `PaperRecord`, `run_date` | `data/clean/papers_clean.{csv,json}` (24 dòng, 16 cột) | Hoàn thành |
| Evaluation set | `src/evaluation/testset.py`: `build_test_set` | Clean dataframe | `data/eval/test_set.json` (10 câu, 4 dạng) | Hoàn thành |
| Quality & freshness | `src/observability/quality.py`: `run_data_quality_checks`, `build_freshness_report` | Dataframe của từng trạng thái | `data/quality/*_quality_report.json`, `*freshness_report.json` | Hoàn thành |
| Reporting | `src/observability/reporting.py`: `generate_phase1_report`, `generate_corruption_report` | Metrics, quality, freshness, corruption log | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Hoàn thành |
| Corruption | `src/ingestion/corruption.py`: `corrupt_clean_dataframe` | Clean dataframe | `data/results/corruption_log.json`, `data/clean/papers_clean_corrupted.*` | Hoàn thành |
| Orchestration | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` | Toàn bộ module trên | Metrics/answers 3 trạng thái, 3 Chroma collections | Hoàn thành |
| LLM provider DeepSeek | `src/core/config.py`, `src/retrieval/llm.py` (`ChatDeepSeek`) | `DEEPSEEK_API_KEY/MODEL/BASE_URL` trong `.env` | LLM judge và agent demo chạy bằng `deepseek-chat` | Hoàn thành |
| Ragas | `evaluation/metrics.py` (có sẵn) | `RUN_RAGAS=1` | — | Chưa chạy (tùy chọn, chưa bật) |

Tôi phụ trách toàn bộ các khối trên. Tôi thực hiện cùng trợ lý AI (Claude Code) theo đúng chính sách AI trong `docs/RULES.md`. Mọi thay đổi đều được tôi chạy lại, đối chiếu với artifact và có thể giải thích (xem mục 4–7).

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ----------------------------- | ------- |
| Viết tài liệu giải thích quá trình thực hiện | Cả nhóm | `GIAI_THICH_THUC_HIEN.md` mô tả kiến trúc, quyết định thiết kế và cách tái hiện |
| Kiểm chứng chế độ Live API trên bản sao tạm | `crossref.py` | `REFRESH_SOURCE=1` lấy được 24 bài thật, snapshot của repo không bị ghi đè |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------- | --------------------------- | ---------------- | ------------- |
| Parse Crossref, bỏ thẻ JATS, retry 429/5xx, fallback offline | `crossref.py` | 24 records | Output giống 100% file `crossref_records.json` gốc; checksum `crossref_response.json` giữ nguyên |
| Clean, dedupe theo `paper_id`, tính `age_days`, ghép `text_for_embedding` | `cleaning.py` | 24 dòng sạch | Lệnh CP1 in `Clean thành công 24 dòng` |
| Quality Gate GX 1.x (7 expectations) + Freshness SLA | `quality.py` | Baseline PASS 7/7, `is_fresh=True` (1/24 stale) | `data/quality/baseline_quality_report.json`, `freshness_report.json` |
| Bộ đề 10 câu deterministic | `testset.py` | summary 3, authors 3, date 2, categories 2 | Lệnh CP2 in `Sinh được 10 câu hỏi test`; hash không đổi qua các lần chạy |
| Tiêm 6 lỗi có kiểm soát (seed 42) | `corruption.py` | 24 → 22 dòng, log đủ 6 loại | `data/results/corruption_log.json` |
| Repair từ raw + đối chiếu 3 trạng thái | `corruption_flow.py`, `reporting.py` | `corruption_report.md` | Exit code 0; `repaired_matches_baseline=True`, `repair_is_idempotent=True` |
| Tích hợp DeepSeek | `config.py`, `llm.py` | 30/30 lượt chấm do LLM thực hiện, agent demo `status: ok` | `data/results/*_answers.json` (không có reasoning "Fallback heuristic"), `agent_demo_answers.json` |

Một output cụ thể do phần việc của tôi tạo ra: bảng so sánh trong `data/reports/corruption_report.md`. Bảng cho thấy trên dữ liệu lỗi hit rate giảm 1.00 → 0.90 và token F1 giảm 1.00 → 0.70, còn sau khi repair cả hai trở về 1.00. Quality Gate chuyển PASS 7/7 → FAIL 4/7 → PASS 7/7.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Một hệ thống RAG không báo lỗi khi dữ liệu hỏng: agent vẫn trả lời trơn tru nhưng sai (silent failure). Phần của tôi phải (1) đưa dữ liệu Crossref vào vector store một cách có kiểm soát, (2) chặn dữ liệu xấu bằng Quality Gate trước khi index, (3) chứng minh bằng số liệu rằng corruption làm agent sai và repair từ raw khôi phục được.

### Cách triển khai

- **Ingestion dual-mode:** mặc định đọc snapshot offline để lab không phụ thuộc mạng. `REFRESH_SOURCE=1` gọi API với retry có backoff (tôn trọng `Retry-After`), ghi nguyên văn `response.text` để bảo toàn raw, lỗi thì fallback về snapshot.
- **Cleaning:** `run_date` được truyền từ ngoài vào để Baseline/Corrupted/Repaired tính `age_days` trên cùng một mốc (flow đọc lại `run_date` từ `freshness_report.json`). Tôi dedupe theo `paper_id` không phân biệt hoa thường vì DOI không phân biệt hoa thường, và sort ổn định (`published` giảm dần, `paper_id` tăng dần) để chạy lại cho cùng thứ tự.
- **Quality Gate:** GX 1.x ephemeral context (`get_context(mode="ephemeral")`, `data_sources.add_pandas`, `add_batch_definition_whole_dataframe`). Gồm 4 expectation bắt buộc (row count 5–5000; not-null `paper_id/title/text_for_embedding`; unique `paper_id`; `summary` ≥ 30 ký tự), thêm `title` ≥ 8 ký tự để bắt lỗi cắt tiêu đề.
- **Test set:** chọn 10 bài cách đều sau khi sort theo `paper_id`, câu hỏi theo đúng mẫu mà `retrieval/qa.py` nhận diện.
- **Corruption:** thao tác trên bản sao, mỗi lỗi đánh vào một nhóm dòng riêng, rebuild `text_for_embedding` sau khi tiêm để vector phản ánh đúng dữ liệu lỗi.
- **Repair:** đọc lại `data/raw/crossref_records.json` và clean lại, không vá dataframe lỗi. Chạy repair hai lần và so hash nội dung để chứng minh idempotent.

### Input, output và contract

| Thành phần | Mô tả |
| ---------- | ----- |
| Input | `data/raw/crossref_response.json` (Crossref `message.items`), `.env` (provider/model/key) |
| Output | Clean schema 16 cột (`paper_id, title, summary, authors, categories, primary_category, published, updated, abs_url, pdf_url, comment, authors_joined, categories_joined, summary_chars, age_days, text_for_embedding`); metrics JSON; quality/freshness JSON; 2 báo cáo Markdown |
| Module phụ thuộc | `core/config.py`, `core/utils.py`, `retrieval/index.py`, `retrieval/qa.py`, `evaluation/metrics.py` |
| Module sử dụng output | `retrieval/index.py` cần `paper_id, title, text_for_embedding, published, authors_joined, categories_joined, summary, abs_url, pdf_url`; `qa.py` cần title nằm trong `'...'` của câu hỏi |
| Điều kiện lỗi cần xử lý | API 429/5xx hoặc mất mạng; record thiếu DOI/title/abstract/ngày; DOI trùng; baseline gate fail (dừng, không index); thiếu artifact baseline khi chạy corruption flow; LLM không hỗ trợ `json_schema` |

### Cách xác minh

```bash
.venv/Scripts/python -m compileall -q src
.venv/Scripts/python script/run_phase1.py
.venv/Scripts/python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** cả hai lệnh exit 0; baseline gate PASS; corrupted gate FAIL và `is_fresh=False`; repaired trở về như baseline.
- **Kết quả thực tế:** như mong đợi, provider `deepseek`, `run_date=2026-09-25T08:47:44Z`. Chạy lại lần hai cho metrics, corruption log và test set giống hệt; Chroma chỉ có `papers-baseline=24`, `papers-corrupted=22`, `papers-repaired=24`.
- **Artifact/log:** `data/results/`, `data/quality/`, `data/reports/`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Freshness SLA (stale > 180 ngày, tối đa 25%) nên chặn cứng việc index hay chỉ cảnh báo?
- **Các phương án đã cân nhắc:** (A) đưa freshness vào GX suite như một expectation chặn index; (B) giữ Quality Gate cho các lỗi cấu trúc (volume, null, unique, độ dài), còn freshness là báo cáo riêng, chỉ cảnh báo.
- **Phương án đã chọn:** B.
- **Lý do:** snapshot offline cố định tự "già" theo thời gian. Với dữ liệu hiện tại, từ khoảng 2026-11-29 sẽ có hơn 25% bài quá 180 ngày. Nếu chặn cứng thì baseline sẽ không chạy được nữa dù dữ liệu không hề hỏng. Dữ liệu cũ vẫn đúng, chỉ cần làm mới, nên đây là tín hiệu vận hành chứ không phải lỗi dữ liệu. Ngược lại, dữ liệu trùng hoặc rỗng thì không bao giờ nên vào index.
- **Bằng chứng quyết định phù hợp:** trên dữ liệu lỗi, hai tầng bổ trợ nhau. Gate bắt `duplicate_rows` (6 dòng không unique), `truncate_title` (3) và `blank_summary` (3). Freshness bắt `stale_date` + `drop_latest_records` (stale 9/22 = 40.9%, bài mới nhất lùi từ 2026-07-22 về 2026-06-12). Trong khi đó baseline vẫn chạy ổn định.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** khi chuyển sang DeepSeek, gọi `llm.with_structured_output(JudgeVerdict)` trả về `Error code: 400 - {'error': {'message': 'This response_format type is unavailable now', 'type': 'invalid_request_error', ...}}`.
- **Lệnh hoặc bước tái hiện:** `LLM_PROVIDER=deepseek`, gọi `build_llm(settings).with_structured_output(JudgeVerdict).invoke(...)`.
- **Nguyên nhân gốc:** `langchain-openai` 1.x mặc định dùng `response_format={"type": "json_schema"}` cho structured output, còn API DeepSeek không hỗ trợ kiểu này. Nguy hiểm hơn: `_judge_answer` trong `metrics.py` bắt mọi exception và âm thầm chuyển sang heuristic. Pipeline vẫn "chạy thành công" nhưng judge không hề là LLM, đúng kiểu silent failure mà bài lab cảnh báo.
- **Cách xử lý:** thêm lớp `ChatDeepSeek(ChatOpenAI)` trong `src/retrieval/llm.py`, mặc định `method="function_calling"` khi gọi `with_structured_output` (DeepSeek hỗ trợ tool calling). Thêm provider `deepseek` vào `core/config.py`, đọc `DEEPSEEK_API_KEY`/`DEEPSEEK_BASE_URL`.
- **Cách xác minh sau khi sửa:** judge trả về `score=5, correct=True` cho câu đúng và `score=1, correct=False` cho câu sai, kèm reasoning riêng. Sau khi chạy lại cả hai pipeline, 30/30 lượt chấm trong `*_answers.json` không có reasoning "Fallback heuristic judge used…".
- **Điều học được:** một cơ chế fallback "an toàn" có thể che mất lỗi cấu hình. Muốn biết LLM có thực sự được dùng thì phải kiểm tra artifact, không chỉ nhìn exit code.

## 7. Hiểu biết về luồng end-to-end

1. **Từ Crossref đến vector index:** response `/works` được lưu nguyên văn vào `data/raw/`, rồi parse thành `PaperRecord` và clean thành dataframe có `text_for_embedding` (Title/Authors/Published/Categories/Summary). Dataframe qua Quality Gate, sau đó `all-MiniLM-L6-v2` nhúng từng dòng (vector chuẩn hóa) và nạp vào ChromaDB collection `papers-baseline` với metric cosine, kèm metadata để trả lời.
2. **Evaluation set và ground-truth doc IDs:** mỗi câu có `ground_truth` (giá trị đúng) và `ground_truth_doc_ids` (DOI). `retrieval_hit_rate` đo xem DOI đúng có nằm trong top-k = 4 hay không. `mean_token_f1` đo mức trùng từ giữa câu trả lời và ground truth. LLM judge (DeepSeek) chấm mức đúng về nghĩa.
3. **Quality checks khác freshness:** quality checks kiểm tra tính hợp lệ về cấu trúc của từng batch (số dòng, null, trùng, độ dài) và thất bại thì chặn index. Freshness đo độ mới theo thời gian (`age_days`, bài mới nhất, tỷ lệ stale) và chỉ là tín hiệu cần làm mới nguồn.
4. **Vì sao dùng cùng test set:** để chênh lệch metric chỉ đến từ dữ liệu. Nếu đổi câu hỏi thì không biết điểm giảm là do corruption hay do đề khác. Test set được giữ cố định (hash `5d5142066aa8f2e9…` không đổi) và chỉ sinh lại khi `REFRESH_TEST_SET=1` hoặc khi DOI không còn trong dữ liệu.
5. **Repair thành công dựa trên:** `repaired_metrics.json` bằng baseline (1.0/1.0/1.0/5), `repaired_quality_report.json` PASS 7/7, `repaired_freshness_report.json` `is_fresh=True`, `repaired_matches_baseline=True` và `repair_is_idempotent=True` trong `corruption_report.md`.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ------------- | -------: | --------: | -------: | -------------------- |
| `retrieval_hit_rate` | 1.0000 | 0.9000 | 1.0000 | Chỉ eval_002 miss vì bài gốc (…1804) bị `drop_latest_records` |
| `mean_token_f1` | 1.0000 | 0.7000 | 1.0000 | 3 câu F1 = 0: hai summary rỗng, một categories sai |
| `judge_accuracy` (DeepSeek) | 1.0000 | 0.7000 | 1.0000 | Judge đồng ý với F1 ở cả 10 câu |
| `mean_judge_score` (DeepSeek) | 5.0 | 3.8 | 5.0 | 7 câu × 5 điểm + 3 câu × 1 điểm |
| Quality checks | PASS 7/7 | FAIL 4/7 | PASS 7/7 | Fail: unique `paper_id`, độ dài `title`, độ dài `summary` |
| Freshness status | Fresh (1/24 stale) | Stale (9/22 = 40.9%) | Fresh (1/24 stale) | Vượt SLA 25% do lùi ngày + mất bài mới |

### Kết luận từ số liệu

1. `blank_summary` (3 dòng, trong đó có …1801 và …1811) → GX `expect_column_value_lengths_to_be_between[summary]` fail (3 dòng) → eval_001 và eval_005 trả về chuỗi rỗng, F1 = 0, judge = 1.
2. `truncate_title` (…1819 thành `Advanc`) → GX `title` fail (3 dòng) → `qa.py` không còn tra cứu chính xác theo title, semantic search đưa …1814 lên top-1 → eval_008 trả lời sai categories (`Software Engineering, Data Systems`).
3. Repair từ raw → gate PASS 7/7 và `is_fresh=True` → cả 4 metric trở về đúng giá trị baseline.

**Corruption ảnh hưởng rõ nhất:** `blank_summary`, vì nó làm hỏng 2/3 câu hỏi dạng summary và agent vẫn "trả lời" (chuỗi rỗng) mà không có lỗi nào.

**Kết quả khác kỳ vọng:**

- **eval_002:** retrieval miss (bài …1804 đã bị xóa) nhưng câu trả lời vẫn đúng và DeepSeek chấm 5/5. Bài "Advanced Perspectives on Freshness SLAs…" (…1816) có cùng tác giả `Bao Do, Linh Ngo`. Đây là đáp án đúng nhưng lấy từ sai nguồn: chỉ nhìn F1 hay judge thì không thấy lỗi, phải xem thêm `retrieval_hit_rate`.
- **`stale_date` và `inject_noise` không làm giảm metric.** Tôi kiểm tra `corruption_log.json` so với test set: các bài bị lùi ngày (…1805, 1809, 1814, 1815, 1822, 1823) không có câu hỏi dạng `date`; các bài bị chèn nhiễu (…1806, 1816, 1820) không có câu hỏi dạng `summary`. Tác động của chúng chỉ hiện ở Freshness.
- **`inject_noise` lọt qua Quality Gate** vì summary rác vẫn không null và đủ 30 ký tự.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data pipeline:** giữ raw nguyên văn và repair bằng cách chạy lại từ raw (không vá dữ liệu lỗi) giúp phục hồi idempotent. Chạy bao nhiêu lần cũng ra cùng một dataset (hash trùng baseline).
2. **Data quality/observability:** Quality Gate và Freshness bổ trợ nhau, mỗi tầng bắt một nhóm lỗi khác. Nhưng có lỗi lọt cả hai (noise), và fallback trong code cũng có thể che lỗi (sự cố DeepSeek ở mục 6).
3. **Ảnh hưởng của data đến RAG agent:** agent không bao giờ báo lỗi khi dữ liệu hỏng. Nó trả lời tự tin với dữ liệu rỗng, tài liệu sai, hoặc đúng đáp án nhưng sai nguồn. Chỉ số liệu đo lường mới lộ ra vấn đề.

### Nếu có thêm thời gian

Tôi sẽ thêm một expectation phát hiện nhiễu cho `summary`, ví dụ `ExpectColumnValuesToMatchRegex` yêu cầu tỷ lệ ký tự chữ cái tối thiểu hoặc cấm chuỗi `@@NOISE@@`/ký tự điều khiển. Cách đo: chạy lại corruption flow, kỳ vọng `failed_expectations` có thêm check mới với `unexpected_count = 3` (đúng 3 dòng `inject_noise`) mà baseline vẫn PASS. Thêm vào đó, tôi sẽ để test set cố ý phủ các bài bị lùi ngày, để đo được tác động của `stale_date` lên câu hỏi dạng `date`.

## 10. Cam kết của thành viên

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [ ] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Cảnh Duy
**Ngày xác nhận:** 2026-09-25
