from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

from core.parser import GraphifyHeuristicParser
from core.synthesizer import PromptSynthesizer

DEFAULT_GRAPHIFY_ARGS = ("--no-cluster",)
SUPPORTED_GRAPH_FILES = ("graph.json", "manifest.json")
DEFAULT_CURSOR_RULES_FILE = ".cursor/rules/project-rules.mdc"
DEFAULT_AGENTS_FILE = "AGENTS.md"
GRAPHIFY_BACKEND_API_ENV = {
    "claude": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "kimi": "MOONSHOT_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def _env_template() -> str:
    return """# PromptGrapher runtime configuration
# Leave AI_BASE_URL blank to use the default OpenAI endpoint.
AI_BASE_URL=

# Required. PromptGrapher also falls back to OPENAI_API_KEY, GROQ_API_KEY,
# and OPENROUTER_API_KEY if AI_API_KEY is not set.
AI_API_KEY=

# Required. Examples: gpt-4.1-mini, llama-3.3-70b-versatile, mistral-large-latest
AI_MODEL_NAME=
"""


def _locate_graph_artifact(project_path: Path) -> Path | None:
    graphify_dir = project_path / "graphify-out"
    for filename in SUPPORTED_GRAPH_FILES:
        candidate = graphify_dir / filename
        if candidate.exists():
            return candidate
    return None


def _default_graphify_command() -> list[str]:
    return [sys.executable, "-m", "graphify"]


def _run_graphify(
    project_path: Path,
    graphify_bin: str | None,
    graphify_args: tuple[str, ...],
    graphify_strategy: str,
    graphify_backend: str | None,
    graphify_model: str | None,
    api_key: str | None,
) -> None:
    if graphify_strategy == "semantic":
        command = ([graphify_bin] if graphify_bin else _default_graphify_command()) + [
            "extract",
            str(project_path),
        ]
        if graphify_backend:
            command.extend(["--backend", graphify_backend])
        if graphify_model:
            command.extend(["--model", graphify_model])
        command.extend(graphify_args)
    else:
        command = ([graphify_bin] if graphify_bin else _default_graphify_command()) + [
            "update",
            str(project_path),
            *graphify_args,
        ]

    env = os.environ.copy()
    backend_api_env = GRAPHIFY_BACKEND_API_ENV.get(graphify_backend or "")
    if backend_api_env and api_key and backend_api_env not in env:
        env[backend_api_env] = api_key

    result = subprocess.run(command, capture_output=True, text=True, check=False, env=env)
    if result.returncode != 0:
        details = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part) or "No output."
        raise click.ClickException(f"Graphify failed with exit code {result.returncode}: {details}")


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def main() -> None:
    """Generate repository-aware AI rules from Graphify dependency graphs."""


@main.command()
@click.option("--force", is_flag=True, help="Overwrite an existing .env file.")
def init(force: bool) -> None:
    """Create a local .env template for the AI provider configuration."""
    env_path = Path(".env")

    if env_path.exists() and not force:
        raise click.ClickException("A .env file already exists. Re-run with --force to overwrite it.")

    env_path.write_text(_env_template(), encoding="utf-8")
    click.echo("Created .env template. Fill in AI_API_KEY and AI_MODEL_NAME before running analyze.")


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--graph-input",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to a Graphify JSON artifact. If omitted, PromptGrapher looks in <path>/graphify-out/.",
)
@click.option(
    "--bootstrap-graph/--no-bootstrap-graph",
    default=True,
    show_default=True,
    help="Run Graphify automatically when no graph artifact exists yet.",
)
@click.option(
    "--refresh-graph/--reuse-graph",
    default=True,
    show_default=True,
    help="Refresh the Graphify artifact before generating rules. Disable to reuse an existing graphify-out artifact as-is.",
)
@click.option(
    "--graphify-strategy",
    type=click.Choice(["code-only", "semantic"], case_sensitive=False),
    default="code-only",
    show_default=True,
    help="Graph bootstrap mode. 'code-only' uses Graphify update with no LLM. 'semantic' uses Graphify extract.",
)
@click.option(
    "--graphify-bin",
    default=None,
    help="Optional Graphify executable override. By default PromptGrapher uses the same Python environment via 'python -m graphify'.",
)
@click.option(
    "--graphify-arg",
    "graphify_args",
    multiple=True,
    help="Additional argument to pass to Graphify. Repeat the option for multiple arguments.",
)
@click.option(
    "--graphify-backend",
    default=None,
    help="Graphify backend for auto-bootstrap, for example: openai, gemini, claude, deepseek, kimi, ollama.",
)
@click.option(
    "--graphify-model",
    default=None,
    help="Model override for Graphify auto-bootstrap.",
)
@click.option("--model", default=None, help="Override AI_MODEL_NAME for this run.")
@click.option("--base-url", default=None, help="Override AI_BASE_URL for this run.")
@click.option("--api-key", default=None, help="Override AI_API_KEY for this run.")
@click.option(
    "--output-file",
    default=DEFAULT_CURSOR_RULES_FILE,
    show_default=True,
    help="Path for the generated Cursor project rules file, written into the target project directory by default.",
)
@click.option(
    "--agents-file",
    default=DEFAULT_AGENTS_FILE,
    show_default=True,
    help="Path for the generated AGENTS.md backup/source-of-truth file, written into the target project directory by default.",
)
@click.option(
    "--legacy-cursorrules-file",
    default=None,
    help="Optional legacy .cursorrules output path for older workflows.",
)
@click.option(
    "--onboarding-docs-dir",
    default=None,
    help="Optional directory for generated onboarding documentation files such as PROJECT_OVERVIEW.md and HOW_TO_RUN.md.",
)
@click.option(
    "--memory-pack-dir",
    default=None,
    help="Optional directory for assistant memory-pack files such as CLAUDE.md, CURSOR_RULES.md, and FEATURE_PROMPTS.md.",
)
@click.option(
    "--feature-pack-dir",
    default=None,
    help="Optional directory for a feature implementation prompt pack with backend, frontend, test, and migration prompts.",
)
@click.option(
    "--bug-pack-dir",
    default=None,
    help="Optional directory for a bug-fix context pack with related files, investigation prompts, and regression-test prompts.",
)
@click.option(
    "--handoff-pack-dir",
    default=None,
    help="Optional directory for a client handoff pack with technical docs, setup, deployment, API, database, and maintenance prompts.",
)
@click.option(
    "--feature-request",
    default=None,
    help="Optional natural-language change request used to generate a request-specific prompt pack and relevant file list.",
)
@click.option(
    "--bug-report",
    default=None,
    help="Optional bug report or symptom statement used to generate a debugging context pack.",
)
@click.option(
    "--quiet-metrics/--show-metrics",
    default=False,
    show_default=True,
    help="Suppress the parsed architecture summary in the terminal output.",
)
def analyze(
    path: Path,
    graph_input: Path | None,
    bootstrap_graph: bool,
    refresh_graph: bool,
    graphify_strategy: str,
    graphify_bin: str | None,
    graphify_args: tuple[str, ...],
    graphify_backend: str | None,
    graphify_model: str | None,
    model: str | None,
    base_url: str | None,
    api_key: str | None,
    output_file: str,
    agents_file: str,
    legacy_cursorrules_file: str | None,
    onboarding_docs_dir: str | None,
    memory_pack_dir: str | None,
    feature_pack_dir: str | None,
    bug_pack_dir: str | None,
    handoff_pack_dir: str | None,
    feature_request: str | None,
    bug_report: str | None,
    quiet_metrics: bool,
) -> None:
    """Analyze a project and generate repository-specific Cursor and agent rules."""
    load_dotenv()
    project_path = path.resolve()
    click.echo(f"[PromptGrapher] Analyzing {project_path}")

    graph_path = graph_input.resolve() if graph_input else _locate_graph_artifact(project_path)
    should_run_graphify = False
    if graph_input is None and bootstrap_graph:
        if graph_path is None:
            click.echo("[PromptGrapher] No graph artifact found. Running Graphify first...")
            should_run_graphify = True
        elif refresh_graph:
            click.echo("[PromptGrapher] Refreshing Graphify artifact before regenerating rules...")
            should_run_graphify = True

    if should_run_graphify:
        strategy = graphify_strategy.lower()
        extra_graphify_args = graphify_args or DEFAULT_GRAPHIFY_ARGS
        _run_graphify(
            project_path,
            graphify_bin,
            extra_graphify_args,
            strategy,
            graphify_backend,
            graphify_model,
            api_key or os.environ.get("AI_API_KEY"),
        )
        graph_path = _locate_graph_artifact(project_path)

    if graph_path is None:
        expected = ", ".join(f"graphify-out/{name}" for name in SUPPORTED_GRAPH_FILES)
        raise click.ClickException(
            "No Graphify artifact was found. "
            f"Expected one of {expected}, or provide --graph-input explicitly."
        )

    if feature_request and bug_report:
        raise click.ClickException("Use either --feature-request or --bug-report, not both in the same run.")
    if feature_pack_dir and not feature_request:
        raise click.ClickException("--feature-pack-dir requires --feature-request.")
    if bug_pack_dir and not bug_report:
        raise click.ClickException("--bug-pack-dir requires --bug-report.")

    parser = GraphifyHeuristicParser(project_path=project_path, graph_path=graph_path)
    dna_metrics = parser.compile_heuristics_payload()
    if feature_request:
        dna_metrics["feature_request_context"] = parser.build_feature_request_context(feature_request, dna_metrics)
    if bug_report:
        dna_metrics["bug_report_context"] = parser.build_bug_report_context(bug_report, dna_metrics)

    if not quiet_metrics:
        click.echo("[PromptGrapher] Heuristic summary:")
        click.echo(json.dumps(dna_metrics, indent=2))
    elif feature_request and not memory_pack_dir and not feature_pack_dir:
        click.echo(
            "[PromptGrapher] Feature request context computed. "
            "Use --show-metrics, --memory-pack-dir, or --feature-pack-dir to inspect the generated prompt pack."
        )
    elif bug_report and not bug_pack_dir:
        click.echo(
            "[PromptGrapher] Bug report context computed. "
            "Use --show-metrics or --bug-pack-dir to inspect the generated debug pack."
        )

    synthesizer = PromptSynthesizer(base_url=base_url, api_key=api_key, model_name=model)
    generated_files = synthesizer.generate_rule_files(
        dna_metrics,
        output_path=project_path,
        cursor_rules_filename=output_file,
        agents_filename=agents_file,
        legacy_cursorrules_filename=legacy_cursorrules_file,
    )
    if onboarding_docs_dir:
        generated_files.update(
            synthesizer.generate_onboarding_files(
                dna_metrics,
                output_path=project_path,
                docs_dir=onboarding_docs_dir,
            )
        )
    if memory_pack_dir:
        generated_files.update(
            synthesizer.generate_memory_pack_files(
                dna_metrics,
                output_path=project_path,
                pack_dir=memory_pack_dir,
            )
        )
    if feature_pack_dir:
        generated_files.update(
            synthesizer.generate_feature_pack_files(
                dna_metrics,
                output_path=project_path,
                pack_dir=feature_pack_dir,
            )
        )
    if bug_pack_dir:
        generated_files.update(
            synthesizer.generate_bug_pack_files(
                dna_metrics,
                output_path=project_path,
                pack_dir=bug_pack_dir,
            )
        )
    if handoff_pack_dir:
        generated_files.update(
            synthesizer.generate_handoff_pack_files(
                dna_metrics,
                output_path=project_path,
                pack_dir=handoff_pack_dir,
            )
        )

    for label, file_path in generated_files.items():
        click.echo(f"[PromptGrapher] {label} generated at {file_path}")


if __name__ == "__main__":
    main()
