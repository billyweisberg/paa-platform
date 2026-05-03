# paa-core

`paa-core` is the shared foundation for both producer-side and consumer-side PAA installs.

It is the lowest-level package in the platform split.

## Responsibilities

- common config loading
- common path conventions
- package metadata handling
- shared lightweight runtime helpers

## Non-goals

- product-specific authority logic
- queue transport behavior
- producer-only publication commands
- consumer-only role orchestration commands

## Initial contents

- `src/paa_core/config.py`
- `src/paa_core/package_metadata.py`
- `src/paa_core/paths.py`

These modules are intentionally minimal placeholders for the first extraction wave.
