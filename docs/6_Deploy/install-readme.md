# Install Docs

This directory documents producer-mode and consumer-mode installation flows for `paa-platform`.

## Current commands

### Producer runtime install/update

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src \
/opt/homebrew/bin/python3.12 -m paa_producer install-producer-runtime \
  --repo-root /absolute/path/to/producer-repo
```

Alias:

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src \
/opt/homebrew/bin/python3.12 -m paa_producer update-producer-runtime \
  --repo-root /absolute/path/to/producer-repo
```

This creates or refreshes:
- `.codex/paa/bin/`
- `.codex/paa/lib/`
- `.codex/paa/schemas/`
- `.codex/paa/templates/`
- `.codex/paa/install-metadata.json`
- `.codex/paa/project-config.example.json`
- `.project/data/paa/publish/`
- `.project/data/paa/cache/`

### Consumer runtime install/update

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-consumer/src \
/opt/homebrew/bin/python3.12 -m paa_consumer install-consumer-runtime \
  --repo-root /absolute/path/to/consumer-repo
```

Alias:

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-consumer/src \
/opt/homebrew/bin/python3.12 -m paa_consumer update-consumer-runtime \
  --repo-root /absolute/path/to/consumer-repo
```

This creates or refreshes:
- `.codex/paa/bin/`
- `.codex/paa/lib/`
- `.codex/paa/schemas/`
- `.codex/paa/templates/`
- `.codex/paa/install-metadata.json`
- `.codex/paa/project-config.example.json`
- `.project/data/paa/authority/current/`
- `.project/data/paa/claims/`
- `.project/data/paa/queue-state/`
- `.project/data/paa/artifacts/`
- `.project/data/paa/evidence/`
- `.project/data/paa/cache/`
- `.project/data/paa/reports/`

### Authority package install into consumer repo

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-consumer/src \
/opt/homebrew/bin/python3.12 -m paa_consumer install-authority-package \
  --repo-root /absolute/path/to/consumer-repo \
  --package-root /absolute/path/to/published-authority-package
```

## Current limitation

These commands currently install the repo-local PAA payload and authority package only.

They do not yet install or update:
- project-local automations
- project-local skills
- queue runtime helpers beyond the copied payload already present in some repos

That remains a follow-on platform slice.
