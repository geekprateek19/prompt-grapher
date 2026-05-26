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
    assert payload["repository_shape"]["source_roots"] == ["src"]
    assert payload["repository_shape"]["test_roots"] == ["tests"]
    assert payload["repository_shape"]["dominant_file_roles"][:3] == ["controller", "service", "repository"]
    assert payload["dependency_flows"] == [
        {"from": "controller", "to": "service", "count": 1},
        {"from": "service", "to": "repository", "count": 1},
    ]
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
    assert payload["repository_shape"]["source_roots"] == ["src"]
    assert payload["repository_shape"]["dominant_file_roles"] == ["component", "page", "hook"]
    assert payload["dependency_flows"] == [
        {"from": "page", "to": "component", "count": 1},
        {"from": "component", "to": "hook", "count": 1},
    ]
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


def test_parser_collects_runtime_and_onboarding_hints(tmp_path: Path) -> None:
    project = tmp_path / "sample-project"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)

    (project / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "dev": "vite",
                    "test": "vitest run",
                }
            }
        ),
        encoding="utf-8",
    )
    (project / "README.md").write_text("# Sample\n", encoding="utf-8")

    graph = {
        "nodes": [
            {"id": "package.json", "type": "file", "path": "package.json"},
            {"id": "README.md", "type": "file", "path": "README.md"},
            {"id": "src/api/users.ts", "type": "file", "path": "src/api/users.ts"},
            {"id": "src/db/schema.sql", "type": "file", "path": "src/db/schema.sql"},
            {"id": "src/main.ts", "type": "file", "path": "src/main.ts"},
            {"id": "tests/user.test.ts", "type": "file", "path": "tests/user.test.ts"},
            {"id": "vitest.config.ts", "type": "file", "path": "vitest.config.ts"},
        ],
        "edges": [
            {"source": "src/main.ts", "target": "src/api/users.ts", "type": "imports"},
            {"source": "src/api/users.ts", "target": "src/db/schema.sql", "type": "imports"},
        ],
    }
    (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    payload = GraphifyHeuristicParser(project).compile_heuristics_payload()

    assert payload["runtime_hints"]["package_managers"] == ["npm"]
    assert payload["runtime_hints"]["run_commands"][0]["command"] == "npm run dev"
    assert payload["runtime_hints"]["test_commands"][0]["command"] == "npm run test"
    assert payload["api_surface"] == [{"path": "src/api/users.ts", "kind": "route"}]
    assert payload["database_surface"][0] == {"path": "src/db/schema.sql", "kind": "schema"}
    assert any(item["path"] == "src/main.ts" for item in payload["important_files"])
    assert any(item["path"] == "README.md" for item in payload["important_files"])


def test_parser_builds_feature_modules_and_request_context(tmp_path: Path) -> None:
    project = tmp_path / "sample-project"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)

    graph = {
        "nodes": [
            {"id": "src/auth/controller.py", "type": "file", "path": "src/auth/controller.py"},
            {"id": "src/auth/service.py", "type": "file", "path": "src/auth/service.py"},
            {"id": "src/auth/repository.py", "type": "file", "path": "src/auth/repository.py"},
            {"id": "src/billing/service.py", "type": "file", "path": "src/billing/service.py"},
            {"id": "tests/test_auth.py", "type": "file", "path": "tests/test_auth.py"},
        ],
        "edges": [
            {"source": "src/auth/controller.py", "target": "src/auth/service.py", "type": "imports"},
            {"source": "src/auth/service.py", "target": "src/auth/repository.py", "type": "imports"},
        ],
    }
    (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    parser = GraphifyHeuristicParser(project)
    payload = parser.compile_heuristics_payload()
    context = parser.build_feature_request_context("Mujhe auth module modify karna hai", payload)

    assert payload["feature_modules"][0]["name"] == "auth"
    assert payload["feature_modules"][0]["file_count"] == 3
    assert context["matched_modules"] == ["auth"]
    assert context["relevant_files"][0]["path"].startswith("src/auth/")
    assert any(item["path"] == "src/auth/service.py" for item in context["relevant_files"])
    assert any(item["path"] == "src/auth/controller.py" for item in context["api_candidates"])
    assert any(item["path"] == "src/auth/repository.py" for item in context["database_candidates"])
    assert any(item["path"] == "tests/test_auth.py" for item in context["test_files"])


def test_parser_marks_frontend_and_backend_feature_surfaces(tmp_path: Path) -> None:
    project = tmp_path / "sample-project"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)

    graph = {
        "nodes": [
            {"id": "src/payments/api/checkout.ts", "type": "file", "path": "src/payments/api/checkout.ts"},
            {"id": "src/payments/pages/CheckoutPage.tsx", "type": "file", "path": "src/payments/pages/CheckoutPage.tsx"},
            {"id": "src/payments/components/PaymentForm.tsx", "type": "file", "path": "src/payments/components/PaymentForm.tsx"},
            {"id": "src/payments/db/schema.sql", "type": "file", "path": "src/payments/db/schema.sql"},
            {"id": "tests/payments/checkout.test.ts", "type": "file", "path": "tests/payments/checkout.test.ts"},
        ],
        "edges": [
            {"source": "src/payments/pages/CheckoutPage.tsx", "target": "src/payments/components/PaymentForm.tsx", "type": "imports"},
            {"source": "src/payments/api/checkout.ts", "target": "src/payments/db/schema.sql", "type": "imports"},
        ],
    }
    (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    parser = GraphifyHeuristicParser(project)
    payload = parser.compile_heuristics_payload()
    context = parser.build_feature_request_context("Add payment gateway in this app", payload)

    assert any(item["path"] == "src/payments/pages/CheckoutPage.tsx" for item in context["frontend_files"])
    assert any(item["path"] == "src/payments/api/checkout.ts" for item in context["backend_files"])
    assert any(item["path"] == "src/payments/pages/CheckoutPage.tsx" for item in context["frontend_screen_candidates"])


def test_parser_builds_bug_report_context(tmp_path: Path) -> None:
    project = tmp_path / "sample-project"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)

    graph = {
        "nodes": [
            {"id": "src/payments/webhook.ts", "type": "file", "path": "src/payments/webhook.ts"},
            {"id": "src/orders/order.service.ts", "type": "file", "path": "src/orders/order.service.ts"},
            {"id": "src/db/schema.prisma", "type": "file", "path": "src/db/schema.prisma"},
            {"id": "mobile/screens/PaymentSuccess.tsx", "type": "file", "path": "mobile/screens/PaymentSuccess.tsx"},
            {"id": "tests/payments/webhook.test.ts", "type": "file", "path": "tests/payments/webhook.test.ts"},
        ],
        "edges": [
            {"source": "src/payments/webhook.ts", "target": "src/orders/order.service.ts", "type": "imports"},
            {"source": "src/orders/order.service.ts", "target": "src/db/schema.prisma", "type": "imports"},
        ],
    }
    (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    parser = GraphifyHeuristicParser(project)
    payload = parser.compile_heuristics_payload()
    context = parser.build_bug_report_context("Payment status is not updating after UPI success", payload)

    assert context["kind"] == "bug"
    assert any(item["path"] == "src/payments/webhook.ts" for item in context["relevant_files"])
    assert any(item["path"] == "src/orders/order.service.ts" for item in context["backend_files"])
    assert any(item["path"] == "src/db/schema.prisma" for item in context["database_candidates"])
    assert any(item["path"] == "mobile/screens/PaymentSuccess.tsx" for item in context["frontend_files"])


def test_parser_collects_deployment_hints(tmp_path: Path) -> None:
    project = tmp_path / "sample-project"
    graphify_dir = project / "graphify-out"
    graphify_dir.mkdir(parents=True)
    (project / "Dockerfile").write_text("FROM node:20\n", encoding="utf-8")
    (project / "docker-compose.yml").write_text("services:\n", encoding="utf-8")
    (project / ".env.example").write_text("PORT=3000\n", encoding="utf-8")
    (project / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "build": "npm run lint && vite build",
                    "deploy": "vercel --prod",
                    "start": "node server.js",
                }
            }
        ),
        encoding="utf-8",
    )

    graph = {
        "nodes": [
            {"id": "Dockerfile", "type": "file", "path": "Dockerfile"},
            {"id": "docker-compose.yml", "type": "file", "path": "docker-compose.yml"},
            {"id": ".github/workflows/deploy.yml", "type": "file", "path": ".github/workflows/deploy.yml"},
            {"id": "infra/k8s/deployment.yaml", "type": "file", "path": "infra/k8s/deployment.yaml"},
            {"id": "src/main.ts", "type": "file", "path": "src/main.ts"},
        ],
        "edges": [],
    }
    (graphify_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")

    payload = GraphifyHeuristicParser(project).compile_heuristics_payload()
    deployment_hints = payload["deployment_hints"]

    assert any(item["path"] == "Dockerfile" for item in deployment_hints["container_files"])
    assert any(item["path"] == ".github/workflows/deploy.yml" for item in deployment_hints["ci_cd_files"])
    assert any(item["path"] == "infra/k8s/deployment.yaml" for item in deployment_hints["infrastructure_files"])
    assert any(item["path"] == ".env.example" for item in deployment_hints["environment_files"])
    assert any(item["command"] == "npm run lint && vite build" for item in deployment_hints["build_commands"])
    assert any(item["command"] == "vercel --prod" for item in deployment_hints["deployment_commands"])
