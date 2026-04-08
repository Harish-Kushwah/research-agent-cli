from pathlib import Path

import ollama

from agent.utils import append_text


def build_prompt(query: str, content: str, memory: str = "") -> str:
    memory_block = memory.strip() or "No saved memory yet."
    return f"""
You are a generic research assistant.

Use the web content below to produce:
1. A concise summary
2. Key findings
3. Important examples, tools, companies, or entities mentioned
4. Risks, caveats, and open questions
5. Key takeaways

Rules:
- Keep it short and structured
- Use bullet points
- Mention when the web content is weak or incomplete
- Prefer concrete details over vague claims
- Use the saved memory when it helps with formatting and continuity, but do not invent facts

Saved memory:
{memory_block}

Query:
{query}

Content:
{content[:12000]}
"""


def summarize_with_streaming(
    query: str,
    content: str,
    report_path: Path,
    model: str,
    memory: str = "",
) -> tuple[str, str]:
    prompt = build_prompt(query, content, memory=memory)
    stream = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        think=True,
        stream=True,
    )

    full_response = ""
    full_thinking = ""
    in_thinking = False

    append_text(report_path, "## Live Stream\n\n")

    for chunk in stream:
        thinking_token = _message_field(chunk, "thinking")
        content_token = _message_field(chunk, "content")

        if thinking_token:
            if not in_thinking:
                print("Thinking:\n", end="", flush=True)
                append_text(report_path, "### Thinking\n\n")
                in_thinking = True
            print(thinking_token, end="", flush=True)
            append_text(report_path, thinking_token)
            full_thinking += thinking_token
        elif content_token:
            if in_thinking:
                print("\n\nAnswer:\n", end="", flush=True)
                append_text(report_path, "\n\n### Answer\n\n")
                in_thinking = False
            elif not full_response:
                append_text(report_path, "### Answer\n\n")
            print(content_token, end="", flush=True)
            append_text(report_path, content_token)
            full_response += content_token

    append_text(report_path, "\n")
    return full_thinking, full_response


def _message_field(chunk, field_name: str) -> str:
    if isinstance(chunk, dict):
        return chunk.get("message", {}).get(field_name, "")

    message = getattr(chunk, "message", None)
    if message is None:
        return ""

    return getattr(message, field_name, "")
