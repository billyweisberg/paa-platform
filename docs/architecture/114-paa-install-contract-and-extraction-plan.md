# 114. PAA Install Contract, Authority Package Format, and First Extraction Plan

Date: 2026-05-03

## Purpose

This document defines:

- how PAA gets installed into producer and consumer repos
- what a published authority package must contain
- the first extraction moves out of:
  - `/Users/billyweisberg/Repos/Individual-Centricity/appdev`
  - `$HOME/.codex`

## Install contract

### Install target

PAA installs into repo-local:

- `.codex/paa/`

This location is for installed tooling and templates, not mutable runtime state.

### Runtime state target

Mutable runtime state installs/operates under:

- `.project/data/paa/`

This location should be gitignored.

### Producer install contract

When PAA is installed into an authority producer repo, it must create:

```text
.codex/paa/bin/
.codex/paa/lib/
.codex/paa/schemas/
.codex/paa/templates/
.codex/paa/install-metadata.json
.codex/paa/project-config.example.json
```

And it may also create:

```text
.project/data/paa/publish/
.project/data/paa/cache/
```

### Consumer install contract

When PAA is installed into a consumer repo, it must create:

```text
.codex/paa/bin/
.codex/paa/lib/
.codex/paa/schemas/
.codex/paa/templates/
.codex/paa/install-metadata.json
.codex/paa/project-config.example.json
```

And it may also create:

```text
.project/data/paa/authority/current/
.project/data/paa/claims/
.project/data/paa/queue-state/
.project/data/paa/artifacts/
.project/data/paa/evidence/
.project/data/paa/cache/
.project/data/paa/reports/
```

### Install metadata

Every install should record:

- platform version
- install mode: `producer` or `consumer`
- installed_at timestamp
- source platform repo revision
- schema bundle version

Example:
- `.codex/paa/install-metadata.json`

## Project config contract

### Producer repo config

Path:
- `.codex/paa/project-config.json`

Expected fields:
- `project_id`
- `mode = producer`
- `authority_manifest_path`
- `supporting_docs_root`
- `artifact_examples_root`
- `publication_output_root`
- `github_repo`

### Consumer repo config

Path:
- `.codex/paa/project-config.json`

Expected fields:
- `project_id`
- `mode = consumer`
- `authority_install_root`
- `runtime_data_root`
- `github_repo`
- `queue_names`
- `db_profile` or runtime DB connection source

## Authority package format

### Package goals

The published authority package should be:
- versioned
- immutable once published
- installable into a consumer repo
- sufficient for runtime startup without reading the producer repo live

### Suggested package layout

```text
authority-package/
  package-metadata.json
  authority/
    fractal-core-python-authority.json
    project-authority.schema.json
  docs/
    11-parity-and-tolerances.md
    32-config-and-tuning-contract.md
    37-port-version-targeting.md
    42-rabbitmq-handoff-system.md
    44-python-implementation-roadmap.md
    47-qa-verification-gate.md
    48-git-and-github-authority-model.md
    49-authority-task-authoring-workflow.md
    50-authority-issue-materialization.md
  artifacts/
    stage1_design_package.*.json
    coder_run_brief.*.json
    dependency_graph_slice.*.json
```

### Package metadata

`package-metadata.json` should include:
- `project_id`
- `authority_version`
- `published_at`
- `published_from_repo`
- `published_from_revision`
- `package_format_version`
- `producer_platform_version`
- `included_docs`
- `included_artifacts`

### Package invariants

1. the manifest inside the package is the published runtime manifest
2. supporting docs are copied into the package, not referenced back into the producer repo
3. explicit task `design_package_id_external` and `coder_brief_id_external` values are preserved
4. package metadata identifies the producing repo revision
5. consumer repos install the package; they do not rebuild it live

## Install / update flow

### Producer flow

1. install producer-mode PAA into `appdev`
2. author source authority content
3. derive dependency graph / Stage 1 packages / coder briefs
4. publish authority package version

### Consumer flow

1. install consumer-mode PAA into `fractal-core-python`
2. install or update the latest published authority package
3. run Dev / QA / Architect roles against:
   - installed package
   - local runtime data
   - GitHub
   - PAA runtime DB

## First extraction wave

The first wave should be intentionally conservative.

### Move out of `appdev`

Move to `paa-platform`:
- queue/claim runtime scripts
- packet compilers
- publication engine implementation
- readiness materializers
- runtime resolver logic
- shared skills and templates

Leave in `appdev`:
- source authority manifest
- source docs
- source task authoring content
- source artifact inputs
- thin project-local publish wrapper/config

### Move out of `$HOME/.codex`

Move into project-local `.codex/` installs:
- project automations
- project-installed skills
- project runtime helper scripts
- project-local platform install metadata

Move into `.project/data/paa/`:
- project queue claims
- runtime mirrors / installed package data
- packet drafts and review files
- evidence artifacts
- local caches used during role runs

Keep in `$HOME/.codex` only:
- personal/global Codex settings
- optional global helper tooling that is not project-specific

## Immediate extraction candidates

### Candidate set A: authority runtime tools

From current authority tooling surface:
- `project_authority.py`
- `publish_current.py`
- packet materializers
- readiness materializer

Target:
- `paa-platform`

### Candidate set B: queue runtime

From current handoff runtime surface:
- `rabbitmq_handoff.py`

Target:
- `paa-platform`

### Candidate set C: project automations

From:
- `$HOME/.codex/automations/...`

Target:
- repo-local project automation definitions

Producer repo target:
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev/.codex/automations/`

Consumer repo target:
- project repo `.codex/automations/`

### Candidate set D: installed skills

From:
- `$HOME/.codex/skills/...`

Target:
- repo-local installed project/runtime skills or thin wrappers into `.codex/paa/`

## First migration sequence

### Step 1

Create the `paa-platform` repo skeleton and define:
- package layout
- install metadata contract
- project config contract

### Step 2

Extract publication and runtime tooling into that repo without changing behavior yet.

### Step 3

Install producer-mode PAA into:
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev`

### Step 4

Install consumer-mode PAA into:
- `fractal-core-python`

### Step 5

Move project-specific automations out of `$HOME/.codex` and into repo-local locations.

### Step 6

Consolidate mutable runtime state into:
- `.project/data/paa/`

### Step 7

Retire sibling-repo mirror copying in favor of:
- authority package publish
- authority package install/update

## Guardrails

1. do not rewrite Fractal Core source authorship during extraction
2. do not require consumer repos to read producer repos live
3. do not keep project-specific runtime truth in the home folder
4. do not mix installed tooling and mutable runtime data in the same path
5. do not make role runs responsible for platform maintenance

## Success criteria for the first extraction wave

We should consider the first wave successful when:

1. `appdev` publishes a versioned authority package using installed PAA producer tools
2. `fractal-core-python` installs that package locally
3. role automations run from repo-local installs, not `$HOME/.codex`
4. runtime claims/artifacts/evidence live under `.project/data/paa/`
5. no cross-repo sibling mirror writes are required during normal role execution

## Recommended next implementation slice

The first extraction implementation slice should be:

- create the `paa-platform` repo skeleton and move the publication/runtime tool surfaces there without changing external behavior yet

That is the smallest meaningful step toward the new architecture.
