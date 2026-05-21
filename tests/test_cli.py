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
