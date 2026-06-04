# 2026-05-03 Core Audit: Doc Classification And Helper Inventory

## Purpose

Record the first core audit pass for the migrated PAA platform.
This note answers three questions:

1. Which remaining `appdev` docs are intentionally still in the producer repo?
2. Which helper/runtime surfaces still exist outside `paa-platform`?
3. Does any live PAA runtime capability still exist only outside `paa-platform`?

## Executive Summary

### Overall result
- The migration is **structurally real**.
- The remaining `appdev` docs are **not automatically migration misses**.
- Most of the remaining `appdev` numbered docs are correctly treated as **producer/source-authority** or historical project-architecture material.
- The remaining concern is **classification coverage**, not “move everything into `paa-platform`”.

### Most important runtime conclusion
- No core live PAA runtime capability should currently be treated as existing **only** outside `paa-platform`.
- However, several **legacy copies** and **deprecated helper surfaces** still exist outside `paa-platform`:
  - home-folder deprecated skills/automations
  - legacy `appdev-authority-source*` copies
  - duplicate `appdev/tools/codex-skills/...` copies
  - old issue-specific load SQL
  - old skill-install helper scripts

### Remaining risk
- The main risk is not feature absence.
- The main risk is:
  - stale legacy copies
  - incomplete classification of remaining docs
  - incomplete helper-script retirement plan
  - automation/runtime assumptions that may still reference old surfaces indirectly

## Section 1. Remaining `appdev` Doc Classification

Path under audit:
- `<producer_repo_root>/docs/architecture/tom-baby7-fractal-core/`

### Classification categories
- `producer-source`: belongs in `appdev` as project-specific source, authority, artifact, or operating context
- `platform-runtime`: should live canonically in `paa-platform`
- `historical-archive`: keep as record, but not as canonical current platform guidance
- `needs-split`: contains both platform-generic and project-specific content; should be cross-referenced or split

### Classification results

| Doc(s) | Classification | Reason | Action |
|---|---|---|---|
| `01`-`38` | `producer-source` | These are Tom Baby-7 source, model, portability, host, and project-architecture materials rather than generic PAA platform runtime docs. | Keep in `appdev`; no migration required. |
| `39`-`41` | `producer-source` | These GitHub cycle diagrams are still tightly tied to the Fractal Core producer/consumer workflow context rather than generic platform runtime contracts. | Keep in `appdev`; optionally cross-reference from `paa-platform`. |
| `42-rabbitmq-handoff-system.md` | `needs-split` | The queue/handoff concepts are platform-generic, but the Fractal Core specifics and examples are project-bound. | Keep source doc in `appdev`; add/maintain generic queue runtime docs in `paa-platform`. |
| `43-queue-handoff-automation-template.md` | `platform-runtime` | This is closest to generic automation/runtime behavior and should be represented canonically in `paa-platform` automation/runtime docs. | Cross-reference and/or migrate the generic portion to `paa-platform`; keep any project-specific examples in `appdev`. |
| `44-python-implementation-roadmap.md` | `producer-source` | Roadmap for this specific consumer project and implementation line. | Keep in `appdev`. |
| `46-rewind-boundary-and-recovery-plan.md` | `historical-archive` | Recovery plan for a specific incident/state transition. Useful history, not canonical runtime design. | Keep in `appdev` as historical context. |
| `47-qa-verification-gate.md` | `needs-split` | The QA gate semantics are partly generic platform behavior, partly Fractal Core-specific policy and evidence conventions. | Keep in `appdev`; review whether the generic contract needs a stronger `paa-platform` counterpart. |
| `48-git-and-github-authority-model.md` | `producer-source` | This is a project/governance operating model tied to producer authority and GitHub usage for this project. | Keep in `appdev`; cross-reference where needed. |
| `49-authority-task-authoring-workflow.md` | `producer-source` | Explicit producer-side authoring workflow for project authority. | Keep in `appdev`. |
| `50-authority-issue-materialization.md` | `producer-source` | Producer-side issue/authority materialization workflow for this project. | Keep in `appdev`. |
| `110`-`113` | `producer-source` | These are cleanup, consolidation, and producer artifact inventory notes for the Fractal Core migration itself. | Keep in `appdev`. |
| `artifact-examples/` | `producer-source` | Canonical project-authored artifacts belong with the producer repo. | Keep in `appdev`; publish/install via package flow. |
| `artifact-schemas/` | `needs-split` | Some schema semantics are platform-level, but these are also project-authored artifacts. | Keep source in `appdev`; maintain runtime/package validation schemas in `paa-platform` where needed. |
| `handoff-schemas/` | `needs-split` | Canonical packet schemas now exist in `paa-platform`, but source copies may still remain for project context/history. | Treat `paa-platform` as canonical runtime schema source; keep project copies only if needed for source context. |
| `project-authority/` | `producer-source` | This is the project authority source and must remain in `appdev`. | Keep in `appdev`. |

## Section 2. Coverage Conclusion For Docs

### What is already covered in `paa-platform`
The key platform-runtime doc families are already present in `paa-platform`, including:
- staged lifecycle
- coder brief derivation and sequencing
- stage1 package/dependency contracts
- readiness materialization
- architect/dev/qa packet compilers
- packet persistence and transport traceability
- TechLead reporting
- platform extraction and install contracts

### What is not yet complete
We should not yet claim “all PAA docs are fully covered” because:
- some `needs-split` documents in `appdev` still need explicit cross-reference or generic extraction
- there is no completed classification ledger for every numbered doc yet outside this audit pass
- the lifecycle-folder documentation strategy is still not formalized

## Section 3. Helper And Runtime Surface Inventory

### Canonical runtime ownership in `paa-platform`
Current canonical runtime modules live in:
- `packages/paa-core/src/paa_core/`
- `packages/paa-core/src/paa_producer/`
- `packages/paa-consumer/src/paa_consumer/`

### Legacy / duplicate / deprecated runtime surfaces

| Capability | Canonical in `paa-platform` | Duplicate or deprecated copies outside platform | Status |
|---|---|---|---|
| Authority runtime / packet compilation | `packages/paa-core/src/paa_producer/authority_runtime.py` | `<producer_repo_root>/tools/codex-skills/fractal-core-authority/scripts/project_authority.py`, `<producer_repo_root>-authority-source/tools/.../project_authority.py`, `<producer_repo_root>-authority-source-clean/tools/.../project_authority.py`, `<codex_home>/skills/fractal-core-authority/scripts/project_authority.py` | Canonicalized in platform; legacy copies remain |
| Authority publication | `packages/paa-core/src/paa_producer/publish.py` | `<producer_repo_root>/tools/codex-skills/fractal-core-authority/scripts/publish_current.py`, legacy source/source-clean copies, home `.codex` copy | Canonicalized in platform; legacy copies remain |
| Readiness materialization | `packages/paa-core/src/paa_core/readiness.py` | `materialize_coder_brief_readiness.py` exists only in legacy source/source-clean and home `.codex` copies | Canonicalized in platform; canonical producer repo no longer owns the old script |
| Queue / handoff runtime | `packages/paa-core/src/paa_core/handoff_runtime.py`, `packages/paa-consumer/src/paa_consumer/inbox.py`, `packages/paa-consumer/src/paa_consumer/delivery_runtime.py` | `<producer_repo_root>/tools/codex-skills/fractal-core-handoff/.../rabbitmq_handoff.py`, legacy source/source-clean copies, home `.codex` copy | Canonicalized in platform; legacy copies remain |
| TechLead reporting | `packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`, `packages/paa-core/src/paa_core/traceability.py` | `<codex_home>/skills/fractal-core-techlead/scripts/techlead_status.py` | Canonicalized in platform; old script still exists only as deprecated legacy copy |
| Generic issue loading | `packages/paa-core/src/paa_producer/issue_loader.py` | issue-specific load SQL in legacy docs | Canonicalized in platform; SQL remains historical |
| Verification obligation loading | `packages/paa-core/src/paa_producer/obligation_loader.py` | issue-specific obligation inserts in legacy SQL | Canonicalized in platform; SQL remains historical |
| Repo-local install/update | `packages/paa-core/src/paa_core/install.py`, producer/consumer CLI entrypoints | `<producer_repo_root>/tools/codex-skills/install_fractal_core_skills.py`, `<producer_repo_root>/tools/codex-skills/fractal-core-handoff/install_to_codex_skills.py`, legacy source/source-clean copies | Canonical platform install exists; old install helpers are still outside platform and should be treated as deprecated migration helpers |

## Section 4. Does Any Live Runtime Capability Exist Only Outside `paa-platform`?

### Answer
For the known Fractal Core PAA system, **no core runtime capability should currently be treated as live only outside `paa-platform`**.

### What still exists outside platform
The following still exist outside `paa-platform`, but should be treated as non-canonical:
- duplicate producer-side tool copies in `appdev/tools/codex-skills/...`
- legacy duplicate tool copies in `appdev-authority-source` and `appdev-authority-source-clean`
- deprecated home-folder skills/automations under `<codex_home>/`
- old issue-specific load SQL in legacy doc folders
- old skill-install helper scripts in `appdev/tools/codex-skills/`

### Important nuance
There is one category that is still only outside `paa-platform` as a **legacy artifact surface**, not as canonical runtime ownership:
- deprecated legacy installer/helper scripts such as:
  - `install_fractal_core_skills.py`
  - `install_to_codex_skills.py`
- These are not the intended current runtime path, but they have not yet been fully inventoried/replaced/retired in documentation.

So the correct statement is:
- core runtime ownership is in `paa-platform`
- but not every old helper surface has been formally retired yet

## Section 5. Open Gaps Exposed By This Audit

1. We still need a **full doc coverage ledger** for all numbered docs, not just the most obviously PAA-related ones.
2. We still need a **helper-script inventory** that goes beyond the runtime-critical scripts listed here.
3. We still need an explicit **retirement/deprecation plan** for:
   - `appdev/tools/codex-skills/...`
   - `appdev-authority-source*`
   - `<codex_home>/fractal-core-*`
4. We still need a **prompt/automation audit** to ensure no repo-local automation silently depends on those old surfaces.
5. We still need an explicit **environment/bootstrap strategy** so wrapper/runtime behavior is predictable across sessions and automations.

## Recommended Next Core-Audit Actions

1. Build the helper-script inventory as a dedicated table-based note.
2. Audit repo-local automations against the legacy helper/runtime paths identified here.
3. Add an `AGENTS.md` to the producer repo clarifying Authority Architect ownership.
4. Design the worktree/workspace model.
5. Define the shared `uv` runtime/bootstrap strategy.
