"""AC-01 dan AC-24: smoke test Streamlit dengan AppTest (tanpa browser)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest  # noqa: E402

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


def _app() -> AppTest:
    app = AppTest.from_file(str(APP_PATH), default_timeout=180)
    app.run()
    return app


def _simulation(app: AppTest):
    try:
        return app.session_state["simulation"]
    except KeyError:
        return None


def test_app_loads_without_side_effects():
    app = _app()
    assert not app.exception
    keys = {button.key for button in app.button}
    for scenario_id in ("S01", "S02", "S03", "S04", "S05", "S06"):
        assert f"scenario_{scenario_id}" in keys
    assert "reset_scenario" in keys
    assert _simulation(app) is None
    reset = [button for button in app.button if button.key == "reset_scenario"][0]
    assert reset.disabled is True


def test_rerun_is_read_only():
    app = _app()
    app.button(key="scenario_S01").click().run()
    assert not app.exception
    simulation = _simulation(app)
    assert simulation is not None
    assert simulation.step_index == 0

    before = dict(simulation.metrics)
    app.run()
    simulation = _simulation(app)
    assert dict(simulation.metrics) == before
    assert simulation.step_index == 0
    assert simulation.case is None


def test_step_button_advances_once_and_reset_is_clean():
    app = _app()
    app.button(key="scenario_S05").click().run()
    simulation = _simulation(app)
    assert simulation.has_pending_work() is True

    app.button(key="step_button").click().run()
    simulation = _simulation(app)
    assert simulation.step_index == 1
    assert simulation.case is not None

    app.button(key="reset_scenario").click().run()
    simulation = _simulation(app)
    assert simulation.step_index == 0
    assert simulation.case is None
    assert simulation.has_pending_work() is True
    assert not app.exception


def test_mode_radio_does_not_change_active_run():
    app = _app()
    app.button(key="scenario_S05").click().run()
    app.button(key="step_button").click().run()
    simulation = _simulation(app)
    assert simulation.active_mode == "mobile"

    app.radio(key="mode_radio").set_value("static").run()
    simulation = _simulation(app)
    assert simulation.active_mode == "mobile"
    assert not app.exception
