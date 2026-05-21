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
    assert "explicitly forbid broad refactors, folder moves, file renames, architecture migrations, dependency swaps, or global formatting changes" in user_prompt
    assert "follow the naming convention already used in the touched directory" in user_prompt
    assert "Use the existing test setup already configured in the repository" in user_prompt
    assert "prefer the matching configured framework and name only those exact frameworks" in user_prompt
    assert "Do not introduce a new test runner unless no test setup exists" in user_prompt
    assert "[BUG FIX PROTOCOL]" in user_prompt
    assert "Identify the root cause before making changes" in user_prompt
    assert "Apply the smallest safe fix in the affected service, component, or utility" in user_prompt
    assert "Add or update a regression test that fails before the fix and passes after the fix" in user_prompt
    assert "Do not add caching, memoization, batching, or lazy loading preemptively" in user_prompt
    assert "[PUBLIC CONTRACT SAFETY]" in user_prompt
    assert "explicitly forbids changing public APIs, exported names, route paths, request and response shapes" in user_prompt
    assert "Do not expose secrets, tokens, credentials, PII, or sensitive data" in user_prompt
    assert "Do not weaken authentication, authorization, encryption, auditability, or permission checks" in user_prompt
    assert "summarize changed files if edits were made; otherwise summarize proposed files and changes" in user_prompt


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
