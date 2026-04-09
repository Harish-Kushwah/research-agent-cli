# Research Agent CLI

`research-agent-cli` is a Python research assistant that:

- searches the web
- summarizes findings with a local Ollama model when available
- saves reports into an Obsidian vault
- supports CLI, scheduling, and desktop-style interfaces

## Features

- Web search with multiple fallback providers
- Friendly progress updates instead of raw thinking spam in the terminal
- Obsidian report and source-note creation
- Persistent `memory.md` for reusable context
- SQLite-backed preferences for vault path, model, max results, and response mode
- CLI command support
- Desktop launcher support

## Installation

Install from a local checkout:

```powershell
pip install -e .
```

Install from TestPyPI during verification:

```powershell
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple research-agent-cli==0.1.2
```

## First Run Behavior

On the first CLI run, the agent will:

- ask for your Obsidian vault path
- let you press Enter to use the current folder
- save that preference for future runs

It also remembers:

- last used vault path
- preferred model
- preferred max results
- preferred response mode
- latest generated report path

These preferences are stored in SQLite in a user-local app data folder, or in a local `.agent-data/` fallback folder when needed.

## Usage

Run from the CLI:

```powershell
research-agent "latest AI news"
```

Run as a Python module:

```powershell
python -m agent "latest AI news"
```

Launch the desktop app:

```powershell
research-agent --app
```

Use a custom vault path:

```powershell
research-agent --vault-dir "D:\MyVault" "what is OS"
```

## Preferences Management

Open the interactive preferences menu:

```powershell
research-agent --preferences
```

Show saved preferences:

```powershell
research-agent --show-preferences
```

Show supported preference keys:

```powershell
research-agent --list-preference-keys
```

Set a preference directly:

```powershell
research-agent --set-preference model qwen3.5:4b
research-agent --set-preference max_results 10
research-agent --set-preference response_mode references_only
```

Delete one preference:

```powershell
research-agent --delete-preference vault_dir
```

Reset all preferences:

```powershell
research-agent --reset-preferences
```

### Preference Keys

These are the current supported preference keys you can manage:

| Key | Meaning | Sample Value |
| --- | --- | --- |
| `vault_dir` | Default Obsidian vault or output folder path | `D:\MyVault` |
| `model` | Default Ollama model name used for summarization | `qwen3.5:4b` |
| `max_results` | Default number of search results to fetch | `5` |
| `response_mode` | Output style: `full` or `references_only` | `references_only` |

### Example Commands

```powershell
research-agent --set-preference vault_dir "D:\MyVault"
research-agent --set-preference model qwen3.5:4b
research-agent --set-preference max_results 8
research-agent --set-preference response_mode references_only
research-agent --show-preferences
```

## References-Only Mode

If you set:

```powershell
research-agent --set-preference response_mode references_only
```

then the agent will:

- skip the local model entirely
- collect and save source references only
- print references in the terminal
- still create the Obsidian report structure

To switch back:

```powershell
research-agent --set-preference response_mode full
```

## Local Model Behavior

If Ollama or the requested local model is not available, the agent will:

- still try to search the web
- still create the report structure
- skip local summarization gracefully
- tell the user how to enable the model

Example:

```powershell
ollama pull qwen3.5:4b
```

## Example Use Cases

- daily AI news monitoring
- competitor research
- developer tooling summaries
- startup and product trend tracking
- building an Obsidian research vault

## Requirements

- Python 3.10+
- Ollama installed locally if you want model summarization
- An Obsidian vault path for note output

## Output

The agent writes:

- research dashboard notes
- timestamped reports
- grouped source notes
- reusable memory context in `memory.md`
- progress notes instead of raw reasoning traces in reports

## Development

Run directly during development:

```powershell
python -m agent --help
```

## License

MIT
