# paa-consumer

`paa-consumer` is an internal consumer-side package bundle for project execution repos such as:

- `billyweisberg/fractal-core-python`

## Responsibilities

- install and update published authority packages
- resolve active runtime state
- manage queue and claim lifecycle
- compile runtime packets
- support Dev / QA / Architect automation flows

## Non-goals

- source-authority derivation
- source-authority publication authoring
- product-specific implementation code

## Initial contents

- `src/paa_consumer/commands.py`
- `src/paa_consumer/__main__.py`

These files are intentionally skeletal so the first extraction wave has a stable runtime target.

## User-facing CLI

Use the unified `paa` CLI for operator/runtime commands.

Examples:

- `paa report techlead-service-map`
- `paa runtime start`
- `paa queue ensure-topology`
