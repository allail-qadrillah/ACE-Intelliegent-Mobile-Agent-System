---
name: google-agents-cli-scaffold
description: >-
  Use this skill when creating new modules, agents, tests, or data files
  from scratch. Provides templates and conventions for adding new components
  to the hotel_demo project structure.
---

# Scaffold — Project Scaffolding

Skill for creating new project components from templates.

## When to Use
- Adding a new agent module
- Creating a new test file
- Adding a new data file or scenario
- Creating new Streamlit UI components

## Templates

### New Agent (in `hotel_demo/agents.py`)
```python
class NewSpecialistAgent:
    """<describe role>."""

    def __init__(self, agent_id: str, node: str) -> None:
        self.agent_id = agent_id
        self.node = node
        self.state: dict = {}

    def handle(self, message: dict) -> dict:
        """Process incoming message and return response."""
        # implement agent logic here
        return {"status": "OK", "agent_id": self.agent_id}
```

### New Test File (in `tests/`)
```python
"""Tests for <module_name>."""
from __future__ import annotations

import pytest


class TestNewFeature:
    """Test suite for <feature>."""

    def test_basic_functionality(self) -> None:
        """Verify <what>."""
        # arrange
        # act
        # assert
        assert True

    def test_edge_case(self) -> None:
        """Verify <edge case>."""
        assert True
```

### New Scenario (in `data/scenarios.json`)
```json
{
  "id": "S07",
  "title": "<scenario title in Bahasa Indonesia>",
  "guest_message": "<guest message>",
  "expected_outcome": "<expected result>"
}
```

## Steps
1. Choose the appropriate template above.
2. Create the file in the correct directory.
3. Update imports in `__init__.py` if needed.
4. Add corresponding tests.
5. Run `python -m pytest -q` to verify.
6. Commit locally: `git add -A && git commit -m "<message>"`
