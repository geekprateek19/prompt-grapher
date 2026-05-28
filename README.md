# PromptGrapher

PromptGrapher turns a Graphify dependency graph into repository-specific Cursor rules. It is designed to work against arbitrary projects, not just a single language or framework.

## What It Does

1. Reads `graphify-out/graph.json` or `graphify-out/manifest.json`.
2. Infers the project's primary languages, framework hints, architecture style, naming patterns, hotspots, entrypoints, and test presence.
3. Sends that summary to an OpenAI-compatible model.
4. Writes `.cursor/rules/project-rules.mdc` for Cursor and `AGENTS.md` as a root-level backup/source-of-truth.
5. Optionally generates onboarding docs such as `PROJECT_OVERVIEW.md`, `ARCHITECTURE.md`, `HOW_TO_RUN.md`, and `KNOWN_RISKS.md`.
6. Optionally generates an assistant memory pack with `CLAUDE.md`, `CURSOR_RULES.md`, `CODING_STYLE.md`, `PROJECT_MEMORY.md`, and `FEATURE_PROMPTS.md`.
7. Optionally generates a feature implementation prompt pack with touched-file analysis plus backend, frontend, test, and migration prompts.
8. Optionally generates a bug-fix context pack from a pasted symptom or failure statement.
9. Optionally generates a client handoff pack with technical docs, setup and deployment guides, API and database docs, improvement notes, and AI maintenance prompts.

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

## TypeScript Migration Shell

This repository now also includes a `pnpm` workspace under `packages/` for the TypeScript migration path:

```text
packages/
  shared/   common types and constants
  core/     TypeScript bridge helpers and future analysis shell
  cli/      future npx prompt-grapher entrypoint
  vscode/   workspace-native VS Code extension package
```

Right now this is a short-lived bridge, not a rewrite. The new TypeScript CLI and VS Code package still call the existing Python backend while the analyzer is being ported.

Bootstrap the workspace:

```bash
corepack pnpm install
corepack pnpm build
```

Run the bridge CLI:

```bash
corepack pnpm --filter prompt-grapher exec prompt-grapher analyze /path/to/project
corepack pnpm --filter prompt-grapher exec prompt-grapher feature "add payment gateway" /path/to/project
corepack pnpm --filter prompt-grapher exec prompt-grapher bug "Payment status is not updating after UPI success" /path/to/project
corepack pnpm --filter prompt-grapher exec prompt-grapher handoff /path/to/project
```

By default the bridge CLI calls the installed Python `prompt-grapher` command. For local migration work inside this repo, point it at the checked-in Python entrypoint instead:

```bash
corepack pnpm --filter prompt-grapher exec prompt-grapher analyze /path/to/project --python-entry cli.py
```

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

Generate onboarding docs for new developer handoff:

```bash
prompt-grapher analyze /path/to/project --onboarding-docs-dir docs/onboarding
```

When `--onboarding-docs-dir` is set, PromptGrapher additionally writes:

- `PROJECT_OVERVIEW.md`
- `ARCHITECTURE.md`
- `DATABASE_FLOW.md`
- `API_MAP.md`
- `IMPORTANT_FILES.md`
- `HOW_TO_RUN.md`
- `KNOWN_RISKS.md`

Generate a cross-assistant memory pack:

```bash
prompt-grapher analyze /path/to/project --memory-pack-dir .ai-memory
```

Generate a request-specific prompt pack for a concrete change request:

```bash
prompt-grapher analyze /path/to/project --memory-pack-dir .ai-memory --feature-request "Mujhe auth module modify karna hai"
```

Generate a first-class feature implementation pack:

```bash
prompt-grapher analyze /path/to/project --feature-request "Add payment gateway in this app" --feature-pack-dir .prompt-grapher/features/payment-gateway
```

Or through the TypeScript migration CLI:

```bash
corepack pnpm --filter prompt-grapher exec prompt-grapher feature "Add payment gateway in this app" /path/to/project
```

The `feature` command defaults the output to `.prompt-grapher/features/<request-slug>/`.

When `--memory-pack-dir` is set, PromptGrapher keeps generating the standard `.cursor` rules and `AGENTS.md`, and additionally writes:

- `CLAUDE.md`
- `CURSOR_RULES.md`
- `CODING_STYLE.md`
- `PROJECT_MEMORY.md`
- `FEATURE_PROMPTS.md`

If `--feature-request` is also set, `FEATURE_PROMPTS.md` includes a request-specific section with matched modules, relevant files, and an exact copy-paste prompt for an AI coding assistant.

When `--feature-pack-dir` is set, PromptGrapher writes a dedicated implementation pack for the active feature request:

- `RELEVANT_FILES.md`
- `API_CONTEXT.md`
- `DATABASE_CHANGES.md`
- `FRONTEND_UPDATES.md`
- `BACKEND_PROMPT.md`
- `FRONTEND_PROMPT.md`
- `TEST_CASES_PROMPT.md`
- `MIGRATION_PROMPT.md`

This pack is the strongest product pivot for PromptGrapher: it turns a plain request such as `Add payment gateway in this app` into concrete touched-file hints, API and database context, frontend impact notes, and copy-paste prompts for backend, frontend, tests, and migrations.

Generate a bug-fix context pack from a pasted symptom:

```bash
prompt-grapher analyze /path/to/project --bug-report "Payment status is not updating after UPI success" --bug-pack-dir .prompt-grapher/bugs/payment-status
```

Or through the TypeScript migration CLI:

```bash
corepack pnpm --filter prompt-grapher exec prompt-grapher bug "Payment status is not updating after UPI success" /path/to/project
```

When `--bug-pack-dir` is set, PromptGrapher writes:

- `RELATED_FILES.md`
- `API_SUSPECTS.md`
- `DATABASE_SUSPECTS.md`
- `FRONTEND_SUSPECTS.md`
- `INVESTIGATION_PROMPT.md`
- `BACKEND_FIX_PROMPT.md`
- `REGRESSION_TEST_PROMPT.md`

This solves a real developer pain point: paste the bug symptom, let PromptGrapher find the graph-adjacent files, then hand a concrete investigation prompt to Cursor, Claude Code, Codex, or another coding assistant.

Generate a client handoff pack for freelancers or agencies:

```bash
prompt-grapher analyze /path/to/project --handoff-pack-dir docs/handoff
```

Or through the TypeScript migration CLI:

```bash
corepack pnpm --filter prompt-grapher exec prompt-grapher handoff /path/to/project
```

When `--handoff-pack-dir` is set, PromptGrapher writes:

- `TECHNICAL_DOCS.md`
- `SETUP_GUIDE.md`
- `DEPLOYMENT_GUIDE.md`
- `API_DOCUMENTATION.md`
- `DATABASE_DOCUMENTATION.md`
- `FUTURE_IMPROVEMENTS.md`
- `AI_MAINTENANCE_PROMPTS.md`

This is the agency handoff path: one command turns the graph into a client-ready technical packet plus copy-paste maintenance prompts for the next developer or AI assistant.

## Local Smoke Tests

```bash
pip install -e .[dev]
pytest
```

## VS Code Extension Scaffold

This repository now includes a bridge-style VS Code extension under [vscode-extension](</d:/prompt-grapher/vscode-extension/README.md>).

- The extension reuses the existing Python `prompt-grapher` CLI instead of reimplementing the backend in TypeScript.
- You still need Python plus an installed `prompt-grapher` executable.
- Extension-specific setup, commands, and packaging steps are documented in `vscode-extension/README.md`.

There is also a new workspace-native migration package under [packages/vscode](</d:/prompt-grapher/packages/vscode/README.md>). That package lives in the `pnpm` monorepo and shares argument-building logic with the new Node CLI, but it still bridges into the Python backend for now.
