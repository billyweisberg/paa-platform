# Producer Publication

## Purpose

This note documents the first config-driven publication entrypoint exposed by `paa-producer`.

## Command

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src \
python3 -m paa_producer publish-authority-package \
  --repo-root /absolute/path/to/producer-repo \
  --project-config /absolute/path/to/.codex/paa/project-config.json
```

## Current state

This command is designed for a producer repo that already contains:

- source authority manifest
- source supporting docs
- repo-local producer config
- repo-local producer-mode PAA install under `.codex/paa/`

The current validated producer target is:

- repo: `/Users/billyweisberg/Repos/Individual-Centricity/appdev`
- branch: `codex/paa-producer-consolidation`

That branch now carries the Fractal Core source authority tree, the stabilized manifest/tooling delta, and the repo-local producer install required to publish directly from `appdev`.

## Transitional note

The authority maintenance lane was used to prove the first publication extraction, but it is no longer the intended long-term producer target.

The migration direction is now:

1. `appdev` publishes the authority package
2. consumer repos install the published package into `.project/data/paa/authority/current/`
3. shared producer/runtime logic continues moving into `paa-platform`
