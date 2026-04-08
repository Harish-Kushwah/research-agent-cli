from datetime import datetime

from agent.config import AppConfig, RunPaths, build_run_paths
from agent.models import RunResult
from agent.search import search_web
from agent.summarize import summarize_with_streaming
from agent.utils import append_text, slugify
from agent.vault import (
    create_report_note,
    create_source_notes,
    ensure_memory_file,
    ensure_vault_dirs,
    load_memory,
    update_index_note,
)


def run_agent(query: str, config: AppConfig | None = None) -> RunResult:
    config = config or AppConfig()
    run_paths = _prepare_run(config, query)
    ensure_vault_dirs(config, run_paths)
    ensure_memory_file(config)
    memory = load_memory(config)

    urls = search_web(query, max_results=config.max_results)
    source_notes = create_source_notes(run_paths, urls)
    create_report_note(run_paths, urls, source_notes, memory)

    full_content = "\n\n".join(note.content for note in source_notes if note.content)
    if not full_content.strip():
        append_text(
            run_paths.report_path,
            "## Live Stream\n\nNo scraped page content was available, so the model was not run.\n",
        )
        update_index_note(config, run_paths, source_notes)
        return RunResult(
            query=query,
            report_path=run_paths.report_path,
            urls=urls,
            source_notes=source_notes,
            memory_used=memory,
            thinking="",
            answer="",
        )

    thinking, answer = summarize_with_streaming(
        query=query,
        content=full_content,
        report_path=run_paths.report_path,
        model=config.model,
        memory=memory,
    )
    update_index_note(config, run_paths, source_notes)
    return RunResult(
        query=query,
        report_path=run_paths.report_path,
        urls=urls,
        source_notes=source_notes,
        memory_used=memory,
        thinking=thinking,
        answer=answer,
    )


def _prepare_run(config: AppConfig, query: str) -> RunPaths:
    timestamp = datetime.now()
    slug = slugify(query)
    return build_run_paths(config=config, query=query, slug=slug, timestamp=timestamp)
