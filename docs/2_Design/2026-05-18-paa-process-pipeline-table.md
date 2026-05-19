# PAA Process Pipeline Table

## Status
Draft.

## Purpose
This document captures the PAA pipeline as a role-oriented process table instead of a diagram.

The goal is to make the end-to-end flow easier to read and easier to challenge:
- from Tom's source note
- through authority and delivery design
- through governed execution authority
- through worker and QA execution
- to running code

## Process Table

| Step | Human Role | Process | PAA System Support | Output |
|---|---|---|---|---|
| 1 | Tom | Write source note / intent | None or simple document storage | Source note |
| 2 | Authority Architect | Interpret source note | Store and retrieve authority inputs | Interpreted authority intent |
| 3 | Authority Architect | Create system design | Persist design records | System design |
| 4 | Authority Architect | Define component model and dependency graph | Persist component records, relationships, and targets | Component model |
| 5 | Authority Architect | Select implementation slice | Record selected slice scope | Slice selection |
| 6 | Authority Architect | Materialize design package | Validate and persist package authority | Design package |
| 7 | Delivery Architect | Derive implementation plan | Persist implementation-plan root | Implementation plan |
| 8 | Delivery Architect | Derive implementation-plan activities | Persist activities and dependencies | Implementation-plan activities |
| 9 | Delivery Architect | Map activities to component, component element, and code artifact target | Persist structured mappings | Structured coder inputs |
| 10 | PAA System | Derive draft coder brief | Use package, plan, and activity mappings | Draft CoderBrief |
| 11 | PAA System + Architect or TechLead governance | Review and approve brief | Record authority lifecycle and approval | Approved CoderBrief |
| 12 | PAA System | Materialize packet-ready execution authority | Packetize approved authority | Packet-ready execution packet |
| 13 | TechLead | Choose next assignment target | Read current workflow and project state | Assignment decision |
| 14 | PAA System | Dispatch assignment | Queue packet, record handoff, record workflow truth | Assignment packet in queue |
| 15 | Worker Agent | Claim assignment and prepare workspace | Resolve execution context and install/runtime surfaces | Active worker execution context |
| 16 | Worker Agent | Generate or edit code | Tooling and runtime support | Working code changes |
| 17 | Worker Agent | Run local validation | Record evidence inputs if configured | Test and validation evidence |
| 18 | Worker Agent | Return result | Compile and send worker result packet | Worker result packet |
| 19 | PAA System | Apply workflow transition for worker result | Persist `worker_result_returned` transition | Updated workflow state |
| 20 | TechLead | Review worker result | Read workflow state and result evidence | QA routing or further decision |
| 21 | TechLead | Emit QA assignment | Select QA target and assignment | QA assignment decision |
| 22 | PAA System | Dispatch QA assignment | Queue packet, record handoff, update workflow truth | QA assignment packet |
| 23 | QA Agent | Claim and verify slice | Resolve execution context as needed | QA verification work |
| 24 | QA Agent | Return QA result | Compile and send `qa_verification_packet` | QA result packet |
| 25 | PAA System | Apply workflow transition for QA result | Persist `qa_result_returned` transition | Updated workflow state |
| 26 | TechLead | Accept, reject, reroute, or close | Read workflow truth, QA result, and merge state | Decision |
| 27 | PAA System | Record closeout and runtime state | Acceptance event, closeout, package/runtime update | Closed or advanced slice state |
| 28 | Runtime / Installed System | Resolve installed package and runtime surfaces | Execution package resolution | Running code |

## Simplified Human Chain

| Sequence | Human Role | Main Responsibility |
|---|---|---|
| 1 | Tom | Provide source intent |
| 2 | Authority Architect | Turn intent into system authority and slice authority |
| 3 | Delivery Architect | Turn slice authority into implementation plan and coder inputs |
| 4 | TechLead | Turn governed execution authority into live assignments |
| 5 | Worker Agent | Turn assignment into code and worker result |
| 6 | QA Agent | Turn built slice into verification result |
| 7 | TechLead | Turn verification result into acceptance, reroute, or closeout |

## What The PAA System Actually Is

| PAA System Is | Meaning |
|---|---|
| Authority store | Holds design package, plans, briefs, and workflow truth |
| Derivation engine | Produces structured execution authority from upstream records |
| Governance surface | Records draft, approved, and packet-ready transitions |
| Handoff system | Packetizes and dispatches work |
| Workflow system | Records authoritative lifecycle transitions |
| Execution-context resolver | Resolves install and runtime context for consumers |
| Closeout recorder | Records acceptance and terminal state |

## Most Important Bridge

| From | To | Why It Matters |
|---|---|---|
| System design | Design package | Narrows broad design into authoritative slice scope |
| Design package | Implementation plan | Turns authority into executable project design |
| Implementation plan | Implementation activities | Turns project design into ordered work |
| Activities | CoderBrief | Gives the coder agent enough structured instruction to generate code safely |

## Key Correction
The important human chain is:
- `Tom -> Authority Architect -> Delivery Architect -> TechLead -> Worker Agent -> QA Agent -> TechLead`

The PAA system is not a human role in that chain.
It is the control plane and record system that supports and governs the handoff between those roles.
