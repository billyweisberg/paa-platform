# paa-consumer

`paa-consumer` is a deprecated compatibility package.

Current state:
- the user-facing CLI is `paa`
- runtime hosts live in `paa_core`
- queue admin, runtime control, and automation flows are owned by `paa_core` and surfaced through `paa_cli`

The remaining `paa_consumer` package exists only so the deprecated `python -m paa_consumer` entrypoint can fail cleanly and point users to `paa`.
