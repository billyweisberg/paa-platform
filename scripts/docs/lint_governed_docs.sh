#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

python "$REPO_ROOT/scripts/docs/paa_docs.py" lint \
  --root "$REPO_ROOT" \
  --path-prefix docs/2_Design/2026-05-17-workflow-lifecycle-service-component-spec.md \
  --path-prefix docs/2_Design/2026-05-17-execution-package-resolution-service-component-spec.md \
  --path-prefix docs/2_Design/2026-05-17-implementation-plan-derivation-service-component-spec.md \
  --path-prefix docs/2_Design/2026-05-17-implementation-plan-repository-contract.md \
  --path-prefix docs/2_Design/2026-05-17-project-delivery-projection-contract.md \
  --path-prefix docs/2_Design/2026-05-18- \
  --path-prefix docs/2_Design/2026-05-19-paa-governed-code-vocabulary-and-type-enforcement.md \
  --path-prefix docs/2_Design/2026-05-19-paa-model-to-code-and-runtime-consistency.md \
  --path-prefix docs/2_Design/2026-05-19-paa-projection-code-consistency.md \
  --path-prefix docs/2_Design/2026-05-19-governed-code-backed-component-materialization-policy.md \
  --path-prefix docs/2_Design/2026-05-20-component-spec-template-materialization-bridge.md \
  --path-prefix docs/2_Design/2026-05-20-component-spec-section-to-model-mapping-table.md \
  --path-prefix docs/2_Design/2026-05-20-workflow-lifecycle-component-spec-template-conformance-delta.md \
  --path-prefix docs/2_Design/2026-05-20-component-spec-doc-to-materialization-extraction-rules.md \
  --path-prefix docs/2_Design/2026-05-20-delivery-architect-component-spec-materialization-assignment-result-contract.md \
  --path-prefix docs/2_Design/2026-05-20-delivery-architect-proof-runner-cli-contract.md \
  --path-prefix docs/3_Plan/2026-05-20-delivery-architect-component-spec-materialization-proof-packet.md \
  --path-prefix docs/3_Plan/2026-05-18- \
  --path-prefix docs/4_Build/2026-05-03-architect-packet-compiler.md \
  --path-prefix docs/4_Build/2026-05-03-coder-brief-readiness-materializer.md \
  --path-prefix docs/4_Build/2026-05-03-dev-and-qa-packet-compilers.md \
  --path-prefix docs/4_Build/2026-05-03-paa-backed-architect-packet-brief-resolution.md \
  --path-prefix docs/4_Build/2026-05-16-assemble-coder-brief-flow.md \
  --path-prefix docs/4_Build/2026-05-16-author-brief-targets-flow.md \
  --path-prefix docs/4_Build/2026-05-16-derive-design-package-flow.md \
  --path-prefix docs/4_Build/2026-05-16-evaluate-derivation-readiness-flow.md \
  --path-prefix docs/4_Build/2026-05-16-review-coder-brief-flow.md \
  --path-prefix docs/4_Build/2026-05-17-derive-implementation-plan-flow.md \
  --path-prefix docs/4_Build/2026-05-19-materialize-governed-code-backed-components-flow.md \
  --path-prefix docs/4_Build/2026-05-17-prepare-architect-packet-flow.md \
  --path-prefix docs/5_Test/2026-05-17-execution-package-resolution-service-validation.md \
  --path-prefix docs/5_Test/2026-05-17-workflow-lifecycle-techlead-bridge-validation.md \
  --path-prefix docs/5_Test/2026-05-17-packet-ready-handoff-and-consumer-claim-validation.md \
  --path-prefix docs/5_Test/2026-05-17-self-hosted-consumer-runtime-validation.md \
  --path-prefix docs/5_Test/2026-05-17-proof-only-closeout-validation.md \
  --path-prefix docs/5_Test/2026-05-17-live-github-closeout-validation.md \
  --path-prefix docs/5_Test/2026-05-19-governed-proof-trio-full-chain-validation.md \
  --path-prefix docs/5_Test/2026-05-19-governed-proof-trio-model-code-validation.md \
  --path-prefix docs/5_Test/2026-05-19-governed-proof-trio-runtime-evidence-validation.md \
  --path-prefix docs/6_Deploy/2026-05-17-paa-db-cutover-plan.md \
  --path-prefix docs/6_Deploy/2026-05-17-paa-local-postgres-setup.md \
  --path-prefix docs/7_Monitor/2026-05-03-techlead-traceability-reporting.md \
  --path-prefix docs/terminology/2026-05-19-paa-language-governance-rules.md \
  --path-prefix docs/terminology/2026-05-19-paa-component-naming-rules.md \
  --path-prefix docs/terminology/2026-05-19-paa-status-claim-rules.md \
  --path-prefix docs/terminology/2026-05-19-paa-architecture-anti-patterns.md \
  --path-prefix docs/terminology/paa-engineering-terminology-glossary.md \
  --format table
