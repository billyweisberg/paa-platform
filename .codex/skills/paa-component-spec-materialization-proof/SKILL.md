# PAA Component Spec Materialization Proof

Use this skill when the task is to turn a governed component authority doc into a materialization-ready bridge and prove that its structured tables reconcile downstream model truth.

## Goal

Make `Component Spec` or equivalent governed component authority docs act as the bridge from design authority into executable PAA model truth.

## Use This For

- refactoring a governed component authority doc to template conformance
- adding required materialization tables
- extracting structured table seeds from a governed doc
- reconciling component, element, realization, plan, activity, and dependency truth from the doc
- proving spec-to-model agreement after reconciliation

## Authority

Read these first:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-20-component-spec-template-materialization-bridge.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-20-component-spec-section-to-model-mapping-table.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-20-component-spec-doc-to-materialization-extraction-rules.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-20-delivery-architect-component-spec-materialization-proof-packet.md`

## Workflow

1. Inspect the governed target doc and identify missing required bridge sections.
2. Add or normalize these sections:
   - `Component Identity Table`
   - `Ownership Boundary`
   - `Non-Ownership Boundary`
   - `Collaborators`
   - `Component Elements Table`
   - `Realizations Table`
   - `Plan Seed Table`
   - `Activity Seed Table`
   - `Activity Dependency Table`
   - `Verification Surface Table`
   - `Constraints And Non-Goals`
3. Run governed doc lint.
4. Extract structured table seeds with the governance extractor.
5. Reconcile the component slice from the doc tables.
6. Validate both:
   - model/code presence proof
   - strict spec/model row agreement proof

## Commands

Governed docs:
```bash
bash /Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/docs/lint_governed_docs.sh
```

Strict proof check:
```bash
cd /Users/billyweisberg/Repos/billyweisberg/paa-platform && PYTHONPATH=packages/paa-core/src python scripts/governance/paa_component_spec_model_consistency.py --spec <spec-path>
```

Coarse model/code proof:
```bash
cd /Users/billyweisberg/Repos/billyweisberg/paa-platform && PYTHONPATH=packages/paa-core/src python scripts/governance/paa_model_code_consistency.py --component <ComponentName>
```

Type/lint safety:
```bash
cd /Users/billyweisberg/Repos/billyweisberg/paa-platform && basedpyright --project pyrightconfig.json packages/paa-core/src/paa_core/governance
```

## Current Proven Examples

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-workflow-lifecycle-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-execution-package-resolution-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-implementation-plan-repository-contract.md`

## Rules

- Fail closed if required tables are missing.
- Do not infer structured truth from prose when the template requires a table.
- Prefer reconciling an existing proof-slice plan over inventing a new orphan slice.
- Do not stop at count agreement when row-level agreement can be checked.
