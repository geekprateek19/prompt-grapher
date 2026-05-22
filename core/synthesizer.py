from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


class PromptSynthesizer:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
    ):
        load_dotenv()

        self.base_url = base_url if base_url is not None else os.environ.get("AI_BASE_URL")
        self.api_key = api_key or self._discover_api_key()
        self.model_name = model_name or os.environ.get("AI_MODEL_NAME") or os.environ.get("OPENAI_MODEL")

        if not self.api_key:
            raise ValueError(
                "No API key configured. Set AI_API_KEY or one of OPENAI_API_KEY, GROQ_API_KEY, "
                "or OPENROUTER_API_KEY."
            )
        if not self.model_name:
            raise ValueError("No model configured. Set AI_MODEL_NAME or pass --model.")

        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.client = OpenAI(**client_kwargs)

    def _discover_api_key(self) -> str | None:
        for env_var in ("AI_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY"):
            value = os.environ.get(env_var)
            if value:
                return value
        return None

    def _build_messages(self, dna_metrics: dict) -> list[dict]:
        payload = json.dumps(dna_metrics, indent=2)
        system_prompt = (
            "You generate production-grade .cursorrules files for software repositories. "
            "Infer the existing architecture and conventions from the provided graph summary. "
            "Preserve the repository's current stack and style instead of forcing a different one. "
            "Avoid vague wording. Prefer explicit, enforceable rules that reference detected frameworks, "
            "directories, dependency flows, naming patterns, file placement patterns, and validation tools when available. "
            "Do not name specific tools, frameworks, or libraries unless they are supported by the analysis payload."
        )
        user_prompt = f"""
Generate a repository-specific .cursorrules file using the analysis payload below.

Requirements:
1. Output plain text only. Do not wrap the file in code fences.
2. Tailor every rule to the detected language, framework, architecture, naming, repository shape, dependency flows, and test posture.
3. Do not mention technologies that are not supported by the payload.
4. If the analysis is ambiguous, instruct the coding agent to preserve existing conventions, mirror neighboring files, and avoid speculative rewrites.
5. Do not use vague phrases such as "mixed approach", "compatible framework", "use appropriate tooling", or "follow best practices".
6. In [ARCHITECTURE RULES]:
   - Convert detected architecture type, source roots, module paths, entrypoints, file roles, and dependency flows into explicit boundaries when that evidence exists in the payload.
   - Mention concrete directories, layers, or module names from the payload instead of generic labels whenever possible.
   - If the payload shows layered boundaries such as controllers/services/repositories or pages/components/hooks, preserve those boundaries explicitly.
   - Explicitly forbid broad refactors, folder moves, file renames, architecture migrations, dependency swaps, or global formatting changes unless explicitly requested.
7. In [CODE STYLE]:
   - Explicitly say: follow the naming convention already used in the touched directory, and do not rename files unless required for the requested change.
   - If the payload includes class, function, or file naming patterns, state those naming patterns directly.
   - If the payload shows recurring file role suffixes or prefixes, preserve those local patterns instead of introducing a new naming scheme.
8. In [TESTING AND VALIDATION]:
   - Use the existing test setup already configured in the repository.
   - If the payload mentions test framework hints, prefer the matching configured framework and name only those exact frameworks.
   - Do not introduce a new test runner unless no test setup exists and the task explicitly requires tests.
   - Mirror the detected test file placement and filename style when adding or updating tests.
9. Include a dedicated [BUG FIX PROTOCOL] section with these rules:
   - First reproduce or reason through the reported bug using the smallest relevant code path.
   - Identify the root cause before making changes.
   - When fixing a bug, change the minimum number of lines required.
   - Apply the smallest safe fix in the affected service, component, or utility.
   - Change only the condition that is wrong. Leave correct conditions untouched.
   - Do not rewrite unrelated logic while fixing the bug.
   - If business rules are unclear, ask before editing instead of assuming.
   - Add or update a regression test that fails before the fix and passes after the fix, when practical.
   - Preserve public contracts and user-visible behavior according to [PUBLIC CONTRACT SAFETY] unless the bug itself is caused by an incorrect contract.
   - If the user clarifies business rules mid-task, revert wrong assumptions and apply only the final agreed rules. Do not layer fixes on top of earlier wrong fixes.
   - Validate nearby edge cases related to the bug.
   - In the final response, explain the root cause, files changed, fix summary, and tests run.
10. Add a dedicated [DIFF HYGIENE] section with these rules:
   - The diff must contain only intentional changes.
   - Never leave commented-out old code in the file.
   - Preserve existing indentation, line breaks, and naming in untouched code.
11. Add a dedicated [FILE PLACEMENT] section with these rules:
   - Say where new files belong based on detected source roots, module paths, and co-location patterns from the payload.
   - Prefer placing code beside the feature or layer being changed instead of creating a new top-level folder when an existing location already fits.
   - If the payload is weak, instruct the agent to mirror the nearest neighboring file layout.
12. Add a dedicated [DEPENDENCY HYGIENE] section with these rules:
   - Respect observed dependency flows and layer boundaries from the payload.
   - Keep imports and call direction aligned with neighboring modules instead of reaching across unrelated layers.
   - Do not bypass an existing service, repository, adapter, hook, store, or shared utility boundary without proof from surrounding code.
13. Add a dedicated [PROVE BEFORE EXPANDING] section with these rules:
   - Before adding defensive code such as null checks, try-catch blocks, caching, eager-loading expansions, or similar safeguards, explain why the existing code fails without it.
   - If that failure is not proven, do not add the defensive code.
14. In [PERFORMANCE HYGIENE], state that performance work should happen only when touching performance-sensitive paths or when a measurable bottleneck is identified. Do not add caching, memoization, batching, or lazy loading preemptively.
15. Add a dedicated [PUBLIC CONTRACT SAFETY] section that explicitly forbids changing public APIs, exported names, route paths, request and response shapes, schema contracts, persistence formats, or user-visible UI behavior unless explicitly requested.
16. In [DATA SAFETY], include rules that:
   - Do not expose secrets, tokens, credentials, PII, or sensitive data in logs, errors, analytics, test snapshots, fixtures, or UI output.
   - Validate and sanitize external input.
   - Do not weaken authentication, authorization, encryption, auditability, or permission checks.
17. In [COMMUNICATION STYLE], require the final response to summarize changed files if edits were made; otherwise summarize proposed files and changes. Also summarize behavior impact, architecture impact, and tests or validation run.
18. Include these exact sections:
[ROLE]
[ARCHITECTURE RULES]
[CODE STYLE]
[TESTING AND VALIDATION]
[BUG FIX PROTOCOL]
[DIFF HYGIENE]
[FILE PLACEMENT]
[DEPENDENCY HYGIENE]
[PROVE BEFORE EXPANDING]
[PERFORMANCE HYGIENE]
[PUBLIC CONTRACT SAFETY]
[DATA SAFETY]
[COMMUNICATION STYLE]
19. Keep the rules strict, concise, and enforceable.
20. Focus on change safety: preserve public behavior, avoid unrelated edits, and require targeted validation.

Analysis payload:
{payload}
"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_rules_body(self, dna_metrics: dict) -> str:
        messages = self._build_messages(dna_metrics)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
            )
        except Exception as exc:
            raise RuntimeError(f"AI synthesis failed: {exc}") from exc

        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("AI synthesis returned an empty response.")

        return content.strip()

    def _resolve_output_path(self, output_path: str | Path, filename: str) -> Path:
        output_dir = Path(output_path).resolve()
        target = Path(filename)
        if not target.is_absolute():
            target = output_dir / target
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def _render_cursor_mdc(self, rules_body: str) -> str:
        return (
            "---\n"
            "description: PromptGrapher generated project-wide rules\n"
            "globs:\n"
            "alwaysApply: true\n"
            "---\n\n"
            f"{rules_body}\n"
        )

    def _render_agents_markdown(self, rules_body: str) -> str:
        return (
            "# AGENTS.md\n\n"
            "This file is generated by PromptGrapher and mirrors the project-wide agent rules.\n\n"
            f"{rules_body}\n"
        )

    def generate_rule_files(
        self,
        dna_metrics: dict,
        output_path: str | Path,
        cursor_rules_filename: str = ".cursor/rules/project-rules.mdc",
        agents_filename: str | None = "AGENTS.md",
        legacy_cursorrules_filename: str | None = None,
    ) -> dict[str, Path]:
        rules_body = self._build_rules_body(dna_metrics)
        written_files: dict[str, Path] = {}

        cursor_rules_path = self._resolve_output_path(output_path, cursor_rules_filename)
        cursor_rules_path.write_text(self._render_cursor_mdc(rules_body), encoding="utf-8")
        written_files["cursor_rules"] = cursor_rules_path

        if agents_filename:
            agents_path = self._resolve_output_path(output_path, agents_filename)
            agents_path.write_text(self._render_agents_markdown(rules_body), encoding="utf-8")
            written_files["agents"] = agents_path

        if legacy_cursorrules_filename:
            legacy_path = self._resolve_output_path(output_path, legacy_cursorrules_filename)
            legacy_path.write_text(rules_body + "\n", encoding="utf-8")
            written_files["legacy_cursorrules"] = legacy_path

        return written_files

    def generate_rules(
        self,
        dna_metrics: dict,
        output_path: str | Path,
        output_filename: str = ".cursorrules",
    ) -> Path:
        rules_body = self._build_rules_body(dna_metrics)
        rules_path = self._resolve_output_path(output_path, output_filename)
        rules_path.write_text(rules_body + "\n", encoding="utf-8")
        return rules_path
