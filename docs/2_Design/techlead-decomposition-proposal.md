# TechLead Decomposition Proposal

**Date**: 2026-05-22  
**Status**: Approved by Billy  
**Architect**: Grok (Lead Architect)

## Outcome Behavior
Transform the monolithic `techlead.py` (5794 lines) into a clean, OO, service-oriented hub following PAA Engineering Terminology.

## Target Components

1. **TechLeadHubStateService**  
   **Role**: Central authority for current workflow state, lineage view, worktree ownership, and staleness detection.

2. **TechLeadRoutingService**  
   **Role**: Owns all route policy evaluation and allowed next-role determination.

3. **TechLeadAssignmentDecisionService**  
   **Role**: Produces `techlead_assignment_packet` and handles assignment logic.

4. **TechLeadDecisionEngine**  
   **Role**: Core decision-making from spoke results to `techlead_decision_packet`.

5. **HandoffOrchestrator**  
   **Role**: Manages handoff lifecycle, DB, and queue coordination.

6. **WorkflowLifecycleManager**  
   **Role**: Owns terminal states, cleanup, and merge readiness.

7. **TechLeadInspectionService**  
   **Role**: Provides inspection surfaces for role automations.

8. **TechLeadResultProcessor**  
   **Role**: Validates incoming result packets.

## Current-State Component Node Diagram

```mermaid
flowchart TD
    subgraph paa_consumer["packages/paa-consumer/src/paa_consumer"]
        CLI["Thin Commands (commands.py)"]
        INBOX["inbox.py"]
        DELIVERY["delivery_runtime.py"]
        TECHLEAD["techlead.py (5794 lines - MONOLITH)"]:::monolith
    end

    TECHLEAD --> REPOS["paa-core Repositories"]
    TECHLEAD --> RMQ["RabbitMQ"]

    classDef monolith fill:#ffcccc,stroke:#990000,stroke-width:3px;
```

## Target-State Component Node Diagram

```mermaid
flowchart TD
    subgraph TyperLayer["Thin Typer CLI"]
        CLI["typer-di Commands"]
    end

    subgraph Services["paa_consumer Application Services"]
        HUB["TechLeadHubStateService"]
        ROUTING["TechLeadRoutingService"]
        ASSIGN["TechLeadAssignmentDecisionService"]
        DECISION["TechLeadDecisionEngine"]
        HANDOFF["HandoffOrchestrator"]
        LIFECYCLE["WorkflowLifecycleManager"]
        INSPECT["TechLeadInspectionService"]
        RESULT["TechLeadResultProcessor"]
    end

    CLI --> HUB & ROUTING & ASSIGN & DECISION
    HUB & ROUTING & HANDOFF & LIFECYCLE --> REPOS["paa-core"]
    DECISION --> ROUTING & HUB
```

**Next**: Proceed to detailed Component Designs starting with TechLeadHubStateService.