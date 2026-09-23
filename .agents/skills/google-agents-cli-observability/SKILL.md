---
name: google-agents-cli-observability
description: >-
  Use this skill when debugging agent behavior, inspecting simulation traces,
  viewing event logs, or monitoring migration state. Covers the Jejak & State
  tab and internal logging.
---

# Observability — Tracing & Debugging

Skill for monitoring, tracing, and debugging agent behavior.

## When to Use
- Inspecting agent state during simulation
- Debugging migration failures (prepare/depart/arrive)
- Viewing event logs and traces
- Understanding why a case reached a certain status

## Steps

### 1. Use the Trace Tab
1. Start the app: `python -m streamlit run app.py`
2. Run a scenario (e.g., S01).
3. Click the **Jejak & State** tab.
4. Inspect:
   - Agent instance IDs (e.g., `MA-001`)
   - Migration count and current node
   - Checkpoint JSON with SHA-256 hash
   - Room inspection results (e.g., R102=DIRTY, R103=READY)

### 2. Key States to Monitor
| State | Meaning |
|-------|---------|
| `CREATED` | Case just opened |
| `PROCESSING` | Agents actively working |
| `WAITING_GUEST` | Waiting for guest consent |
| `WAITING_HUMAN` | Escalated — needs staff |
| `DIGITAL_COMPLETED` | Resolved automatically |
| `CLOSED_GUEST_DECLINED` | Guest declined the offer |

### 3. Migration Debugging
During migration, check:
- **PREPARE**: Transit area has checkpoint JSON with agent ID, case ID, goal, candidates, phase, SHA-256 hash, byte size.
- **DEPART**: `active_instance_count = 0`, `owner = None` — agent is in transit only.
- **ARRIVE**: ID preserved (e.g., `MA-001`), new instance object, node changed to `OPERATIONS`, `migration_count = 1`.

### 4. Test Observability
```bash
python -m pytest tests/test_migration.py -v
python -m pytest tests/test_scenarios.py -v
```

### 5. Simulation Event Log
The simulation engine (`simulation.py`) records events in order. Export via:
```python
simulation = st.session_state.get("simulation")
if simulation:
    log = simulation.export_log()  # returns list of event dicts
```
