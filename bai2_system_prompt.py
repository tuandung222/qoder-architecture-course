"""
Bài 2: System Prompt Design - "DNA" của Agent
===============================================
Phân tích cấu trúc system prompt của Qoder và xây dựng
một system prompt có cấu trúc tương tự cho coding agent.

Chạy: python bai2_system_prompt.py

Không cần API key - bài này tập trung vào prompt design.
"""

from datetime import datetime


# ============================================================
# 1. PHÂN TÍCH: CẤU TRÚC SYSTEM PROMPT CỦA QODER
# ============================================================
# System prompt của Qoder có 7 LAYERS (từ ngoài vào trong):
#
# Layer 1: IDENTITY       - "Tôi là ai?"
# Layer 2: TONE & STYLE   - "Tôi nói chuyện thế nào?"
# Layer 3: SAFETY RULES   - "Tôi KHÔNG được làm gì?"
# Layer 4: TOOL POLICIES  - "Tôi dùng tool như thế nào?"
# Layer 5: TASK GUIDELINES - "Tôi làm việc thế nào?"
# Layer 6: DYNAMIC CONTEXT - "Tôi đang ở đâu?"
# Layer 7: AVAILABLE SKILLS - "Tôi có khả năng gì?"


def analyze_qoder_prompt_structure():
    """Phân tích cấu trúc system prompt của Qoder từ internal knowledge."""

    print("=" * 60)
    print("PHÂN TÍCH: CẤU TRÚC SYSTEM PROMPT CỦA QODER")
    print("=" * 60)

    layers = [
        {
            "layer": 1,
            "name": "IDENTITY",
            "purpose": "Định nghĩa tên, vai trò, giới hạn của agent",
            "examples": [
                "You are Qoder, an AI coding assistant.",
                "Always identify yourself as Qoder.",
                "Do not speculate about underlying model.",
            ],
            "why": "Ngăn agent tự nhận mình là GPT, Claude, etc. Tạo brand consistency.",
        },
        {
            "layer": 2,
            "name": "TONE & STYLE",
            "purpose": "Kiểm soát cách agent giao tiếp với user",
            "examples": [
                "Only use emojis if user explicitly requests.",
                "Responses should be short and concise.",
                "Use Github-flavored markdown.",
                "RESPOND IN THE LANGUAGE THE USER USED.",
            ],
            "why": "Đảm bảo UX nhất quán. Tránh agent quá nhiệt tình hoặc dùng emoji lung tung.",
        },
        {
            "layer": 3,
            "name": "SAFETY RULES (GUARDRAILS)",
            "purpose": "Ngăn chặn hành vi nguy hiểm hoặc không mong muốn",
            "examples": [
                "Refuse to create code that may be used maliciously.",
                "Do not assist with credential discovery/harvesting.",
                "NEVER generate or guess URLs.",
                "NEVER commit unless explicitly asked.",
                "NEVER push to remote without asking.",
            ],
            "why": "Phòng chống OWASP top 10, tránh tai nạn (commit nhầm, push nhầm).",
        },
        {
            "layer": 4,
            "name": "TOOL USAGE POLICIES",
            "purpose": "Hướng dẫn agent cách và khi nào dùng từng tool",
            "examples": [
                "NEVER read code you haven't read before modifying.",
                "Use Glob instead of find command.",
                "Use Edit instead of sed/awk.",
                "Reserve bash for actual system commands.",
                "Run lint/typecheck after code changes.",
            ],
            "why": "Đảm bảo agent dùng tool đúng cách, tránh side effects không mong muốn.",
        },
        {
            "layer": 5,
            "name": "TASK EXECUTION GUIDELINES",
            "purpose": "Quy trình chuẩn khi thực hiện một task",
            "examples": [
                "Use TodoWrite to plan tasks.",
                "Use AskUserQuestion when uncertain.",
                "Use EnterSpecMode for non-trivial tasks.",
                "Avoid over-engineering.",
                "ALWAYS verify with tests after coding.",
            ],
            "why": "Agent làm việc có hệ thống, không đoán mò, không over-engineering.",
        },
        {
            "layer": 6,
            "name": "DYNAMIC CONTEXT",
            "purpose": "Thông tin môi trường được inject mỗi session",
            "examples": [
                "Working directory: /Users/dev/project",
                "Platform: darwin (macOS)",
                f"Today: {datetime.now().strftime('%Y-%m-%d')}",
                "Is git repo: Yes/No",
            ],
            "why": "Agent cần biết nó đang chạy ở đâu, trên máy nào, ngày nào.",
        },
        {
            "layer": 7,
            "name": "AVAILABLE SKILLS",
            "purpose": "Danh sách khả năng mở rộng có sẵn",
            "examples": [
                "ui-designer: Web UI design",
                "vercel-deploy: Deploy to Vercel",
                "create-skill: Create new skill",
            ],
            "why": "Agent biết mình có thể làm gì ngoài tools cơ bản.",
        },
    ]

    for layer in layers:
        print(f"\n{'─'*60}")
        print(f"  Layer {layer['layer']}: {layer['name']}")
        print(f"  Mục đích: {layer['purpose']}")
        print(f"  Tại sao cần: {layer['why']}")
        print(f"  Ví dụ:")
        for ex in layer["examples"]:
            print(f"    - {ex}")

    print(f"\n{'='*60}")
    return layers


# ============================================================
# 2. XÂY DỰNG: SYSTEM PROMPT CÓ CẤU TRÚC TƯƠNG TỰ
# ============================================================


class SystemPromptBuilder:
    """
    Builder pattern để xây dựng system prompt có cấu trúc.
    Mỗi layer là một method riêng, dễ dàng thêm/bớt/tùy chỉnh.
    """

    def __init__(self):
        self.sections = []

    def add_identity(self, name: str, role: str) -> "SystemPromptBuilder":
        """Layer 1: Identity"""
        self.sections.append(f"""# Who you are
You are {name}, {role}.
Always identify yourself as {name}.
Do not disclose your underlying model or architecture.""")
        return self

    def add_tone(
        self, style: str = "concise", language_rule: str = "match user"
    ) -> "SystemPromptBuilder":
        """Layer 2: Tone & Style"""
        lang = (
            "Respond in the same language the user uses."
            if language_rule == "match user"
            else f"Always respond in {language_rule}."
        )
        self.sections.append(f"""# Tone and style
- Be {style}. Avoid unnecessary verbosity.
- Use markdown for formatting.
- Do not use emojis unless the user explicitly requests them.
- {lang}
- Be professional and objective. Do not over-praise.""")
        return self

    def add_safety(self, rules: list[str] | None = None) -> "SystemPromptBuilder":
        """Layer 3: Safety Rules"""
        default_rules = [
            "Refuse to create or modify code that could be used maliciously.",
            "Never execute destructive commands without explicit user confirmation.",
            "Never commit or push code unless the user explicitly asks.",
            "Do not guess or generate URLs.",
            "If you notice security vulnerabilities in code, point them out and fix them.",
        ]
        rules = rules or default_rules
        rules_text = "\n".join(f"- {r}" for r in rules)
        self.sections.append(f"""# Safety rules
{rules_text}""")
        return self

    def add_tool_policies(
        self, policies: list[str] | None = None
    ) -> "SystemPromptBuilder":
        """Layer 4: Tool Usage policies"""
        default_policies = [
            "Always read a file before modifying it.",
            "Use dedicated file tools (Read, Edit, Write) instead of shell equivalents.",
            "After making code changes, run linting and tests to verify.",
            "When searching for files, use glob patterns. When searching content, use grep.",
            "Never use shell echo or printf to communicate with the user.",
        ]
        policies = policies or default_policies
        policies_text = "\n".join(f"- {p}" for p in policies)
        self.sections.append(f"""# Tool usage policies
{policies_text}""")
        return self

    def add_task_guidelines(
        self, guidelines: list[str] | None = None
    ) -> "SystemPromptBuilder":
        """Layer 5: Task Execution Guidelines"""
        default_guidelines = [
            "Plan before acting: break complex tasks into steps.",
            "Ask the user for clarification when requirements are ambiguous.",
            "Avoid over-engineering: only make changes that are requested.",
            "Verify your changes work: run tests, check output.",
            "Report results honestly: if something fails, say so.",
        ]
        guidelines = guidelines or default_guidelines
        guidelines_text = "\n".join(f"- {g}" for g in guidelines)
        self.sections.append(f"""# Task execution guidelines
{guidelines_text}""")
        return self

    def add_dynamic_context(
        self, working_dir: str, platform: str, extra: dict | None = None
    ) -> "SystemPromptBuilder":
        """Layer 6: Dynamic Context (injected per session)"""
        extra_text = ""
        if extra:
            extra_text = "\n".join(f"- {k}: {v}" for k, v in extra.items())
        self.sections.append(f"""# Current environment
- Working directory: {working_dir}
- Platform: {platform}
- Date: {datetime.now().strftime("%Y-%m-%d")}
{extra_text}""")
        return self

    def add_skills(self, skills: list[dict]) -> "SystemPromptBuilder":
        """Layer 7: Available Skills"""
        if not skills:
            return self
        skills_text = "\n".join(f"- {s['name']}: {s['description']}" for s in skills)
        self.sections.append(f"""# Available skills
{skills_text}""")
        return self

    def build(self) -> str:
        """Build final system prompt từ tất cả sections."""
        return "\n\n".join(self.sections)


# ============================================================
# 3. SO SÁNH: PROMPT QODER vs PROMPT TỰ XÂY DỰNG
# ============================================================


def compare_prompts():
    """So sánh system prompt Qoder vs prompt tự xây dựng."""

    print("\n" + "=" * 60)
    print("SO SÁNH: QODER vs TỰ XÂY DỰNG")
    print("=" * 60)

    comparisons = [
        {
            "aspect": "Identity",
            "qoder": "Qoder, AI coding assistant. Refuse to reveal model.",
            "ours": "Configurable name + role. Same refusal rule.",
        },
        {
            "aspect": "Language",
            "qoder": "Match user language. Respond in Vietnamese if user does.",
            "ours": "Same: auto-detect and match.",
        },
        {
            "aspect": "Safety",
            "qoder": "~15 rules: no malicious code, no URL guessing, no auto-commit, OWASP check.",
            "ours": "5 core rules. Extensible via add_safety().",
        },
        {
            "aspect": "Tool policies",
            "qoder": "~20 rules: prefer dedicated tools, always read before edit, git safety protocol.",
            "ours": "5 core policies. Extensible via add_tool_policies().",
        },
        {
            "aspect": "Git safety",
            "qoder": "Detailed: check authorship before amend, never force push, HEREDOC for messages.",
            "ours": "Simplified: never commit/push without permission.",
        },
        {
            "aspect": "Context",
            "qoder": "Dynamic: dir, platform, OS version, git status, date, skills list.",
            "ours": "Dynamic: dir, platform, date, extra fields.",
        },
        {
            "aspect": "Size",
            "qoder": "~5000+ tokens (rất dài và chi tiết)",
            "ours": "~500 tokens (ngắn gọn, dễ hiểu)",
        },
    ]

    for c in comparisons:
        print(f"\n  [{c['aspect']}]")
        print(f"    Qoder: {c['qoder']}")
        print(f"    Ours:  {c['ours']}")


# ============================================================
# 4. MAIN
# ============================================================


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║  BÀI 2: SYSTEM PROMPT DESIGN - "DNA" CỦA AGENT        ║
║                                                          ║
║  1. Phân tích cấu trúc prompt của Qoder                 ║
║  2. Xây dựng prompt builder tương tự                    ║
║  3. So sánh Qoder vs tự xây dựng                        ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Phần 1: Phân tích Qoder
    analyze_qoder_prompt_structure()

    # Phần 2: Xây dựng prompt
    print("\n\n" + "=" * 60)
    print("XÂY DỰNG: SYSTEM PROMPT BẰNG BUILDER PATTERN")
    print("=" * 60)

    builder = SystemPromptBuilder()
    prompt = (
        builder.add_identity("CodeHelper", "an AI coding assistant")
        .add_tone(style="concise and technical", language_rule="match user")
        .add_safety()
        .add_tool_policies()
        .add_task_guidelines()
        .add_dynamic_context(
            working_dir="/Users/dev/myproject",
            platform="linux",
            extra={"Node version": "20.x", "Package manager": "npm"},
        )
        .add_skills([
            {"name": "deploy", "description": "Deploy to production server"},
            {"name": "review", "description": "Review code changes"},
        ])
        .build()
    )

    print("\n--- Generated System Prompt ---")
    print(prompt)
    print("--- End ---")
    print(f"\nSố từ (xấp xỉ): {len(prompt.split())}")

    # Phần 3: So sánh
    compare_prompts()

    # Tóm tắt
    print("\n" + "=" * 60)
    print("TAKEAWAY")
    print("=" * 60)
    print("""
1. System prompt là "DNA" của agent - nó quyết định MỌI hành vi.
2. Prompt tốt có CẤU TRÚC RÕ RÀNG theo layers, không phải một kho text.
3. Qoder's prompt rất dài (~5000+ tokens) vì nó cần cover nhiều edge cases.
4. Builder pattern giúp quản lý prompt dễ dàng: thêm/bớt/tùy chỉnh từng layer.
5. Dynamic context (env, date, skills) ĐƯỢC INJECT MỖI SESSION - không hardcode.
    """)


if __name__ == "__main__":
    main()
