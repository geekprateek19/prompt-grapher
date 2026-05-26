from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ONBOARDING_DOC_FILENAMES = (
    "PROJECT_OVERVIEW.md",
    "ARCHITECTURE.md",
    "DATABASE_FLOW.md",
    "API_MAP.md",
    "IMPORTANT_FILES.md",
    "HOW_TO_RUN.md",
    "KNOWN_RISKS.md",
)

MEMORY_PACK_FILENAMES = (
    "CLAUDE.md",
    "CURSOR_RULES.md",
    "CODING_STYLE.md",
    "PROJECT_MEMORY.md",
    "FEATURE_PROMPTS.md",
)

FEATURE_PACK_FILENAMES = (
    "RELEVANT_FILES.md",
    "API_CONTEXT.md",
    "DATABASE_CHANGES.md",
    "FRONTEND_UPDATES.md",
    "BACKEND_PROMPT.md",
    "FRONTEND_PROMPT.md",
    "TEST_CASES_PROMPT.md",
    "MIGRATION_PROMPT.md",
)

BUG_PACK_FILENAMES = (
    "RELATED_FILES.md",
    "API_SUSPECTS.md",
    "DATABASE_SUSPECTS.md",
    "FRONTEND_SUSPECTS.md",
    "INVESTIGATION_PROMPT.md",
    "BACKEND_FIX_PROMPT.md",
    "REGRESSION_TEST_PROMPT.md",
)

HANDOFF_PACK_FILENAMES = (
    "TECHNICAL_DOCS.md",
    "SETUP_GUIDE.md",
    "DEPLOYMENT_GUIDE.md",
    "API_DOCUMENTATION.md",
    "DATABASE_DOCUMENTATION.md",
    "FUTURE_IMPROVEMENTS.md",
    "AI_MAINTENANCE_PROMPTS.md",
)


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
   - explicitly forbid broad refactors, folder moves, file renames, architecture migrations, dependency swaps, or global formatting changes unless explicitly requested.
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

    def _build_onboarding_messages(self, dna_metrics: dict) -> list[dict]:
        payload = json.dumps(dna_metrics, indent=2)
        required_files = ", ".join(ONBOARDING_DOC_FILENAMES)
        system_prompt = (
            "You generate repository onboarding documentation for software teams. "
            "Use only the provided repository analysis payload. "
            "Do not invent commands, frameworks, files, endpoints, tables, or flows that are not supported by the payload. "
            "When evidence is missing, say so plainly instead of guessing."
        )
        user_prompt = f"""
Generate a JSON object where each key is one of these exact filenames and each value is the full markdown content for that file:
{required_files}

Requirements:
1. Output valid JSON only. Do not wrap the response in markdown fences.
2. Each file must be repository-specific, concise, and immediately useful for a new developer joining the project.
3. Use exact directories, files, entrypoints, package scripts, runtime hints, dependency flows, and hotspot paths from the payload when they exist.
4. If the payload lacks evidence for a database layer or API surface, state that clearly in the relevant file instead of inventing one.
5. `PROJECT_OVERVIEW.md` must summarize the stack, architecture style, entrypoints, test posture, and key directories.
6. `ARCHITECTURE.md` must explain the detected architecture, source roots, dominant file roles, dependency flows, and hotspots.
7. `DATABASE_FLOW.md` must map schema, migration, model, repository, or db-related files and explain what is or is not evident.
8. `API_MAP.md` must map route, controller, handler, view, or api-related files and explain request flow using only supported evidence.
9. `IMPORTANT_FILES.md` must list important files with a short reason for each.
10. `HOW_TO_RUN.md` must include install, run, and test commands from `runtime_hints`; clearly label inferred commands when confidence is `inferred`.
11. `KNOWN_RISKS.md` must summarize hotspots, missing tests, architectural ambiguity, or operational gaps using the payload's `risk_flags` and other evidence.
12. Prefer headings, short sections, and tables or bullets where they improve scanability.
13. Keep the tone factual and practical. Avoid generic process advice.

Analysis payload:
{payload}
"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_memory_pack_messages(self, dna_metrics: dict) -> list[dict]:
        payload = json.dumps(dna_metrics, indent=2)
        required_files = ", ".join(MEMORY_PACK_FILENAMES)
        system_prompt = (
            "You generate repository memory-pack documentation for AI coding assistants. "
            "Use only the provided repository analysis payload. "
            "Do not invent files, commands, frameworks, endpoints, or architectural rules that are not supported by the payload. "
            "When evidence is missing, say so explicitly."
        )
        user_prompt = f"""
Generate a JSON object where each key is one of these exact filenames and each value is the full markdown content for that file:
{required_files}

Requirements:
1. Output valid JSON only. Do not wrap the response in markdown fences.
2. The memory pack must be repository-specific and optimized for coding assistants that need fast working context.
3. Use exact directories, files, entrypoints, runtime commands, dependency flows, hotspots, and feature modules from the payload where available.
4. Keep the content practical and terse. Avoid generic best-practice filler.
5. `CLAUDE.md` must work as a session bootstrap for Claude Code:
   - summarize stack, architecture boundaries, key commands, risky areas, and rules for safe edits.
6. `CURSOR_RULES.md` must be a concise markdown memory file for Cursor chat context:
   - include architecture, naming, validation, file placement, dependency hygiene, and change-safety rules.
7. `CODING_STYLE.md` must capture naming patterns, file-role conventions, test placement, dependency boundaries, and diff hygiene.
8. `PROJECT_MEMORY.md` must summarize the project map:
   - stack, entrypoints, source roots, test roots, API surface, database surface, important files, hotspots, and known risks.
9. `FEATURE_PROMPTS.md` must include:
   - reusable prompt templates for bug fixes, feature updates, refactors, and test additions.
   - a section for inferred feature modules from `feature_modules`, each with sample files and a module-specific prompt starter.
   - if `feature_request_context` exists in the payload, add a `Current Request Pack` section with the request text, matched modules, relevant files, and one exact copy-paste prompt for an AI coding assistant.
10. The exact prompt in `FEATURE_PROMPTS.md` must:
   - name the relevant files from `feature_request_context.relevant_files`.
   - instruct the assistant to inspect those files first.
   - preserve current architecture and naming.
   - call out the most relevant validation command if one exists in `runtime_hints.test_commands` or `runtime_hints.run_commands`.
11. If no feature modules are evident, say that explicitly in `FEATURE_PROMPTS.md` instead of inventing module names.
12. If the payload lacks direct evidence for API or database layers, say so plainly in `PROJECT_MEMORY.md`.

Analysis payload:
{payload}
"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_feature_pack_messages(self, dna_metrics: dict) -> list[dict]:
        payload = json.dumps(dna_metrics, indent=2)
        required_files = ", ".join(FEATURE_PACK_FILENAMES)
        system_prompt = (
            "You generate feature implementation prompt packs for software repositories. "
            "Use only the provided repository analysis payload. "
            "Do not invent files, endpoints, tables, screens, commands, or layers that are not supported by the payload. "
            "When the evidence is weak, say that directly and keep the prompt scoped to what is known."
        )
        user_prompt = f"""
Generate a JSON object where each key is one of these exact filenames and each value is the full markdown content for that file:
{required_files}

Requirements:
1. Output valid JSON only. Do not wrap the response in markdown fences.
2. The payload must include `feature_request_context`. Use that request as the active implementation task.
3. Keep the pack concrete and execution-oriented. Avoid generic product or engineering advice.
4. `RELEVANT_FILES.md` must list:
   - the most relevant files likely to be touched
   - why each file matters
   - whether each file is frontend, backend, test, or shared when that evidence exists
5. `API_CONTEXT.md` must summarize:
   - existing API-related files already present
   - likely request flow or service boundaries for the feature
   - clear gaps if no API surface is evident
6. `DATABASE_CHANGES.md` must summarize:
   - existing db, schema, repository, or migration-related files
   - what database changes might be required for the feature request
   - whether migrations or persistence changes are likely, uncertain, or not evident
7. `FRONTEND_UPDATES.md` must summarize:
   - frontend files and screen candidates that may need updates
   - what user-visible flows or screens are likely impacted
   - if no frontend surface is evident, say so clearly
8. `BACKEND_PROMPT.md` must provide one copy-paste implementation prompt for a coding assistant focused on backend changes only.
9. `FRONTEND_PROMPT.md` must provide one copy-paste implementation prompt for a coding assistant focused on frontend changes only.
10. `TEST_CASES_PROMPT.md` must provide one copy-paste prompt for generating or updating tests for this feature.
11. `MIGRATION_PROMPT.md` must provide one copy-paste prompt for schema, migration, seed, or rollout-related work if database changes seem relevant; otherwise say that no clear migration surface was detected and provide a narrow verification prompt instead.
12. Every prompt file must:
   - explicitly name the relevant files from `feature_request_context`
   - preserve current architecture and naming conventions
   - avoid unrelated refactors
   - use the most relevant validation command from `feature_request_context.validation_commands` or `runtime_hints`
13. If there is no clear backend or frontend evidence, keep the corresponding prompt conservative and say what the assistant should inspect first to confirm scope.
14. If the payload indicates API or database uncertainty, call that out as an assumption-check step before editing.

Analysis payload:
{payload}
"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_bug_pack_messages(self, dna_metrics: dict) -> list[dict]:
        payload = json.dumps(dna_metrics, indent=2)
        required_files = ", ".join(BUG_PACK_FILENAMES)
        system_prompt = (
            "You generate bug-fix context packs for software repositories. "
            "Use only the provided repository analysis payload. "
            "Do not invent files, endpoints, tables, screens, workflows, or commands that are not supported by the payload. "
            "When the evidence is incomplete, say so and keep the investigation prompt conservative."
        )
        user_prompt = f"""
Generate a JSON object where each key is one of these exact filenames and each value is the full markdown content for that file:
{required_files}

Requirements:
1. Output valid JSON only. Do not wrap the response in markdown fences.
2. The payload must include `bug_report_context`. Use that report as the active bug to investigate.
3. Keep the pack practical and debugging-focused. Avoid generic QA or engineering advice.
4. `RELATED_FILES.md` must list the most relevant files likely connected to the bug:
   - include why each file is suspected
   - label files as backend, frontend, test, or shared when that evidence exists
5. `API_SUSPECTS.md` must summarize API, webhook, controller, route, or handler files that could influence the bug and explain the likely call flow.
6. `DATABASE_SUSPECTS.md` must summarize schema, repository, db, migration, or persistence files that may affect the bug and explain whether data writes or state transitions seem relevant.
7. `FRONTEND_SUSPECTS.md` must summarize affected frontend screens or UI files and explain what user-visible state might fail to update.
8. `INVESTIGATION_PROMPT.md` must provide one copy-paste investigation prompt for an AI coding assistant that:
   - explicitly names the relevant files from `bug_report_context.relevant_files`
   - asks the assistant to inspect those files first
   - asks for root-cause analysis before code changes
   - preserves architecture and avoids unrelated refactors
9. `BACKEND_FIX_PROMPT.md` must provide one copy-paste backend bug-fix prompt that:
   - focuses on the minimum safe fix
   - calls out API or database suspects when relevant
   - preserves existing contracts unless the bug requires correcting a broken contract
10. `REGRESSION_TEST_PROMPT.md` must provide one copy-paste prompt for creating or updating regression coverage for this bug.
11. Every prompt file must mention the best available validation command from `bug_report_context.validation_commands` or `runtime_hints`.
12. If there is weak evidence for API, database, or frontend involvement, say so clearly in the relevant file and make the prompt verify scope before editing.

Analysis payload:
{payload}
"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_handoff_pack_messages(self, dna_metrics: dict) -> list[dict]:
        payload = json.dumps(dna_metrics, indent=2)
        required_files = ", ".join(HANDOFF_PACK_FILENAMES)
        system_prompt = (
            "You generate client handoff documentation packs for software repositories. "
            "Use only the provided repository analysis payload. "
            "Do not invent commands, environments, endpoints, database tables, deployment platforms, or operational steps "
            "that are not supported by the payload. When evidence is weak or missing, say that plainly."
        )
        user_prompt = f"""
Generate a JSON object where each key is one of these exact filenames and each value is the full markdown content for that file:
{required_files}

Requirements:
1. Output valid JSON only. Do not wrap the response in markdown fences.
2. The pack must be repository-specific and suitable for a freelancer or agency handing the project to a client or the next maintenance team.
3. Use exact files, commands, entrypoints, dependency flows, runtime hints, deployment hints, hotspots, and risk flags from the payload whenever possible.
4. Keep every file practical and scan-friendly. Avoid generic software-process advice.
5. `TECHNICAL_DOCS.md` must summarize:
   - stack, architecture style, key directories, entrypoints, dependency flows, important files, and structural hotspots
6. `SETUP_GUIDE.md` must summarize:
   - install, local run, test, and environment setup instructions from `runtime_hints`
   - clearly label inferred commands when the payload marks them as inferred
7. `DEPLOYMENT_GUIDE.md` must summarize:
   - container, CI/CD, hosting, infrastructure, and environment files from `deployment_hints`
   - build and deployment commands when present
   - any missing deployment evidence that a client should confirm before production rollout
8. `API_DOCUMENTATION.md` must summarize:
   - existing routes, controllers, handlers, views, and likely request flow from `api_surface` and dependency signals
   - clear uncertainty when the API surface is weak
9. `DATABASE_DOCUMENTATION.md` must summarize:
   - schema, model, repository, migration, seed, and database-related files from `database_surface`
   - likely persistence flow and migration touchpoints
   - clear uncertainty when the database surface is weak
10. `FUTURE_IMPROVEMENTS.md` must prioritize the most credible next improvements using `risk_flags`, hotspots, missing tests, setup ambiguity, deployment gaps, or architecture ambiguity from the payload.
11. `AI_MAINTENANCE_PROMPTS.md` must include copy-paste prompts for:
   - safe bug investigation
   - safe feature enhancement
   - regression test addition
   - dependency upgrade review
   - deployment issue investigation
   Each prompt must name the most relevant files or commands from the payload when available and instruct the assistant to preserve existing architecture and avoid unrelated refactors.
12. If API, database, or deployment evidence is missing, say that directly instead of guessing.
13. The tone must be factual and operational, suitable for a real client handoff packet.

Analysis payload:
{payload}
"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _request_completion(self, messages: list[dict], temperature: float = 0.2) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
            )
        except Exception as exc:
            raise RuntimeError(f"AI synthesis failed: {exc}") from exc

        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("AI synthesis returned an empty response.")

        return content.strip()

    def _build_rules_body(self, dna_metrics: dict) -> str:
        messages = self._build_messages(dna_metrics)
        return self._request_completion(messages, temperature=0.2)

    def _extract_json_payload(self, content: str) -> dict:
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        if not text.startswith("{"):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start : end + 1]

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"AI JSON response was not valid JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise RuntimeError("AI JSON response must be a JSON object.")

        return data

    def _build_json_docs_map(
        self,
        messages: list[dict],
        filenames: tuple[str, ...],
        response_label: str,
    ) -> dict[str, str]:
        raw_content = self._request_completion(messages, temperature=0.2)
        payload = self._extract_json_payload(raw_content)

        docs_map: dict[str, str] = {}
        missing_files = []
        for filename in filenames:
            content = payload.get(filename)
            if not isinstance(content, str) or not content.strip():
                missing_files.append(filename)
                continue
            docs_map[filename] = content.strip() + "\n"

        if missing_files:
            missing = ", ".join(missing_files)
            raise RuntimeError(f"{response_label} omitted required files: {missing}")

        return docs_map

    def _build_onboarding_docs_map(self, dna_metrics: dict) -> dict[str, str]:
        messages = self._build_onboarding_messages(dna_metrics)
        return self._build_json_docs_map(messages, ONBOARDING_DOC_FILENAMES, "AI onboarding docs response")

    def _build_memory_pack_docs_map(self, dna_metrics: dict) -> dict[str, str]:
        messages = self._build_memory_pack_messages(dna_metrics)
        return self._build_json_docs_map(messages, MEMORY_PACK_FILENAMES, "AI memory pack response")

    def _build_feature_pack_docs_map(self, dna_metrics: dict) -> dict[str, str]:
        messages = self._build_feature_pack_messages(dna_metrics)
        return self._build_json_docs_map(messages, FEATURE_PACK_FILENAMES, "AI feature pack response")

    def _build_bug_pack_docs_map(self, dna_metrics: dict) -> dict[str, str]:
        messages = self._build_bug_pack_messages(dna_metrics)
        return self._build_json_docs_map(messages, BUG_PACK_FILENAMES, "AI bug pack response")

    def _build_handoff_pack_docs_map(self, dna_metrics: dict) -> dict[str, str]:
        messages = self._build_handoff_pack_messages(dna_metrics)
        return self._build_json_docs_map(messages, HANDOFF_PACK_FILENAMES, "AI handoff pack response")

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

    def generate_onboarding_files(
        self,
        dna_metrics: dict,
        output_path: str | Path,
        docs_dir: str = "docs/onboarding",
    ) -> dict[str, Path]:
        docs_map = self._build_onboarding_docs_map(dna_metrics)
        written_files: dict[str, Path] = {}

        for filename, body in docs_map.items():
            relative_target = str(Path(docs_dir) / filename)
            target_path = self._resolve_output_path(output_path, relative_target)
            target_path.write_text(body, encoding="utf-8")
            written_files[filename] = target_path

        return written_files

    def generate_memory_pack_files(
        self,
        dna_metrics: dict,
        output_path: str | Path,
        pack_dir: str = ".ai-memory",
    ) -> dict[str, Path]:
        docs_map = self._build_memory_pack_docs_map(dna_metrics)
        written_files: dict[str, Path] = {}

        for filename, body in docs_map.items():
            relative_target = str(Path(pack_dir) / filename)
            target_path = self._resolve_output_path(output_path, relative_target)
            target_path.write_text(body, encoding="utf-8")
            written_files[filename] = target_path

        return written_files

    def generate_feature_pack_files(
        self,
        dna_metrics: dict,
        output_path: str | Path,
        pack_dir: str = ".prompt-grapher/features",
    ) -> dict[str, Path]:
        docs_map = self._build_feature_pack_docs_map(dna_metrics)
        written_files: dict[str, Path] = {}

        for filename, body in docs_map.items():
            relative_target = str(Path(pack_dir) / filename)
            target_path = self._resolve_output_path(output_path, relative_target)
            target_path.write_text(body, encoding="utf-8")
            written_files[filename] = target_path

        return written_files

    def generate_bug_pack_files(
        self,
        dna_metrics: dict,
        output_path: str | Path,
        pack_dir: str = ".prompt-grapher/bugs",
    ) -> dict[str, Path]:
        docs_map = self._build_bug_pack_docs_map(dna_metrics)
        written_files: dict[str, Path] = {}

        for filename, body in docs_map.items():
            relative_target = str(Path(pack_dir) / filename)
            target_path = self._resolve_output_path(output_path, relative_target)
            target_path.write_text(body, encoding="utf-8")
            written_files[filename] = target_path

        return written_files

    def generate_handoff_pack_files(
        self,
        dna_metrics: dict,
        output_path: str | Path,
        pack_dir: str = "docs/handoff",
    ) -> dict[str, Path]:
        docs_map = self._build_handoff_pack_docs_map(dna_metrics)
        written_files: dict[str, Path] = {}

        for filename, body in docs_map.items():
            relative_target = str(Path(pack_dir) / filename)
            target_path = self._resolve_output_path(output_path, relative_target)
            target_path.write_text(body, encoding="utf-8")
            written_files[filename] = target_path

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
