# PromptGrapher

PromptGrapher turns a Graphify dependency graph into repository-specific Cursor rules. It is designed to work against arbitrary projects, not just a single language or framework.

## What It Does

1. Reads `graphify-out/graph.json` or `graphify-out/manifest.json`.
2. Infers the project's primary languages, framework hints, architecture style, naming patterns, hotspots, entrypoints, and test presence.
3. Sends that summary to an OpenAI-compatible model.
4. Writes `.cursor/rules/project-rules.mdc` for Cursor and `AGENTS.md` as a root-level backup/source-of-truth.

## Requirements

- Python 3.10+
- No separate Graphify install step. `graphifyy` is installed as a dependency.
- An OpenAI-compatible API key and model name

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

## Configuration

Create a `.env` file:

```bash
prompt-grapher init
```

Then set:

- `AI_API_KEY`
- `AI_MODEL_NAME`
- `AI_BASE_URL` if you are using a non-default OpenAI-compatible endpoint such as Groq, OpenRouter, or Ollama

PromptGrapher also falls back to `OPENAI_API_KEY`, `GROQ_API_KEY`, and `OPENROUTER_API_KEY`.

## Usage

Analyze a project and auto-run Graphify when needed:

```bash
prompt-grapher analyze /path/to/project
```

Re-running `prompt-grapher analyze` refreshes the Graphify artifact by default before regenerating rules, so architecture and module changes are picked up automatically.

If you intentionally want to reuse the current `graphify-out` contents without refreshing them, use:

```bash
prompt-grapher analyze /path/to/project --reuse-graph
```

By default, PromptGrapher bootstraps Graphify with a code-only graph build that does not require a second LLM provider:

```bash
python -m graphify update /path/to/project --no-cluster
```

This mode is enough for PromptGrapher's architecture heuristics and works well for PyPI installs.

If you explicitly want Graphify's semantic extraction path, switch strategies:

```bash
prompt-grapher analyze /path/to/project --graphify-strategy semantic --graphify-backend openai --graphify-model gpt-4.1-mini
```

Semantic extraction requires a Graphify-supported backend and its API key.

Reuse an existing Graphify artifact:

```bash
prompt-grapher analyze /path/to/project --graph-input /path/to/project/graphify-out/graph.json
```

Override the model or output filename:

```bash
prompt-grapher analyze /path/to/project --model gpt-4.1-mini --output-file .cursor/rules/project-rules.mdc --agents-file AGENTS.md
```

## Local Smoke Tests

```bash
pip install -e .[dev]
pytest
```
