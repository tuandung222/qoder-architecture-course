"""
Bài 1: Agent Core Loop - ReAct Pattern
=======================================
Xây dựng một coding agent cơ bản với vòng lặp ReAct:
  Think -> Act (tool call) -> Observe -> Decide -> Repeat

Chạy: python bai1_react_loop.py

Yêu cầu: pip install openai (hoặc dùng bất kỳ LLM provider nào)
"""

import json
from typing import Any


# ============================================================
# 1. TOOL DEFINITIONS - "Tay và chân" của Agent
# ============================================================
# Mỗi tool có: name, description, parameters (JSON Schema)
# Đây chính là cách Qoder định nghĩa 20+ tools của mình

TOOLS = {
    "read_file": {
        "description": "Đọc nội dung file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Đường dẫn file"}
            },
            "required": ["path"],
        },
    },
    "write_file": {
        "description": "Ghi nội dung vào file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Đường dẫn file"},
                "content": {"type": "string", "description": "Nội dung ghi"},
            },
            "required": ["path", "content"],
        },
    },
    "run_command": {
        "description": "Chạy lệnh shell",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Lệnh cần chạy"},
            },
            "required": ["command"],
        },
    },
}


# ============================================================
# 2. TOOL EXECUTION - Thực thi tool khi LLM yêu cầu
# ============================================================
# Khi LLM trả về tool_call, ta thực thi và trả kết quả lại

def execute_tool(name: str, args: dict[str, Any]) -> str:
    """Thực thi tool và trả về kết quả (hoặc error message)."""
    try:
        if name == "read_file":
            with open(args["path"], "r", encoding="utf-8") as f:
                return f.read()

        elif name == "write_file":
            with open(args["path"], "w", encoding="utf-8") as f:
                f.write(args["content"])
            return f"Đã ghi thành công vào {args['path']}"

        elif name == "run_command":
            import subprocess
            result = subprocess.run(
                args["command"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout + result.stderr
            return output if output else "(không có output)"

        else:
            return f"Error: Tool '{name}' không tồn tại"

    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


# ============================================================
# 3. SYSTEM PROMPT - "DNA" của Agent
# ============================================================
# Đây là phần quyết định hành vi của agent
# (Sẽ học chi tiết ở Bài 2)

SYSTEM_PROMPT = """Bạn là một AI Coding Agent. Bạn có khả năng đọc, ghi file và chạy lệnh shell.

QUY TẮC:
1. LUÔN đọc file trước khi sửa
2. Sau khi sửa, LUÔN chạy lệnh để kiểm tra
3. Giải thích ngắn gọn từng bước bạn đang làm
4. Khi hoàn thành task, nói DONE

TOOLS CÓ SẴN:
- read_file(path): Đọc nội dung file
- write_file(path, content): Ghi nội dung vào file
- run_command(command): Chạy lệnh shell

Hãy dùng tools bằng cách gọi function call.
"""


# ============================================================
# 4. REACT LOOP - Bộ não của Agent
# ============================================================
# Đây là phần QUAN TRỌNG NHẤT - core loop của mọi agent

def react_loop(user_request: str, llm_call_fn, max_iterations: int = 10):
    """
    ReAct Loop - vòng lặp cơ bản của mọi AI Agent.

    Flow:
      1. Nhận yêu cầu từ user
      2. Think: LLM phân tích và quyết định bước tiếp theo
      3. Act:  Nếu LLM muốn gọi tool -> thực thi tool
      4. Observe: Lấy kết quả tool, thêm vào conversation
      5. Decide: LLM đọc kết quả, quyết định:
         - Cần làm thêm? -> quay lại bước 2
         - Xong rồi? -> trả lời user
      6. Repeat cho đến khi xong hoặc đạt max iterations

    Args:
        user_request: Yêu cầu từ người dùng
        llm_call_fn: Function gọi LLM (nhận messages, trả response)
        max_iterations: Số vòng lặp tối đa (chặn vòng lặp vô hạn)
    """
    # Khởi tạo conversation history
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_request},
    ]

    print(f"\n{'='*60}")
    print(f"YÊU CẦU CỦA USER: {user_request}")
    print(f"{'='*60}\n")

    for i in range(max_iterations):
        print(f"--- Vòng lặp {i + 1}/{max_iterations} ---")

        # BƯỚC 1: THINK - Gọi LLM để phân tích
        response = llm_call_fn(messages)

        # BƯỚC 2: DECIDE - LLM quyết định làm gì?
        if response.get("tool_calls"):
            # LLM muốn sử dụng tool -> ACT
            # Thêm assistant message với tool calls vào history
            messages.append({
                "role": "assistant",
                "content": response.get("content", ""),
                "tool_calls": response["tool_calls"],
            })

            # Thực thi TỪNG tool call
            for tool_call in response["tool_calls"]:
                name = tool_call["name"]
                args = tool_call["args"]
                print(f"  [ACT]  Gọi tool: {name}({json.dumps(args, ensure_ascii=False)})")

                # BƯỚC 3: OBSERVE - Thực thi và lấy kết quả
                result = execute_tool(name, args)
                print(f"  [OBS]  Kết quả: {result[:200]}{'...' if len(result) > 200 else ''}")

                # Thêm kết quả tool vào conversation để LLM đọc
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result,
                })

        else:
            # LLM không gọi tool -> có thể là final answer
            final_text = response.get("content", "")
            print(f"  [THINK] {final_text[:200]}")

            # Kiểm tra nếu agent báo DONE
            if "DONE" in final_text.upper():
                print(f"\n{'='*60}")
                print("AGENT HOÀN THÀNH TASK")
                print(f"{'='*60}")
                return final_text

            # Nếu chưa DONE nhưng không có tool call -> hỏi user
            print("  Agent không gọi tool và chưa báo DONE. Dừng vòng lặp.")
            return final_text

    print(f"\n[WARNING] Đạt max iterations ({max_iterations}). Dừng vòng lặp.")
    return "Không thể hoàn thành task trong giới hạn vòng lặp."


# ============================================================
# 5. MOCK LLM - Để chạy demo không cần API key
# ============================================================
# Trong thực tế, bạn sẽ thay bằng OpenAI/Anthropic API call

class MockLLM:
    """
    Mock LLM để demo ReAct loop không cần API key.
    Trong thực tế, thay bằng: openai.chat.completions.create()
    """

    def __init__(self):
        self.call_count = 0

    def __call__(self, messages: list[dict]) -> dict:
        self.call_count += 1

        # Script: tạo ra trình tự tool calls cố định để demo
        if self.call_count == 1:
            # Bước 1: Đọc file cần fix
            print("  [THINK] Tôi cần đọc file trước khi sửa...")
            return {
                "content": "",
                "tool_calls": [{
                    "id": "call_1",
                    "name": "read_file",
                    "args": {"path": "demo_app.py"},
                }],
            }

        elif self.call_count == 2:
            # Bước 2: Ghi file đã fix
            print("  [THINK] Tôi đã tìm thấy lỗi. Tôi sẽ ghi file mới...")
            return {
                "content": "",
                "tool_calls": [{
                    "id": "call_2",
                    "name": "write_file",
                    "args": {
                        "path": "demo_app.py",
                        "content": "# Fixed version\nprint('Hello, World!')\n",
                    },
                }],
            }

        elif self.call_count == 3:
            # Bước 3: Chạy file để verify
            print("  [THINK] Tôi sẽ chạy file để kiểm tra...")
            return {
                "content": "",
                "tool_calls": [{
                    "id": "call_3",
                    "name": "run_command",
                    "args": {"command": "python3 demo_app.py"},
                }],
            }

        else:
            # Bước 4: Báo hoàn thành
            print("  [THINK] Mọi thứ đã xong!")
            return {
                "content": "Đã fix xong file demo_app.py và chạy thành công. DONE",
                "tool_calls": None,
            }


# ============================================================
# 6. MAIN - Chạy demo
# ============================================================

def main():
    # Tạo file demo trước
    with open("demo_app.py", "w", encoding="utf-8") as f:
        f.write("print('Hello World')  # Thiếu dấu chấm than\n")

    print("""
╔══════════════════════════════════════════════════════════╗
║  BÀI 1: AGENT CORE LOOP - ReAct Pattern                ║
║                                                          ║
║  Demo: Coding Agent fix một file Python đơn giản        ║
║                                                          ║
║  Flow: Think -> Act (tool) -> Observe -> Decide -> ... ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Chạy ReAct loop với Mock LLM
    mock_llm = MockLLM()
    result = react_loop(
        user_request="Fix file demo_app.py, thêm dấu chấm than vào cuối chuỗi Hello World",
        llm_call_fn=mock_llm,
        max_iterations=10,
    )

    print(f"\nKết quả cuối: {result}")
    print(f"Tổng số lần gọi LLM: {mock_llm.call_count}")


if __name__ == "__main__":
    main()
