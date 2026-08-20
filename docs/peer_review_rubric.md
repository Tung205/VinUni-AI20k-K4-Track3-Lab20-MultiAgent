# Peer Review Rubric

Mỗi nhóm review repo/trace của một nhóm khác trong 8 phút.

| Tiêu chí | Câu hỏi | Điểm |
|---|---|---:|
| Role clarity | Mỗi agent có nhiệm vụ rõ, không overlap quá nhiều không? | 0-2 |
| State design | Shared state có đủ thông tin để handoff mà không mất context không? | 0-2 |
| Failure guard | Có max iterations, timeout, retry/fallback, validation không? | 0-2 |
| Benchmark | Có so sánh single vs multi-agent bằng metric cụ thể không? | 0-2 |
| Trace explanation | Nhóm giải thích được trace: ai làm gì, tốn bao nhiêu, sai ở đâu không? | 0-2 |

## Sample Peer Review Evaluation

```text
Strength: Phân tách vai trò cực kỳ mạch lạc (Supervisor điều phối, Researcher tìm kiếm, Analyst đối chiếu mâu thuẫn, Writer tổng hợp có citation, Critic thẩm định). State design rõ ràng, đầy đủ trace event cho từng agent step.
Risk / failure mode: Chi phí token tăng tuyến tính khi shared state tích lũy qua nhiều iteration. Nếu Researcher trích xuất sai thông tin mà Critic không phát hiện được thì có thể dẫn đến cascading hallucination.
One concrete improvement: Bổ sung cơ chế summarization/pruning cho intermediate notes trong state khi số lượng documents vượt quá 10.
Score: 10/10 (Role clarity: 2/2, State design: 2/2, Failure guard: 2/2, Benchmark: 2/2, Trace explanation: 2/2)
```
