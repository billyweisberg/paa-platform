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

At the moment, the cleanest runnable producer target is the authority maintenance lane, not `/Users/billyweisberg/Repos/Individual-Centricity/appdev`, because `appdev` does not yet contain the source authority tree.

That is expected during the migration.

## Migration note

The next producer migration step is to make `appdev` carry the producer-side source authority inputs so this command can run there directly.
