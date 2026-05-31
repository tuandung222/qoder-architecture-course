"""
Bài 3: Tool System - Tay và chân của Agent
============================================
Phân tích hệ thống tool của Qoder và xây dựng
tool system với function calling.

Chạy: python bai3_tool_system.py

Yêu cầu: Không cần API key (dùng MockLLM)
"""

import json
import os
import subprocess
from typing import Any


# ============================================================
# 1. PHÂN TÍCH: HỆ THỐNG TOOL CỦA QODER
# ============================================================
# Qoder có ~25 tools, chia thành 6 nhóm:

QODER_TOOL_CATEGORIES = {
    "File Operations": {
        "tools": ["Read", "Write", "Edit", "DeleteFile", "Glob", "Grep"],
        "purpose": "Đọc, ghi, sửa, xóa, tìm kiếm file",
        "design_principle": "Mỗi tool làm MỘT việc thật tốt (Unix philosophy)",
        "note": "Edit chỉ gửi diff, không gửi toàn bộ file -> tiết kiệm token",
    },
    "Terminal": {
        "tools": ["Bash", "CheckRuntime", "KillBash"],
        "purpose": "Chạy lệnh shell, kiểm tra runtime, dừng process",
        "design_principle": "Bash có timeout, background mode, output truncation",
        "note": "KillBash để dừng background processes",
    },
    "Web": {
        "tools": ["WebSearch", "WebFetch"],
        "purpose": "Tìm kiếm web, truy xuất nội dung URL",
        "design_principle": "WebFetch tự động cache 15 phút, xử lý redirect",
        "note": "Không generate URL, chỉ dùng URL từ user hoặc search results",
    },
    "Code Intelligence": {
        "tools": ["search_codebase", "search_symbol", "get_problems"],
        "purpose": "Tìm code theo ngữ nghĩa, tìm symbol, kiểm tra lỗi",
        "design_principle": "Semantic search hiểu ý nghĩa, không chỉ exact match",
        "note": "search_symbol tìm relationships: calls, extends, implements...",
    },
    "UI/Visual": {
        "tools": ["ImageGen", "show_widget"],
        "purpose": "Tạo hình ảnh, hiển thị widget tương tác",
        "design_principle": "Widget dùng CSS variables, flat design, CDN only",
        "note": "Widget hỗ trợ patch mode để update incrementally",
    },
    "Meta": {
        "tools": ["TodoWrite", "AskUserQuestion", "EnterSpecMode", "Task"],
        "purpose": "Quản lý task, hỏi user, lập kế hoạch, spawn sub-agents",
        "design_principle": "Meta tools điều khiển FLOW của agent",
        "note": "EnterSpecMode tách planning và execution thành 2 phase",
    },
}


def analyze_tool_system():
    """Phân tích hệ thống tool của Qoder."""
    print("=" * 60)
    print("PHÂN TÍCH: HỆ THỐNG TOOL CỦA QODER")
    print("=" * 60)

    for category, info in QODER_TOOL_CATEGORIES.items():
        print(f"\n{'─'*60}")
        print(f"  Nhóm: {category}")
        print(f"  Tools: {', '.join(info['tools'])}")
        print(f"  Mục đích: {info['purpose']}")
        print(f"  Nguyên tắc thiết kế: {info['design_principle']}")
        print(f"  Ghi chú: {info['note']}")

    print(f"\n{'='*60}")


# ============================================================
# 2. TOOL SCHEMA DESIGN - Thiết kế schema cho tool
# ============================================================
# Mỗi tool cần: name, description, JSON Schema cho parameters

def design_tool_schemas():
    """Thiết kế schema cho các tools cơ bản."""

    print("\n" + "=" * 60)
    print("THIẾT KẾ TOOL SCHEMA")
    print("=" * 60)

    # Schema theo chuẩn OpenAI function calling
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Đọc nội dung file. Trả về nội dung text với số dòng. Hình ảnh sẽ được hiển thị trực quan.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Đường dẫn tuyệt đối đến file cần đọc",
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Dòng bắt đầu đọc (optional, mặc định là 1)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Số dòng tối đa đọc (optional, mặc định 2000)",
                        },
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "edit_file",
                "description": "Sửa file bằng cách thay thế chính xác một đoạn text. old_string PHẢI unique trong file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Đường dẫn tuyệt đối đến file cần sửa",
                        },
                        "old_string": {
                            "type": "string",
                            "description": "Đoạn text cần thay thế (phải xuất hiện CHÍNH XÁC 1 lần trong file)",
                        },
                        "new_string": {
                            "type": "string",
                            "description": "Đoạn text thay thế",
                        },
                    },
                    "required": ["path", "old_string", "new_string"],
                },
            },
        },
    ]

    print("\n  Ví dụ tool schemas (OpenAI format):")
    for tool in tools:
        name = tool["function"]["name"]
        desc = tool["function"]["description"][:60]
        params = list(tool["function"]["parameters"]["properties"].keys())
        required = tool["function"]["parameters"]["required"]
        print(f"\n  Tool: {name}")
        print(f"    Mô tả: {desc}...")
        print(f"    Params: {params}")
        print(f"    Required: {required}")

    print(f"\n  Nguyên tắc thiết kế schema:")
    print(f"    1. Description rõ ràng: nói tool làm gì, khi nào dùng")
    print(f"    2. Required params: chỉ những param BẮT BUỘC")
    print(f"    3. Optional params: có default value hoặc behavior")
    print(f"    4. Type rõ ràng: string, integer, boolean, array, object")

    return tools


# ============================================================
# 3. TOOL EXECUTION ENGINE - Bộ máy thực thi tool
# ============================================================

class ToolExecutor:
    """
    Engine thực thi tool calls.
    Nhận tool name + args -> thực thi -> trả kết quả hoặc error.
    """

    def __init__(self, working_dir: str = "."):
        self.working_dir = os.path.abspath(working_dir)
        self.handlers: dict[str, callable] = {}
        self.call_history: list[dict] = []

    def register(self, name: str, handler: callable, description: str = ""):
        """Đăng ký một tool handler."""
        self.handlers[name] = {"handler": handler, "description": description}

    def execute(self, name: str, args: dict[str, Any]) -> dict:
        """
        Thực thi một tool call.

        Returns:
            {"success": bool, "result": str, "error": str | None}
        """
        record = {"name": name, "args": args}

        if name not in self.handlers:
            error = f"Tool '{name}' không tồn tại. Có sẵn: {list(self.handlers.keys())}"
            record["result"] = {"success": False, "result": "", "error": error}
            self.call_history.append(record)
            return record["result"]

        try:
            result = self.handlers[name]["handler"](**args)
            record["result"] = {"success": True, "result": str(result), "error": None}
        except Exception as e:
            record["result"] = {"success": False, "result": "", "error": f"{type(e).__name__}: {e}"}

        self.call_history.append(record)
        return record["result"]

    def get_history(self) -> list[dict]:
        """Lấy lịch sử tool calls."""
        return self.call_history.copy()


# ============================================================
# 4. ĐĂNG KÝ CÁC TOOL HANDLERS
# ============================================================

def create_coding_agent_tools(working_dir: str = ".") -> ToolExecutor:
    """Tạo ToolExecutor với các tools cho coding agent."""

    executor = ToolExecutor(working_dir)

    # Tool: read_file
    def read_file(path: str, offset: int = 0, limit: int = 2000) -> str:
        full_path = os.path.join(working_dir, path) if not os.path.isabs(path) else path
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        selected = lines[offset:offset + limit]
        # Thêm số dòng (giống Qoder's Read tool)
        numbered = [f"{i + offset + 1:6d} | {line}" for i, line in enumerate(selected)]
        return "".join(numbered)

    # Tool: write_file
    def write_file(path: str, content: str) -> str:
        full_path = os.path.join(working_dir, path) if not os.path.isabs(path) else path
        os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Đã ghi {len(content)} ký tự vào {path}"

    # Tool: edit_file
    def edit_file(path: str, old_string: str, new_string: str) -> str:
        full_path = os.path.join(working_dir, path) if not os.path.isabs(path) else path
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        count = content.count(old_string)
        if count == 0:
            return f"Error: Không tìm thấy đoạn text cần thay thế trong {path}"
        if count > 1:
            return f"Error: Đoạn text xuất hiện {count} lần (cần unique). Hãy thêm context."

        new_content = content.replace(old_string, new_string, 1)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"Đã sửa thành công {path}"

    # Tool: list_files (tương tự Glob đơn giản)
    def list_files(pattern: str = "*", directory: str = ".") -> str:
        import glob as glob_module
        full_dir = os.path.join(working_dir, directory) if not os.path.isabs(directory) else directory
        search = os.path.join(full_dir, pattern)
        files = glob_module.glob(search, recursive=True)
        if not files:
            return f"Không tìm thấy file matching '{pattern}' trong {directory}"
        return "\n".join(sorted(files))

    # Tool: run_command
    def run_command(command: str, timeout: int = 30) -> str:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        return output.strip() if output.strip() else "(không có output)"

    # Đăng ký tất cả tools
    executor.register("read_file", read_file, "Đọc nội dung file với số dòng")
    executor.register("write_file", write_file, "Ghi nội dung vào file")
    executor.register("edit_file", edit_file, "Sửa file bằng exact string replacement")
    executor.register("list_files", list_files, "Tìm file theo glob pattern")
    executor.register("run_command", run_command, "Chạy lệnh shell")

    return executor


# ============================================================
# 5. PARALLEL vs SEQUENTIAL TOOL CALLS
# ============================================================

def demo_parallel_vs_sequential():
    """
    Minh họa sự khác biệt giữa parallel và sequential tool calls.

    Trong Qoder:
    - Sequential: Đọc file -> Sửa file (phụ thuộc nhau)
    - Parallel: Đọc 3 file cùng lúc (độc lập)
    """

    print("\n" + "=" * 60)
    print("PARALLEL vs SEQUENTIAL TOOL CALLS")
    print("=" * 60)

    print("""
  SEQUENTIAL (tuần tự) - Khi tool sau PHỤ THUỘC tool trước:

    User: "Fix bug trong file login.py"

    Step 1: read_file("login.py")        <-- Cần đọc trước
    Step 2: edit_file("login.py", ...)   <-- Phụ thuộc kết quả Step 1
    Step 3: run_command("pytest")        <-- Phụ thuộc Step 2 đã sửa xong


  PARALLEL (song song) - Khi các tool ĐỘC LẬP nhau:

    User: "Review toàn bộ auth module"

    Step 1 (đồng thời):
      ├── read_file("auth/login.py")
      ├── read_file("auth/register.py")
      └── read_file("auth/middleware.py")

    Step 2: Phân tích tổng hợp kết quả từ 3 file


  QUY TẮC:
    - Độc lập → PARALLEL (nhanh hơn, giảm latency)
    - Phụ thuộc → SEQUENTIAL (cần kết quả bước trước)
""")


# ============================================================
# 6. DEMO: TOOL EXECUTION THỰC TẾ
# ============================================================

def demo_tool_execution():
    """Demo thực thi tool thực tế."""

    print("\n" + "=" * 60)
    print("DEMO: TOOL EXECUTION THỰC TẾ")
    print("=" * 60)

    # Tạo executor
    executor = create_coding_agent_tools(working_dir=".")

    # Bước 1: Tạo file
    print("\n  Bước 1: Tạo file demo...")
    result = executor.execute("write_file", {
        "path": "demo_tool_test.py",
        "content": "def hello():\n    print('Hello World')\n\ndef goodbye():\n    print('Goodbye')\n",
    })
    print(f"    Kết quả: {result['result']}")

    # Bước 2: Đọc file
    print("\n  Bước 2: Đọc file vừa tạo...")
    result = executor.execute("read_file", {"path": "demo_tool_test.py"})
    print(f"    Kết quả:\n{result['result']}")

    # Bước 3: Sửa file (edit_file - giống Qoder's Edit tool)
    print("\n  Bước 3: Sửa file bằng edit_file...")
    result = executor.execute("edit_file", {
        "path": "demo_tool_test.py",
        "old_string": "    print('Hello World')",
        "new_string": "    print('Hello, Qoder Architecture Course!')",
    })
    print(f"    Kết quả: {result['result']}")

    # Bước 4: Chạy file
    print("\n  Bước 4: Chạy file để kiểm tra...")
    result = executor.execute("run_command", {
        "command": "cd . && python3 -c \"\nimport sys\nsys.path.insert(0, '.')\nexec(open('demo_tool_test.py').read())\nhello()\n\"",
    })
    print(f"    Kết quả: {result['result']}")

    # Bước 5: Xem lịch sử tool calls
    print("\n  Lịch sử tool calls:")
    for i, record in enumerate(executor.get_history(), 1):
        status = "OK" if record["result"]["success"] else "FAIL"
        print(f"    {i}. [{status}] {record['name']}({list(record['args'].keys())})")


# ============================================================
# 7. MAIN
# ============================================================

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║  BÀI 3: TOOL SYSTEM - TAY VÀ CHÂN CỦA AGENT           ║
║                                                          ║
║  1. Phân tích hệ thống tool của Qoder                   ║
║  2. Thiết kế tool schema                                 ║
║  3. Xây dựng Tool Execution Engine                       ║
║  4. Parallel vs Sequential calls                         ║
║  5. Demo thực tế                                        ║
╚══════════════════════════════════════════════════════════╝
    """)

    analyze_tool_system()
    design_tool_schemas()
    demo_parallel_vs_sequential()
    demo_tool_execution()

    print("\n" + "=" * 60)
    print("TAKEAWAY")
    print("=" * 60)
    print("""
1. Tools = khả năng hành động của agent. Không có tools = chỉ biết nói.
2. Mỗi tool cần SCHEMA RÕ RÀNG (JSON Schema) để LLM biết cách dùng.
3. Edit tool chỉ gửi DIFF, không gửi cả file -> tiết kiệm token.
4. ToolExecutor pattern: register handlers -> execute by name -> track history.
5. Parallel calls khi tools ĐỘC LẬP, Sequential khi PHỤ THUỘC.
6. Error handling: LUÔN trả về lỗi cho LLM, đừng crash.
    """)


if __name__ == "__main__":
    main()
