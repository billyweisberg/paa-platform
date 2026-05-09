# PAA Data Contracts

## Purpose

Document the primary persisted and transported data contracts in the current PAA system.

This note is not a schema dump.
It is the architectural summary of the data contracts that other components rely on.

## Contract Layers

PAA currently has four major data-contract layers:

1. project and role control-plane records
2. design and brief records
3. transport packet records
4. runtime reporting / lineage records

## 1. Project And Role Control-Plane Contracts

### `paa.projects`
Purpose:
- anchor project identity for all other records

Key fields:
- `project_id`
- `slug`
- `name`
- `execution_surface`
- `status`

Contract significance:
- all roles, work items, handoffs, and queue messages are project-scoped

### `paa.roles`
Purpose:
- persist role identity within a project

Key fields:
- `role_id`
- `project_id`
- `name`
- `category`
- `description`
- `is_human_capable`
- `is_automation_capable`
- `sort_order`
- `active`

Contract significance:
- this is the strongest existing foundation for dynamic roles
- role identity is data, not a dedicated DB column set

Current gap:
- runtime and automation layers still assume a finite hard-coded role vocabulary

### `paa.work_items`
Purpose:
- provide the durable slice / issue anchor

Key fields:
- `work_item_id`
- `project_id`
- `authority_version_id`
- `title`
- `status`
- `merge_policy`
- `requires_qa`
- `issue_number`
- `implementation_target_ref`
- `spec_fragment_ref`

Contract significance:
- all handoff and lifecycle state should resolve back to a work item

## 2. Design And Brief Contracts

### `paa.design_packages`
Purpose:
- persist design-package assignment basis

Key fields:
- `design_package_id`
- `project_id`
- `work_item_id`
- `package_id_external`
- `status`
- `package_json`
- `provenance_json`

Contract significance:
- assignment packets should be traceable back to design-package authority

### `paa.coder_run_briefs`
Purpose:
- persist implementation brief basis

Key fields:
- `coder_run_brief_id`
- `project_id`
- `work_item_id`
- `brief_id_external`
- `status`
- `component_assignment_json`
- `architecture_constraints_json`
- `brief_json`

Contract significance:
- worker execution packets must remain traceable to the triggering brief

### Authority manifest
Purpose:
- published source authority outside the DB row model

Key fields in practice:
- authority version identity
- milestone / phase / task identity
- issue linkage
- package / brief source pointers

Contract significance:
- packet `authority_context` relies on this external authority surface

## 3. Transport Packet Contracts

All packet families share a common top-level envelope.

### Common envelope fields
- `message_id`
- `schema_type`
- `schema_version`
- `project`
- `from_role`
- `to_role`
- `created_at`
- `correlation_id`
- `github_context`
- `payload`
- `authority_context`

Contract significance:
- this is the transport contract for RabbitMQ and queue persistence

### `techlead_assignment_packet`
Purpose:
- bounded role assignment from `TechLead`

Critical payload fields:
- `issue`
- `pr`
- `target_role`
- `assignment_type`
- `canonical_branch`
- `role_branch`
- `lineage_state`
- `allowed_result_types`
- `assignment_summary`

Contract significance:
- active assignment semantics are already role-as-data at the packet layer
- this is good for dynamic roles

Current gap:
- allowed targets are still constrained by runtime role enumerations

### `worker_result_packet`
Purpose:
- generalized implementation-worker result back to `TechLead`

Critical payload fields:
- `issue`
- `branch`
- `pr`
- `worker_role`
- `worker_family`
- `result_type`
- `workflow_compliance`
- `implementation_summary`
- `validation_summary`
- `artifacts`
- `merge_status`
- `techlead_action_recommended`
- `source_assignment_ref`

Contract significance:
- this is the key target-state packet for dynamic worker roles
- the schema already models worker identity as data

Current gap:
- runtime, route policy, prompts, and automations do not yet treat `worker_role` as fully dynamic

### `delivery_review_packet`
Purpose:
- specialized Delivery Architect result

Critical payload fields:
- `review_type`
- `result_type`
- `scope_recommendation`
- `authority_impact`
- `branch_recommendation`
- `techlead_action_recommended`

Contract significance:
- Delivery Architect remains a specialized spoke role, not a generic worker role

### `qa_verification_packet`
Purpose:
- specialized QA result

Critical payload fields:
- `verification_status`
- `verification_scope`
- `mechanical_checks`
- `technical_scope_checks`
- `protected_path_checks`
- `findings`
- `recommended_action`

Contract significance:
- QA remains a specialized spoke role, not a generic worker role

### `techlead_decision_packet`
Purpose:
- durable routing / lineage / lifecycle decision record

Critical payload fields:
- `source_packet_ref`
- `decision_type`
- `decision_rationale`
- `target_role`
- `next_assignment_type`
- `canonical_branch`
- `role_branch`
- `lineage_state`
- `lineage_action`
- `reset_reason`

Contract significance:
- workflow control remains centralized in `TechLead`

## 4. Persistence Of Transport Events

### `paa.handoffs`
Purpose:
- durable route record between roles

Key fields:
- `project_id`
- `work_item_id`
- `from_role_id`
- `to_role_id`
- `handoff_type`
- `status`
- `created_at`
- `claimed_at`
- `acknowledged_at`

Contract significance:
- route identity is persisted generically using role foreign keys
- DB can support arbitrary role-to-role records

### `paa.queue_messages`
Purpose:
- persist queue-level delivery state

Key fields:
- `handoff_id`
- `queue_name`
- `schema_type`
- `message_id_external`
- `correlation_key`
- `payload_json`
- `status`
- `sent_at`
- `claimed_at`
- `acknowledged_at`
- `metadata_json`

Contract significance:
- queue history is durable and decoupled from pure RabbitMQ state

Current gap:
- queue naming and queue-topology assumptions are still static

## 5. Runtime Reporting Contracts

### `techlead-status`
Purpose:
- report current workflow state, lineage, and recommendations

Current contract includes:
- workflow stage
- current owner role
- lineage view
- worktree ownership
- worktree staleness
- next recommended actions

Contract significance:
- status reporting is already the human/operator-facing state synthesis layer
- future dynamic worker roles will need this surface to derive role metadata from data, not hard-coded branch logic

### Lineage view
Purpose:
- represent canonical branch, role branch, source branch, supersession state, and cleanup intent

Contract significance:
- lifecycle cleanup and worktree retirement already depend on this view
- dynamic roles will need lineage contracts that are role-data driven rather than suffix-enumeration driven

## Current Contract Assessment

### Already compatible with dynamic worker roles
- `paa.roles`
- `paa.handoffs`
- `paa.queue_messages`
- packet fields carrying role identity as data
- `worker_result_packet` payload model

### Not yet compatible with true dynamic worker roles
- route policy defined as fixed role pairs
- role normalization defined as fixed mappings
- branch suffix selection defined in code
- CLI role choices defined in code
- automation registration and prompt surfaces keyed to known role names
- queue topology defined by a fixed queue list

## Design Implication

Dynamic Worker Roles will require a contract layer above the DB that defines:
- project role registry
- queue binding model
- branch suffix model
- automation registration model
- route-policy derivation model
