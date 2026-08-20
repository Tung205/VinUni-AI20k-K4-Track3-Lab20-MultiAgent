# Design Template: Multi-Agent Research Lab

## Problem

Xây dựng hệ thống Research Assistant tự động có khả năng xử lý các yêu cầu nghiên cứu kỹ thuật chuyên sâu (ví dụ: *"Research GraphRAG state-of-the-art"*). Hệ thống cần tìm kiếm tài liệu từ nhiều nguồn, trích xuất sự kiện, phân tích đối chiếu ưu nhược điểm, và xuất báo cáo hoàn chỉnh có trích dẫn nguồn chuẩn xác.

## Why multi-agent?

Single-agent (zero-shot prompt hoặc single-pass RAG) thường gặp các hạn chế lớn:
- **Hallucination và trích dẫn giả mạo**: Khi phải vừa tìm kiếm, vừa đọc hiểu, vừa viết văn trong một context duy nhất, LLM dễ bỏ sót nguồn hoặc tự sinh trích dẫn.
- **Thiếu chiều sâu phản biện**: Single-agent không có bước trung gian tách biệt để kiểm tra mâu thuẫn giữa các tài liệu.
- **Khó debug và kiểm soát lỗi**: Khi kết quả đầu ra sai, rất khó xác định lỗi bắt nguồn từ khâu truy vấn, khâu lọc dữ liệu hay khâu tổng hợp.

Multi-agent phân tách bài toán thành các vai trò chuyên biệt (Researcher -> Analyst -> Writer -> Critic) dưới sự điều phối của Supervisor, lưu vết toàn bộ state trung gian để đảm bảo chất lượng.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Điều phối thứ tự thực thi, kiểm tra điều kiện dừng và chuyển bước | Shared state (`ResearchState`) | Next route (`researcher`, `analyst`, `writer`, `critic`, `done`) | Vòng lặp vô hạn nếu không có `max_iterations` |
| Researcher | Tìm kiếm tài liệu ngoài qua Search API và trích xuất ghi chú dữ liệu ban đầu | `request.query`, `request.max_sources` | `sources: list[SourceDocument]`, `research_notes` | Không tìm thấy nguồn phù hợp hoặc nguồn rác |
| Analyst | Phân tích đối chiếu các nguồn, đánh giá độ tin cậy, tổng hợp ưu/nhược điểm | `sources`, `research_notes` | `analysis_notes` | Bỏ qua mâu thuẫn thông tin giữa các tài liệu |
| Writer | Tổng hợp báo cáo kỹ thuật hoàn chỉnh kèm trích dẫn inline `[1]`, `[2]` và danh mục References | `request`, `research_notes`, `analysis_notes`, `sources` | `final_answer` | Bỏ quên citation hoặc định dạng không đúng chuẩn |
| Critic | Thẩm định tính chính xác, kiểm tra citation coverage và phát hiện hallucination | `final_answer`, `sources`, `analysis_notes` | `critic_notes`, verify flag | Bỏ sót lỗi sai tinh vi hoặc quá khắt khe |

## Shared state

- `request: ResearchQuery`: Chứa query gốc, số lượng nguồn tối đa (`max_sources`) và đối tượng độc giả (`audience`).
- `iteration: int`: Đếm số bước routing để chặn infinite loop.
- `route_history: list[str]`: Ghi lại lịch sử chuỗi quyết định của Supervisor.
- `sources: list[SourceDocument]`: Danh sách các tài liệu thô được Researcher tìm thấy.
- `research_notes: str`: Ghi chú dữ liệu, sự kiện trích xuất từ các sources.
- `analysis_notes: str`: Kết quả phân tích sâu, so sánh đối chiếu của Analyst.
- `final_answer: str`: Báo cáo hoàn chỉnh cuối cùng của Writer.
- `agent_results: list[AgentResult]`: Lưu output và metadata (token, cost, latency) của từng agent.
- `trace: list[dict]`: Dấu vết thực thi từng event phục vụ observability.
- `errors: list[str]`: Danh sách lỗi phát sinh (nếu có).

## Routing policy

```
                 +-------------------+
                 |    SUPERVISOR     |<-------------------+
                 +---------+---------+                    |
                           |                              |
           +---------------+---------------+              |
           |               |               |              |
    [no sources]     [no analysis]    [no answer]    [has answer]
           |               |               |              |
           v               v               v              v
     +------------+  +-----------+  +------------+  +------------+
     | Researcher |  |  Analyst  |  |   Writer   |  |   Critic   |
     +-----+------+  +-----+-----+  +-----+------+  +-----+------+
           |               |              |               |
           +---------------+--------------+---------------+
```

Supervisor quyết định dựa trên tính đầy đủ của state:
1. `iteration >= max_iterations` -> `done`
2. `sources` hoặc `research_notes` chưa có -> `researcher`
3. `analysis_notes` chưa có -> `analyst`
4. `final_answer` chưa có -> `writer`
5. `critic` chưa chạy -> `critic`
6. Hoàn tất toàn bộ -> `done`

## Guardrails

- **Max iterations**: Cấu hình `MAX_ITERATIONS` (mặc định 6) ngăn chặn triệt để vòng lặp routing vô hạn.
- **Timeout**: `TIMEOUT_SECONDS` giới hạn thời gian chạy mạng cho từng API call.
- **Retry**: Áp dụng Tenacity Exponential Backoff Retry (3 lần) khi gọi LLM/Search API.
- **Fallback**: Tự động fallback sang Mock Search / Local Completion khi API key không khả dụng hoặc mạng chập chờn.
- **Validation**: Kiểm tra schema Pydantic chặt chẽ tại tầng input và state transitions.

## Benchmark plan

- **Queries**: *"Research GraphRAG state-of-the-art"*, *"Multi-agent systems orchestration patterns"*, v.v.
- **Metrics**: Wall-clock Latency (s), Total Cost (USD), Heuristic Quality Score (0-10), Citation Coverage (%), Failure Rate (%).
- **Expected outcome**: Multi-agent đạt chất lượng và độ phủ trích dẫn cao hơn rõ rệt (Quality ~9.5-10 vs ~5-6, Citation 100% vs ~30%), chấp nhận trade-off về latency và chi phí token.
