# paa-consumer

`paa-consumer` is the consumer-side install bundle for project execution repos such as:

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

## Bootstrap CLI

- `paa-consumer techlead-service-map`
  - print the extracted TechLead service inventory and the remaining shell-owned pockets
