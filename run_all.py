"""
Chạy tất cả 7 bài học trong khóa học.

Chạy: python run_all.py
"""

import subprocess
import sys
import os
import time


LESSONS = [
    ("bai1_react_loop.py", "Bài 1: Agent Core Loop - ReAct Pattern"),
    ("bai2_system_prompt.py", "Bài 2: System Prompt Design - DNA của Agent"),
    ("bai3_tool_system.py", "Bài 3: Tool System - Tay và chân của Agent"),
    ("bai4_context_management.py", "Bài 4: Context Management - Quản lý bộ nhớ"),
    ("bai5_multi_agent.py", "Bài 5: Multi-Agent Orchestration - Đội quân Agent"),
    ("bai6_skills_extensibility.py", "Bài 6: Skills & Extensibility - Plugin Architecture"),
    ("bai7_guardrails_production.py", "Bài 7: Guardrails & Production - Đưa Agent ra trận"),
]


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 60)
    print("  KHÓA HỌC: KIẾN TRÚC AI CODING AGENT - PHÂN TÍCH QODER")
    print(f"  Tổng số bài: {len(LESSONS)}")
    print("=" * 60)

    results = []
    total_start = time.time()

    for filename, title in LESSONS:
        filepath = os.path.join(script_dir, filename)
        print(f"\n{'#' * 60}")
        print(f"# {title}")
        print(f"{'#' * 60}\n")

        start = time.time()
        try:
            result = subprocess.run(
                [sys.executable, filepath],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=script_dir,
            )
            elapsed = time.time() - start

            if result.returncode == 0:
                print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
                results.append((title, "PASS", f"{elapsed:.1f}s"))
            else:
                print(f"LỖI:\n{result.stderr[-300:]}")
                results.append((title, "FAIL", result.stderr[:100]))

        except subprocess.TimeoutExpired:
            results.append((title, "TIMEOUT", ">60s"))
            print("  [TIMEOUT] Bài chạy quá 60 giây, bỏ qua.")

        except Exception as e:
            results.append((title, "ERROR", str(e)))
            print(f"  [ERROR] {e}")

    total_elapsed = time.time() - total_start

    # Tóm tắt
    print(f"\n\n{'=' * 60}")
    print("  KẾT QUẢ TỔNG KẾT")
    print(f"{'=' * 60}")
    print(f"  {'Bài':<50} {'Trạng thái':<10} {'Thời gian'}")
    print(f"  {'─' * 75}")

    passed = 0
    for title, status, info in results:
        icon = "OK" if status == "PASS" else "XX"
        print(f"  [{icon}] {title:<47} {status:<10} {info}")
        if status == "PASS":
            passed += 1

    print(f"\n  Tổng: {passed}/{len(LESSONS)} bài chạy thành công")
    print(f"  Thời gian tổng: {total_elapsed:.1f}s")
    print(f"{'=' * 60}")

    return 0 if passed == len(LESSONS) else 1


if __name__ == "__main__":
    sys.exit(main())
