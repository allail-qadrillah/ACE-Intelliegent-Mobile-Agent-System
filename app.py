"""Entry point Streamlit: page config, cache model, dan inisialisasi session."""

from __future__ import annotations

import streamlit as st

from hotel_demo import ml
from hotel_demo.ui import (
    render_evaluation_tab,
    render_header,
    render_sidebar,
    render_simulation_tab,
    render_trace_tab,
)

st.set_page_config(page_title="Demo Mobile Agent Hotel", layout="wide")


@st.cache_resource(show_spinner=False)
def get_model() -> ml.MLModel:
    """Model read-only; rerun tidak melatih ulang."""
    return ml.load_or_train()


def main() -> None:
    model = get_model()
    render_header()
    render_sidebar(model)

    simulation = st.session_state.get("simulation")
    snapshot = simulation.snapshot() if simulation is not None else None

    tab_simulation, tab_trace, tab_evaluation = st.tabs(["Simulasi", "Jejak & State", "Evaluasi"])
    with tab_simulation:
        render_simulation_tab(snapshot, simulation)
    with tab_trace:
        render_trace_tab(snapshot, simulation)
    with tab_evaluation:
        render_evaluation_tab(model)


main()
