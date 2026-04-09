# Research Agent CLI

`research-agent-cli` is a Python research assistant that:

- searches the web
- summarizes findings with a local Ollama model
- saves reports into an Obsidian vault
- supports CLI, scheduling, and desktop-style interfaces

## Features

- Web search with multiple fallback providers
- Streaming summary generation
- Obsidian report and source-note creation
- Persistent `memory.md` for reusable context
- CLI command support
- Desktop launcher support

## Installation

Install from a local checkout:

```powershell
pip install -e .
```

Install from TestPyPI during verification:

```powershell
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple research-agent-cli==0.1.1
```

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

## Development

Run directly during development:

```powershell
python -m agent --help
```

## License

MIT
