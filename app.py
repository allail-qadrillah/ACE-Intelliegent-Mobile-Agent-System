"""Entry point Streamlit: page config, cache model, dan inisialisasi session."""

from __future__ import annotations

import streamlit as st

from hotel_demo import ml
from hotel_demo.ui import (
    render_business_suite,
    render_header,
    render_sidebar,
    render_technical_suite,
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

    tab_suite_bisnis, tab_suite_teknis = st.tabs(
        [
            "👔 Mode Pure Bisnis (Operations & Executive Suite)",
            "🛠️ Mode Teknikal (Engineering & Architecture Console)",
        ]
    )

    with tab_suite_bisnis:
        render_business_suite(snapshot, simulation, model)

    with tab_suite_teknis:
        render_technical_suite(snapshot, simulation, model)


main()
