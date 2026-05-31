# paa-cli

Unified operator CLI for the PAA platform.

This package currently exposes a thin Typer shell over the already-governed
`component` and `plan` command families. It is intentionally not yet the full
methodology-aware control plane.

Current pointer-facing reads:
- `paa status inspect`
- `paa status next`
- `paa report explain`

Compatibility alias:
- `paa report next`
  - This currently remains available for continuity, but `paa status next` is the
    preferred long-term operator surface.

Methodology preflight:
- `component` and `plan` commands may be preflighted when methodology anchors are
  supplied, such as `--methodology-execution-id` or `--project-id` with
  `--work-item-id`.
- Preflight may:
  - allow execution
  - warn and continue
  - block execution
  - redirect the operator to a pointer-facing read such as `paa status inspect`
