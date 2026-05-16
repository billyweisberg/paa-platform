# Stratum 2 Service Dependency Comparison

Date: 2026-05-15

## Purpose

Compare the three first-buildable Stratum 2 services from the layered component dependency graph and determine which one currently has the fewest unresolved sub-dependencies.

This note exists to replace “which one should we do next?” with a dependency-graph-based readiness comparison.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-component-dependency-graph.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-architecture-proposal.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-authority-package-authoring-process.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-workflow-state-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-runtime-event-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-execution-package-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md`

## Scope

This comparison evaluates the three services identified in the layered dependency graph as the earliest valid Stratum 2 logic-service candidates:
- `Workflow Lifecycle Service`
- `Execution Package Resolution Service`
- `Component Design Planning Service`

The comparison is based on:
- current design maturity
- current repository contract maturity
- current repository implementation maturity
- remaining unresolved policy or decomposition questions

It is not based on:
- preference
- perceived urgency
- current script pain

## Comparison Method

For each service, evaluate:
1. upstream domain-model maturity
2. upstream port-contract maturity
3. upstream port-implementation maturity
4. policy dependency maturity
5. unresolved decomposition questions
6. likely blast radius if implemented now

Each category is summarized as:
- `resolved`
- `partially resolved`
- `unresolved`

## Candidate 1. Component Design Planning Service

## Intended role
Translate stable component-design structures into structured implementation targets and planning outputs.

## Upstream dependencies from the graph
- `Authority Taxonomy Model`
- `ComponentDesignRepository`
- `StructuredLogger`

## Maturity assessment

### Domain-model maturity
- `resolved`

Reason:
The taxonomy side is already substantially modeled and documented through:
- `Component`
- `ComponentElementType`
- `ComponentElement`
- `CodeArtifactType`
- `CodeArtifactTarget`
- `CoderBrief` / `BriefTarget`

### Port-contract maturity
- `resolved`

Reason:
`ComponentDesignRepository` contract exists and is already fairly detailed.

### Port-implementation maturity
- `resolved` for the first meaningful slice

Reason:
`PostgresComponentDesignRepository` already exists with:
- read operations
- realization taxonomy upsert
- realization instance create/update
- brief realization target create/update

This is the most mature concrete repository implementation in the current DAL set.

### Policy dependency maturity
- `resolved` or not yet materially required

Reason:
This service does not currently depend on a separate unresolved policy object the way workflow-related services do.

### Unresolved decomposition questions
- `partially resolved`

Open questions remain around:
- how much of brief sequencing belongs here versus in `Brief Assembly Service`
- how much validation/promotion logic belongs here versus producer-side application services

But these are not fundamental blockers.

### Blast radius if implemented now
- `low`

Reason:
This service is strongly aligned with already-built taxonomy and repository work and has relatively contained upstream dependencies.

## Candidate 2. Execution Package Resolution Service

## Intended role
Resolve the effective execution-time package context for a work item and runtime surface.

## Upstream dependencies from the graph
- `Domain Core Model`
- `ExecutionPackageRepository`
- `DeploymentCapabilityPolicy`
- `StructuredLogger`

## Maturity assessment

### Domain-model maturity
- `resolved`

Reason:
The published-vs-installed execution package distinction is now well established.

### Port-contract maturity
- `resolved`

Reason:
`ExecutionPackageRepository` contract exists and is reasonably clear.

### Port-implementation maturity
- `partially resolved`

Reason:
The repository contract exists, but unlike `ComponentDesignRepository`, it does not yet have a concrete code implementation slice in place.

### Policy dependency maturity
- `unresolved`

Reason:
`DeploymentCapabilityPolicy` has been named in architecture, but not yet specified as a real component contract.

### Unresolved decomposition questions
- `partially resolved`

Open questions include:
- how much overlay resolution belongs in this service versus the repository
- how deployment capability constraints are expressed and injected

### Blast radius if implemented now
- `medium`

Reason:
The service is relatively compact, but it still depends on an unresolved policy contract and a not-yet-implemented repository adapter slice.

## Candidate 3. Workflow Lifecycle Service

## Intended role
Own workflow lifecycle semantics, transition legality, blocking rules, repair rules, and terminal decision rules.

## Upstream dependencies from the graph
- `Domain Core Model`
- `WorkflowTransitionPolicy`
- `AcceptancePolicy`
- `ResetRecoveryPolicy`
- `WorkflowStateRepository`
- `RuntimeEventRepository`
- `ExecutionPackageRepository`
- `TransactionRunner`
- `Clock`
- `StructuredLogger`

## Maturity assessment

### Domain-model maturity
- `partially resolved`

Reason:
The domain object model is strong enough to support this service, but the decomposition away from the earlier over-compressed `Workflow State Machine` is still fresh and not yet further split.

### Port-contract maturity
- `resolved`

Reason:
Relevant repository contracts exist.

### Port-implementation maturity
- `partially resolved`

Reason:
- `WorkflowStateRepository` contract exists, but no implementation exists yet.
- `RuntimeEventRepository` contract exists, but no implementation exists yet.
- `ExecutionPackageRepository` contract exists, but no implementation exists yet.

### Policy dependency maturity
- `unresolved`

Reason:
This service depends on multiple policy components that are named but not yet fully specified:
- `WorkflowTransitionPolicy`
- `AcceptancePolicy`
- `ResetRecoveryPolicy`

### Unresolved decomposition questions
- `unresolved`

Open questions include:
- exact split between lifecycle service and transition policy
- exact relationship to application services
- exact relationship to acceptance/verification logic
- exact treatment of repair and closeout semantics

### Blast radius if implemented now
- `high`

Reason:
This service sits at the center of the old hybrid mess and has the most upstream unresolved semantics. Implementing it too early would risk baking in assumptions that the newer architecture is explicitly trying to avoid.

## Comparison Matrix

| Service | Domain Model | Port Contracts | Port Implementations | Policy Maturity | Decomposition Clarity | Current Build Risk |
|---|---|---|---|---|---|---|
| `Component Design Planning Service` | resolved | resolved | resolved (first slice) | resolved / minimal | partially resolved | low |
| `Execution Package Resolution Service` | resolved | resolved | partially resolved | unresolved | partially resolved | medium |
| `Workflow Lifecycle Service` | partially resolved | resolved | partially resolved | unresolved | unresolved | high |

## Current Readiness Ranking

Based on unresolved sub-dependencies, the current readiness order is:

1. `Component Design Planning Service`
2. `Execution Package Resolution Service`
3. `Workflow Lifecycle Service`

## Why This Ranking Makes Sense

### 1. `Component Design Planning Service` comes first
It has:
- the most mature upstream structured model
- the most mature repository support
- the fewest unresolved policy dependencies
- the lowest blast radius

This makes it the earliest clean logic-service candidate.

### 2. `Execution Package Resolution Service` comes second
It is conceptually narrow and fairly mature, but it still depends on:
- a not-yet-real `DeploymentCapabilityPolicy`
- an `ExecutionPackageRepository` implementation that has not been built yet

### 3. `Workflow Lifecycle Service` comes third
It is important, but importance is not the same as readiness.

It still has the highest number of unresolved semantic and implementation dependencies, so the graph says it should not be first.

## Dependency-Graph Build Conclusion

If we are following the graph honestly, the next Stratum 2 implementation candidate should be:
- `Component Design Planning Service`

Followed by:
- `Execution Package Resolution Service`

And only after more prerequisite clarification should we move into:
- `Workflow Lifecycle Service`

## Process Conclusion

This note reinforces the method rule now recorded in the process document:
- the next component to build is determined by dependency readiness
- not by architectural importance alone
- and not by whichever current runtime script is most painful

That means the current graph is doing its job.
