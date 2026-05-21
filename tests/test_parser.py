import json
from pathlib import Path

from core.parser import GraphifyHeuristicParser


def test_parser_supports_manifest_json(tmp_path: Path) -> None:
    project = tmp_path / "sample-project"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)

    manifest = {
        "nodes": [
            {"id": "src/controllers/user_controller.py", "type": "file"},
            {"id": "src/services/user_service.py", "type": "file"},
            {"id": "src/repositories/user_repository.py", "type": "file"},
            {"id": "tests/test_user_service.py", "type": "file"},
        ],
        "edges": [
            {"source": "src/controllers/user_controller.py", "target": "src/services/user_service.py", "type": "imports"},
            {"source": "src/services/user_service.py", "target": "src/repositories/user_repository.py", "type": "imports"},
        ],
    }
    (graphify_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    payload = GraphifyHeuristicParser(project).compile_heuristics_payload()

    assert payload["project_profile"]["primary_languages"] == ["Python"]
    assert payload["project_profile"]["architecture_type"] == "Layered service / repository architecture"
    assert payload["project_profile"]["has_tests"] is True
    assert payload["graph_source"].endswith("manifest.json")


def test_parser_supports_graph_json_links_schema(tmp_path: Path) -> None:
    project = tmp_path / "sample-project"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)

    graph = {
        "nodes": [
            {"id": "src/components/App.tsx", "type": "file", "path": "src/components/App.tsx"},
            {"id": "src/pages/Home.tsx", "type": "file", "path": "src/pages/Home.tsx"},
            {"id": "src/hooks/useAuth.ts", "type": "file", "path": "src/hooks/useAuth.ts"},
        ],
        "links": [
            {"source": "src/pages/Home.tsx", "target": "src/components/App.tsx", "type": "imports"},
            {"source": "src/components/App.tsx", "target": "src/hooks/useAuth.ts", "type": "imports"},
        ],
    }
    (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    payload = GraphifyHeuristicParser(project).compile_heuristics_payload()

    assert payload["project_profile"]["primary_languages"] == ["React TSX", "TypeScript"]
    assert payload["project_profile"]["architecture_type"] == "Component-oriented frontend architecture"
    assert payload["graph_source"].endswith("graph.json")


def test_parser_detects_test_framework_hints(tmp_path: Path) -> None:
    project = tmp_path / "sample-project"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)

    graph = {
        "nodes": [
            {"id": "src/app.ts", "type": "file", "path": "src/app.ts"},
            {"id": "tests/user.test.ts", "type": "file", "path": "tests/user.test.ts"},
            {"id": "vitest.config.ts", "type": "file", "path": "vitest.config.ts"},
            {"id": "playwright.config.ts", "type": "file", "path": "playwright.config.ts"},
        ],
        "edges": [],
    }
    (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    payload = GraphifyHeuristicParser(project).compile_heuristics_payload()

    assert payload["project_profile"]["has_tests"] is True
    assert payload["project_profile"]["test_framework_hints"] == ["Vitest", "Playwright"]
