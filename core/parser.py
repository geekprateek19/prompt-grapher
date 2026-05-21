from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import networkx as nx

EXTENSION_LANGUAGE_MAP = {
    ".cs": "C#",
    ".css": "CSS",
    ".go": "Go",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "React JSX",
    ".kt": "Kotlin",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".scala": "Scala",
    ".sql": "SQL",
    ".swift": "Swift",
    ".ts": "TypeScript",
    ".tsx": "React TSX",
}

FRAMEWORK_SIGNATURES = {
    "Django": ("django", "urls.py", "views.py", "manage.py"),
    "FastAPI": ("fastapi", "apirouter", "asgi.py"),
    "Flask": ("flask", "blueprint"),
    "React": ("react", "component", "tsx", "jsx", "hook"),
    "Next.js": ("next.config", "app/", "pages/", "layout.tsx"),
    "Vue": ("vue", "pinia", "nuxt"),
    "Angular": ("angular", "component.ts", "service.ts", "module.ts"),
    "Express": ("express", "router", "middleware"),
    "NestJS": ("nestjs", "controller.ts", "service.ts", "module.ts"),
    "Spring": ("spring", "controller", "service", "repository"),
    "Rails": ("app/models", "app/controllers", "active_record"),
    "Laravel": ("artisan", "eloquent", "controller.php", "middleware"),
}

TEST_FRAMEWORK_SIGNATURES = {
    "Pytest": ("pytest.ini", "conftest.py"),
    "unittest": ("unittest",),
    "Jest": ("jest.config", "jest.setup", "jest.", "__tests__"),
    "Vitest": ("vitest.config", "vitest.setup", "vitest."),
    "Mocha": (".mocharc", "mocha.opts"),
    "Cypress": ("cypress/", "cypress.config"),
    "Playwright": ("playwright.config", "@playwright"),
    "JUnit": ("junit", "surefire"),
    "RSpec": ("rspec", ".rspec", "spec/"),
    "xUnit": ("xunit",),
    "NUnit": ("nunit",),
}

ENTRYPOINT_PATTERNS = {
    "main.py",
    "app.py",
    "manage.py",
    "server.py",
    "server.js",
    "main.ts",
    "main.go",
    "Program.cs",
    "package.json",
    "setup.py",
    "pyproject.toml",
}


class GraphifyHeuristicParser:
    def __init__(self, project_path: str | Path, graph_path: str | Path | None = None):
        self.project_path = Path(project_path).resolve()
        self.graph_path = Path(graph_path).resolve() if graph_path else None
        self.nodes: list[dict] = []
        self.edges: list[dict] = []
        self.graph = nx.DiGraph()

    def resolve_graph_path(self) -> Path:
        if self.graph_path and self.graph_path.exists():
            return self.graph_path

        graphify_dir = self.project_path / "graphify-out"
        for filename in ("graph.json", "manifest.json"):
            candidate = graphify_dir / filename
            if candidate.exists():
                self.graph_path = candidate
                return candidate

        raise FileNotFoundError(
            f"Graphify artifact not found under '{graphify_dir}'. "
            "Expected graph.json or manifest.json."
        )

    def load_graph(self) -> None:
        graph_path = self.resolve_graph_path()
        with graph_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        nodes = data.get("nodes", [])
        raw_edges = data.get("edges") or data.get("links") or []
        if not isinstance(nodes, list) or not isinstance(raw_edges, list):
            raise ValueError(f"Unsupported Graphify schema in '{graph_path}'.")

        self.nodes = [node for node in nodes if isinstance(node, dict)]
        self.edges = []
        self.graph = nx.DiGraph()

        for node in self.nodes:
            node_id = self._node_id(node)
            if not node_id:
                continue
            self.graph.add_node(node_id, **node)

        for raw_edge in raw_edges:
            if not isinstance(raw_edge, dict):
                continue

            edge = self._normalize_edge(raw_edge)
            if edge is None:
                continue

            self.edges.append(edge)
            self.graph.add_edge(
                edge["source"],
                edge["target"],
                relation=edge["type"],
            )

    def _normalize_edge(self, edge: dict) -> dict | None:
        source = edge.get("source") or edge.get("from")
        target = edge.get("target") or edge.get("to")
        if source is None or target is None:
            return None

        return {
            "source": str(source),
            "target": str(target),
            "type": str(edge.get("type") or edge.get("relation") or edge.get("label") or "unknown"),
        }

    def _node_id(self, node: dict) -> str:
        for key in ("id", "name", "label"):
            value = node.get(key)
            if value is not None:
                return str(value)
        return ""

    def _node_type(self, node: dict) -> str:
        node_type = node.get("type") or node.get("kind") or node.get("category") or "unknown"
        return str(node_type).lower()

    def _node_path(self, node: dict) -> str:
        containers = [node]
        for nested_key in ("metadata", "attributes", "data"):
            nested_value = node.get(nested_key)
            if isinstance(nested_value, dict):
                containers.append(nested_value)

        for container in containers:
            for key in ("path", "file", "filepath", "file_path", "location", "source_file"):
                value = container.get(key)
                if isinstance(value, str) and value.strip():
                    return value

        node_id = self._node_id(node)
        if "/" in node_id or "\\" in node_id or Path(node_id).suffix:
            return node_id
        return ""

    def _identifier_from_node(self, node: dict) -> str:
        node_path = self._node_path(node)
        if node_path:
            return Path(node_path).stem
        node_id = self._node_id(node)
        return Path(node_id).stem if Path(node_id).suffix else node_id

    def detect_architecture_pattern(self) -> dict:
        corpus = " ".join(
            {
                self._node_id(node).lower()
                for node in self.nodes
                if self._node_id(node)
            }
            | {
                self._node_path(node).lower()
                for node in self.nodes
                if self._node_path(node)
            }
        )

        signals = {
            "controllers": corpus.count("controller"),
            "services": corpus.count("service"),
            "repositories": corpus.count("repository") + corpus.count("/repo"),
            "components": corpus.count("component"),
            "pages": corpus.count("/pages/") + corpus.count("/app/"),
            "hooks": corpus.count("hook"),
            "domain": corpus.count("domain"),
            "use_cases": corpus.count("usecase") + corpus.count("use_case"),
            "adapters": corpus.count("adapter"),
            "utilities": corpus.count("util") + corpus.count("helper"),
        }

        if signals["controllers"] and signals["services"] and signals["repositories"]:
            label = "Layered service / repository architecture"
        elif signals["domain"] and signals["use_cases"] and signals["adapters"]:
            label = "Clean architecture / hexagonal architecture"
        elif signals["components"] and (signals["pages"] or signals["hooks"]):
            label = "Component-oriented frontend architecture"
        elif signals["utilities"] > max(3, len(self.nodes) // 5):
            label = "Utility-heavy monolith"
        else:
            label = "Custom or mixed modular architecture"

        return {"label": label, "signals": signals}

    def extract_naming_conventions(self) -> dict:
        identifiers_by_type = {
            "classes": [],
            "functions": [],
            "files": [],
        }

        for node in self.nodes:
            node_type = self._node_type(node)
            identifier = self._identifier_from_node(node)
            if not identifier:
                continue

            if "class" in node_type:
                identifiers_by_type["classes"].append(identifier)
            elif "function" in node_type or "method" in node_type:
                identifiers_by_type["functions"].append(identifier)

            node_path = self._node_path(node)
            if node_path:
                identifiers_by_type["files"].append(Path(node_path).stem)

        summary = {}
        for group, identifiers in identifiers_by_type.items():
            summary[group] = self._dominant_case(identifiers)

        return {
            "classes": summary["classes"],
            "functions": summary["functions"],
            "files": summary["files"],
            "summary": (
                f"Classes: {summary['classes']}; "
                f"Functions: {summary['functions']}; "
                f"Files: {summary['files']}"
            ),
        }

    def _dominant_case(self, identifiers: list[str]) -> str:
        cases = [self._classify_identifier(identifier) for identifier in identifiers if identifier]
        if not cases:
            return "Unknown"
        return Counter(cases).most_common(1)[0][0]

    def _classify_identifier(self, identifier: str) -> str:
        if re.fullmatch(r"[A-Z][A-Za-z0-9]*", identifier):
            return "PascalCase"
        if re.fullmatch(r"[a-z]+(?:[A-Z][A-Za-z0-9]*)+", identifier):
            return "camelCase"
        if re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)+", identifier):
            return "snake_case"
        if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)+", identifier):
            return "kebab-case"
        if re.fullmatch(r"[A-Z0-9]+(?:_[A-Z0-9]+)+", identifier):
            return "UPPER_SNAKE_CASE"
        return "Mixed"

    def infer_languages(self) -> list[str]:
        counts: Counter[str] = Counter()
        for node in self.nodes:
            language = self._language_from_node(node)
            if language:
                counts[language] += 1

        return [language for language, _ in counts.most_common(3)] or ["Unknown"]

    def _language_from_node(self, node: dict) -> str | None:
        containers = [node]
        for nested_key in ("metadata", "attributes", "data"):
            nested_value = node.get(nested_key)
            if isinstance(nested_value, dict):
                containers.append(nested_value)

        for container in containers:
            for key in ("language", "lang"):
                value = container.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        node_path = self._node_path(node)
        if not node_path:
            return None

        return EXTENSION_LANGUAGE_MAP.get(Path(node_path).suffix.lower())

    def infer_framework_hints(self) -> list[str]:
        corpus = " ".join(
            [
                self._node_id(node).lower()
                for node in self.nodes
                if self._node_id(node)
            ]
            + [
                self._node_path(node).lower()
                for node in self.nodes
                if self._node_path(node)
            ]
        )

        hints = [
            framework
            for framework, markers in FRAMEWORK_SIGNATURES.items()
            if any(marker in corpus for marker in markers)
        ]
        return hints[:5]

    def infer_test_framework_hints(self) -> list[str]:
        corpus = " ".join(
            [
                self._node_id(node).lower()
                for node in self.nodes
                if self._node_id(node)
            ]
            + [
                self._node_path(node).lower()
                for node in self.nodes
                if self._node_path(node)
            ]
        )

        hints = [
            framework
            for framework, markers in TEST_FRAMEWORK_SIGNATURES.items()
            if any(marker in corpus for marker in markers)
        ]
        return hints[:5]

    def identify_structural_hotspots(self) -> list[dict]:
        if not self.graph.nodes:
            return []

        ranked_nodes = sorted(self.graph.degree(), key=lambda item: item[1], reverse=True)
        hotspots = []
        for node_id, degree in ranked_nodes[:5]:
            hotspots.append(
                {
                    "id": str(node_id),
                    "degree": int(degree),
                    "type": self._node_type(self.graph.nodes[node_id]),
                }
            )
        return hotspots

    def list_entrypoints(self) -> list[str]:
        entrypoints = []
        for node in self.nodes:
            node_path = self._node_path(node)
            if not node_path:
                continue

            normalized_path = node_path.replace("\\", "/")
            name = Path(normalized_path).name
            if name in ENTRYPOINT_PATTERNS:
                entrypoints.append(normalized_path)

        return sorted(set(entrypoints))[:10]

    def detect_test_presence(self) -> dict:
        tests = []
        for node in self.nodes:
            node_path = self._node_path(node)
            if not node_path:
                continue

            lowered = node_path.lower().replace("\\", "/")
            filename = Path(lowered).name
            if (
                "/tests/" in lowered
                or "/__tests__/" in lowered
                or "/spec/" in lowered
                or filename.startswith("test_")
                or ".test." in filename
                or ".spec." in filename
            ):
                tests.append(node_path)

        return {
            "has_tests": bool(tests),
            "sample_test_files": sorted(set(tests))[:10],
        }

    def top_node_types(self) -> list[dict]:
        counts = Counter(self._node_type(node) for node in self.nodes if self._node_type(node))
        return [{"type": node_type, "count": count} for node_type, count in counts.most_common(8)]

    def compile_heuristics_payload(self) -> dict:
        self.load_graph()

        architecture = self.detect_architecture_pattern()
        naming = self.extract_naming_conventions()
        hotspots = self.identify_structural_hotspots()
        tests = self.detect_test_presence()
        languages = self.infer_languages()
        frameworks = self.infer_framework_hints()
        test_frameworks = self.infer_test_framework_hints()

        payload = {
            "graph_source": str(self.resolve_graph_path()),
            "metrics": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "total_graph_nodes": self.graph.number_of_nodes(),
                "total_graph_edges": self.graph.number_of_edges(),
            },
            "project_profile": {
                "primary_languages": languages,
                "framework_hints": frameworks,
                "test_framework_hints": test_frameworks,
                "architecture_type": architecture["label"],
                "architecture_signals": architecture["signals"],
                "entrypoints": self.list_entrypoints(),
                "has_tests": tests["has_tests"],
                "sample_test_files": tests["sample_test_files"],
            },
            "naming_patterns": naming,
            "hotspots": hotspots,
            "top_node_types": self.top_node_types(),
            "architecture_type": architecture["label"],
            "naming_pattern": naming["summary"],
            "god_classes": [hotspot["id"] for hotspot in hotspots],
        }
        return payload
