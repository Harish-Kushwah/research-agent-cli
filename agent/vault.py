from pathlib import Path
from urllib.parse import urlparse

from agent.config import AppConfig, RunPaths
from agent.models import SourceNote
from agent.search import scrape_page
from agent.utils import slugify, write_text


def ensure_vault_dirs(config: AppConfig, run_paths: RunPaths) -> None:
    config.reports_root.mkdir(parents=True, exist_ok=True)
    config.sources_root.mkdir(parents=True, exist_ok=True)
    run_paths.report_path.parent.mkdir(parents=True, exist_ok=True)
    run_paths.sources_dir.mkdir(parents=True, exist_ok=True)



def ensure_memory_file(config: AppConfig) -> None:
    if config.memory_file.exists():
        return

    content = "\n".join(
        [
            "# Research Agent Memory",
            "",
            "Use this file to store reusable context for future runs.",
            "",
            "## Preferences",
            "",
            "- Prefer concise bullet summaries.",
            "- Highlight key risks and caveats.",
            "- Call out important companies, products, and dates when available.",
            "",
            "## Ongoing Topics",
            "",
            "- Add recurring research themes here.",
            "",
        ]
    )
    write_text(config.memory_file, content)



def load_memory(config: AppConfig) -> str:
    if not config.memory_file.exists():
        return ""
    return config.memory_file.read_text(encoding="utf-8")



def create_source_notes(run_paths: RunPaths, urls: list[str]) -> list[SourceNote]:
    source_notes: list[SourceNote] = []

    for index, url in enumerate(urls, start=1):
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "") or "source"
        source_slug = slugify(f"{index}-{domain}")
        note_name = f"Source {index} {domain}"
        note_path = run_paths.sources_dir / f"{source_slug}.md"
        vault_link = f"{run_paths.sources_link_dir}/{note_path.stem}"
        scraped = scrape_page(url)
        excerpt = scraped[:1500] if scraped else "No page content could be scraped."

        body = "\n".join(
            [
                f"# {note_name}",
                "",
                f"- URL: {url}",
                f"- Domain: {domain}",
                f"- Report: [[{run_paths.report_link_path}|{run_paths.report_title}]]",
                "",
                "## Excerpt",
                "",
                excerpt,
                "",
                "#source-note",
            ]
        )
        write_text(note_path, body)
        source_notes.append(
            SourceNote(
                name=note_name,
                path=note_path,
                vault_link=vault_link,
                url=url,
                domain=domain,
                content=scraped,
            )
        )

    return source_notes



def create_report_note(
    run_paths: RunPaths,
    urls: list[str],
    source_notes: list[SourceNote],
    memory: str,
) -> None:
    source_links = [f"- [[{item.vault_link}|{item.name}]]" for item in source_notes]
    web_links = [f"- {url}" for url in urls] or ["- No search results found"]

    mermaid_lines = [
        "```mermaid",
        "graph TD",
        '    T["[[Research]]"] --> R["Current Report"]',
    ]
    for idx, item in enumerate(source_notes, start=1):
        mermaid_lines.append(f'    R --> S{idx}["{item.name}"]')
    mermaid_lines.append("```")

    content = "\n".join(
        [
            f"# {run_paths.report_title}",
            "",
            f"- Query: {run_paths.query}",
            f"- Created: {run_paths.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- Source folder: `{run_paths.sources_dir}`",
            "- Memory file: [[memory|memory]]",
            "- Tags: #research #summary #agent",
            "",
            "## Search Results",
            "",
            *web_links,
            "",
            "## Linked Source Notes",
            "",
            *(source_links or ["- No source notes created"]),
            "",
            "## Active Memory",
            "",
            memory.strip() or "No saved memory yet.",
            "",
            "## Obsidian Graph",
            "",
            *mermaid_lines,
            "",
        ]
    )
    write_text(run_paths.report_path, content)



def update_index_note(config: AppConfig, latest_run: RunPaths, latest_sources: list[SourceNote]) -> None:
    report_files = sorted(config.reports_root.rglob("*.md"), reverse=True)
    recent_report_lines = []
    for report_file in report_files[:10]:
        relative = report_file.relative_to(config.vault_dir).with_suffix("")
        recent_report_lines.append(f"- [[{relative.as_posix()}|{report_file.stem}]]")

    latest_report_link = f"[[{latest_run.report_link_path}|{latest_run.report_title}]]"
    source_lines = [f"- [[{item.vault_link}|{item.name}]]" for item in latest_sources]

    content = "\n".join(
        [
            "# Research",
            "",
            f"- Latest report: {latest_report_link}",
            f"- Query: {latest_run.query}",
            f"- Latest source folder: `{latest_run.sources_dir}`",
            "- Memory: [[memory|memory]]",
            "- Tags: #dashboard #research",
            "",
            "## Recent Reports",
            "",
            *(recent_report_lines or ["- No reports yet"]),
            "",
            "## Latest Sources",
            "",
            *(source_lines or ["- No sources yet"]),
            "",
            "## Graph Tips",
            "",
            "- Obsidian graph view will connect the dashboard, each report, the memory note, and grouped source notes.",
            "- Each run is grouped by `Reports/YYYY/MM/DD/query-slug` and `Sources/YYYY/MM/DD/query-slug`.",
            "",
        ]
    )
    write_text(config.index_note, content)
