# Codex Project Config and UV Bootstrap Strategy

## Purpose
This note defines the next hardening strategy for environment consistency.
It addresses two related concerns:
- how repo-local Codex project config should be used
- how `uv` should become the shared bootstrap path for human sessions and automation runs

## Current State

### What is true right now
- `uv` is installed locally:
  - `uv 0.8.13`
- default `python3` in the shell is still:
  - `Python 3.9.6`
- the repo-local PAA wrappers now:
  - prefer `uv` with Python 3.12
  - fall back only to `python3 >= 3.12` if `uv` is unavailable
- `paa-platform` package pyprojects require:
  - `>=3.12`
- `fractal-core-python` already uses `uv` in CI and developer commands
- there is currently no repo-local `.codex/config.toml` contract for the canonical producer or consumer repos
- there is currently no single documented bootstrap contract shared by:
  - interactive coder sessions
  - producer automations
  - consumer automations
  - installer-generated PAA wrappers

### Why this is a problem
The system is functionally working, but environment behavior is still too implicit.
That creates the exact class of automation/session drift that has already hurt us.

## Role of Repo-Local `.codex/config.toml`

## Recommendation
Adopt repo-local Codex project config files in canonical repos:
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev/.codex/config.toml`
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/config.toml`

These files should be used for **Codex-native session configuration** first.
That includes things like:
- `model`
- `approval_policy`
- any future Codex-supported project behavior toggles

### Important boundary
Repo-local `.codex/config.toml` should not be treated as the only source of PAA runtime truth.

Use it for:
- Codex session defaults
- declaring the intended repo role to humans and local tooling
- optionally pointing at PAA-owned config locations

Do not depend on it alone for:
- dynamic issue/session state
- current coder brief resolution
- queue claim state
- installed authority state
- PAA database/runtime state

Those belong in PAA-owned config and runtime surfaces.

## Candidate values to record in `.codex/config.toml`
These are good candidates for repo-local Codex project config because they are stable or semi-stable session defaults.

### Good candidates
- repo role:
  - `producer` or `consumer`
- project pack:
  - `fractal-core`
- stable source paths such as:
  - authority manifest path
  - coder brief schema path
  - artifact roots
- preferred model / approval defaults for this repo

### Not good as fixed repo-level defaults
These are too session-specific to be treated as stable repo config:
- current coder run brief path for one issue
- current issue number
- current package id
- current queue claim id

Those should be resolved at runtime or written into session/runtime state under `.project/data/paa/`.

## Recommended configuration split
Use two layers.

### Layer 1: Codex project config
Location:
- `.codex/config.toml`

Responsibility:
- configure Codex behavior for this repo
- declare stable repo-local defaults that help sessions start consistently
- serve as the repo-local bridge to the PAA runtime contract

Example shape:

```toml
model = "gpt-5.5"
approval_policy = "never"

[paa]
role = "producer"
project_pack = "fractal-core"
project_config = ".codex/paa/project-config.json"

[paths]
authority_manifest_path = "docs/architecture/tom-baby7-fractal-core/project-authority/fractal-core-python-authority.json"
coder_run_brief_schema_path = "docs/architecture/tom-baby7-fractal-core/handoff-schemas/coder_run_brief.schema.json"
artifact_examples_root = "docs/architecture/tom-baby7-fractal-core/artifact-examples"
```

### Layer 2: PAA runtime/session state
Location examples:
- `.codex/paa/project-config.json`
- `.project/data/paa/session/current.json`
- `.project/data/paa/authority/current/`

Responsibility:
- dynamic and resolved runtime state
- installed authority package state
- current issue/brief/session context
- queue/runtime state

This layer stays with PAA, not Codex.

## UV Bootstrap Strategy

## Goal
Every human session and every automation run should use the same Python toolchain path and the same dependency strategy.

The system should stop depending on:
- shell-default `python3` being correct
- manually remembered virtualenv activation
- machine-specific Python path assumptions

## Recommended target model

### 1. UV becomes the standard Python entrypoint
Use `uv` as the official bootstrap mechanism for:
- PAA platform development
- producer runtime installs
- consumer runtime installs
- repo-local automation execution
- validation commands in coder briefs

### 2. Canonical repos should declare Python version intentionally
Recommended repo-level pin:
- `.python-version` with `3.12`

Why:
- PAA packages already require `>=3.12`
- current wrappers already assume 3.12
- this removes ambiguity between shell `python3` and intended runtime

### 3. Installed repo-local PAA runtime should be a UV-managed project
Target install layout:
- `.codex/paa/runtime/`

This runtime directory should eventually contain:
- generated `pyproject.toml`
- generated `uv.lock`
- installed platform-owned libraries
- vendor/runtime dependencies needed for repo-local command execution

Then wrappers in:
- `.codex/paa/bin/`

should execute through `uv run`, not a hardcoded Python interpreter.

### 4. Human sessions should use explicit repo-local entrypoints
Producer repo:
- use `.codex/paa/bin/paa-producer`
- use `uv run` for project validation commands where applicable

Consumer repo:
- use `.codex/paa/bin/paa-consumer`
- use `uv run` for repo validation commands

This gives one shared operational rule:
- humans and automations run the same repo-local commands

### 5. Automations should run from repo root and call repo-local wrappers only
Automations should:
- set `cwd` to the canonical repo root
- call repo-local installed wrappers
- never depend on globally activated environments
- never depend on `$HOME/.codex` Python/runtime surfaces

## Short-term vs target-state bootstrap

### Short-term acceptable state
For the current transition window, repo-local wrappers prefer `uv` and fall back to `python3 >= 3.12`.

That is acceptable as a first pass, but it should still be treated as transitional until the full repo-local runtime project layout is in place.

### Target state
Replace generated Python shebang wrappers with a `uv`-managed bootstrap path.
Possible implementation patterns:
- shell wrapper that calls `uv run --project <runtime_root> ...`
- generated runtime project with entrypoints executed through `uv`

The specific wrapper mechanics can be decided during implementation.
The important contract is:
- no dependence on shell-default Python
- no dependence on hardcoded system Python path
- repo-local runtime only

## Proposed Execution Contract

### Producer repo
- Codex session defaults come from:
  - `.codex/config.toml`
- stable PAA producer config comes from:
  - `.codex/paa/project-config.json`
- repo-local runtime executes from:
  - `.codex/paa/runtime/`
- runtime state lives under:
  - `.project/data/paa/`

### Consumer repo
- Codex session defaults come from:
  - `.codex/config.toml`
- stable PAA consumer config comes from:
  - `.codex/paa/project-config.json`
- repo-local runtime executes from:
  - `.codex/paa/runtime/`
- runtime state lives under:
  - `.project/data/paa/`

## Implementation Sequence
1. add repo-local `.codex/config.toml` to the canonical producer and consumer repos
2. add `.python-version` pins to canonical producer, consumer, and platform repos where appropriate
3. define generated UV-managed runtime layout under `.codex/paa/runtime/`
4. update installer-generated wrappers to execute through `uv`, not a hardcoded system Python path
5. validate producer and consumer repo-local commands under that model
6. validate automation runs under the same model

## What this strategy intentionally does not do
- It does not move dynamic issue/session state into `.codex/config.toml`
- It does not treat Codex project config as a replacement for PAA runtime state
- It does not assume arbitrary custom TOML keys are automatically consumed by Codex itself

Instead, it treats `.codex/config.toml` as:
- a Codex-native project config surface
- and a useful repo-local place to declare stable session defaults that our own tooling can also read if we choose

## Bottom Line
Yes, repo-local `.codex/config.toml` is a strong candidate surface for stabilizing session behavior and helping automation terminal environments stay consistent.
But the full fix is not just adding that file.

The real fix is:
- Codex project config for stable session defaults
- PAA-owned config for runtime truth
- UV-managed repo-local runtime for both humans and automations

That combination is the path to consistent environments instead of accidental ones.
