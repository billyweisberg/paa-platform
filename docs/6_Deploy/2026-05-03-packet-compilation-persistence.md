# Packet Compilation Persistence

Packet compilation is now treated as a durable automation event in PAA.

## Storage choice

Compiled packet metadata and review snapshots are currently persisted in `paa.automation_runs` rather than a new dedicated packet table.

That gives us an immediate durable trail with:

- agent identity
- optional linked work item
- trigger type
- completion status
- timestamp
- summary
- packet JSON snapshot
- review markdown snapshot
- design package and brief provenance
- source input file path

## Trigger types

Current packet compilation trigger types:

- `packet_compilation:architect_cycle_packet`
- `packet_compilation:slice_result_packet`
- `packet_compilation:qa_verification_packet`

## Persisted fields

The packet compiler stores these in `artifacts_json`:

- `packet_schema_type`
- `package_id_external`
- `brief_id_external`
- `message_id`
- `correlation_id`
- `review_markdown`
- `output_path`
- `review_output_path`
- `source_input_path`
- `source_packet_path`
- `packet_json`
- `persistence_version`

## Why `automation_runs` is good enough for now

This keeps the packet-compilation trail aligned with the broader runtime story:

- TechLead report persistence
- packet compilation
- handoff transport
- Dev verification
- QA verification
- acceptance decisions

If packet compilation grows into a richer lifecycle later, we can still introduce a dedicated table without losing the current trail.

## Proving run

The proving package now has durable automation-run records for:

- compiled `architect_cycle_packet`
- compiled `slice_result_packet`
- compiled `qa_verification_packet`

This means packet compilation is no longer just a filesystem artifact. It is now part of the durable project record in PAA.
