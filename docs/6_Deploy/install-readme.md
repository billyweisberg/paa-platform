# Install Docs

This directory documents producer-mode and consumer-mode installation flows for `paa-platform`.

## Current commands

### Producer runtime install/update

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src \
uv run --python 3.12 --isolated python -m paa_producer install-producer-runtime \
  --repo-root /absolute/path/to/producer-repo \
  --project-pack fractal-core
```

Alias:

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-producer/src \
uv run --python 3.12 --isolated python -m paa_producer update-producer-runtime \
  --repo-root /absolute/path/to/producer-repo \
  --project-pack fractal-core
```

This creates or refreshes:
- `.codex/paa/bin/`
- `.codex/paa/lib/`
- `.codex/paa/schemas/`
- `.codex/paa/templates/`
- `.codex/paa/install-metadata.json`
- `.codex/paa/project-config.example.json`
- `.codex/automations/`
- `.codex/skills/`
- `.project/data/paa/publish/`
- `.project/data/paa/cache/`

The producer install selects project-specific skills and automations from:
- `project-packs/<project-pack>/pack.json`

### Consumer runtime install/update

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-consumer/src \
uv run --python 3.12 --isolated python -m paa_consumer install-consumer-runtime \
  --repo-root /absolute/path/to/consumer-repo \
  --project-pack fractal-core
```

Alias:

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-consumer/src \
uv run --python 3.12 --isolated python -m paa_consumer update-consumer-runtime \
  --repo-root /absolute/path/to/consumer-repo \
  --project-pack fractal-core
```

This creates or refreshes:
- `.codex/paa/bin/`
- `.codex/paa/lib/`
- `.codex/paa/schemas/`
- `.codex/paa/templates/`
- `.codex/paa/install-metadata.json`
- `.codex/paa/project-config.example.json`
- `.codex/automations/`
- `.codex/skills/`
- `.project/data/paa/authority/current/`
- `.project/data/paa/claims/`
- `.project/data/paa/queue-state/`
- `.project/data/paa/artifacts/`
- `.project/data/paa/evidence/`
- `.project/data/paa/cache/`
- `.project/data/paa/reports/`

The consumer install selects project-specific skills and automations from:
- `project-packs/<project-pack>/pack.json`

### Authority package install into consumer repo

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-consumer/src \
uv run --python 3.12 --isolated python -m paa_consumer install-authority-package \
  --repo-root /absolute/path/to/consumer-repo \
  --package-root /absolute/path/to/published-authority-package
```

## Current note

These commands now install the repo-local PAA payload plus repo-local automations and skills.

They do not yet fully replace every legacy operational entrypoint by policy on their own. The canonical path is still:
- install from `paa-platform`
- run producer workflows from repo-local producer installs
- run consumer workflows from repo-local consumer installs
