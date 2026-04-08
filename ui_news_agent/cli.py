import argparse

from ui_news_agent.config import AppConfig, DEFAULT_QUERY
from ui_news_agent.pipeline import run_agent


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the UI news agent.")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Search query to run.")
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

    config = AppConfig(
        vault_dir=_path_from_string(args.vault_dir),
        model=args.model,
        max_results=args.max_results,
    )

    if args.schedule_minutes > 0:
        from ui_news_agent.scheduler import run_interval

        run_interval(args.query, args.schedule_minutes, config)
        return 0

    result = run_agent(args.query, config)
    print(f"\n\nSaved report to: {result.report_path}")
    return 0


def _path_from_string(value: str):
    from pathlib import Path

    return Path(value)

