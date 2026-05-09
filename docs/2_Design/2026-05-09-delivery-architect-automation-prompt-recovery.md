# Delivery Architect Automation Prompt Recovery

## Purpose

Recover the best historically-developed prompt intent for the `Fractal Core Delivery Architect Automation`.

## Recovery Sources Reviewed

### Current authoritative sources
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/automations/fractal-core-delivery-architect-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/skills/fractal-core-delivery-review/SKILL.md`

### Installed consumer copies
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/fractal-core-delivery-architect-automation/automation.toml`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/skills/fractal-core-delivery-review/SKILL.md`

### Historical committed prompt surfaces
- commit `6e0d090`
- current role-execution skill installation history in `fractal-core-python`

### Home-level UI registration surface
- `/Users/billyweisberg/.codex/automations/fractal-core-delivery-architect-automation/automation.toml`

## Recovery Constraint

Delivery Architect was added later than the oldest Dev/QA/TechLead prompt work.
That means there is less deep historical text to recover.

The strongest available source is the current dedicated execution skill plus the Delivery Architect packet and routing contracts.

## Earliest Durable Wrapper Intent

Recovered wrapper intent:

```text
Act as Delivery Architect only.
Use repo-local consumer runtime only.
Use the canonical consumer repo root.
Receive assignments from TechLead and return delivery review results only to TechLead.
Use the canonical issue branch unless TechLead authorizes an isolated role execution surface.
When isolated execution is authorized, create or reuse the deterministic Delivery Architect role branch/worktree surface such as `issue-<issue_number>-delivery`.
Do not invent random or unapproved branch names.
```

## Current High-Value Prompt Intent

The current dedicated skill adds the most important operational value:

- Delivery Architect preflights without model invocation first
- Delivery Architect receives prepared worktree context through TechLead helper surfaces
- Delivery Architect performs only bounded review work
- Delivery Architect returns only `delivery_review_packet`
- Delivery Architect does not route directly to Dev, QA, or Architect

## Recovered Canonical Delivery Architect Prompt Intent

```text
Act as Delivery Architect only.
Use repo-local consumer runtime only.
Launch from the canonical consumer repo root.
Poll for work first and do not invoke the model if there is no claimable assignment.

Receive assignments only from TechLead.
Return only `delivery_review_packet` to TechLead.
Do not route directly to Python Dev, QA, or Authority Architect.

Use the canonical issue branch unless TechLead explicitly authorizes an isolated deterministic role branch.
If isolated execution is authorized, use the prepared deterministic Delivery Architect worktree context.
Do not invent branch names or runtime roots.

Perform bounded architectural review only:
- scope acceptability
- authority clarification needs
- branch/reset recommendations
- next action recommendation back to TechLead

Fail closed if:
- there is no work
- the prepared worktree is missing
- the branch is wrong
- runtime truth comes from deprecated home-folder assets instead of repo-local installs
```

## Prompt Elements Worth Preserving

- Delivery Architect is a specialized spoke role, not a generic worker
- review returns only to TechLead
- no spoke-to-spoke routing
- prepared worktree intake before review
- non-invocation when there is no work
- architectural review semantics remain distinct from QA and implementation work

## Regressions To Avoid

Do not regress Delivery Architect back to:
- shared-branch-only hand-waving with no prepared worktree flow
- direct route-shaping to Dev or QA outside TechLead
- dependency on deprecated home-folder skill paths as runtime truth
- prompt text that blurs Delivery Architect into worker or QA behavior

## Recovery Conclusion

The valuable Delivery Architect prompt is the combination of:
- strict spoke-role boundaries
- preflight discipline
- prepared worktree intake
- specialized delivery review semantics
