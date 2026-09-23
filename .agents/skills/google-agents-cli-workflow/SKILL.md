---
name: google-agents-cli-workflow
description: >-
  Use this skill when orchestrating multi-step agent workflows, managing
  simulation scenarios, or modifying the simulation engine. Covers the
  simulation lifecycle, case state machine, and agent orchestration.
---

# Workflow — Simulation & Orchestration

Skill for managing agent workflows and the simulation engine.

## When to Use
- Modifying the simulation engine (`simulation.py`)
- Changing case lifecycle or state transitions
- Orchestrating multi-agent interactions
- Adding or modifying scenarios (S01–S06)

## Case State Machine
```
CREATED → PROCESSING → WAITING_GUEST / WAITING_HUMAN
                       → HUMAN_HANDLING
                       → DIGITAL_COMPLETED / CLOSED_GUEST_DECLINED
                       / CLOSED_BY_STAFF / FAILED
```

## Ticket Lifecycle
```
PENDING → IN_PROGRESS → DONE
```
Tickets are separate from case status. Closing a case does NOT close tickets.

## Scenario Overview
| ID | Topic | Key Behavior |
|----|-------|--------------|
| S01 | AC broken, equal room | Migration, inspection, guest consent |
| S02 | AC broken, free upgrade | Migration + evidence, WAITING_HUMAN |
| S03 | Minibar billing dispute | Billing reads folio, mandatory escalation |
| S04 | Check-in time | FAQ answer, no ticket/migration |
| S05 | Request towels | Housekeeping ticket PENDING→DONE |
| S06 | Billing details | Show folio, no changes |

## Agent Roles
| Agent | Responsibility |
|-------|---------------|
| Scenario Scout | Classify incoming requests |
| Orchestrator | Route cases to appropriate agents |
| Reservation | Handle room changes and bookings |
| Billing | Read/manage folios |
| Concierge | Answer FAQs and simple requests |
| Operations | Manage room status and housekeeping |
| Mobile Investigator | Migrate between nodes to inspect rooms |

## Steps for Modifying Workflows
1. Edit `hotel_demo/simulation.py` for engine changes.
2. Edit `data/scenarios.json` for scenario data.
3. Edit `hotel_demo/agents.py` for agent behavior.
4. Validate:
   ```bash
   python -m pytest tests/test_scenarios.py -v
   python -m pytest -q
   ```
5. Commit locally.
