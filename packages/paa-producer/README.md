# paa-producer

`paa-producer` is the producer-side install bundle for source-authority repos such as:

- `/Users/billyweisberg/Repos/Individual-Centricity/appdev`

## Responsibilities

- validate source authority inputs
- derive dependency graph artifacts
- derive Stage 1 design packages
- derive coder briefs
- publish versioned authority packages

## Non-goals

- role queue execution
- queue claim runtime
- project implementation orchestration

## Initial contents

- `src/paa_producer/commands.py`
- `src/paa_producer/__main__.py`

These files are intentionally skeletal so the first extraction wave has a stable target surface.
