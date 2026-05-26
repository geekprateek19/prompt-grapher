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

TEST_ROOT_NAMES = {"test", "tests", "spec", "specs", "__tests__"}

FILE_ROLE_MARKERS = {
    "controller": ("controller",),
    "service": ("service",),
    "repository": ("repository", "repo"),
    "component": ("component", "components"),
    "page": ("page", "pages"),
    "hook": ("hook", "hooks"),
    "model": ("model", "models"),
    "view": ("view", "views"),
    "adapter": ("adapter", "adapters"),
    "store": ("store", "stores"),
    "middleware": ("middleware",),
    "schema": ("schema", "schemas"),
    "serializer": ("serializer", "serializers"),
    "util": ("util", "utils", "helper", "helpers"),
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

ROOT_CONFIG_FILES = {
    "README.md",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    "Makefile",
    "Procfile",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "bun.lock",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "vercel.json",
    "netlify.toml",
    "render.yaml",
    "render.yml",
    "fly.toml",
    "railway.json",
    "railway.toml",
    "cloudbuild.yml",
    "cloudbuild.yaml",
    "Jenkinsfile",
    ".env",
    ".env.example",
}

PACKAGE_MANAGER_INSTALL_COMMAND = {
    "npm": "npm install",
    "pnpm": "pnpm install",
    "yarn": "yarn install",
    "bun": "bun install",
}

PACKAGE_MANAGER_RUN_PREFIX = {
    "npm": "npm run",
    "pnpm": "pnpm",
    "yarn": "yarn",
    "bun": "bun run",
}

API_SURFACE_MARKERS = {
    "route": ("route", "routes", "router", "routers", "/api/", "api/"),
    "controller": ("controller", "controllers"),
    "handler": ("handler", "handlers", "endpoint", "endpoints"),
    "view": ("view", "views"),
}

DATABASE_SURFACE_MARKERS = {
    "schema": ("schema", "schemas", "prisma", ".sql", ".prisma"),
    "migration": ("migration", "migrations", "alembic", "versions/"),
    "model": ("model", "models", "entity", "entities"),
    "repository": ("repository", "repositories", "/repo", "/repos"),
    "seed": ("seed", "seeds", "fixtures"),
    "database": ("database", "db", "sqlite", "postgres", "mysql", "mongo"),
}

DEPLOYMENT_SURFACE_MARKERS = {
    "ci": (
        ".github/workflows/",
        ".gitlab-ci.yml",
        ".gitlab-ci.yaml",
        ".circleci/",
        "azure-pipelines",
        "bitbucket-pipelines.yml",
        "jenkinsfile",
        "cloudbuild.yml",
        "cloudbuild.yaml",
    ),
    "container": (
        "dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml",
        "procfile",
        "nginx.conf",
    ),
    "hosting": (
        "vercel.json",
        "netlify.toml",
        "render.yaml",
        "render.yml",
        "fly.toml",
        "railway.json",
        "railway.toml",
        "app.yaml",
        "serverless.yml",
        "serverless.yaml",
    ),
    "infrastructure": (
        "/k8s/",
        "/kubernetes/",
        "/helm/",
        "chart.yaml",
        ".tf",
        "terraform/",
        "pulumi.",
        "skaffold.yml",
        "skaffold.yaml",
    ),
}

IMPORTANT_ROOT_FILE_REASONS = {
    "README.md": "Existing human-written project documentation.",
    "Dockerfile": "Container build definition.",
    "docker-compose.yml": "Local multi-service orchestration definition.",
    "docker-compose.yaml": "Local multi-service orchestration definition.",
    "compose.yml": "Local multi-service orchestration definition.",
    "compose.yaml": "Local multi-service orchestration definition.",
    "Makefile": "Common developer task entrypoints.",
    "Procfile": "Process-type startup definition for platform deploys.",
    "package.json": "Node package manifest and script entrypoint.",
    "pyproject.toml": "Python project metadata and tool configuration.",
    "requirements.txt": "Python dependency installation list.",
    "setup.py": "Python package installation entrypoint.",
    "vercel.json": "Deployment configuration for Vercel hosting.",
    "netlify.toml": "Deployment configuration for Netlify hosting.",
    "render.yaml": "Deployment configuration for Render hosting.",
    "render.yml": "Deployment configuration for Render hosting.",
    "fly.toml": "Deployment configuration for Fly.io hosting.",
    "railway.json": "Deployment configuration for Railway hosting.",
    "railway.toml": "Deployment configuration for Railway hosting.",
    "cloudbuild.yml": "CI or deployment pipeline configuration.",
    "cloudbuild.yaml": "CI or deployment pipeline configuration.",
    "Jenkinsfile": "CI or deployment pipeline configuration.",
    ".env": "Runtime environment variable template or local overrides.",
    ".env.example": "Runtime environment variable template or local overrides.",
}

BACKEND_FRAMEWORK_HINTS = {
    "Django",
    "FastAPI",
    "Flask",
    "Express",
    "NestJS",
    "Spring",
    "Rails",
    "Laravel",
}

GENERIC_MODULE_SEGMENTS = {
    "src",
    "app",
    "apps",
    "lib",
    "libs",
    "package",
    "packages",
    "pkg",
    "server",
    "client",
    "frontend",
    "backend",
    "web",
    "ui",
    "api",
    "apis",
    "rest",
    "graphql",
    "routes",
    "route",
    "router",
    "routers",
    "controllers",
    "controller",
    "services",
    "service",
    "repositories",
    "repository",
    "repos",
    "repo",
    "models",
    "model",
    "views",
    "view",
    "components",
    "component",
    "hooks",
    "hook",
    "pages",
    "page",
    "utils",
    "util",
    "helpers",
    "helper",
    "shared",
    "common",
    "core",
    "features",
    "feature",
    "modules",
    "module",
    "domains",
    "domain",
    "usecases",
    "use_cases",
    "adapters",
    "adapter",
    "stores",
    "store",
    "middleware",
    "schemas",
    "schema",
    "db",
    "database",
    "migrations",
    "migration",
    "tests",
    "test",
    "spec",
    "specs",
    "__tests__",
    "config",
    "configs",
    "scripts",
    "bin",
    "cmd",
}

FEATURE_REQUEST_STOPWORDS = GENERIC_MODULE_SEGMENTS | {
    "please",
    "need",
    "want",
    "update",
    "modify",
    "change",
    "edit",
    "fix",
    "improve",
    "add",
    "remove",
    "delete",
    "refactor",
    "implement",
    "build",
    "create",
    "support",
    "make",
    "module",
    "feature",
    "code",
    "project",
    "repo",
    "repository",
    "mujhe",
    "karna",
    "karo",
    "karni",
    "hai",
    "ke",
    "ko",
    "mein",
    "me",
    "ka",
    "ki",
    "aur",
}

FRONTEND_PATH_MARKERS = {
    "frontend",
    "client",
    "web",
    "ui",
    "pages",
    "page",
    "screens",
    "screen",
    "components",
    "component",
    "hooks",
    "hook",
    "views",
    "view",
    "layouts",
    "layout",
}

FRONTEND_FILE_EXTENSIONS = {
    ".tsx",
    ".jsx",
    ".vue",
    ".svelte",
    ".css",
    ".scss",
    ".sass",
    ".less",
}

BACKEND_FILE_ROLES = {
    "controller",
    "service",
    "repository",
    "model",
    "middleware",
    "schema",
    "serializer",
    "adapter",
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

    def _normalize_path(self, node_path: str) -> str:
        return node_path.replace("\\", "/").strip()

    def _path_parts(self, node_path: str) -> list[str]:
        normalized = self._normalize_path(node_path)
        return [part for part in normalized.split("/") if part and part != "."]

    def _top_directory_from_path(self, node_path: str) -> str:
        parts = self._path_parts(node_path)
        if len(parts) < 2:
            return ""
        return parts[0]

    def _all_node_paths(self) -> list[str]:
        return sorted(
            {
                self._normalize_path(self._node_path(node))
                for node in self.nodes
                if self._node_path(node)
            }
        )

    def _parent_directory(self, node_path: str) -> str:
        normalized = self._normalize_path(node_path)
        parent = str(Path(normalized).parent).replace("\\", "/")
        return "" if parent == "." else parent

    def _normalized_segment(self, segment: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", segment.lower()).strip("-")

    def _is_generic_module_segment(self, segment: str) -> bool:
        normalized = self._normalized_segment(segment)
        return not normalized or normalized.isdigit() or normalized in GENERIC_MODULE_SEGMENTS

    def _path_contains_feature_signal(self, node_path: str, signals: list[str]) -> bool:
        lowered = self._normalize_path(node_path).lower()
        normalized_parts = [self._normalized_segment(part) for part in self._path_parts(lowered)]
        stem = self._normalized_segment(Path(lowered).stem)

        for signal in signals:
            normalized_signal = self._normalized_segment(signal)
            if not normalized_signal:
                continue
            if (
                normalized_signal == stem
                or normalized_signal in normalized_parts
                or normalized_signal in lowered
            ):
                return True

        return False

    def _is_frontend_like_path(self, node_path: str) -> bool:
        normalized = self._normalize_path(node_path)
        path_parts = {self._normalized_segment(part) for part in self._path_parts(normalized)}
        suffix = Path(normalized).suffix.lower()
        file_role = self._classify_file_role(normalized)

        return (
            suffix in FRONTEND_FILE_EXTENSIONS
            or file_role in {"page", "component", "hook", "view"}
            or bool(path_parts & FRONTEND_PATH_MARKERS)
        )

    def _is_backend_like_path(self, node_path: str) -> bool:
        normalized = self._normalize_path(node_path)
        file_role = self._classify_file_role(normalized)

        if file_role in BACKEND_FILE_ROLES:
            return True

        if any(
            marker in normalized.lower()
            for marker in ("/api/", "/controllers/", "/services/", "/repositories/", "/models/", "/db/")
        ):
            return True

        return not self._is_frontend_like_path(normalized)

    def _test_files_for_request(self, request_signals: list[str], sample_test_files: list[str]) -> list[dict]:
        matched_tests = []

        for test_path in sample_test_files:
            reasons = []
            if self._path_contains_feature_signal(test_path, request_signals):
                reasons.append("Test path matches the feature request.")
            if reasons:
                matched_tests.append({"path": self._normalize_path(test_path), "reasons": reasons})

        return matched_tests[:8]

    def _matches_role_marker(self, path_parts: list[str], stem: str, marker: str) -> bool:
        return (
            any(part == marker or part == f"{marker}s" for part in path_parts)
            or stem == marker
            or stem.endswith(f"_{marker}")
            or stem.endswith(f".{marker}")
            or stem.endswith(f"-{marker}")
        )

    def _classify_file_role(self, node_path: str) -> str | None:
        normalized = self._normalize_path(node_path).lower()
        path_parts = self._path_parts(normalized)
        if not path_parts:
            return None

        stem = Path(normalized).stem.lower()
        for role, markers in FILE_ROLE_MARKERS.items():
            if any(self._matches_role_marker(path_parts, stem, marker) for marker in markers):
                return role

        if stem.startswith("use") and Path(normalized).suffix.lower() in {".js", ".jsx", ".ts", ".tsx"}:
            return "hook"

        return None

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

    def summarize_repository_shape(self) -> dict:
        top_dir_counts: Counter[str] = Counter()
        source_root_counts: Counter[str] = Counter()
        test_root_counts: Counter[str] = Counter()
        parent_dir_counts: Counter[str] = Counter()
        role_counts: Counter[str] = Counter()

        for node in self.nodes:
            node_path = self._node_path(node)
            if not node_path:
                continue

            normalized = self._normalize_path(node_path)
            top_dir = self._top_directory_from_path(normalized)
            is_test_path = False
            if top_dir:
                top_dir_counts[top_dir] += 1
                if top_dir.lower() in TEST_ROOT_NAMES or "test" in top_dir.lower() or "spec" in top_dir.lower():
                    test_root_counts[top_dir] += 1
                    is_test_path = True
                else:
                    source_root_counts[top_dir] += 1

            parent_dir = self._parent_directory(normalized)
            if parent_dir:
                parent_dir_counts[parent_dir] += 1

            role = self._classify_file_role(normalized)
            if role and not is_test_path:
                role_counts[role] += 1

        return {
            "top_directories": [
                {"path": path, "count": count}
                for path, count in top_dir_counts.most_common(6)
            ],
            "source_roots": [path for path, _ in source_root_counts.most_common(4)],
            "test_roots": [path for path, _ in test_root_counts.most_common(4)],
            "module_path_examples": [path for path, _ in parent_dir_counts.most_common(8)],
            "dominant_file_roles": [role for role, _ in role_counts.most_common(6)],
        }

    def _root_files(self) -> list[str]:
        root_files = {
            Path(node_path).name
            for node_path in self._all_node_paths()
            if len(self._path_parts(node_path)) == 1
        }

        for filename in ROOT_CONFIG_FILES:
            if (self.project_path / filename).exists():
                root_files.add(filename)

        return sorted(root_files)

    def _detect_package_manager(self, root_files: list[str]) -> str | None:
        root_file_set = set(root_files)
        if "pnpm-lock.yaml" in root_file_set:
            return "pnpm"
        if "yarn.lock" in root_file_set:
            return "yarn"
        if "bun.lockb" in root_file_set or "bun.lock" in root_file_set:
            return "bun"
        if "package-lock.json" in root_file_set or "package.json" in root_file_set:
            return "npm"
        return None

    def _load_package_json(self) -> dict:
        package_json_path = self.project_path / "package.json"
        if not package_json_path.exists():
            return {}

        try:
            with package_json_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError, ValueError):
            return {}

        return data if isinstance(data, dict) else {}

    def infer_runtime_hints(
        self,
        entrypoints: list[str],
        test_framework_hints: list[str],
        has_tests: bool,
    ) -> dict:
        root_files = self._root_files()
        package_manager = self._detect_package_manager(root_files)
        package_json = self._load_package_json()
        raw_scripts = package_json.get("scripts", {})
        scripts = raw_scripts if isinstance(raw_scripts, dict) else {}

        install_commands: list[dict] = []
        run_commands: list[dict] = []
        test_commands: list[dict] = []
        seen_commands: set[str] = set()

        def add_command(target: list[dict], command: str, reason: str, confidence: str = "observed") -> None:
            normalized = command.strip()
            if not normalized or normalized in seen_commands:
                return

            seen_commands.add(normalized)
            target.append(
                {
                    "command": normalized,
                    "reason": reason,
                    "confidence": confidence,
                }
            )

        if package_manager:
            install_command = PACKAGE_MANAGER_INSTALL_COMMAND[package_manager]
            add_command(install_commands, install_command, "Package manager lockfile or package.json detected.")

        if "requirements.txt" in root_files:
            add_command(install_commands, "pip install -r requirements.txt", "requirements.txt detected.")

        if "setup.py" in root_files or "pyproject.toml" in root_files:
            add_command(install_commands, "pip install -e .", "Python package metadata detected.", confidence="inferred")

        run_prefix = PACKAGE_MANAGER_RUN_PREFIX.get(package_manager or "")
        for script_name in ("dev", "start", "serve", "preview", "build"):
            script_body = scripts.get(script_name)
            if not isinstance(script_body, str):
                continue

            if run_prefix:
                add_command(
                    run_commands,
                    f"{run_prefix} {script_name}",
                    f"package.json script '{script_name}' detected.",
                )

        if isinstance(scripts.get("test"), str) and run_prefix:
            add_command(
                test_commands,
                f"{run_prefix} test",
                "package.json script 'test' detected.",
            )

        if "manage.py" in {Path(entrypoint).name for entrypoint in entrypoints}:
            add_command(
                run_commands,
                "python manage.py runserver",
                "manage.py entrypoint detected.",
                confidence="inferred",
            )

        if not run_commands:
            for entrypoint in entrypoints:
                entry_name = Path(entrypoint).name
                if entry_name in {"main.py", "app.py", "server.py"}:
                    add_command(
                        run_commands,
                        f"python {entrypoint}",
                        f"{entry_name} entrypoint detected.",
                        confidence="inferred",
                    )

        if "docker-compose.yml" in root_files or "docker-compose.yaml" in root_files:
            add_command(
                run_commands,
                "docker compose up",
                "docker-compose file detected.",
                confidence="inferred",
            )

        if has_tests and not test_commands:
            if "Pytest" in test_framework_hints:
                add_command(test_commands, "pytest", "Pytest markers detected.", confidence="inferred")
            elif "unittest" in test_framework_hints:
                add_command(test_commands, "python -m unittest", "unittest markers detected.", confidence="inferred")
            elif "Jest" in test_framework_hints and run_prefix:
                add_command(test_commands, f"{run_prefix} test", "Jest markers detected.", confidence="inferred")
            elif "Vitest" in test_framework_hints and run_prefix:
                add_command(test_commands, f"{run_prefix} test", "Vitest markers detected.", confidence="inferred")

        package_scripts = [
            {"name": name, "command": command}
            for name, command in scripts.items()
            if isinstance(name, str) and isinstance(command, str)
        ][:8]

        package_managers = [package_manager] if package_manager else []
        return {
            "package_managers": package_managers,
            "root_files": root_files,
            "install_commands": install_commands,
            "run_commands": run_commands,
            "test_commands": test_commands,
            "package_scripts": package_scripts,
        }

    def _match_surface_kind(self, node_path: str, markers: dict[str, tuple[str, ...]]) -> str | None:
        lowered = node_path.lower()
        for kind, kind_markers in markers.items():
            if any(marker in lowered for marker in kind_markers):
                return kind
        return None

    def infer_api_surface(self) -> list[dict]:
        api_surface = []
        seen_paths = set()

        for node_path in self._all_node_paths():
            kind = self._match_surface_kind(node_path, API_SURFACE_MARKERS)
            if not kind or node_path in seen_paths:
                continue

            seen_paths.add(node_path)
            api_surface.append({"path": node_path, "kind": kind})

        return api_surface[:12]

    def infer_database_surface(self) -> list[dict]:
        database_surface = []
        seen_paths = set()

        for node_path in self._all_node_paths():
            kind = self._match_surface_kind(node_path, DATABASE_SURFACE_MARKERS)
            if not kind or node_path in seen_paths:
                continue

            seen_paths.add(node_path)
            database_surface.append({"path": node_path, "kind": kind})

        return database_surface[:12]

    def infer_deployment_hints(self, runtime_hints: dict, entrypoints: list[str]) -> dict:
        deployment_files: list[dict] = []
        environment_files: list[dict] = []
        build_commands: list[dict] = []
        deployment_commands: list[dict] = []
        seen_files: set[str] = set()
        seen_build_commands: set[str] = set()
        seen_deployment_commands: set[str] = set()

        def add_file(target: list[dict], path: str, kind: str, reason: str) -> None:
            normalized = self._normalize_path(path)
            if not normalized or normalized in seen_files:
                return

            seen_files.add(normalized)
            target.append({"path": normalized, "kind": kind, "reason": reason})

        def add_command(target: list[dict], seen_commands: set[str], command: str, reason: str) -> None:
            normalized = command.strip()
            if not normalized or normalized in seen_commands:
                return

            seen_commands.add(normalized)
            target.append({"command": normalized, "reason": reason})

        kind_reasons = {
            "ci": "CI or deployment pipeline file detected.",
            "container": "Container or process startup configuration detected.",
            "hosting": "Hosting-platform deployment configuration detected.",
            "infrastructure": "Infrastructure or orchestration definition detected.",
        }
        environment_paths = {".env", ".env.example", ".env.local", ".env.production", ".env.staging"}

        for root_file in runtime_hints.get("root_files", []):
            kind = self._match_surface_kind(root_file, DEPLOYMENT_SURFACE_MARKERS)
            if kind:
                add_file(deployment_files, root_file, kind, kind_reasons[kind])
            if root_file in environment_paths:
                add_file(
                    environment_files,
                    root_file,
                    "environment",
                    "Environment-variable template or runtime override file detected.",
                )

        for node_path in self._all_node_paths():
            lowered = node_path.lower()
            kind = self._match_surface_kind(node_path, DEPLOYMENT_SURFACE_MARKERS)
            if kind:
                add_file(deployment_files, node_path, kind, kind_reasons[kind])
            if Path(lowered).name in environment_paths:
                add_file(
                    environment_files,
                    node_path,
                    "environment",
                    "Environment-variable template or runtime override file detected.",
                )

        for script in runtime_hints.get("package_scripts", []):
            name = str(script.get("name", "")).strip().lower()
            command = str(script.get("command", "")).strip()
            if not name or not command:
                continue

            if name in {"build", "compile", "bundle", "dist"} or "docker build" in command.lower():
                add_command(
                    build_commands,
                    seen_build_commands,
                    command,
                    f"package.json script '{name}' detected.",
                )

            if name in {"deploy", "release", "start", "serve", "preview"} or any(
                marker in command.lower()
                for marker in ("vercel", "netlify", "render", "railway", "fly", "kubectl", "helm", "docker")
            ):
                add_command(
                    deployment_commands,
                    seen_deployment_commands,
                    command,
                    f"package.json script '{name}' detected.",
                )

        for run_command in runtime_hints.get("run_commands", []):
            command = str(run_command.get("command", "")).strip()
            reason = str(run_command.get("reason", "")).strip() or "Runtime command detected."
            if command and any(marker in command.lower() for marker in ("docker", "serve", "start", "runserver")):
                add_command(deployment_commands, seen_deployment_commands, command, reason)

        return {
            "entrypoints": entrypoints[:6],
            "container_files": [item for item in deployment_files if item["kind"] == "container"][:8],
            "ci_cd_files": [item for item in deployment_files if item["kind"] == "ci"][:8],
            "hosting_files": [item for item in deployment_files if item["kind"] == "hosting"][:8],
            "infrastructure_files": [item for item in deployment_files if item["kind"] == "infrastructure"][:8],
            "environment_files": environment_files[:8],
            "build_commands": build_commands[:6],
            "deployment_commands": deployment_commands[:6],
        }

    def infer_feature_modules(self) -> list[dict]:
        module_map: dict[str, dict] = {}

        for node_path in self._all_node_paths():
            path_parts = self._path_parts(node_path)
            if len(path_parts) < 2:
                continue

            candidate_name = None
            for segment in reversed(path_parts[:-1]):
                if self._is_generic_module_segment(segment):
                    continue
                candidate_name = self._normalized_segment(segment)
                break

            if not candidate_name:
                continue

            module_entry = module_map.setdefault(
                candidate_name,
                {
                    "name": candidate_name,
                    "file_count": 0,
                    "sample_files": [],
                    "role_counts": Counter(),
                    "source_root_counts": Counter(),
                },
            )
            module_entry["file_count"] += 1
            if len(module_entry["sample_files"]) < 6:
                module_entry["sample_files"].append(node_path)

            file_role = self._classify_file_role(node_path)
            if file_role:
                module_entry["role_counts"][file_role] += 1

            source_root = self._top_directory_from_path(node_path)
            if source_root:
                module_entry["source_root_counts"][source_root] += 1

        ranked_modules = sorted(
            module_map.values(),
            key=lambda item: (-item["file_count"], item["name"]),
        )

        feature_modules = []
        for module_entry in ranked_modules[:12]:
            feature_modules.append(
                {
                    "name": module_entry["name"],
                    "file_count": module_entry["file_count"],
                    "sample_files": module_entry["sample_files"],
                    "related_roles": [
                        role for role, _ in module_entry["role_counts"].most_common(4)
                    ],
                    "source_roots": [
                        root for root, _ in module_entry["source_root_counts"].most_common(3)
                    ],
                }
            )

        return feature_modules

    def _feature_request_tokens(self, feature_request: str) -> list[str]:
        raw_tokens = re.findall(r"[a-zA-Z0-9]+", feature_request.lower())
        tokens = []
        seen = set()

        for token in raw_tokens:
            if len(token) < 3 or token in FEATURE_REQUEST_STOPWORDS or token in seen:
                continue
            seen.add(token)
            tokens.append(token)

        return tokens[:8]

    def _build_change_request_context(self, request_text: str, payload: dict, request_kind: str) -> dict:
        tokens = self._feature_request_tokens(request_text)
        feature_modules = payload.get("feature_modules", [])
        important_files = payload.get("important_files", [])
        api_surface = payload.get("api_surface", [])
        database_surface = payload.get("database_surface", [])
        hotspots = payload.get("hotspots", [])
        runtime_hints = payload.get("runtime_hints", {})
        sample_test_files = payload.get("project_profile", {}).get("sample_test_files", [])

        path_scores: Counter[str] = Counter()
        reasons_by_path: dict[str, set[str]] = {}

        def add_score(path: str, score: int, reason: str) -> None:
            normalized = self._normalize_path(path)
            if not normalized:
                return

            path_scores[normalized] += score
            reasons_by_path.setdefault(normalized, set()).add(reason)

        matched_modules = []
        for module in feature_modules:
            module_name = str(module.get("name") or "").lower()
            if not module_name:
                continue

            if any(token == module_name or token in module_name or module_name in token for token in tokens):
                matched_modules.append(module_name)
                for sample_file in module.get("sample_files", []):
                    add_score(str(sample_file), 10, f"Matches inferred module '{module_name}'.")

        request_signals = tokens + matched_modules

        for node_path in self._all_node_paths():
            lowered_path = node_path.lower()
            path_parts = [part.lower() for part in self._path_parts(lowered_path)]
            stem = Path(lowered_path).stem
            for token in tokens:
                if token in path_parts or token == stem:
                    add_score(node_path, 8, f"Path matches token '{token}'.")
                elif token in lowered_path:
                    add_score(node_path, 5, f"Path contains token '{token}'.")

        for highlighted_file in important_files:
            path = highlighted_file.get("path")
            if path and self._normalize_path(path) in path_scores:
                add_score(str(path), 3, "Repository-important file.")

        for api_file in api_surface:
            path = api_file.get("path")
            if path and self._normalize_path(path) in path_scores:
                add_score(str(path), 2, "Touches detected API surface.")

        for database_file in database_surface:
            path = database_file.get("path")
            if path and self._normalize_path(path) in path_scores:
                add_score(str(path), 2, "Touches detected database surface.")

        for hotspot in hotspots:
            path = hotspot.get("path") or hotspot.get("id")
            if path and self._normalize_path(str(path)) in path_scores:
                add_score(str(path), 2, "Structural hotspot in the dependency graph.")

        node_paths = {
            self._node_id(node): self._normalize_path(self._node_path(node))
            for node in self.nodes
            if self._node_id(node) and self._node_path(node)
        }
        neighbor_map: dict[str, set[str]] = {}
        for edge in self.edges:
            source_path = node_paths.get(edge["source"])
            target_path = node_paths.get(edge["target"])
            if not source_path or not target_path:
                continue

            neighbor_map.setdefault(source_path, set()).add(target_path)
            neighbor_map.setdefault(target_path, set()).add(source_path)

        for path, _score in path_scores.most_common(4):
            for neighbor_path in sorted(neighbor_map.get(path, set()))[:3]:
                add_score(neighbor_path, 2, f"One-hop dependency neighbor of {path}.")

        if not path_scores:
            for important_file in important_files[:6]:
                path = important_file.get("path")
                if path:
                    add_score(str(path), 1, "Fallback important file because no direct request token matched.")

        relevant_files = [
            {
                "path": path,
                "score": score,
                "role": self._classify_file_role(path),
                "reasons": sorted(reasons_by_path.get(path, set()))[:3],
            }
            for path, score in path_scores.most_common(12)
        ]

        relevant_paths = [item["path"] for item in relevant_files]
        relevant_path_set = set(relevant_paths)

        def summarize_surface_items(surface_items: list[dict], limit: int = 8) -> list[dict]:
            matches = []
            for item in surface_items:
                path = self._normalize_path(str(item.get("path") or ""))
                if not path:
                    continue

                neighbor_matches = sorted(relevant_path_set & neighbor_map.get(path, set()))
                if (
                    path not in relevant_path_set
                    and not self._path_contains_feature_signal(path, request_signals)
                    and not neighbor_matches
                ):
                    continue

                if path in relevant_path_set:
                    reason = "Already ranked as a relevant file."
                elif neighbor_matches:
                    reason = f"One-hop dependency neighbor of {neighbor_matches[0]}."
                else:
                    reason = f"Surface path matches the {request_kind} request."
                matches.append(
                    {
                        "path": path,
                        "kind": str(item.get("kind") or "unknown"),
                        "reasons": [reason],
                    }
                )

            return matches[:limit]

        api_candidates = summarize_surface_items(api_surface)
        database_candidates = summarize_surface_items(database_surface)

        frontend_candidates = [
            {
                "path": item["path"],
                "role": item.get("role"),
                "reasons": item["reasons"],
            }
            for item in relevant_files
            if self._is_frontend_like_path(item["path"])
        ][:8]

        backend_candidates = [
            {
                "path": item["path"],
                "role": item.get("role"),
                "reasons": item["reasons"],
            }
            for item in relevant_files
            if self._is_backend_like_path(item["path"])
        ][:8]

        frontend_screen_candidates = [
            item
            for item in frontend_candidates
            if (item.get("role") in {"page", "component", "view"})
            or self._path_contains_feature_signal(item["path"], ["screen", "page", "view", "component"])
        ][:6]

        test_candidates = self._test_files_for_request(request_signals, sample_test_files)
        validation_commands = {
            "test": runtime_hints.get("test_commands", [])[:3],
            "run": runtime_hints.get("run_commands", [])[:3],
        }

        return {
            "kind": request_kind,
            "request": request_text,
            "tokens": tokens,
            "matched_modules": sorted(set(matched_modules))[:6],
            "relevant_files": relevant_files,
            "api_candidates": api_candidates,
            "database_candidates": database_candidates,
            "frontend_files": frontend_candidates,
            "backend_files": backend_candidates,
            "frontend_screen_candidates": frontend_screen_candidates,
            "test_files": test_candidates,
            "validation_commands": validation_commands,
        }

    def build_feature_request_context(self, feature_request: str, payload: dict) -> dict:
        return self._build_change_request_context(feature_request, payload, request_kind="feature")

    def build_bug_report_context(self, bug_report: str, payload: dict) -> dict:
        return self._build_change_request_context(bug_report, payload, request_kind="bug")

    def infer_important_files(
        self,
        entrypoints: list[str],
        hotspots: list[dict],
        runtime_hints: dict,
        api_surface: list[dict],
        database_surface: list[dict],
    ) -> list[dict]:
        important_files: list[dict] = []
        seen_paths = set()

        def add_file(path: str, reason: str) -> None:
            normalized = self._normalize_path(path)
            if not normalized or normalized in seen_paths:
                return

            seen_paths.add(normalized)
            important_files.append({"path": normalized, "reason": reason})

        for entrypoint in entrypoints:
            add_file(entrypoint, "Detected entrypoint for running or bootstrapping the project.")

        for hotspot in hotspots[:3]:
            hotspot_path = hotspot.get("path") or hotspot.get("id")
            if hotspot_path:
                add_file(
                    str(hotspot_path),
                    f"Highly connected hotspot with graph degree {hotspot['degree']}.",
                )

        for root_file in runtime_hints.get("root_files", []):
            reason = IMPORTANT_ROOT_FILE_REASONS.get(root_file)
            if reason:
                add_file(root_file, reason)

        for api_file in api_surface[:2]:
            add_file(api_file["path"], f"API-related {api_file['kind']} file.")

        for database_file in database_surface[:2]:
            add_file(database_file["path"], f"Database-related {database_file['kind']} file.")

        return important_files[:12]

    def infer_risk_flags(
        self,
        architecture: dict,
        tests: dict,
        frameworks: list[str],
        runtime_hints: dict,
        hotspots: list[dict],
        api_surface: list[dict],
    ) -> list[dict]:
        risk_flags = []

        if not tests["has_tests"]:
            risk_flags.append(
                {
                    "summary": "Automated test coverage is not evident from the repository graph.",
                    "evidence": "No files matched common test directories or filename patterns.",
                }
            )

        if architecture["label"] == "Custom or mixed modular architecture":
            risk_flags.append(
                {
                    "summary": "Architecture boundaries appear implicit rather than strongly codified.",
                    "evidence": "The graph did not show a dominant layered, component, or clean-architecture pattern.",
                }
            )

        if architecture["label"] == "Utility-heavy monolith":
            risk_flags.append(
                {
                    "summary": "Utility-heavy structure can hide business logic and blur module ownership.",
                    "evidence": "Utility and helper markers dominate the repository shape signals.",
                }
            )

        if hotspots:
            top_hotspot = hotspots[0]
            hotspot_path = top_hotspot.get("path") or top_hotspot["id"]
            risk_flags.append(
                {
                    "summary": "A small number of files are structurally central to the codebase.",
                    "evidence": f"{hotspot_path} has graph degree {top_hotspot['degree']}.",
                }
            )

        if not runtime_hints.get("run_commands"):
            risk_flags.append(
                {
                    "summary": "A local run command is not obvious from the detected entrypoints and config files.",
                    "evidence": "No package script or standard boot command could be confidently inferred.",
                }
            )

        if set(frameworks) & BACKEND_FRAMEWORK_HINTS and not api_surface:
            risk_flags.append(
                {
                    "summary": "Backend framework signals exist, but the API surface is not clearly mapped by filename.",
                    "evidence": "No controller, route, router, handler, or api-marked files were detected.",
                }
            )

        return risk_flags[:6]

    def infer_dependency_flows(self) -> list[dict]:
        node_paths = {
            self._node_id(node): self._normalize_path(self._node_path(node))
            for node in self.nodes
            if self._node_id(node) and self._node_path(node)
        }
        flow_counts: Counter[tuple[str, str]] = Counter()

        for edge in self.edges:
            source_path = node_paths.get(edge["source"])
            target_path = node_paths.get(edge["target"])
            if not source_path or not target_path:
                continue

            source_role = self._classify_file_role(source_path)
            target_role = self._classify_file_role(target_path)
            if source_role and target_role and source_role != target_role:
                flow_counts[(source_role, target_role)] += 1

        return [
            {"from": source, "to": target, "count": count}
            for (source, target), count in flow_counts.most_common(6)
        ]

    def identify_structural_hotspots(self) -> list[dict]:
        if not self.graph.nodes:
            return []

        ranked_nodes = sorted(self.graph.degree(), key=lambda item: item[1], reverse=True)
        hotspots = []
        for node_id, degree in ranked_nodes[:5]:
            node_data = dict(self.graph.nodes[node_id])
            node_path = self._normalize_path(self._node_path(node_data))
            hotspots.append(
                {
                    "id": str(node_id),
                    "path": node_path,
                    "degree": int(degree),
                    "type": self._node_type(node_data),
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
        repository_shape = self.summarize_repository_shape()
        dependency_flows = self.infer_dependency_flows()
        entrypoints = self.list_entrypoints()
        runtime_hints = self.infer_runtime_hints(entrypoints, test_frameworks, tests["has_tests"])
        api_surface = self.infer_api_surface()
        database_surface = self.infer_database_surface()
        deployment_hints = self.infer_deployment_hints(runtime_hints, entrypoints)
        feature_modules = self.infer_feature_modules()
        important_files = self.infer_important_files(
            entrypoints,
            hotspots,
            runtime_hints,
            api_surface,
            database_surface,
        )
        risk_flags = self.infer_risk_flags(
            architecture,
            tests,
            frameworks,
            runtime_hints,
            hotspots,
            api_surface,
        )

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
                "entrypoints": entrypoints,
                "has_tests": tests["has_tests"],
                "sample_test_files": tests["sample_test_files"],
            },
            "repository_shape": repository_shape,
            "dependency_flows": dependency_flows,
            "runtime_hints": runtime_hints,
            "api_surface": api_surface,
            "database_surface": database_surface,
            "deployment_hints": deployment_hints,
            "feature_modules": feature_modules,
            "important_files": important_files,
            "risk_flags": risk_flags,
            "naming_patterns": naming,
            "hotspots": hotspots,
            "top_node_types": self.top_node_types(),
            "architecture_type": architecture["label"],
            "naming_pattern": naming["summary"],
            "god_classes": [hotspot["id"] for hotspot in hotspots],
        }
        return payload
