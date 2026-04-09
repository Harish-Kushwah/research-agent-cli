from pathlib import Path

import ollama

from agent.models import LocalModelStatus
from agent.utils import append_text


PROGRESS_PHRASES = [
    "Dusting off the encyclopedia...",
    "Chasing hyperlinks through the internet jungle...",
    "Convincing the model to drink its coffee...",
    "Untangling facts from hype...",
    "Polishing the summary with extra sparkle...",
]


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



def get_local_model_status(model: str) -> LocalModelStatus:
    try:
        response = ollama.list()
    except Exception as exc:
        return LocalModelStatus(
            available=False,
            reason=(
                "Local Ollama is not available. Install Ollama, start the local service, "
                f"and pull the model '{model}'. Details: {exc}"
            ),
        )

    model_names = _extract_model_names(response)
    if model in model_names:
        return LocalModelStatus(available=True, reason="Local model is ready.")

    return LocalModelStatus(
        available=False,
        reason=(
            f"Local model '{model}' was not found. Run `ollama pull {model}` to enable summaries."
        ),
    )



def summarize_with_streaming(
    query: str,
    content: str,
    report_path: Path,
    model: str,
    memory: str = "",
    progress_callback=None,
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
    phrase_index = 0
    thinking_chars_since_update = 0
    progress_log: list[str] = []

    append_text(report_path, "## Live Stream\n\n")

    for chunk in stream:
        thinking_token = _message_field(chunk, "thinking")
        content_token = _message_field(chunk, "content")

        if thinking_token:
            if not in_thinking:
                in_thinking = True
                progress_log.append(PROGRESS_PHRASES[phrase_index])
                _emit_progress(progress_callback, PROGRESS_PHRASES[phrase_index])
            full_thinking += thinking_token
            thinking_chars_since_update += len(thinking_token)
            if thinking_chars_since_update >= 160:
                phrase_index = (phrase_index + 1) % len(PROGRESS_PHRASES)
                progress_log.append(PROGRESS_PHRASES[phrase_index])
                _emit_progress(progress_callback, PROGRESS_PHRASES[phrase_index])
                thinking_chars_since_update = 0
        elif content_token:
            if in_thinking:
                in_thinking = False
                progress_log.append("Answer is landing on the page...")
                _emit_progress(progress_callback, "Answer is landing on the page...")
                append_text(report_path, "### Progress Notes\n\n")
                for line in progress_log:
                    append_text(report_path, f"- {line}\n")
                append_text(report_path, "\n### Answer\n\n")
            elif not full_response:
                progress_log.append("Wrapping everything into a neat summary...")
                _emit_progress(progress_callback, "Wrapping everything into a neat summary...")
                append_text(report_path, "### Progress Notes\n\n")
                for line in progress_log:
                    append_text(report_path, f"- {line}\n")
                append_text(report_path, "\n### Answer\n\n")
            if progress_callback is None:
                print(content_token, end="", flush=True)
            append_text(report_path, content_token)
            full_response += content_token

    if not full_response:
        append_text(report_path, "### Progress Notes\n\n")
        for line in progress_log:
            append_text(report_path, f"- {line}\n")
    append_text(report_path, "\n")
    return full_thinking, full_response



def _emit_progress(progress_callback, message: str) -> None:
    if progress_callback is None:
        print(f"[progress] {message}", flush=True)
        return
    progress_callback(message)



def _extract_model_names(response) -> set[str]:
    if isinstance(response, dict):
        models = response.get("models", [])
    else:
        models = getattr(response, "models", [])

    names: set[str] = set()
    for model in models:
        if isinstance(model, dict):
            name = model.get("model") or model.get("name")
        else:
            name = getattr(model, "model", None) or getattr(model, "name", None)
        if name:
            names.add(name)
    return names



def _message_field(chunk, field_name: str) -> str:
    if isinstance(chunk, dict):
        return chunk.get("message", {}).get(field_name, "")

    message = getattr(chunk, "message", None)
    if message is None:
        return ""

    return getattr(message, field_name, "")
