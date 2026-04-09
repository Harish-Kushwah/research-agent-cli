import argparse

from agent.config import AppConfig, DEFAULT_QUERY
from agent.pipeline import run_agent


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the generic research agent.")
    parser.add_argument(
        "query_text",
        nargs="*",
        help='Search query as plain text, for example: research-agent "what is OS"',
    )
    parser.add_argument(
        "--app",
        action="store_true",
        help="Launch the desktop terminal app.",
    )
    parser.add_argument("--query", default=None, help="Search query to run.")
    parser.add_argument(
        "--vault-dir",
        default="Vault/Harish",
        help="Path to the Obsidian vault folder.",
    )
    parser.add_argument(
        "--model",
        default="qwen3.5:4b",
        help="Ollama model name.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum search results to fetch.",
    )
    parser.add_argument(
        "--schedule-minutes",
        type=int,
        default=0,
        help="Run repeatedly every N minutes. Use 0 for one-off execution.",
    )
    args = parser.parse_args()

    query = args.query or " ".join(args.query_text).strip() or DEFAULT_QUERY

    if args.app:
        from agent.desktop_app import launch_desktop_app

        launch_desktop_app()
        return 0

    config = AppConfig(
        vault_dir=_path_from_string(args.vault_dir),
        model=args.model,
        max_results=args.max_results,
    )

    if args.schedule_minutes > 0:
        from agent.scheduler import run_interval

        run_interval(query, args.schedule_minutes, config)
        return 0

    result = run_agent(query, config)
    print(f"\n\nSaved report to: {result.report_path}")
    return 0


def _path_from_string(value: str):
    from pathlib import Path

    return Path(value)
