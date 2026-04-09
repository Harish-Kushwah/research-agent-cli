import argparse
import sys
from pathlib import Path

from agent.config import AppConfig, DEFAULT_MODEL, DEFAULT_QUERY, DEFAULT_RESPONSE_MODE
from agent.pipeline import run_agent
from agent.storage import (
    clear_preferences,
    delete_preference,
    get_preference,
    initialize_storage,
    list_preferences,
    set_preference,
)


VAULT_PREF_KEY = "vault_dir"
MODEL_PREF_KEY = "model"
MAX_RESULTS_PREF_KEY = "max_results"
RESPONSE_MODE_PREF_KEY = "response_mode"
KNOWN_PREFERENCE_KEYS = (VAULT_PREF_KEY, MODEL_PREF_KEY, MAX_RESULTS_PREF_KEY, RESPONSE_MODE_PREF_KEY)
PREFERENCE_HELP = {
    VAULT_PREF_KEY: ("Default Obsidian vault or output folder path", r"D:\MyVault"),
    MODEL_PREF_KEY: ("Default Ollama model name used for summarization", "qwen3.5:4b"),
    MAX_RESULTS_PREF_KEY: ("Default number of search results to fetch", "5"),
    RESPONSE_MODE_PREF_KEY: ("How results should be returned: 'full' or 'references_only'", "references_only"),
}
VALID_RESPONSE_MODES = {"full", "references_only"}



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
    parser.add_argument(
        "--preferences",
        action="store_true",
        help="Open an interactive preferences menu.",
    )
    parser.add_argument(
        "--show-preferences",
        action="store_true",
        help="List saved preferences and exit.",
    )
    parser.add_argument(
        "--list-preference-keys",
        action="store_true",
        help="Show supported preference keys with sample values and exit.",
    )
    parser.add_argument(
        "--delete-preference",
        metavar="KEY",
        help="Delete a saved preference and exit.",
    )
    parser.add_argument(
        "--set-preference",
        nargs=2,
        metavar=("KEY", "VALUE"),
        help="Set a preference directly and exit.",
    )
    parser.add_argument(
        "--reset-preferences",
        action="store_true",
        help="Delete all saved preferences and exit.",
    )
    parser.add_argument("--query", default=None, help="Search query to run.")
    parser.add_argument(
        "--vault-dir",
        default=None,
        help="Path to the Obsidian vault folder.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Ollama model name.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        help="Maximum search results to fetch.",
    )
    parser.add_argument(
        "--schedule-minutes",
        type=int,
        default=0,
        help="Run repeatedly every N minutes. Use 0 for one-off execution.",
    )
    args = parser.parse_args()

    initialize_storage()

    if args.preferences:
        return preferences_menu()
    if args.show_preferences:
        print_preferences()
        return 0
    if args.list_preference_keys:
        print_preference_keys()
        return 0
    if args.delete_preference:
        removed = delete_preference(args.delete_preference)
        print(f"Deleted: {args.delete_preference}" if removed else f"Not found: {args.delete_preference}")
        return 0
    if args.set_preference:
        key, value = args.set_preference
        if key == RESPONSE_MODE_PREF_KEY and value not in VALID_RESPONSE_MODES:
            print("response_mode must be one of: full, references_only")
            return 1
        set_preference(key, value)
        print(f"Saved preference: {key}={value}")
        return 0
    if args.reset_preferences:
        clear_preferences()
        print("All saved preferences were deleted.")
        return 0

    query = args.query or " ".join(args.query_text).strip() or DEFAULT_QUERY

    if args.app:
        from agent.desktop_app import launch_desktop_app

        launch_desktop_app()
        return 0

    vault_dir = resolve_vault_dir(args.vault_dir)
    model = resolve_model(args.model)
    max_results = resolve_max_results(args.max_results)
    response_mode = resolve_response_mode(None)
    config = AppConfig(
        vault_dir=vault_dir,
        model=model,
        max_results=max_results,
        response_mode=response_mode,
    )

    if args.schedule_minutes > 0:
        from agent.scheduler import run_interval

        run_interval(query, args.schedule_minutes, config)
        return 0

    result = run_agent(query, config)
    if config.response_mode == "references_only":
        print("\nReferences only mode is enabled. Model summarization was skipped.")
        if result.urls:
            print("References:")
            for url in result.urls:
                print(f"- {url}")
    elif not result.model_status.available:
        print(f"\n[info] Search completed, but summary was skipped. {result.model_status.reason}")
    print(f"\n\nSaved report to: {result.report_path}")
    return 0



def preferences_menu() -> int:
    if not sys.stdin.isatty():
        print("Interactive preferences menu requires a terminal.")
        return 1

    while True:
        print("\nPreferences Menu")
        print("1. Show preferences")
        print("2. Show supported preference keys")
        print("3. Update vault path")
        print("4. Update model")
        print("5. Update max results")
        print("6. Update response mode")
        print("7. Delete one preference")
        print("8. Reset all preferences")
        print("9. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            print_preferences()
        elif choice == "2":
            print_preference_keys()
        elif choice == "3":
            value = input("Enter vault path: ").strip()
            if value:
                set_preference(VAULT_PREF_KEY, str(_normalize_path(value)))
                print("Vault path updated.")
        elif choice == "4":
            value = input("Enter model name: ").strip()
            if value:
                set_preference(MODEL_PREF_KEY, value)
                print("Model updated.")
        elif choice == "5":
            value = input("Enter max results: ").strip()
            if value.isdigit():
                set_preference(MAX_RESULTS_PREF_KEY, value)
                print("Max results updated.")
            else:
                print("Please enter a valid number.")
        elif choice == "6":
            value = input("Enter response mode (full/references_only): ").strip()
            if value in VALID_RESPONSE_MODES:
                set_preference(RESPONSE_MODE_PREF_KEY, value)
                print("Response mode updated.")
            else:
                print("Please enter either 'full' or 'references_only'.")
        elif choice == "7":
            print(f"Known keys: {', '.join(KNOWN_PREFERENCE_KEYS)}")
            key = input("Enter key to delete: ").strip()
            removed = delete_preference(key)
            print(f"Deleted: {key}" if removed else f"Not found: {key}")
        elif choice == "8":
            confirm = input("Delete all saved preferences? (y/N): ").strip().lower()
            if confirm == "y":
                clear_preferences()
                print("All preferences deleted.")
        elif choice == "9":
            return 0
        else:
            print("Please choose a valid option.")



def print_preferences() -> None:
    rows = list_preferences()
    if not rows:
        print("No saved preferences.")
        return

    print("Saved preferences:")
    for key, value, updated_at in rows:
        print(f"- {key} = {value} (updated {updated_at})")



def print_preference_keys() -> None:
    print("Supported preference keys:")
    for key, (meaning, sample) in PREFERENCE_HELP.items():
        print(f"- {key}")
        print(f"  Meaning: {meaning}")
        print(f"  Sample:  {sample}")



def resolve_vault_dir(cli_value: str | None) -> Path:
    if cli_value:
        vault_dir = _normalize_path(cli_value)
        set_preference(VAULT_PREF_KEY, str(vault_dir))
        return vault_dir

    saved = get_preference(VAULT_PREF_KEY)
    if saved:
        return _normalize_path(saved)

    default_path = Path.cwd()
    if not sys.stdin.isatty():
        set_preference(VAULT_PREF_KEY, str(default_path))
        return default_path

    print("No Obsidian vault path is saved yet.")
    print(f"Press Enter to use the current folder: {default_path}")
    user_value = input("Vault path: ").strip()
    chosen = _normalize_path(user_value) if user_value else default_path
    set_preference(VAULT_PREF_KEY, str(chosen))
    return chosen



def resolve_model(cli_value: str | None) -> str:
    if cli_value:
        set_preference(MODEL_PREF_KEY, cli_value)
        return cli_value

    saved = get_preference(MODEL_PREF_KEY)
    return saved or DEFAULT_MODEL



def resolve_max_results(cli_value: int | None) -> int:
    if cli_value is not None:
        set_preference(MAX_RESULTS_PREF_KEY, str(cli_value))
        return cli_value

    saved = get_preference(MAX_RESULTS_PREF_KEY)
    if saved and saved.isdigit():
        return int(saved)
    return 5



def resolve_response_mode(cli_value: str | None) -> str:
    if cli_value:
        set_preference(RESPONSE_MODE_PREF_KEY, cli_value)
        return cli_value

    saved = get_preference(RESPONSE_MODE_PREF_KEY)
    return saved if saved in VALID_RESPONSE_MODES else DEFAULT_RESPONSE_MODE



def _normalize_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()
