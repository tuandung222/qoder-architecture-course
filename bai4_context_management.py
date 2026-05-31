"""
Bài 4: Context Management - Quản lý bộ nhớ
=============================================
Phân tích cách Qoder quản lý context window và xây dựng
context manager với summarization + memory retrieval.

Chạy: python bai4_context_management.py

Yêu cầu: Không cần API key (dùng mock)
"""

import json
from datetime import datetime


# ============================================================
# 1. PHÂN TÍCH: CONTEXT MANAGEMENT CỦA QODER
# ============================================================

def analyze_context_management():
    """Phân tích cách Qoder quản lý context."""

    print("=" * 60)
    print("PHÂN TÍCH: CONTEXT MANAGEMENT CỦA QODER")
    print("=" * 60)

    strategies = [
        {
            "name": "Automatic Summarization",
            "problem": "Context window có giới hạn (128K-200K tokens)",
            "solution": "Tự động tóm tắt conversation khi quá dài",
            "qoder_detail": "Hệ thống tự tóm tắt -> 'unlimited context through automatic summarization'",
            "trade_off": "Mất chi tiết cũ, nhưng giữ được ý chính",
        },
        {
            "name": "Plan Mode",
            "problem": "Task phức tạp cần planning + execution, context sẽ rất dài",
            "solution": "Tách thành 2 phase: Planning (read-only) và Execution (read-write)",
            "qoder_detail": "EnterSpecMode -> write plan file -> ExitSpecMode -> execute",
            "trade_off": "Thêm bước trung gian, nhưng giảm context load mỗi phase",
        },
        {
            "name": "Sub-agent Delegation",
            "problem": "Main agent context bị đầy khi xử lý task con phức tạp",
            "solution": "Spawn sub-agents cho task con, chỉ nhận kết quả cuối",
            "qoder_detail": "Task tool với explore-agent, code-reviewer, plan-agent...",
            "trade_off": "Sub-agent không có context của main agent, cần prompt rõ",
        },
        {
            "name": "Long-term Memory",
            "problem": "Mỗi session là conversation mới, mất kiến thức cũ",
            "solution": "Memory system lưu trữ kiến thức qua nhiều sessions",
            "qoder_detail": "search_memory (fetch/shallow/deep/explore) + update_memory",
            "trade_off": "Memory có thể outdated, cần update thường xuyên",
        },
        {
            "name": "Knowledge Tree",
            "problem": "Kiến thức project quá nhiều, không thể load hết",
            "solution": "Organize theo tree structure, explore từng nhánh khi cần",
            "qoder_detail": "knowledge_module_tree trong memory_overview, explore by path",
            "trade_off": "Cần cấu trúc hóa kiến thức trước, không automatic",
        },
        {
            "name": "Dynamic Context Injection",
            "problem": "Agent cần biết environment nhưng không nên hardcode",
            "solution": "Inject thông tin môi trường ĐỘNG mỗi session",
            "qoder_detail": "<env> block: working dir, platform, OS version, date, git status",
            "trade_off": "Tốn tokens mỗi session cho context info",
        },
    ]

    for i, s in enumerate(strategies, 1):
        print(f"\n{'─'*60}")
        print(f"  Chiến lược {i}: {s['name']}")
        print(f"  Vấn đề: {s['problem']}")
        print(f"  Giải pháp: {s['solution']}")
        print(f"  Qoder áp dụng: {s['qoder_detail']}")
        print(f"  Trade-off: {s['trade_off']}")

    print(f"\n{'='*60}")


# ============================================================
# 2. CONTEXT WINDOW SIMULATOR - Mô phỏng context window
# ============================================================

class ContextWindow:
    """
    Mô phỏng context window của LLM.
    Giới hạn số tokens, tự động summarize khi đầy.
    """

    def __init__(self, max_tokens: int = 1000):
        self.max_tokens = max_tokens
        self.messages: list[dict] = []
        self.summary: str = ""
        self.total_tokens_used: int = 0
        self.summarization_count: int = 0

    def _count_tokens(self, text: str) -> int:
        """Ước tính số tokens (xấp xỉ: 1 token ~ 4 ký tự English, ~ 2 ký tự Vietnamese)."""
        return len(text) // 3

    def _total_tokens(self) -> int:
        """Tính tổng tokens hiện tại."""
        total = self._count_tokens(self.summary)
        for msg in self.messages:
            total += self._count_tokens(msg.get("content", ""))
        return total

    def _summarize_if_needed(self):
        """Tự động tóm tắt các message cũ khi context sắp đầy."""
        while self._total_tokens() > self.max_tokens * 0.8 and len(self.messages) > 4:
            # Lấy 3 message đầu tiên để summarize
            old_messages = self.messages[:3]
            self.messages = self.messages[3:]

            # Tạo summary đơn giản (trong thực tế, dùng LLM để summarize)
            old_content = " ".join(m.get("content", "")[:50] for m in old_messages)
            summary_line = f"[Tóm tắt {len(old_messages)} messages cũ: {old_content}...]"

            if self.summary:
                self.summary += "\n" + summary_line
            else:
                self.summary = summary_line

            self.summarization_count += 1
            print(f"    [SUMMARIZE] Đã tóm tắt {len(old_messages)} messages (lần thứ {self.summarization_count})")

    def add_message(self, role: str, content: str) -> None:
        """Thêm message vào context."""
        self.messages.append({"role": role, "content": content})
        self._summarize_if_needed()
        self.total_tokens_used = self._total_tokens()

    def get_context(self) -> list[dict]:
        """Lấy context hiện tại để gửi cho LLM."""
        context = []
        if self.summary:
            context.append({
                "role": "system",
                "content": f"Previous conversation summary:\n{self.summary}",
            })
        context.extend(self.messages)
        return context

    def get_stats(self) -> dict:
        """Thống kê context hiện tại."""
        return {
            "total_messages": len(self.messages),
            "total_tokens": self._total_tokens(),
            "max_tokens": self.max_tokens,
            "usage_percent": round(self._total_tokens() / self.max_tokens * 100, 1),
            "summarization_count": self.summarization_count,
            "has_summary": bool(self.summary),
        }


# ============================================================
# 3. MEMORY SYSTEM - Hệ thống nhớ dài hạn
# ============================================================

class MemorySystem:
    """
    Mô phỏng hệ thống memory của Qoder.
    Lưu trữ kiến thức qua nhiều sessions.
    """

    CATEGORIES = [
        "user_info",
        "user_hobby",
        "user_communication",
        "user_behavior",
        "project_introduction",
        "project_tech_stack",
        "project_build_configuration",
        "development_code_specification",
        "development_practice_specification",
        "development_test_specification",
        "expert_experience",
        "learned_skill_experience",
    ]

    RETRIEVAL_MODES = {
        "fetch": "Truy xuất chính xác theo title (độ chính xác cao nhất)",
        "shallow": "Tìm theo keyword, trả về nhiều kết quả liên quan",
        "deep": "Graph-based retrieval, phủ rộng nhất",
        "explore": "Duyệt topic tree theo path, trả về cấu trúc subtree",
    }

    def __init__(self):
        self.memories: list[dict] = []
        self._next_id = 1

    def create(self, title: str, content: str, category: str, keywords: list[str]) -> int:
        """Tạo memory mới."""
        if category not in self.CATEGORIES:
            raise ValueError(f"Category '{category}' không hợp lệ. Chọn từ: {self.CATEGORIES}")

        memory = {
            "id": self._next_id,
            "title": title,
            "content": content,
            "category": category,
            "keywords": keywords,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self.memories.append(memory)
        self._next_id += 1
        return memory["id"]

    def search(self, query: str, mode: str = "shallow") -> list[dict]:
        """Tìm kiếm memories."""
        if mode == "fetch":
            # Exact title match
            return [m for m in self.memories if m["title"].lower() == query.lower()]

        elif mode == "shallow":
            # Keyword-based search
            query_words = query.lower().split()
            results = []
            for m in self.memories:
                score = sum(
                    1 for w in query_words
                    if w in m["title"].lower()
                    or w in m["content"].lower()
                    or any(w in k.lower() for k in m["keywords"])
                )
                if score > 0:
                    results.append({**m, "_score": score})
            return sorted(results, key=lambda x: x["_score"], reverse=True)

        elif mode == "deep":
            # Simplified graph-based: find connected memories via shared keywords
            query_words = set(query.lower().split())
            results = []
            for m in self.memories:
                memory_words = set(k.lower() for k in m["keywords"])
                overlap = len(query_words & memory_words)
                if overlap > 0:
                    results.append({**m, "_relevance": overlap})
            return sorted(results, key=lambda x: x["_relevance"], reverse=True)

        return []

    def update(self, memory_id: int, content: str) -> bool:
        """Cập nhật memory."""
        for m in self.memories:
            if m["id"] == memory_id:
                m["content"] = content
                m["updated_at"] = datetime.now().isoformat()
                return True
        return False

    def delete(self, memory_id: int) -> bool:
        """Xóa memory."""
        self.memories = [m for m in self.memories if m["id"] != memory_id]
        return True

    def get_overview(self) -> dict:
        """Lấy tổng quan memories (giống memory_overview trong Qoder)."""
        overview = {}
        for m in self.memories:
            cat = m["category"]
            if cat not in overview:
                overview[cat] = []
            overview[cat].append({
                "id": m["id"],
                "title": m["title"],
                "keywords": m["keywords"],
            })
        return overview


# ============================================================
# 4. DEMO: CONTEXT + MEMORY HOẠT ĐỘNG CÙNG NHAU
# ============================================================

def demo_context_and_memory():
    """Demo cách context window và memory system hoạt động cùng nhau."""

    print("\n" + "=" * 60)
    print("DEMO: CONTEXT WINDOW + MEMORY SYSTEM")
    print("=" * 60)

    # Khởi tạo
    ctx = ContextWindow(max_tokens=500)
    memory = MemorySystem()

    # Tạo một số memories
    memory.create(
        title="User GitHub account",
        content="GitHub username: tuandung222",
        category="user_info",
        keywords=["github", "account", "tuandung222"],
    )
    memory.create(
        title="Project tech stack",
        content="Dự án dùng Python 3.9, FastAPI, PostgreSQL",
        category="project_tech_stack",
        keywords=["python", "fastapi", "postgresql"],
    )
    memory.create(
        title="Code style preference",
        content="User thích viết code tiếng Việt có dấu, dùng type hints",
        category="development_code_specification",
        keywords=["tiếng việt", "type hints", "code style"],
    )

    print("\n  Memory overview:")
    overview = memory.get_overview()
    for cat, items in overview.items():
        print(f"    {cat}: {len(items)} memories")
        for item in items:
            print(f"      - {item['title']} (keywords: {item['keywords']})")

    # Mô phỏng conversation
    print("\n  Mô phỏng conversation dài...")
    conversation_steps = [
        ("user", "Tôi muốn tạo API endpoint cho user registration"),
        ("assistant", "Tôi sẽ tạo endpoint POST /api/users/register với FastAPI"),
        ("user", "Thêm validation cho email và password"),
        ("assistant", "Đã thêm Pydantic model với email validator và password strength check"),
        ("user", "Giờ tạo endpoint login với JWT token"),
        ("assistant", "Tạo POST /api/users/login, trả về JWT access token và refresh token"),
        ("user", "Thêm middleware để verify JWT token"),
        ("assistant", "Đã tạo auth middleware, decode JWT và attach user vào request"),
        ("user", "Tôi cần thêm rate limiting cho API"),
        ("assistant", "Thêm slowapi rate limiter: 100 requests/minute cho anonymous, 1000 cho authenticated"),
        ("user", "Giờ viết unit tests cho các endpoints"),
        ("assistant", "Đã viết tests với pytest, mock database, test cả happy path và error cases"),
        ("user", "Thêm endpoint reset password"),
        ("assistant", "Tạo POST /api/users/reset-password, gửi email với reset token"),
        ("user", "Review lại toàn bộ auth module"),
    ]

    for i, (role, content) in enumerate(conversation_steps):
        ctx.add_message(role, content)

        if (i + 1) % 5 == 0 or i == len(conversation_steps) - 1:
            stats = ctx.get_stats()
            print(f"\n    Sau {i + 1} messages:")
            print(f"      Tokens: {stats['total_tokens']}/{stats['max_tokens']} ({stats['usage_percent']}%)")
            print(f"      Messages trong context: {stats['total_messages']}")
            print(f"      Đã summarize: {stats['summarization_count']} lần")

    # Tìm memory
    print("\n  Tìm memory liên quan đến 'python fastapi':")
    results = memory.search("python fastapi", mode="shallow")
    for r in results:
        print(f"    - [{r['category']}] {r['title']}: {r['content']}")

    print(f"\n{'='*60}")


# ============================================================
# 5. MAIN
# ============================================================

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║  BÀI 4: CONTEXT MANAGEMENT - QUẢN LÝ BỘ NHỚ           ║
║                                                          ║
║  1. Phân tích chiến lược context của Qoder              ║
║  2. Context Window simulator với auto-summarization     ║
║  3. Memory System với 4 retrieval modes                 ║
║  4. Demo kết hợp Context + Memory                       ║
╚══════════════════════════════════════════════════════════╝
    """)

    analyze_context_management()
    demo_context_and_memory()

    print("\n" + "=" * 60)
    print("TAKEAWAY")
    print("=" * 60)
    print("""
1. Context window là TÀI NGUYÊN QUÝ NHẤT của agent - có giới hạn.
2. Auto-summarization: khi context đầy -> tóm tắt messages cũ -> "unlimited context".
3. Sub-agent delegation giúp giảm context load: chỉ nhận KẾT QUẢ, không nhận chi tiết.
4. Memory system = bộ nhớ dài hạn qua sessions: create, search (4 modes), update, delete.
5. Plan mode tách planning/execution -> mỗi phase dùng ít context hơn.
6. Dynamic context injection: env info được inject mỗi session, không hardcode.
    """)


if __name__ == "__main__":
    main()
