# Service-Oriented Code-Artifact Target Taxonomy Extension

Date: 2026-05-16

## Purpose

Close Priority 0 remediation item 2 by extending the Component Element and Component Element Realization taxonomy so service-oriented slices can be derived without overloading repository-shaped target labels.

This note records the specific taxonomy changes required by the `Component Design Planning Service` proof slice.

## Related Notes

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-16-paa-derivation-remediation-backlog.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-derivation-dry-run.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-component-element-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-element-realization-model.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/009-step9-service-oriented-target-taxonomy.sql`

## Problem Statement

The dry run proved that the original realization taxonomy was still too repository-shaped.

It could already express artifacts such as:
- `repository_interface`
- `concrete_repository_class`
- `dto`
- `mapper`
- `query_object`

But the proof slice needed to express service-oriented artifacts such as:
- `service_interface`
- `service_implementation`
- `test_module`
- `package_export`

Without those types, the system could describe the intended build sequence only in prose, not in structured derivation authority.

## Key Design Correction

The correction is not only second-level realization growth.

The proof slice also exposed one top-level taxonomy gap:
- there was no clean Component Element type for test/proving assignments

So Priority 0 item 2 requires both:
1. realization-type extension
2. one top-level Component Element extension

## Top-Level Component Element Extension

Added Component Element type:
- `verification_surfaces`

Label:
- `Verification Surfaces`

Purpose:
- represent test and proving work as a first-class component-design assignment category
- allow coder-agent briefs to target verification work without pretending tests are only a side effect of `Functions`

This is consistent with the corrected rule that the top-level Component Element list is a controlled starting taxonomy, not a permanently frozen set.

## New Realization Types

Added realization types:
- `service_interface`
- `service_implementation`
- `test_module`
- `package_export`

### `service_interface`
Use for:
- service contracts or protocols
- interface modules such as `contracts.py`

### `service_implementation`
Use for:
- default service classes
- implementation modules such as `default.py`

### `test_module`
Use for:
- dedicated unit-test or proving modules
- verification surfaces such as `test_component_design_planning_service.py`

### `package_export`
Use for:
- package-level public export surfaces
- modules such as `__init__.py` that publish the public package boundary

## Allowed Mapping Extensions

The taxonomy is extended with these allowed mappings:
- `interfaces -> service_interface`
- `functions -> service_implementation`
- `service_contract -> service_interface`
- `verification_surfaces -> test_module`
- `interfaces -> package_export`

## Why `package_export` maps from `interfaces`

`package_export` is not a top-level Component Element by itself.
It is a concrete code artifact that exposes or binds the component's public interface surface.

So it belongs as a realization of:
- `Interfaces`

rather than as a separate top-level design concern.

## Why `verification_surfaces` is a top-level element

`test_module` alone is not enough.

The proof slice needed a way to say:
- this run includes explicit verification/proving work for the component

That is a design concern, not just a file type.

So the right split is:
- top-level concern: `Verification Surfaces`
- concrete artifact type: `test_module`

## Proof-Slice Consequence

The `Component Design Planning Service` proof slice can now be expressed much more faithfully as structured targets such as:
1. `Interfaces -> service_interface`
2. `Functions -> service_implementation`
3. `Interfaces -> package_export`
4. `Verification Surfaces -> test_module`

That is materially closer to the intended service build sequence than the old repository-shaped vocabulary.

## Remaining Limitation

This extension removes the main service-oriented taxonomy blocker.

It does **not** yet solve Priority 0 item 3:
- draft -> approved -> packet-ready lifecycle governance

So the global derivation decision remains:
- `NO-GO`

until lifecycle governance is also made explicit enough to govern execution authority cleanly.

## Decision

Decision:
- `Priority 0 item 2 complete`

Meaning:
- service-oriented slices now have a controlled target taxonomy capable of expressing the proof slice in structured form

Not implied:
- the proof slice is not yet packet-ready execution authority
- authoritative implementation still does not resume until Priority 0 item 3 is complete
