# Kiến trúc AI Coding Agent - Phân tích Qoder

> Khóa học phân tích kiến trúc của Qoder - một AI Coding Agent đang hoạt động thực tế - từ internal knowledge.

**Tác giả:** Qwen3.7-Max

---

## Tổng quan

Khóa học gồm 7 bài, đi từ cơ bản đến nâng cao, phân tích cách một AI Coding Agent thực sự hoạt động từ bên trong:

| Bài | Chủ đề | Nội dung chính |
|-----|--------|----------------|
| 1 | **Agent Core Loop** | ReAct pattern, Think-Act-Observe loop |
| 2 | **System Prompt Design** | "DNA" của agent, cấu trúc prompt 7 tầng |
| 3 | **Tool System** | 25+ tools, function calling, parallel vs sequential |
| 4 | **Context Management** | Summarization, memory system, knowledge tree |
| 5 | **Multi-Agent Orchestration** | Single orchestrator + 7 specialized sub-agents |
| 6 | **Skills & Extensibility** | Plugin system, MCP protocol |
| 7 | **Guardrails & Production** | Safety, evaluation, monitoring, cost optimization |

## Yêu cầu

- Python 3.9+
- Không cần API key (tất cả demo dùng MockLLM)

## Cài đặt và chạy

```bash
# Clone repository
git clone https://github.com/tuandung222/qoder-architecture-course.git
cd qoder-architecture-course

# Chạy từng bài
python bai1_react_loop.py
python bai2_system_prompt.py
python bai3_tool_system.py
python bai4_context_management.py
python bai5_multi_agent.py
python bai6_skills_extensibility.py
python bai7_guardrails_production.py

# Hoặc chạy tất cả
python run_all.py
```

## Cấu trúc thư mục

```
qoder-architecture-course/
├── README.md
├── run_all.py                      # Chạy tất cả bài
├── bai1_react_loop.py              # Agent Core Loop
├── bai2_system_prompt.py           # System Prompt Design
├── bai3_tool_system.py             # Tool System
├── bai4_context_management.py      # Context Management
├── bai5_multi_agent.py             # Multi-Agent Orchestration
├── bai6_skills_extensibility.py    # Skills & Extensibility
├── bai7_guardrails_production.py   # Guardrails & Production
└── .github/
    └── workflows/
        └── ci.yml                  # GitHub Actions CI
```

## Phương pháp giảng dạy

Mỗi bài theo cấu trúc:
- **Lý thuyết (20%)**: Khái niệm, pattern
- **Phân tích Qoder (30%)**: Mổ xẻ kiến trúc thực tế từ internal knowledge
- **Code demo (40%)**: Python code chạy được, minh họa từng khái niệm
- **Tóm tắt (10%)**: Takeaway, bài tập gợi ý

## Đối tượng

- Lập trình viên đã có kiến thức nền về LLM
- Muốn hiểu sâu cách AI Coding Agent hoạt động từ bên trong
- Muốn tự xây dựng agent cho dự án của mình

## License

MIT
