from core.synthesizer import PromptSynthesizer


def test_build_messages_contains_specific_rule_requirements(monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL_NAME", "test-model")
    synthesizer = PromptSynthesizer()

    messages = synthesizer._build_messages(
        {
            "project_profile": {
                "primary_languages": ["TypeScript"],
                "framework_hints": ["React"],
                "test_framework_hints": ["Vitest"],
            }
        }
    )

    user_prompt = messages[1]["content"]

    assert "Do not use vague phrases such as \"mixed approach\"" in user_prompt
    assert "Convert detected architecture type, source roots, module paths, entrypoints, file roles, and dependency flows into explicit boundaries" in user_prompt
    assert "Mention concrete directories, layers, or module names from the payload instead of generic labels" in user_prompt
    assert "explicitly forbid broad refactors, folder moves, file renames, architecture migrations, dependency swaps, or global formatting changes" in user_prompt
    assert "follow the naming convention already used in the touched directory" in user_prompt
    assert "If the payload includes class, function, or file naming patterns, state those naming patterns directly" in user_prompt
    assert "If the payload shows recurring file role suffixes or prefixes, preserve those local patterns instead of introducing a new naming scheme" in user_prompt
    assert "Use the existing test setup already configured in the repository" in user_prompt
    assert "prefer the matching configured framework and name only those exact frameworks" in user_prompt
    assert "Do not introduce a new test runner unless no test setup exists" in user_prompt
    assert "Mirror the detected test file placement and filename style when adding or updating tests" in user_prompt
    assert "[BUG FIX PROTOCOL]" in user_prompt
    assert "Identify the root cause before making changes" in user_prompt
    assert "When fixing a bug, change the minimum number of lines required" in user_prompt
    assert "Apply the smallest safe fix in the affected service, component, or utility" in user_prompt
    assert "Change only the condition that is wrong. Leave correct conditions untouched" in user_prompt
    assert "If business rules are unclear, ask before editing instead of assuming" in user_prompt
    assert "Add or update a regression test that fails before the fix and passes after the fix" in user_prompt
    assert "If the user clarifies business rules mid-task, revert wrong assumptions and apply only the final agreed rules" in user_prompt
    assert "[DIFF HYGIENE]" in user_prompt
    assert "The diff must contain only intentional changes" in user_prompt
    assert "Never leave commented-out old code in the file" in user_prompt
    assert "Preserve existing indentation, line breaks, and naming in untouched code" in user_prompt
    assert "[FILE PLACEMENT]" in user_prompt
    assert "Say where new files belong based on detected source roots, module paths, and co-location patterns from the payload" in user_prompt
    assert "[DEPENDENCY HYGIENE]" in user_prompt
    assert "Respect observed dependency flows and layer boundaries from the payload" in user_prompt
    assert "[PROVE BEFORE EXPANDING]" in user_prompt
    assert "Before adding defensive code such as null checks, try-catch blocks, caching, eager-loading expansions, or similar safeguards" in user_prompt
    assert "If that failure is not proven, do not add the defensive code" in user_prompt
    assert "Do not add caching, memoization, batching, or lazy loading preemptively" in user_prompt
    assert "[PUBLIC CONTRACT SAFETY]" in user_prompt
    assert "explicitly forbids changing public APIs, exported names, route paths, request and response shapes" in user_prompt
    assert "Do not expose secrets, tokens, credentials, PII, or sensitive data" in user_prompt
    assert "Do not weaken authentication, authorization, encryption, auditability, or permission checks" in user_prompt
    assert "summarize changed files if edits were made; otherwise summarize proposed files and changes" in user_prompt
    assert "Also summarize behavior impact, architecture impact, and tests or validation run" in user_prompt


def test_generate_rule_files_writes_cursor_and_agents_outputs(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL_NAME", "test-model")
    synthesizer = PromptSynthesizer()
    monkeypatch.setattr(synthesizer, "_build_rules_body", lambda dna_metrics: "[ROLE]\nPreserve architecture.")

    written = synthesizer.generate_rule_files({}, tmp_path)

    cursor_rules = written["cursor_rules"]
    agents = written["agents"]

    assert cursor_rules.name == "project-rules.mdc"
    assert agents.name == "AGENTS.md"
    assert "alwaysApply: true" in cursor_rules.read_text(encoding="utf-8")
    assert "[ROLE]" in cursor_rules.read_text(encoding="utf-8")
    assert "# AGENTS.md" in agents.read_text(encoding="utf-8")
    assert "[ROLE]" in agents.read_text(encoding="utf-8")


def test_extract_json_payload_accepts_fenced_json(monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL_NAME", "test-model")
    synthesizer = PromptSynthesizer()

    payload = synthesizer._extract_json_payload('```json\n{"PROJECT_OVERVIEW.md":"# Overview"}\n```')

    assert payload == {"PROJECT_OVERVIEW.md": "# Overview"}


def test_generate_onboarding_files_writes_expected_documents(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL_NAME", "test-model")
    synthesizer = PromptSynthesizer()
    monkeypatch.setattr(
        synthesizer,
        "_build_onboarding_docs_map",
        lambda dna_metrics: {
            "PROJECT_OVERVIEW.md": "# Project Overview\n",
            "ARCHITECTURE.md": "# Architecture\n",
            "DATABASE_FLOW.md": "# Database Flow\n",
            "API_MAP.md": "# API Map\n",
            "IMPORTANT_FILES.md": "# Important Files\n",
            "HOW_TO_RUN.md": "# How To Run\n",
            "KNOWN_RISKS.md": "# Known Risks\n",
        },
    )

    written = synthesizer.generate_onboarding_files({}, tmp_path, docs_dir="docs/onboarding")

    assert written["PROJECT_OVERVIEW.md"].name == "PROJECT_OVERVIEW.md"
    assert written["HOW_TO_RUN.md"].read_text(encoding="utf-8") == "# How To Run\n"


def test_build_memory_pack_messages_mentions_current_request_pack(monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL_NAME", "test-model")
    synthesizer = PromptSynthesizer()

    messages = synthesizer._build_memory_pack_messages(
        {
            "feature_modules": [{"name": "auth", "sample_files": ["src/auth/service.py"]}],
            "feature_request_context": {
                "request": "Mujhe auth module modify karna hai",
                "relevant_files": [{"path": "src/auth/service.py"}],
            },
            "runtime_hints": {
                "test_commands": [{"command": "pytest"}],
                "run_commands": [],
            },
        }
    )

    user_prompt = messages[1]["content"]

    assert "FEATURE_PROMPTS.md" in user_prompt
    assert "Current Request Pack" in user_prompt
    assert "matched modules, relevant files, and one exact copy-paste prompt" in user_prompt


def test_generate_memory_pack_files_writes_expected_documents(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL_NAME", "test-model")
    synthesizer = PromptSynthesizer()
    monkeypatch.setattr(
        synthesizer,
        "_build_memory_pack_docs_map",
        lambda dna_metrics: {
            "CLAUDE.md": "# Claude\n",
            "CURSOR_RULES.md": "# Cursor Rules\n",
            "CODING_STYLE.md": "# Coding Style\n",
            "PROJECT_MEMORY.md": "# Project Memory\n",
            "FEATURE_PROMPTS.md": "# Feature Prompts\n",
        },
    )

    written = synthesizer.generate_memory_pack_files({}, tmp_path, pack_dir=".ai-memory")

    assert written["CLAUDE.md"].name == "CLAUDE.md"
    assert written["FEATURE_PROMPTS.md"].read_text(encoding="utf-8") == "# Feature Prompts\n"


def test_build_feature_pack_messages_mentions_backend_frontend_and_migration(monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL_NAME", "test-model")
    synthesizer = PromptSynthesizer()

    messages = synthesizer._build_feature_pack_messages(
        {
            "feature_request_context": {
                "request": "Add payment gateway in this app",
                "relevant_files": [{"path": "src/payments/service.py"}],
                "validation_commands": {"test": [{"command": "pytest"}], "run": []},
            }
        }
    )

    user_prompt = messages[1]["content"]

    assert "RELEVANT_FILES.md" in user_prompt
    assert "BACKEND_PROMPT.md" in user_prompt
    assert "FRONTEND_PROMPT.md" in user_prompt
    assert "TEST_CASES_PROMPT.md" in user_prompt
    assert "MIGRATION_PROMPT.md" in user_prompt
    assert "feature_request_context" in user_prompt


def test_generate_feature_pack_files_writes_expected_documents(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL_NAME", "test-model")
    synthesizer = PromptSynthesizer()
    monkeypatch.setattr(
        synthesizer,
        "_build_feature_pack_docs_map",
        lambda dna_metrics: {
            "RELEVANT_FILES.md": "# Relevant Files\n",
            "API_CONTEXT.md": "# API Context\n",
            "DATABASE_CHANGES.md": "# Database Changes\n",
            "FRONTEND_UPDATES.md": "# Frontend Updates\n",
            "BACKEND_PROMPT.md": "# Backend Prompt\n",
            "FRONTEND_PROMPT.md": "# Frontend Prompt\n",
            "TEST_CASES_PROMPT.md": "# Test Cases Prompt\n",
            "MIGRATION_PROMPT.md": "# Migration Prompt\n",
        },
    )

    written = synthesizer.generate_feature_pack_files({}, tmp_path, pack_dir=".prompt-grapher/features/payment")

    assert written["RELEVANT_FILES.md"].name == "RELEVANT_FILES.md"
    assert written["BACKEND_PROMPT.md"].read_text(encoding="utf-8") == "# Backend Prompt\n"


def test_build_bug_pack_messages_mentions_investigation_and_regression(monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL_NAME", "test-model")
    synthesizer = PromptSynthesizer()

    messages = synthesizer._build_bug_pack_messages(
        {
            "bug_report_context": {
                "request": "Payment status is not updating after UPI success",
                "relevant_files": [{"path": "src/payments/webhook.ts"}],
                "validation_commands": {"test": [{"command": "pytest"}], "run": []},
            }
        }
    )

    user_prompt = messages[1]["content"]

    assert "RELATED_FILES.md" in user_prompt
    assert "INVESTIGATION_PROMPT.md" in user_prompt
    assert "BACKEND_FIX_PROMPT.md" in user_prompt
    assert "REGRESSION_TEST_PROMPT.md" in user_prompt
    assert "bug_report_context" in user_prompt


def test_generate_bug_pack_files_writes_expected_documents(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL_NAME", "test-model")
    synthesizer = PromptSynthesizer()
    monkeypatch.setattr(
        synthesizer,
        "_build_bug_pack_docs_map",
        lambda dna_metrics: {
            "RELATED_FILES.md": "# Related Files\n",
            "API_SUSPECTS.md": "# API Suspects\n",
            "DATABASE_SUSPECTS.md": "# Database Suspects\n",
            "FRONTEND_SUSPECTS.md": "# Frontend Suspects\n",
            "INVESTIGATION_PROMPT.md": "# Investigation Prompt\n",
            "BACKEND_FIX_PROMPT.md": "# Backend Fix Prompt\n",
            "REGRESSION_TEST_PROMPT.md": "# Regression Test Prompt\n",
        },
    )

    written = synthesizer.generate_bug_pack_files({}, tmp_path, pack_dir=".prompt-grapher/bugs/payment-status")

    assert written["RELATED_FILES.md"].name == "RELATED_FILES.md"
    assert written["INVESTIGATION_PROMPT.md"].read_text(encoding="utf-8") == "# Investigation Prompt\n"


def test_build_handoff_pack_messages_mentions_deployment_and_maintenance(monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL_NAME", "test-model")
    synthesizer = PromptSynthesizer()

    messages = synthesizer._build_handoff_pack_messages(
        {
            "deployment_hints": {
                "container_files": [{"path": "Dockerfile", "kind": "container"}],
                "build_commands": [{"command": "npm run build"}],
                "deployment_commands": [{"command": "docker compose up"}],
            },
            "runtime_hints": {
                "run_commands": [{"command": "npm run dev"}],
                "test_commands": [{"command": "npm run test"}],
            },
        }
    )

    user_prompt = messages[1]["content"]

    assert "TECHNICAL_DOCS.md" in user_prompt
    assert "DEPLOYMENT_GUIDE.md" in user_prompt
    assert "AI_MAINTENANCE_PROMPTS.md" in user_prompt
    assert "deployment_hints" in user_prompt
    assert "safe bug investigation" in user_prompt


def test_generate_handoff_pack_files_writes_expected_documents(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL_NAME", "test-model")
    synthesizer = PromptSynthesizer()
    monkeypatch.setattr(
        synthesizer,
        "_build_handoff_pack_docs_map",
        lambda dna_metrics: {
            "TECHNICAL_DOCS.md": "# Technical Docs\n",
            "SETUP_GUIDE.md": "# Setup Guide\n",
            "DEPLOYMENT_GUIDE.md": "# Deployment Guide\n",
            "API_DOCUMENTATION.md": "# API Documentation\n",
            "DATABASE_DOCUMENTATION.md": "# Database Documentation\n",
            "FUTURE_IMPROVEMENTS.md": "# Future Improvements\n",
            "AI_MAINTENANCE_PROMPTS.md": "# AI Maintenance Prompts\n",
        },
    )

    written = synthesizer.generate_handoff_pack_files({}, tmp_path, pack_dir="docs/handoff")

    assert written["TECHNICAL_DOCS.md"].name == "TECHNICAL_DOCS.md"
    assert written["AI_MAINTENANCE_PROMPTS.md"].read_text(encoding="utf-8") == "# AI Maintenance Prompts\n"
