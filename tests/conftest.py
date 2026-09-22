"""Fixture bersama untuk seluruh suite."""

import sys
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from hotel_demo import ml  # noqa: E402
from hotel_demo.simulation import Simulation  # noqa: E402


class StubModel:
    """Model stub untuk menguji jalur policy tanpa bergantung distribusi model kecil."""

    def __init__(self, probability: float) -> None:
        self.probability = probability
        self.report = {"stub": True, "probability": probability}

    def predict(self, features):  # noqa: ANN001, D401
        return self.probability


@pytest.fixture(scope="session")
def model():
    return ml.load_or_train()


@pytest.fixture
def stub_model_factory():
    return StubModel


@pytest.fixture
def make_sim(model):
    created = []

    def _make(scenario_id, mode="mobile", **kwargs):
        simulation = Simulation(mode=mode, scenario_id=scenario_id, model=model, **kwargs)
        created.append(simulation)
        return simulation

    yield _make
    for simulation in created:
        try:
            simulation.close()
        except Exception:  # pragma: no cover - pembersihan defensif
            pass


@pytest.fixture
def run_scenario(make_sim):
    def _run(scenario_id, mode="mobile", accept=None, max_steps=200):
        simulation = make_sim(scenario_id, mode)
        simulation.start_scenario()
        simulation.run_until_pause(max_steps=max_steps)
        if (
            accept is not None
            and simulation.case is not None
            and simulation.case.status == "WAITING_GUEST"
        ):
            simulation.submit_guest_choice(accept)
            simulation.run_until_pause(max_steps=max_steps)
        return simulation

    return _run
