import json
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

import cli


class StubSynthesizer:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def generate_rule_files(
        self,
        dna_metrics,
        output_path,
        cursor_rules_filename=".cursor/rules/project-rules.mdc",
        agents_filename="AGENTS.md",
        legacy_cursorrules_filename=None,
    ):
        output_root = Path(output_path)
        cursor_target = output_root / cursor_rules_filename
        cursor_target.parent.mkdir(parents=True, exist_ok=True)
        cursor_target.write_text("---\nalwaysApply: true\n---\n\n[ROLE]\nKeep changes focused.\n", encoding="utf-8")

        written = {"cursor_rules": cursor_target}
        if agents_filename:
            agents_target = output_root / agents_filename
            agents_target.write_text("# AGENTS.md\n\n[ROLE]\nKeep changes focused.\n", encoding="utf-8")
            written["agents"] = agents_target
        if legacy_cursorrules_filename:
            legacy_target = output_root / legacy_cursorrules_filename
            legacy_target.write_text("[ROLE]\nKeep changes focused.\n", encoding="utf-8")
            written["legacy_cursorrules"] = legacy_target
        return written

    def generate_onboarding_files(self, dna_metrics, output_path, docs_dir="docs/onboarding"):
        output_root = Path(output_path) / docs_dir
        output_root.mkdir(parents=True, exist_ok=True)
        overview_target = output_root / "PROJECT_OVERVIEW.md"
        overview_target.write_text("# Project Overview\n", encoding="utf-8")
        how_to_run_target = output_root / "HOW_TO_RUN.md"
        how_to_run_target.write_text("# How To Run\n", encoding="utf-8")
        return {
            "PROJECT_OVERVIEW.md": overview_target,
            "HOW_TO_RUN.md": how_to_run_target,
        }

    def generate_memory_pack_files(self, dna_metrics, output_path, pack_dir=".ai-memory"):
        output_root = Path(output_path) / pack_dir
        output_root.mkdir(parents=True, exist_ok=True)
        claude_target = output_root / "CLAUDE.md"
        claude_target.write_text("# Claude\n", encoding="utf-8")
        prompts_target = output_root / "FEATURE_PROMPTS.md"
        prompts_target.write_text("# Feature Prompts\n", encoding="utf-8")
        return {
            "CLAUDE.md": claude_target,
            "FEATURE_PROMPTS.md": prompts_target,
        }

    def generate_feature_pack_files(self, dna_metrics, output_path, pack_dir=".prompt-grapher/features"):
        output_root = Path(output_path) / pack_dir
        output_root.mkdir(parents=True, exist_ok=True)
        relevant_target = output_root / "RELEVANT_FILES.md"
        relevant_target.write_text("# Relevant Files\n", encoding="utf-8")
        backend_target = output_root / "BACKEND_PROMPT.md"
        backend_target.write_text("# Backend Prompt\n", encoding="utf-8")
        return {
            "RELEVANT_FILES.md": relevant_target,
            "BACKEND_PROMPT.md": backend_target,
        }

    def generate_bug_pack_files(self, dna_metrics, output_path, pack_dir=".prompt-grapher/bugs"):
        output_root = Path(output_path) / pack_dir
        output_root.mkdir(parents=True, exist_ok=True)
        related_target = output_root / "RELATED_FILES.md"
        related_target.write_text("# Related Files\n", encoding="utf-8")
        investigation_target = output_root / "INVESTIGATION_PROMPT.md"
        investigation_target.write_text("# Investigation Prompt\n", encoding="utf-8")
        return {
            "RELATED_FILES.md": related_target,
            "INVESTIGATION_PROMPT.md": investigation_target,
        }

    def generate_handoff_pack_files(self, dna_metrics, output_path, pack_dir="docs/handoff"):
        output_root = Path(output_path) / pack_dir
        output_root.mkdir(parents=True, exist_ok=True)
        technical_target = output_root / "TECHNICAL_DOCS.md"
        technical_target.write_text("# Technical Docs\n", encoding="utf-8")
        maintenance_target = output_root / "AI_MAINTENANCE_PROMPTS.md"
        maintenance_target.write_text("# AI Maintenance Prompts\n", encoding="utf-8")
        return {
            "TECHNICAL_DOCS.md": technical_target,
            "AI_MAINTENANCE_PROMPTS.md": maintenance_target,
        }


def test_init_creates_env_file(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(cli.main, ["init"])

    assert result.exit_code == 0
    assert (tmp_path / ".env").exists()


def test_analyze_uses_existing_graph_artifact(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "target"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)

    graph = {
        "nodes": [
            {"id": "src/main.py", "type": "file", "path": "src/main.py"},
            {"id": "src/service.py", "type": "file", "path": "src/service.py"},
        ],
        "edges": [
            {"source": "src/main.py", "target": "src/service.py", "type": "imports"},
        ],
    }
    (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called when --reuse-graph is set")

    monkeypatch.setattr(cli, "PromptSynthesizer", StubSynthesizer)
    monkeypatch.setattr(cli.subprocess, "run", fail_if_called)
    runner = CliRunner()

    result = runner.invoke(cli.main, ["analyze", str(project), "--reuse-graph"])

    assert result.exit_code == 0
    assert (project / ".cursor" / "rules" / "project-rules.mdc").exists()
    assert (project / "AGENTS.md").exists()
    assert "cursor_rules generated at" in result.output
    assert "agents generated at" in result.output


def test_analyze_bootstraps_graphify_via_current_python(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "target"
    project.mkdir(parents=True)

    def fake_run(command, capture_output, text, check, env):
        assert command[:4] == [cli.sys.executable, "-m", "graphify", "update"]
        assert command[4] == str(project)
        assert "--no-cluster" in command

        graphify_dir = project / "graphify-out"
        graphify_dir.mkdir(parents=True, exist_ok=True)
        graph = {
            "nodes": [
                {"id": "src/main.py", "type": "file", "path": "src/main.py"},
            ],
            "edges": [],
        }
        (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(cli, "PromptSynthesizer", StubSynthesizer)
    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    runner = CliRunner()

    result = runner.invoke(cli.main, ["analyze", str(project)])

    assert result.exit_code == 0
    assert (project / ".cursor" / "rules" / "project-rules.mdc").exists()
    assert (project / "AGENTS.md").exists()


def test_analyze_refreshes_existing_graph_by_default(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "target"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)
    (graphify_dir / "graph.json").write_text(json.dumps({"nodes": [], "edges": []}), encoding="utf-8")

    def fake_run(command, capture_output, text, check, env):
        assert command[:4] == [cli.sys.executable, "-m", "graphify", "update"]
        assert command[4] == str(project)
        refreshed_graph = {
            "nodes": [
                {"id": "src/main.py", "type": "file", "path": "src/main.py"},
            ],
            "edges": [],
        }
        (graphify_dir / "graph.json").write_text(json.dumps(refreshed_graph), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(cli, "PromptSynthesizer", StubSynthesizer)
    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    runner = CliRunner()

    result = runner.invoke(cli.main, ["analyze", str(project)])

    assert result.exit_code == 0
    assert "Refreshing Graphify artifact before regenerating rules..." in result.output
    assert (project / ".cursor" / "rules" / "project-rules.mdc").exists()


def test_analyze_generates_onboarding_docs_when_requested(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "target"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)

    graph = {
        "nodes": [
            {"id": "src/main.py", "type": "file", "path": "src/main.py"},
        ],
        "edges": [],
    }
    (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    monkeypatch.setattr(cli, "PromptSynthesizer", StubSynthesizer)
    runner = CliRunner()

    result = runner.invoke(
        cli.main,
        [
            "analyze",
            str(project),
            "--reuse-graph",
            "--onboarding-docs-dir",
            "docs/onboarding",
        ],
    )

    assert result.exit_code == 0
    assert (project / "docs" / "onboarding" / "PROJECT_OVERVIEW.md").exists()
    assert (project / "docs" / "onboarding" / "HOW_TO_RUN.md").exists()
    assert "PROJECT_OVERVIEW.md generated at" in result.output


def test_analyze_generates_memory_pack_when_requested(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "target"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)

    graph = {
        "nodes": [
            {"id": "src/auth/service.py", "type": "file", "path": "src/auth/service.py"},
            {"id": "src/auth/controller.py", "type": "file", "path": "src/auth/controller.py"},
        ],
        "edges": [
            {"source": "src/auth/controller.py", "target": "src/auth/service.py", "type": "imports"},
        ],
    }
    (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    monkeypatch.setattr(cli, "PromptSynthesizer", StubSynthesizer)
    runner = CliRunner()

    result = runner.invoke(
        cli.main,
        [
            "analyze",
            str(project),
            "--reuse-graph",
            "--memory-pack-dir",
            ".ai-memory",
            "--feature-request",
            "Mujhe auth module modify karna hai",
        ],
    )

    assert result.exit_code == 0
    assert (project / ".ai-memory" / "CLAUDE.md").exists()
    assert (project / ".ai-memory" / "FEATURE_PROMPTS.md").exists()
    assert "CLAUDE.md generated at" in result.output


def test_analyze_generates_feature_pack_when_requested(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "target"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)

    graph = {
        "nodes": [
            {"id": "src/payments/controller.py", "type": "file", "path": "src/payments/controller.py"},
            {"id": "src/payments/service.py", "type": "file", "path": "src/payments/service.py"},
        ],
        "edges": [
            {"source": "src/payments/controller.py", "target": "src/payments/service.py", "type": "imports"},
        ],
    }
    (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    monkeypatch.setattr(cli, "PromptSynthesizer", StubSynthesizer)
    runner = CliRunner()

    result = runner.invoke(
        cli.main,
        [
            "analyze",
            str(project),
            "--reuse-graph",
            "--feature-request",
            "Add payment gateway in this app",
            "--feature-pack-dir",
            ".prompt-grapher/features/payments",
        ],
    )

    assert result.exit_code == 0
    assert (project / ".prompt-grapher" / "features" / "payments" / "RELEVANT_FILES.md").exists()
    assert (project / ".prompt-grapher" / "features" / "payments" / "BACKEND_PROMPT.md").exists()
    assert "RELEVANT_FILES.md generated at" in result.output


def test_analyze_rejects_feature_pack_without_feature_request(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "target"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)
    (graphify_dir / "graph.json").write_text(json.dumps({"nodes": [], "edges": []}), encoding="utf-8")

    monkeypatch.setattr(cli, "PromptSynthesizer", StubSynthesizer)
    runner = CliRunner()

    result = runner.invoke(
        cli.main,
        [
            "analyze",
            str(project),
            "--reuse-graph",
            "--feature-pack-dir",
            ".prompt-grapher/features/payments",
        ],
    )

    assert result.exit_code != 0
    assert "--feature-pack-dir requires --feature-request." in result.output


def test_analyze_generates_bug_pack_when_requested(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "target"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)

    graph = {
        "nodes": [
            {"id": "src/payments/webhook.ts", "type": "file", "path": "src/payments/webhook.ts"},
            {"id": "src/orders/order.service.ts", "type": "file", "path": "src/orders/order.service.ts"},
            {"id": "mobile/screens/PaymentSuccess.tsx", "type": "file", "path": "mobile/screens/PaymentSuccess.tsx"},
        ],
        "edges": [
            {"source": "src/payments/webhook.ts", "target": "src/orders/order.service.ts", "type": "imports"},
        ],
    }
    (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    monkeypatch.setattr(cli, "PromptSynthesizer", StubSynthesizer)
    runner = CliRunner()

    result = runner.invoke(
        cli.main,
        [
            "analyze",
            str(project),
            "--reuse-graph",
            "--bug-report",
            "Payment status is not updating after UPI success",
            "--bug-pack-dir",
            ".prompt-grapher/bugs/payment-status",
        ],
    )

    assert result.exit_code == 0
    assert (project / ".prompt-grapher" / "bugs" / "payment-status" / "RELATED_FILES.md").exists()
    assert (project / ".prompt-grapher" / "bugs" / "payment-status" / "INVESTIGATION_PROMPT.md").exists()
    assert "RELATED_FILES.md generated at" in result.output


def test_analyze_rejects_bug_pack_without_bug_report(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "target"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)
    (graphify_dir / "graph.json").write_text(json.dumps({"nodes": [], "edges": []}), encoding="utf-8")

    monkeypatch.setattr(cli, "PromptSynthesizer", StubSynthesizer)
    runner = CliRunner()

    result = runner.invoke(
        cli.main,
        [
            "analyze",
            str(project),
            "--reuse-graph",
            "--bug-pack-dir",
            ".prompt-grapher/bugs/payment-status",
        ],
    )

    assert result.exit_code != 0
    assert "--bug-pack-dir requires --bug-report." in result.output


def test_analyze_generates_handoff_pack_when_requested(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "target"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)

    graph = {
        "nodes": [
            {"id": "src/main.ts", "type": "file", "path": "src/main.ts"},
            {"id": "src/api/orders.ts", "type": "file", "path": "src/api/orders.ts"},
            {"id": "src/db/schema.prisma", "type": "file", "path": "src/db/schema.prisma"},
        ],
        "edges": [
            {"source": "src/main.ts", "target": "src/api/orders.ts", "type": "imports"},
            {"source": "src/api/orders.ts", "target": "src/db/schema.prisma", "type": "imports"},
        ],
    }
    (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    monkeypatch.setattr(cli, "PromptSynthesizer", StubSynthesizer)
    runner = CliRunner()

    result = runner.invoke(
        cli.main,
        [
            "analyze",
            str(project),
            "--reuse-graph",
            "--handoff-pack-dir",
            "docs/handoff",
        ],
    )

    assert result.exit_code == 0
    assert (project / "docs" / "handoff" / "TECHNICAL_DOCS.md").exists()
    assert (project / "docs" / "handoff" / "AI_MAINTENANCE_PROMPTS.md").exists()
    assert "TECHNICAL_DOCS.md generated at" in result.output
