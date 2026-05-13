# PAA Helper Script Inventory and Retirement Table

## Purpose
This note closes the second core-audit slice:
- inventory helper scripts and duplicate runtime surfaces
- make retirement status explicit
- prevent future sessions from silently re-adopting legacy paths just because they still exist on disk

This document is intentionally stronger than "non-canonical" language.
Every legacy helper or duplicate runtime surface should have one of these statuses:
- `canonical`
- `duplicate-retire`
- `deprecated-paused`
- `historical-archive`
- `needs-follow-up`

## Interpretation Rules
- `canonical`: active supported implementation surface
- `duplicate-retire`: duplicate of a canonical implementation; should not be used operationally and should be retired/removed after dependent references are cleaned up
- `deprecated-paused`: intentionally left in place only to block accidental reuse and communicate deprecation
- `historical-archive`: retained for historical reference only; not part of supported flow
- `needs-follow-up`: still requires a migration/retirement decision or a reference cleanup pass

## Canonical Platform Runtime Surfaces

| Status | Current Path | Purpose | Canonical Owner | Action |
|---|---|---|---|---|
| canonical | `packages/paa-core/src/paa_core/db.py` | DB config and query/persistence adapter | `paa-platform` | keep |
| canonical | `packages/paa-core/src/paa_core/readiness.py` | coder-brief readiness materialization logic | `paa-platform` | keep |
| canonical | `packages/paa-core/src/paa_core/handoff_runtime.py` | queue/handoff runtime | `paa-platform` | keep |
| canonical | `packages/paa-core/src/paa_core/traceability.py` | traceability/report query helpers | `paa-platform` | keep |
| canonical | `packages/paa-core/src/paa_core/runtime_guardrails.py` | stale-topology/runtime guardrails | `paa-platform` | keep |
| canonical | `packages/paa-core/src/paa_core/install.py` | repo-local producer/consumer install/update | `paa-platform` | keep |
| canonical | `packages/paa-producer/src/paa_producer/authority_runtime.py` | producer authority runtime commands | `paa-platform` | keep |
| canonical | `packages/paa-producer/src/paa_producer/publish.py` | authority package publish flow | `paa-platform` | keep |
| canonical | `packages/paa-producer/src/paa_producer/obligation_loader.py` | generic verification obligation loader | `paa-platform` | keep |
| canonical | `packages/paa-producer/src/paa_producer/issue_loader.py` | generic source-to-PAA issue loader | `paa-platform` | keep |
| canonical | `packages/paa-consumer/src/paa_consumer/authority_install.py` | authority package install/update | `paa-platform` | keep |
| canonical | `packages/paa-consumer/src/paa_consumer/inbox.py` | consumer queue operations | `paa-platform` | keep |
| canonical | `packages/paa-consumer/src/paa_consumer/delivery_runtime.py` | consumer delivery/handoff runtime | `paa-platform` | keep |
| canonical | `packages/paa-consumer/src/paa_consumer/techlead.py` | TechLead runtime/report behavior | `paa-platform` | keep |

## Producer-Repo Duplicate Tool Surfaces
These paths remain in the canonical producer repo, but they are no longer the supported runtime implementation source.

| Status | Current Path | Legacy Purpose | Canonical Replacement | Action |
|---|---|---|---|---|
| duplicate-retire | `<producer_repo_root>/tools/codex-skills/fractal-core-authority/scripts/project_authority.py` | old authority runtime entrypoint | `paa_producer.authority_runtime` | retire after reference cleanup |
| duplicate-retire | `<producer_repo_root>/tools/codex-skills/fractal-core-authority/scripts/publish_current.py` | old authority publication helper | `paa_producer.publish` | retire after reference cleanup |
| duplicate-retire | `<producer_repo_root>/tools/codex-skills/fractal-core-handoff/fractal-core-handoff-common/scripts/rabbitmq_handoff.py` | old queue/handoff runtime helper | `paa_core.handoff_runtime` and `paa_consumer.inbox` | retire after reference cleanup |
| needs-follow-up | `<producer_repo_root>/tools/codex-skills/install_fractal_core_skills.py` | legacy install-to-home/repo helper | `paa_core.install` | audit references, then retire |
| needs-follow-up | `<producer_repo_root>/tools/codex-skills/fractal-core-handoff/install_to_codex_skills.py` | legacy handoff skill installer | `paa_core.install` | audit references, then retire |
| duplicate-retire | `<producer_repo_root>/tools/codex-skills/fractal-core-authority/SKILL.md` | old producer skill surface | repo-local installed skill from project pack | retire after automation prompt audit |
| duplicate-retire | `<producer_repo_root>/tools/codex-skills/fractal-core-handoff/fractal-core-architect-handoff/SKILL.md` | old architect handoff skill surface | repo-local installed skill from project pack | retire after automation prompt audit |
| duplicate-retire | `<producer_repo_root>/tools/codex-skills/fractal-core-handoff/fractal-core-handoff-common/SKILL.md` | old shared handoff skill surface | repo-local installed skill from project pack | retire after automation prompt audit |

## Transitional Authority-Source Runtime Duplicates
These are not supported operational surfaces anymore. They are retained only as migration history unless explicitly referenced during audits.

| Status | Current Path | Legacy Purpose | Canonical Replacement | Action |
|---|---|---|---|---|
| historical-archive | `<producer_repo_root>-authority-source/tools/codex-skills/fractal-core-authority/scripts/project_authority.py` | old producer authority runtime | `paa_producer.authority_runtime` | archive only |
| historical-archive | `<producer_repo_root>-authority-source/tools/codex-skills/fractal-core-authority/scripts/publish_current.py` | old publication helper | `paa_producer.publish` | archive only |
| historical-archive | `<producer_repo_root>-authority-source/tools/codex-skills/fractal-core-authority/scripts/materialize_coder_brief_readiness.py` | old readiness materializer | `paa_core.readiness` | archive only |
| historical-archive | `<producer_repo_root>-authority-source/tools/codex-skills/fractal-core-handoff/fractal-core-handoff-common/scripts/rabbitmq_handoff.py` | old queue/handoff runtime | `paa_core.handoff_runtime` | archive only |
| historical-archive | `<producer_repo_root>-authority-source-clean/tools/codex-skills/fractal-core-authority/scripts/project_authority.py` | recovery-lane authority runtime | `paa_producer.authority_runtime` | archive only |
| historical-archive | `<producer_repo_root>-authority-source-clean/tools/codex-skills/fractal-core-authority/scripts/publish_current.py` | recovery-lane publication helper | `paa_producer.publish` | archive only |
| historical-archive | `<producer_repo_root>-authority-source-clean/tools/codex-skills/fractal-core-authority/scripts/materialize_coder_brief_readiness.py` | recovery-lane readiness materializer | `paa_core.readiness` | archive only |
| historical-archive | `<producer_repo_root>-authority-source-clean/tools/codex-skills/fractal-core-handoff/fractal-core-handoff-common/scripts/rabbitmq_handoff.py` | recovery-lane handoff runtime | `paa_core.handoff_runtime` | archive only |

## Deprecated Home-Folder Runtime Surfaces
These are the most dangerous confusion surfaces because they look operational and were historically active. They must remain clearly deprecated until fully removed.

| Status | Current Path | Legacy Purpose | Canonical Replacement | Action |
|---|---|---|---|---|
| deprecated-paused | `<codex_home>/skills/fractal-core-authority/` | old home-folder producer runtime/skill | repo-local installed skill and `.codex/paa/bin/paa-producer` | keep paused until final removal |
| deprecated-paused | `<codex_home>/skills/fractal-core-techlead/` | old home-folder TechLead runtime | repo-local installed skill and `.codex/paa/bin/paa-consumer techlead-status` | keep paused until final removal |
| deprecated-paused | `<codex_home>/skills/fractal-core-handoff-common/` | old shared handoff runtime | repo-local installed runtime from `paa-platform` | keep paused until final removal |
| deprecated-paused | `<codex_home>/skills/fractal-core-inbox/` | old consumer inbox skill | repo-local installed skill from project pack | keep paused until final removal |
| deprecated-paused | `<codex_home>/skills/fractal-core-queue-admin/` | old queue admin skill | repo-local installed skill from project pack | keep paused until final removal |
| deprecated-paused | `<codex_home>/skills/fractal-core-dev-result/` | old dev result skill | repo-local installed skill from project pack | keep paused until final removal |
| deprecated-paused | `<codex_home>/skills/fractal-core-qa-review/` | old QA review skill | repo-local installed skill from project pack | keep paused until final removal |
| deprecated-paused | `<codex_home>/skills/fractal-core-architect-handoff/` | old architect handoff skill | repo-local installed skill from project pack | keep paused until final removal |
| deprecated-paused | `<codex_home>/automations/fractal-core-architect-automation/automation.toml` | old home-folder architect automation | repo-local project-pack automation | keep paused until final removal |
| deprecated-paused | `<codex_home>/automations/fractal-core-architect-automation-2/automation.toml` | old alternate architect automation | repo-local project-pack automation | keep paused until final removal |
| deprecated-paused | `<codex_home>/automations/fractal-core-qa-automation-2/automation.toml` | old QA automation | repo-local project-pack automation | keep paused until final removal |
| deprecated-paused | `<codex_home>/automations/fractal-core-techlead-automation/automation.toml` | old TechLead automation | repo-local project-pack automation | keep paused until final removal |
| deprecated-paused | `<codex_home>/automations/python-team-automation/automation.toml` | old team automation surface | repo-local project-pack automation | keep paused until final removal |
| deprecated-paused | `<codex_home>/README-paa-runtime-deprecated.md` | deprecation marker | n/a | keep until final removal |

## Legacy Issue-Specific Loader SQL
These are no longer supported operationally. Their behavior has been replaced by generic producer-side loaders.

| Status | Current Path | Legacy Purpose | Canonical Replacement | Action |
|---|---|---|---|---|
| historical-archive | `<producer_repo_root>-authority-source/docs/architecture/tom-baby7-fractal-core/91-load-retirement-subsystem-proving-package-into-paa.sql` | one-off source-to-PAA loader | `paa-producer load-issue-into-paa` | archive only |
| historical-archive | `<producer_repo_root>-authority-source/docs/architecture/tom-baby7-fractal-core/104-load-issue101-retirement-subsystem-into-paa.sql` | one-off issue loader | `paa-producer load-issue-into-paa` | archive only |
| historical-archive | `<producer_repo_root>-authority-source/docs/architecture/tom-baby7-fractal-core/106-load-issue103-retirement-lifecycle-executor-into-paa.sql` | one-off issue loader | `paa-producer load-issue-into-paa` | archive only |
| historical-archive | `<producer_repo_root>-authority-source-clean/docs/architecture/tom-baby7-fractal-core/91-load-retirement-subsystem-proving-package-into-paa.sql` | recovery-lane one-off loader | `paa-producer load-issue-into-paa` | archive only |
| historical-archive | `<producer_repo_root>-authority-source-clean/docs/architecture/tom-baby7-fractal-core/104-load-issue101-retirement-subsystem-into-paa.sql` | recovery-lane one-off loader | `paa-producer load-issue-into-paa` | archive only |
| historical-archive | `<producer_repo_root>-authority-source-clean/docs/architecture/tom-baby7-fractal-core/106-load-issue103-retirement-lifecycle-executor-into-paa.sql` | recovery-lane one-off loader | `paa-producer load-issue-into-paa` | archive only |
| historical-archive | `<producer_repo_root>-authority-source-clean/docs/architecture/tom-baby7-fractal-core/108-load-issue106-retirement-boundary-diagnostics-into-paa.sql` | recovery-lane one-off obligation/source loader | `paa-producer load-issue-into-paa` and `paa-producer materialize-verification-obligations` | archive only |
| historical-archive | `<producer_repo_root>-authority-source-clean/docs/architecture/tom-baby7-fractal-core/109-load-issue106-retirement-boundary-diagnostics-minimal-into-paa.sql` | recovery-lane minimal one-off loader | `paa-producer load-issue-into-paa` and `paa-producer materialize-verification-obligations` | archive only |

## Risk Notes

### Highest confusion risk
The highest-risk future derailers are:
- `<codex_home>/skills/fractal-core-*`
- `<codex_home>/automations/*fractal-core*`
- `<producer_repo_root>/tools/codex-skills/*`

Reason:
- they still look runnable
- they resemble the old successful operating surfaces
- future sessions can easily rediscover them and mistake them for supported entrypoints

### Highest operational risk
The highest operational risk is not that the legacy files exist.
It is that prompts, automation configs, or local habits may still reference them.
That means the next required slice is an automation/reference audit, not just filesystem cleanup.

## Required Follow-Up Actions
- audit automation prompts/configs for references to:
  - `<codex_home>/skills/`
  - `<codex_home>/automations/`
  - `<producer_repo_root>/tools/codex-skills/`
  - transitional authority-source repo paths
- decide final removal timing for deprecated home-folder Fractal Core runtime surfaces
- decide final removal timing for `appdev/tools/codex-skills/...` duplicates after prompt/config cleanup
- classify any remaining install/helper scripts not covered here if they are discovered during automation review

## Bottom Line
We should no longer say only that these surfaces are "non-canonical."
We now have an explicit retirement map:
- platform runtime lives in `paa-platform`
- producer and consumer repos receive installed copies only
- old helper/runtime copies are either:
  - `duplicate-retire`
  - `deprecated-paused`
  - or `historical-archive`

That distinction is important because future sessions should treat any rediscovered legacy path as a cleanup target, not as an alternative implementation source.
