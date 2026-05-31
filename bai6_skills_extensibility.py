"""
Bài 6: Skills & Extensibility - Plugin Architecture
=====================================================
Phân tích hệ thống Skills và MCP (Model Context Protocol)
của Qoder. Xây dựng plugin/skill system cho coding agent.

Chạy: python bai6_skills_extensibility.py

Yêu cầu: Không cần API key (dùng mock)
"""

import json
import os
from typing import Any, Callable


# ============================================================
# 1. PHÂN TÍCH: SKILLS VÀ MCP CỦA QODER
# ============================================================

def analyze_skills_and_mcp():
    """Phân tích hệ thống Skills và MCP của Qoder."""

    print("=" * 60)
    print("PHÂN TÍCH: SKILLS & MCP CỦA QODER")
    print("=" * 60)

    # Skills vs Tools
    print("""
  SO SÁNH: SKILLS vs TOOLS
  ┌──────────────┬──────────────────────┬──────────────────────┐
  │              │ TOOLS                │ SKILLS               │
  ├──────────────┼──────────────────────┼──────────────────────┤
  │ Cấp độ       │ Thấp (primitive)     │ Cao (high-level)     │
  │ Tương tự     │ Hàm function         │ Plugin/App           │
  │ Ví dụ        │ Read, Edit, Bash     │ ui-designer, deploy  │
  │ Invocation   │ Agent tự chọn        │ Slash command/auto   │
  │ Complexity   │ Đơn giản (1 action)  │ Phức tạp (workflow)  │
  │ Customizable │ Không (built-in)     │ Có (user tạo được)   │
  └──────────────┴──────────────────────┴──────────────────────┘
""")

    # Built-in skills của Qoder
    print("  BUILT-IN SKILLS CỦA QODER:")
    skills = [
        {"name": "ui-designer", "desc": "Thiết kế Web UI/prototype", "trigger": "Web UI tasks"},
        {"name": "vercel-deploy", "desc": "Deploy lên Vercel", "trigger": "Deploy web apps"},
        {"name": "create-skill", "desc": "Tạo skill mới cho Qoder", "trigger": "User muốn tạo skill"},
        {"name": "create-subagent", "desc": "Tạo sub-agent mới", "trigger": "User muốn tạo agent"},
        {"name": "canvas", "desc": "Tạo visual artifacts", "trigger": "Slash command /canvas"},
    ]
    for s in skills:
        print(f"    - {s['name']}: {s['desc']} (kích hoạt: {s['trigger']})")

    # User-created skills
    print("\n  USER-CREATED SKILL (ví dụ):")
    print("    - microsoft-foundry: Deploy và quản lý Foundry agents")
    print("    -> User tự tạo skill qua create-skill, lưu trong thư mục skill/")

    # Skill lifecycle
    print("\n  SKILL LIFECYCLE:")
    print("""
    1. Check available skills (<available_skills> trong context)
    2. Match user request -> skill description
    3. Invoke skill (Skill tool)
    4. Load SKILL.md instructions
    5. Execute theo instructions
    6. Return result
    """)

    # MCP
    print("\n" + "─" * 60)
    print("  MCP (MODEL CONTEXT PROTOCOL)")
    print("─" * 60)
    print("""
  MCP là gì?
    - Protocol CHUẨN để extend agent capabilities từ BÊN NGOÀI
    - Tương tự USB-C: một chuẩn kết nối cho mọi thiết bị
    - MCP Server cung cấp additional tools cho agent

  MCP trong Qoder:
    - mcp__genui__: Widget rendering (show_widget, load_guidelines)
    - mcp__quest__: Code intelligence (search_codebase, search_symbol, memory)
    - mcp__supabase__: Database operations (khi kết nối Supabase)

  Tại sao MCP quan trọng?
    - Agent không cần biết implementation detail của external service
    - Bất kỳ ai cũng có thể tạo MCP server -> open ecosystem
    - Tools được load ĐỘNG: kết nối server -> tools available
""")

    print(f"\n{'='*60}")


# ============================================================
# 2. SKILL SYSTEM IMPLEMENTATION
# ============================================================

class Skill:
    """
    Đại diện cho một Skill (plugin).
    Skill = tên + mô tả + trigger conditions + instructions + executor.
    """

    def __init__(
        self,
        name: str,
        description: str,
        trigger_keywords: list[str],
        instructions: str,
        executor: Callable[[str, dict], str] | None = None,
    ):
        self.name = name
        self.description = description
        self.trigger_keywords = trigger_keywords
        self.instructions = instructions
        self.executor = executor

    def matches(self, user_request: str) -> bool:
        """Kiểm tra user request có match skill này không."""
        request_lower = user_request.lower()
        return any(kw in request_lower for kw in self.trigger_keywords)

    def execute(self, task: str, context: dict | None = None) -> str:
        """Thực thi skill."""
        if self.executor:
            return self.executor(task, context or {})
        return f"[{self.name}] Executing: {task}\nInstructions: {self.instructions}"

    def to_dict(self) -> dict:
        """Chuyển sang dict để hiển thị."""
        return {
            "name": self.name,
            "description": self.description,
            "trigger_keywords": self.trigger_keywords,
        }


class SkillRegistry:
    """
    Registry quản lý tất cả skills.
    Tương tự <available_skills> trong Qoder's context.
    """

    def __init__(self):
        self.skills: dict[str, Skill] = {}

    def register(self, skill: Skill):
        """Đăng ký skill mới."""
        self.skills[skill.name] = skill

    def unregister(self, name: str):
        """Gỡ bỏ skill."""
        self.skills.pop(name, None)

    def find_matching(self, user_request: str) -> Skill | None:
        """Tìm skill phù hợp với user request."""
        for skill in self.skills.values():
            if skill.matches(user_request):
                return skill
        return None

    def get_available_skills_display(self) -> str:
        """Tạo danh sách skills hiển thị cho agent (giống <available_skills>)."""
        lines = ["<available_skills>"]
        for skill in self.skills.values():
            lines.append(f"  <skill>")
            lines.append(f"    <name>{skill.name}</name>")
            lines.append(f"    <description>{skill.description}</description>")
            lines.append(f"  </skill>")
        lines.append("</available_skills>")
        return "\n".join(lines)

    def list_skills(self) -> list[dict]:
        return [s.to_dict() for s in self.skills.values()]


# ============================================================
# 3. MCP SERVER SIMULATOR
# ============================================================

class MCPServer:
    """
    Mô phỏng MCP Server.
    Cung cấp additional tools cho agent qua protocol chuẩn.
    """

    def __init__(self, name: str, prefix: str):
        self.name = name
        self.prefix = prefix  # Ví dụ: "mcp__genui"
        self.tools: dict[str, dict] = {}
        self.connected = False

    def add_tool(self, name: str, description: str, handler: Callable):
        """Thêm tool vào MCP server."""
        full_name = f"{self.prefix}__{name}"
        self.tools[full_name] = {
            "name": full_name,
            "description": description,
            "handler": handler,
        }

    def connect(self):
        """Kết nối MCP server -> tools available."""
        self.connected = True

    def disconnect(self):
        """Ngắt kết nối."""
        self.connected = False

    def get_tools(self) -> list[dict]:
        """Lấy danh sách tools (chỉ khi đã kết nối)."""
        if not self.connected:
            return []
        return [{"name": t["name"], "description": t["description"]} for t in self.tools.values()]

    def call_tool(self, name: str, args: dict) -> str:
        """Gọi tool trên MCP server."""
        if not self.connected:
            return f"Error: MCP server '{self.name}' chưa kết nối"
        if name not in self.tools:
            return f"Error: Tool '{name}' không tồn tại trên server '{self.name}'"
        try:
            return self.tools[name]["handler"](**args)
        except Exception as e:
            return f"Error: {e}"


class MCPManager:
    """Quản lý nhiều MCP servers."""

    def __init__(self):
        self.servers: dict[str, MCPServer] = {}

    def register_server(self, server: MCPServer):
        self.servers[server.name] = server

    def get_all_tools(self) -> list[dict]:
        """Lấy tất cả tools từ các server đã kết nối."""
        tools = []
        for server in self.servers.values():
            tools.extend(server.get_tools())
        return tools

    def call_tool(self, name: str, args: dict) -> str:
        """Gọi tool trên server phù hợp."""
        for server in self.servers.values():
            if name in server.tools:
                return server.call_tool(name, args)
        return f"Error: Không tìm thấy tool '{name}' trên bất kỳ MCP server nào"


# ============================================================
# 4. DEMO: SKILL + MCP HOẠT ĐỘNG
# ============================================================

def demo_skill_system():
    """Demo hệ thống Skill."""

    print("\n" + "=" * 60)
    print("DEMO: SKILL SYSTEM")
    print("=" * 60)

    # Tạo registry
    registry = SkillRegistry()

    # Đăng ký built-in skills
    registry.register(Skill(
        name="ui-designer",
        description="Thiết kế Web UI và prototype",
        trigger_keywords=["thiết kế ui", "design web", "landing page", "giao diện"],
        instructions="1. Xác định requirements -> 2. Design system -> 3. Build prototype",
        executor=lambda task, ctx: f"[ui-designer] Đang thiết kế: {task}\n  -> Tạo design system\n  -> Build HTML prototype",
    ))

    registry.register(Skill(
        name="deploy-vercel",
        description="Deploy project lên Vercel",
        trigger_keywords=["deploy", "triển khai", "đưa lên mạng", "publish"],
        instructions="1. Check build -> 2. Install Vercel CLI -> 3. Deploy",
        executor=lambda task, ctx: f"[deploy-vercel] Đang deploy: {task}\n  -> Build OK\n  -> Deployed to https://example.vercel.app",
    ))

    registry.register(Skill(
        name="create-skill",
        description="Tạo skill mới cho agent",
        trigger_keywords=["tạo skill", "skill mới", "thêm skill"],
        instructions="1. Xác định mục đích -> 2. Viết SKILL.md -> 3. Register",
        executor=lambda task, ctx: f"[create-skill] Đang tạo skill: {task}\n  -> Tạo SKILL.md\n  -> Registered!",
    ))

    # Hiển thị available skills (giống Qoder's <available_skills>)
    print("\n  Available Skills (inject vào context):")
    print(f"  {registry.get_available_skills_display()}")

    # Mô phỏng user requests
    requests = [
        "Hãy thiết kế giao diện landing page cho sản phẩm",
        "Deploy project này lên mạng",
        "Fix bug trong file login.py",  # Không match skill nào
    ]

    for req in requests:
        print(f"\n  User: '{req}'")
        skill = registry.find_matching(req)
        if skill:
            print(f"    -> Match skill: {skill.name}")
            print(f"    -> Result: {skill.execute(req)}")
        else:
            print(f"    -> Không match skill nào. Agent tự xử lý bằng tools.")


def demo_mcp_system():
    """Demo hệ thống MCP."""

    print("\n" + "=" * 60)
    print("DEMO: MCP (MODEL CONTEXT PROTOCOL)")
    print("=" * 60)

    # Tạo MCP Manager
    manager = MCPManager()

    # MCP Server 1: genui (widget rendering)
    genui = MCPServer("genui", "mcp__genui")
    genui.add_tool(
        "show_widget",
        "Hiển thị widget HTML tương tác",
        lambda widget_code="", title="widget": f"Widget '{title}' đã hiển thị",
    )
    genui.add_tool(
        "load_guidelines",
        "Load design guidelines",
        lambda modules=None: f"Đã load guidelines: {modules or ['core']}",
    )

    # MCP Server 2: quest (code intelligence)
    quest = MCPServer("quest", "mcp__quest")
    quest.add_tool(
        "search_codebase",
        "Tìm kiếm code theo ngữ nghĩa",
        lambda query="", key_words="": f"Tìm thấy 8 kết quả cho '{query}'",
    )
    quest.add_tool(
        "search_symbol",
        "Tìm symbol và relationships",
        lambda queries=None: f"Tìm thấy 3 definitions, 12 references",
    )

    # Đăng ký servers
    manager.register_server(genui)
    manager.register_server(quest)

    # Kết nối
    print("\n  Kết nối MCP servers...")
    genui.connect()
    quest.connect()

    # Liệt kê tools từ MCP
    print("\n  Tools từ MCP servers:")
    for tool in manager.get_all_tools():
        print(f"    - {tool['name']}: {tool['description']}")

    # Gọi tools
    print("\n  Gọi MCP tools:")
    result = manager.call_tool("mcp__genui__show_widget", {"title": "calculator", "widget_code": "<div>...</div>"})
    print(f"    {result}")

    result = manager.call_tool("mcp__quest__search_codebase", {"query": "authentication logic", "key_words": "auth,login"})
    print(f"    {result}")

    # Ngắt kết nối genui
    genui.disconnect()
    print("\n  Sau khi ngắt genui:")
    print(f"    Tools còn lại: {[t['name'] for t in manager.get_all_tools()]}")


# ============================================================
# 5. MAIN
# ============================================================

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║  BÀI 6: SKILLS & EXTENSIBILITY - PLUGIN ARCHITECTURE   ║
║                                                          ║
║  1. Phân tích Skills và MCP của Qoder                   ║
║  2. Skill System (Registry + matching + execution)       ║
║  3. MCP Server simulator                                ║
║  4. Demo Skill + MCP hoạt động                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    analyze_skills_and_mcp()
    demo_skill_system()
    demo_mcp_system()

    print("\n" + "=" * 60)
    print("TAKEAWAY")
    print("=" * 60)
    print("""
1. Skills = HIGH-LEVEL capabilities (plugins). Tools = LOW-LEVEL primitives.
2. Skill lifecycle: check available -> match intent -> invoke -> load instructions -> execute.
3. User có thể TẠO SKILL MỚI -> extensibility (create-skill).
4. MCP = protocol CHUẨN để extend agent từ bên ngoài (như USB-C cho AI).
5. MCP tools được load ĐỘNG: connect server -> tools available -> disconnect -> gone.
6. Kiến trúc plugin giúp agent mở rộng mà không sửa core code.
    """)


if __name__ == "__main__":
    main()
