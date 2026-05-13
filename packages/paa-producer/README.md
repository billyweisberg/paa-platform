# paa-producer

`paa-producer` is the producer-side install bundle for source-authority repos such as:

- `appdev`

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
- `src/paa_producer/publish.py`

These files are intentionally small, but they now include the first extracted authority publication surface as a library module.
