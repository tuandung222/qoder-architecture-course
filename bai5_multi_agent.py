"""
Bài 5: Multi-Agent Orchestration - Đội quân Agent
====================================================
Phân tích kiến trúc multi-agent của Qoder và xây dựng
mini multi-agent system với orchestrator + specialized agents.

Chạy: python bai5_multi_agent.py

Yêu cầu: Không cần API key (dùng mock)
"""

import json
from typing import Any


# ============================================================
# 1. PHÂN TÍCH: MULTI-AGENT CỦA QODER
# ============================================================

def analyze_multi_agent():
    """Phân tích kiến trúc multi-agent của Qoder."""

    print("=" * 60)
    print("PHÂN TÍCH: MULTI-AGENT ORCHESTRATION CỦA QODER")
    print("=" * 60)

    print("""
  Kiến trúc: SINGLE ORCHESTRATOR + SPECIALIZED SUB-AGENTS

  ┌─────────────────────────────────────────────────┐
  │              MAIN AGENT (Qoder)                   │
  │  - Nhận yêu cầu từ user                          │
  │  - Phân tích intent                              │
  │  - Quyết định delegate hay tự xử lý              │
  │  - Tổng hợp kết quả                              │
  │  - Giao tiếp với user                            │
  └──────────────┬──────────────────────────────────┘
                 │ Task tool
       ┌─────────┼──────────┬──────────────┐
       v         v          v              v
  ┌─────────┐ ┌──────┐ ┌───────┐ ┌─────────────┐
  │ explore │ │ code │ │ plan  │ │  browser     │
  │ -agent  │ │review│ │-agent │ │  -agent      │
  └─────────┘ └──────┘ └───────┘ └─────────────┘
""")

    agents = {
        "explore-agent": {
            "description": "Khám phá codebase nhanh",
            "tools": ["Read", "Glob", "Grep", "Bash", "search_codebase", "search_symbol"],
            "when_to_use": "Cần tìm file, tìm code, trả lời câu hỏi về codebase",
            "example": "Tìm tất cả API endpoints trong project",
        },
        "code-reviewer": {
            "description": "Review code changes",
            "tools": ["Bash", "Read", "Glob", "Grep", "WebSearch", "WebFetch"],
            "when_to_use": "Sau khi viết code đáng kể, cần review correctness/security",
            "example": "Review các thay đổi chưa commit",
        },
        "plan-agent": {
            "description": "Thiết kế kế hoạch triển khai",
            "tools": ["Read", "Glob", "Grep", "Bash", "search_codebase", "search_symbol"],
            "when_to_use": "Task phức tạp cần planning trước khi code",
            "example": "Lập kế hoạch refactor authentication system",
        },
        "design-agent": {
            "description": "Phân tích requirements và thiết kế",
            "tools": ["Read", "Write", "Edit", "Glob", "Grep", "WebFetch", "WebSearch"],
            "when_to_use": "Cần gather requirements, design documentation",
            "example": "Phân tích và thiết kế feature mới",
        },
        "browser-agent": {
            "description": "Tự động hóa trình duyệt",
            "tools": ["Read", "Glob", "Grep", "WebFetch", "WebSearch", "browser-use tools"],
            "when_to_use": "Cần navigate web, fill forms, take screenshots",
            "example": "Test web app trên trình duyệt",
        },
        "general-purpose": {
            "description": "Tác vụ tổng hợp, multi-step",
            "tools": "Tất cả tools",
            "when_to_use": "Task phức tạp không phù hợp agent chuyên biệt",
            "example": "Research + code + test một feature",
        },
        "qoder-guide": {
            "description": "Hướng dẫn sử dụng Qoder",
            "tools": ["Read", "Glob", "Grep", "WebFetch", "WebSearch"],
            "when_to_use": "User cần help về Qoder features",
            "example": "Hướng dẫn cấu hình MCP server",
        },
    }

    for name, info in agents.items():
        print(f"\n  Agent: {name}")
        print(f"    Mô tả: {info['description']}")
        print(f"    Tools: {info['tools'] if isinstance(info['tools'], str) else ', '.join(info['tools'])}")
        print(f"    Khi nào dùng: {info['when_to_use']}")
        print(f"    Ví dụ: {info['example']}")

    print(f"\n{'='*60}")

    # Decision matrix
    print("\n  QUYẾT ĐỊNH DELEGATE HAY TỰ XỬ LÝ:")
    print(f"  {'─'*56}")
    print("""
    TỰ XỬ LÝ khi:
      - Task đơn giản (1-2 bước)
      - Đã biết rõ file cần sửa
      - Chỉ cần đọc/ghi 1 file

    DELEGATE khi:
      - Cần khám phá codebase (explore-agent)
      - Task cần chuyên môn riêng (code-reviewer)
      - Cần planning phức tạp (plan-agent)
      - Task độc lập, có thể chạy song song
      - Context đang đầy -> offload cho sub-agent
    """)


# ============================================================
# 2. SUB-AGENT BASE CLASS
# ============================================================

class SubAgent:
    """
    Base class cho sub-agent.
    Mỗi sub-agent có: name, description, tools, system_prompt.
    """

    def __init__(self, name: str, description: str, tools: list[str], system_prompt: str):
        self.name = name
        self.description = description
        self.tools = tools
        self.system_prompt = system_prompt

    def execute(self, task: str, context: dict | None = None) -> str:
        """
        Thực thi task. Trong thực tế, gọi LLM với system_prompt + task.
        Override trong subclass để implement logic cụ thể.
        """
        raise NotImplementedError


# ============================================================
# 3. SPECIALIZED AGENTS
# ============================================================

class ExploreAgent(SubAgent):
    """Agent chuyên khám phá codebase."""

    def __init__(self):
        super().__init__(
            name="explore-agent",
            description="Khám phá codebase nhanh",
            tools=["Read", "Glob", "Grep", "Bash"],
            system_prompt="Bạn là codebase explorer. Tìm kiếm nhanh và chính xác.",
        )

    def execute(self, task: str, context: dict | None = None) -> str:
        # Mock: trả về kết quả giả lập
        return f"[explore-agent] Đã tìm kiếm: '{task}'\n  Kết quả: Tìm thấy 5 files liên quan, 12 functions matching."


class CodeReviewerAgent(SubAgent):
    """Agent chuyên review code."""

    def __init__(self):
        super().__init__(
            name="code-reviewer",
            description="Review code changes",
            tools=["Read", "Bash", "Grep"],
            system_prompt="Bạn là code reviewer. Tập trung correctness, security, performance.",
        )

    def execute(self, task: str, context: dict | None = None) -> str:
        return f"[code-reviewer] Đã review: '{task}'\n  Kết quả: 2 issues found (1 security, 1 performance). 0 critical bugs."


class PlanAgent(SubAgent):
    """Agent chuyên lập kế hoạch."""

    def __init__(self):
        super().__init__(
            name="plan-agent",
            description="Thiết kế kế hoạch triển khai",
            tools=["Read", "Glob", "Grep"],
            system_prompt="Bạn là software architect. Thiết kế kế hoạch triển khai chi tiết.",
        )

    def execute(self, task: str, context: dict | None = None) -> str:
        return f"[plan-agent] Đã phân tích: '{task}'\n  Kế hoạch: 4 bước, 3 files cần sửa, ước tính 5 iterations."


# ============================================================
# 4. ORCHESTRATOR - Bộ não điều phối
# ============================================================

class Orchestrator:
    """
    Main orchestrator - điều phối sub-agents.
    Tương tự cách Qoder quyết định khi nào spawn sub-agent.
    """

    def __init__(self):
        self.agents: dict[str, SubAgent] = {}
        self.execution_log: list[dict] = []

        # Đăng ký sub-agents
        self.register_agent(ExploreAgent())
        self.register_agent(CodeReviewerAgent())
        self.register_agent(PlanAgent())

    def register_agent(self, agent: SubAgent):
        """Đăng ký một sub-agent."""
        self.agents[agent.name] = agent

    def route_task(self, task: str) -> str:
        """
        Quyết định agent nào nên xử lý task.
        Trong thực tế, dùng LLM để phân tích intent.
        """
        task_lower = task.lower()

        # Routing rules (đơn giản hóa)
        if any(kw in task_lower for kw in ["tìm", "search", "find", "explore", "khám phá"]):
            return "explore-agent"
        elif any(kw in task_lower for kw in ["review", "đánh giá", "kiểm tra code"]):
            return "code-reviewer"
        elif any(kw in task_lower for kw in ["kế hoạch", "plan", "thiết kế", "design"]):
            return "plan-agent"
        else:
            return "self"  # Orchestrator tự xử lý

    def execute(self, task: str) -> dict:
        """
        Thực thi task: route -> delegate hoặc tự xử lý -> log.
        """
        # Bước 1: Route task
        target_agent = self.route_task(task)

        record = {
            "task": task,
            "routed_to": target_agent,
            "result": "",
        }

        # Bước 2: Delegate hoặc tự xử lý
        if target_agent == "self":
            record["result"] = f"[orchestrator] Tự xử lý: '{task}'"
            print(f"  [ORCHESTRATOR] Tự xử lý: {task}")
        else:
            agent = self.agents[target_agent]
            print(f"  [ORCHESTRATOR] Delegate -> {target_agent}: {task}")
            record["result"] = agent.execute(task)
            print(f"  [{target_agent}] {record['result']}")

        self.execution_log.append(record)
        return record

    def execute_parallel(self, tasks: list[str]) -> list[dict]:
        """
        Thực thi nhiều tasks song song (nếu có thể).
        Trong thực tế, spawn nhiều sub-agents cùng lúc.
        """
        print(f"\n  [ORCHESTRATOR] Chạy {len(tasks)} tasks song song:")
        results = []
        for task in tasks:
            print(f"\n  Task: {task}")
            result = self.execute(task)
            results.append(result)
        return results

    def get_log(self) -> list[dict]:
        return self.execution_log


# ============================================================
# 5. DEMO
# ============================================================

def demo_multi_agent():
    """Demo hệ thống multi-agent."""

    print("\n" + "=" * 60)
    print("DEMO: MULTI-AGENT ORCHESTRATION")
    print("=" * 60)

    orch = Orchestrator()

    print("\n  Agents đã đăng ký:")
    for name, agent in orch.agents.items():
        print(f"    - {name}: {agent.description}")

    # Demo 1: Sequential tasks
    print("\n\n  --- DEMO 1: Sequential Tasks ---")
    print("  User: 'Hãy phân tích và xây dựng feature authentication'\n")

    # Bước 1: Plan
    orch.execute("Lập kế hoạch triển khai feature authentication")
    # Bước 2: Explore
    orch.execute("Tìm kiếm code authentication hiện có trong codebase")
    # Bước 3: Self-handle (code)
    orch.execute("Viết code login endpoint")
    # Bước 4: Review
    orch.execute("Review code login endpoint vừa viết")

    # Demo 2: Parallel tasks
    print("\n\n  --- DEMO 2: Parallel Tasks ---")
    print("  User: 'Khám phá toàn bộ project structure'\n")

    orch.execute_parallel([
        "Tìm tất cả API endpoints",
        "Tìm tất cả database models",
        "Tìm tất cả test files",
    ])

    # Log
    print("\n\n  Execution log:")
    for i, record in enumerate(orch.get_log(), 1):
        print(f"    {i}. [{record['routed_to']}] {record['task'][:50]}...")


# ============================================================
# 6. MAIN
# ============================================================

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║  BÀI 5: MULTI-AGENT ORCHESTRATION                      ║
║                                                          ║
║  1. Phân tích multi-agent của Qoder                     ║
║  2. Sub-agent base class                                 ║
║  3. Specialized agents (Explore, Review, Plan)           ║
║  4. Orchestrator với task routing                        ║
║  5. Demo sequential + parallel execution                 ║
╚══════════════════════════════════════════════════════════╝
    """)

    analyze_multi_agent()
    demo_multi_agent()

    print("\n" + "=" * 60)
    print("TAKEAWAY")
    print("=" * 60)
    print("""
1. Qoder = Single Orchestrator + 7 Specialized Sub-agents.
2. Sub-agents có TOOL SET RIÊNG phù hợp vai trò (explore: Read/Glob/Grep).
3. Task routing: orchestrator phân tích intent -> chọn agent phù hợp.
4. Parallel spawning: launch nhiều agents cùng lúc cho tasks độc lập.
5. Communication: prompt in -> result out (black box). Sub-agent KHÔNG thấy context của main.
6. Delegate khi: task phức tạp, cần chuyên môn, context đầy. Tự xử lý khi: task đơn giản.
    """)


if __name__ == "__main__":
    main()
