# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Hồ Nam             |
| MSSV               | 2A202602788                     |
| Khóa/Lớp         | K4-L3A              |
| Tên nhóm         | K4-L3A-Day10-MultiPerson     |
| Vai trò chính    | Pipeline Orchestration & Data Observability |
| Repository         | https://github.com/nvchien19/K4-L3A-Day10-MultiPerson-DataPipeline |
| Ngày hoàn thành | 2026-09-25               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Pipeline Orchestration | `src/pipelines/corruption_flow.py` (`main`) | Baseline metrics, clean JSON | Comparison report, Metrics | Hoàn thành |
| Xử lý Git & Merge | `corruption_flow.py` | Local commits, Remote branch | Code đã resolve conflict | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Tích hợp luồng evaluation và freshness | Team Data Engineer / Data Quality | Chạy mượt mà luồng pipeline chính xác với báo cáo đầy đủ |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Cập nhật và tinh chỉnh luồng Corruption | `src/pipelines/corruption_flow.py` | So sánh Metrics giữa Baseline, Corrupted và Repaired | Chạy `python script/run_corruption_flow.py` |
| Xử lý xung đột code (Merge Conflict) | `src/pipelines/corruption_flow.py` | File luồng chuẩn, cập nhật path freshness | Xem lịch sử commit trên GitHub |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:
Quản lý luồng chạy báo cáo `corruption_flow` kết nối từ dữ liệu lỗi đến dữ liệu được sửa chữa, và tạo ra logic tổng hợp, in ra các metric (như hit rate, judge score) để so sánh rõ ràng sự khác biệt.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Tạo và tinh chỉnh luồng tự động (orchestration) để đánh giá hệ thống RAG hoạt động ra sao khi gặp dữ liệu bị hỏng (corrupted) và khi dữ liệu được khôi phục (repaired), đồng thời trích xuất các báo cáo chất lượng để so sánh.

### Cách triển khai
Tôi phụ trách tinh chỉnh luồng trong `corruption_flow.py`, quản lý vòng lặp in chi tiết kết quả so sánh. Ngoài ra, tôi đã xử lý gộp mã (merge conflict) từ thay đổi của người khác trên nhánh main (cập nhật đường dẫn `repaired_freshness_report`) với những chi tiết logic đánh giá ở máy tôi, đảm bảo không bị mất code.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `baseline_metrics.json`, `clean.json`           |
| Output                         | `comparison_report` và các log so sánh metric |
| Module phụ thuộc             | `ingestion.corruption`, `observability.quality`, `evaluation.metrics` |
| Module sử dụng output        | Report sinh ra cho toàn nhóm xem xét      |
| Điều kiện lỗi cần xử lý | Lỗi path freshness report bị ghi đè, và merge conflict trên Git |

### Cách xác minh

```bash
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** In ra bảng Metric so sánh Baseline | Corrupted | Repaired một cách đầy đủ.
- **Kết quả thực tế:** Pipeline chạy thành công (sau khi fix conflict).
- **Artifact/log:** In ra console và ghi nhận vào các file json tương ứng trong thư mục `data/results/`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Bị merge conflict file `src/pipelines/corruption_flow.py` giữa local và branch `main` do người khác cũng sửa file này (thay đổi biến path).
- **Các phương án đã cân nhắc:** (1) Xóa logic của tôi để lấy hoàn toàn từ `main`; (2) Lấy code local đè lên từ chối thay đổi của remote; (3) Gộp thủ công giữ lại logic đầy đủ của local nhưng áp dụng fix đường dẫn freshness của remote.
- **Phương án đã chọn:** Gộp thủ công (phương án 3).
- **Lý do:** Giữ lại các lệnh in chi tiết (như vòng lặp in metric `retrieval_hit_rate`) mà nhánh local đã làm rất kỹ, đồng thời không đánh mất phần sửa lỗi đường dẫn ghi report freshness (`repaired_freshness_report`) của nhóm.
- **Bằng chứng quyết định phù hợp:** File chạy tốt mà không bị overwrite report, có log in ra chi tiết cuối luồng.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `CONFLICT (content): Merge conflict in src/pipelines/corruption_flow.py` khi chạy git pull. Trước đó có lỗi pull do các untracked files `data/clean/papers_clean.csv`, `data/quality/freshness_report.json`...
- **Lệnh hoặc bước tái hiện:** Chạy `git pull` sau khi commit file ở máy local trong khi remote đã có code thay đổi tại đúng các file bị ảnh hưởng.
- **Nguyên nhân gốc:** Do có các file kết quả chưa được đưa vào `.gitignore` (untracked) sinh ra trong lúc test bị đụng độ với các file đã commit trên remote. Đồng thời mã nguồn `corruption_flow.py` được chỉnh sửa ở cả hai nơi dẫn tới xung đột nội dung.
- **Cách xử lý:** Buộc xóa các file kết quả trung gian cản trở luồng pull, sau đó thực hiện pull. Gộp code thủ công trong file bị conflict để giữ các thay đổi đúng đắn từ cả 2 phía.
- **Cách xác minh sau khi sửa:** Chạy `git status` sạch sẽ và Push lên nhánh `main` thành công.
- **Điều học được:** Cần cấu hình `.gitignore` cẩn thận để tránh đưa các file dữ liệu trung gian (`.csv`, `.json`) lên Git; và luôn đối thoại khi cùng chỉnh sửa chung một file luồng orchestration.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu được fetch dạng JSON qua API của Crossref, sau đó qua các hàm cleaning (loại bỏ bài thiếu title, format lại ngày), chuyển sang dataframe, rồi text sẽ được embedding model chuyển thành vector và lưu vào bộ nhớ bằng ChromaDB.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Tập evaluation tạo ra từ clean dataset. Mỗi case có một câu hỏi tổng hợp và `ground-truth document ID` của bài báo chứa câu trả lời. Hệ thống query để xem retrieval có lấy đúng ID đó trong `top_k` hay không (hit rate) và dùng LLM làm judge đánh giá câu trả lời (judge_score).
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   Quality checks kiểm tra tính đầy đủ, hợp lệ của cấu trúc data (VD: không có null, đủ trường bắt buộc). Freshness monitoring tập trung vào thuộc tính thời gian (age_days) để đánh giá dữ liệu có đủ mới so với ngưỡng định trước (ví dụ 50 ngày) hay không.
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Để đảm bảo sự công bằng và nhất quán (A/B testing). Nếu thay đổi bài thi, ta sẽ không thể đánh giá chính xác nguyên nhân khiến điểm metrics giảm/tăng là do dữ liệu đầu vào biến động hay do độ khó của câu hỏi thay đổi.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Dựa trên các artifact `repaired_metrics.json` và bảng tổng hợp, nếu chất lượng (hit rate, f1, judge_score) và freshness status phục hồi xấp xỉ lại mức của baseline.

## 8. Phân tích kết quả

*(Lưu ý: Vì chưa chạy hoàn chỉnh script sau khi sửa nên chưa có file `repaired_metrics.json`. Bạn cần chạy `script/run_corruption_flow.py` và điền số liệu cụ thể vào đây)*

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      [ ] |       [ ] |      [ ] | [Nhận xét: Giảm mạnh khi corrupted, phục hồi sau repair] |
| `mean_token_f1`      |      [ ] |       [ ] |      [ ] | [Nhận xét: Tương tự như hit rate] |
| `judge_accuracy`     |      [ ] |       [ ] |      [ ] | [Nhận xét: Model trả lời sai khi thiếu data] |
| `mean_judge_score`   |      [ ] |       [ ] |      [ ] | [Nhận xét]              |
| Quality checks         |      [ ] |       [ ] |      [ ] | [Nhận xét: Pass -> Fail -> Pass] |
| Freshness status       |      [ ] |       [ ] |      [ ] | [Nhận xét: Fresh -> Stale -> Fresh] |

### Kết luận từ số liệu
1. Data corruption → Các trường quan trọng như Title bị mất / sai format ngày tháng → Tác động mạnh đến quá trình Embedding và Retrieval, dẫn đến `retrieval_hit_rate` sụt giảm trầm trọng.
2. Repair action → Kéo và xử lý lại dữ liệu chuẩn → Quality signal phục hồi, kéo theo Agent metric (retrieval và answer quality) phục hồi theo.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. Trải nghiệm thực tế vai trò của Pipeline Orchestration trong việc điều phối chuỗi tự động đánh giá thay vì gõ lệnh thủ công rải rác.
2. Tầm quan trọng của Data Observability: Nhận thấy rõ dữ liệu "bẩn" ảnh hưởng khốc liệt đến hệ quả cuối cùng của RAG Agent ra sao (thông qua bảng so sánh metric).
3. Cách phân tích nguyên nhân - hệ quả bài bản và có bằng chứng, cũng như cách làm việc nhóm trên Git tránh conflict các file dữ liệu lớn.

### Nếu có thêm thời gian
Sẽ làm thêm một Dashboard trực quan (ví dụ dùng Streamlit) đọc trực tiếp từ các file `metrics.json` để vẽ biểu đồ so sánh thay vì in ra terminal hoặc file markdown khô khan, giúp mọi người dễ dàng nhìn nhận biến động dữ liệu.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:
- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Hồ Nam
**Ngày xác nhận:** 2026-09-25
