# Lab Guide: Multi-Agent Research System

## Scenario

Bạn cần xây dựng một research assistant có thể nhận câu hỏi dài, tìm thông tin, phân tích và viết câu trả lời cuối cùng. Lab yêu cầu so sánh hai cách làm:

1. **Single-agent baseline**: một agent làm toàn bộ.
2. **Multi-agent workflow**: Supervisor điều phối Researcher, Analyst, Writer.

## Quy tắc quan trọng

- Không thêm agent nếu không có lý do rõ ràng.
- Mỗi agent phải có responsibility riêng.
- Shared state phải đủ rõ để debug.
- Phải có trace hoặc log cho từng bước.
- Phải benchmark, không chỉ nhìn output bằng cảm tính.

## Milestone 1: Baseline

File:

- `src/multi_agent_research_lab/cli.py`
- `src/multi_agent_research_lab/services/llm_client.py`

Thay baseline placeholder bằng một call LLM thật và đo lường latency/token usage/cost.

## Milestone 2: Supervisor

File:

- `src/multi_agent_research_lab/agents/supervisor.py`
- `src/multi_agent_research_lab/graph/workflow.py`

Implement routing policy và StateGraph workflow với stop condition (max_iterations).

## Milestone 3: Worker agents

File:

- `src/multi_agent_research_lab/agents/researcher.py`
- `src/multi_agent_research_lab/agents/analyst.py`
- `src/multi_agent_research_lab/agents/writer.py`

Implement các worker agents: Researcher, Analyst, Writer và Critic.

## Milestone 4: Trace và benchmark

File gợi ý:

- `src/multi_agent_research_lab/observability/tracing.py`
- `src/multi_agent_research_lab/evaluation/benchmark.py`
- `src/multi_agent_research_lab/evaluation/report.py`

Benchmark tối thiểu:

| Metric | Cách đo gợi ý |
|---|---|
| Latency | wall-clock time |
| Cost | token usage hoặc provider usage |
| Quality | rubric 0-10 do peer review |
| Citation coverage | số claims có source / tổng claims chính |
| Failure rate | số query fail / tổng query |

## Troubleshooting

### macOS: lỗi SSL certificate khi gọi API qua HTTPS (Tavily, OpenAI, ...)

Triệu chứng: khi implement `SearchClient` (hoặc bất kỳ HTTPS call nào) trên macOS, bạn có thể gặp lỗi kiểu:

```
ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
unable to get local issuer certificate
```

Nguyên nhân: Python cài từ python.org trên macOS **không dùng** certificate store của hệ điều hành, nên không tìm thấy CA bundle hợp lệ. Đây là lỗi môi trường, **không phải** do API key sai.

Cách khắc phục (chọn 1 trong 3):

1. **Chạy script cài certificate đi kèm Python** (nhanh nhất):

   ```bash
   /Applications/Python\ 3.12/Install\ Certificates.command
   ```

   (thay `3.12` bằng version Python của bạn)

2. **Dùng `certifi` trong code** — thêm `certifi` vào dependencies, rồi tạo SSL context khi gọi HTTPS:

   ```python
   import certifi
   import ssl
   from urllib.request import urlopen

   ssl_context = ssl.create_default_context(cafile=certifi.where())
   urlopen(request, timeout=timeout, context=ssl_context)
   ```

3. **Set biến môi trường** trỏ tới CA bundle của certifi (không cần đổi code):

   ```bash
   export SSL_CERT_FILE=$(python -m certifi)
   ```

## Exit ticket

### 1. Case nào nên dùng multi-agent? Vì sao?

- **Nghiên cứu sâu, tổng hợp đa nguồn (Complex Research & Synthesis)**: Các bài toán đòi hỏi tìm kiếm nhiều tài liệu, đối chiếu mâu thuẫn, kiểm tra chéo độ tin cậy và tổng hợp báo cáo dài (như tổng quan công nghệ, thẩm định pháp lý, báo cáo tài chính).
- **Phân tách trách nhiệm chuyên biệt (Separation of Concerns)**: Mỗi agent có system prompt, tool set, và reasoning focus riêng (vd: Researcher chỉ tìm kiếm & trích xuất sự thật, Analyst chỉ phân tích đối chiếu, Writer tập trung viết rõ ràng có trích dẫn, Critic kiểm tra hallucination).
- **Yêu cầu kiểm soát chất lượng & audit trail**: Cần trace rõ từng bước trung gian (intermediate states) để debug, đánh giá hallucination và tối ưu từng agent độc lập mà không làm hỏng toàn bộ pipeline.

### 2. Case nào không nên dùng multi-agent? Vì sao?

- **Truy vấn đơn giản, single-hop lookup hoặc Q&A trực tiếp**: Khi câu hỏi chỉ cần 1 bước tìm kiếm hoặc dữ liệu đã có sẵn trong context, single-agent hoặc naive RAG nhanh hơn, rẻ hơn và ít điểm lỗi hơn.
- **Ứng dụng yêu cầu độ trễ cực thấp (Ultra-low latency / Real-time chat)**: Multi-agent qua nhiều bước tuần tự (Supervisor -> Researcher -> Analyst -> Writer -> Critic) làm tăng đáng kể wall-clock time.
- **Ngân sách token / chi phí eo hẹp**: Chuyển giao shared state qua nhiều LLM calls làm nhân số token và chi phí API lên gấp 3-5 lần so với single-agent baseline.
