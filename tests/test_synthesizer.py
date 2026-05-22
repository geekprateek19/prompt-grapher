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
