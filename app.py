"""Entry point Streamlit: page config, cache model, dan inisialisasi session."""

from __future__ import annotations

import streamlit as st

from hotel_demo import ml
from hotel_demo.ui import (
    render_autorun_tab,
    render_evaluation_tab,
    render_guest_portal,
    render_header,
    render_landing_page,
    render_sidebar,
    render_simulation_tab,
    render_staff_portal,
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

    tab_beranda, tab_guest, tab_staff, tab_it, tab_simulation, tab_autorun, tab_evaluation = st.tabs(
        [
            "🏠 Beranda",
            "🛎️ Portal Tamu",
            "👔 Dashboard Staf",
            "💻 Konsol IT",
            "⚡ Lab Simulasi",
            "🎯 Uji Skenario",
            "📊 Evaluasi ML",
        ]
    )
    with tab_beranda:
        render_landing_page(model)
    with tab_guest:
        render_guest_portal(snapshot, simulation, model)
    with tab_staff:
        render_staff_portal(snapshot, simulation)
    with tab_it:
        render_trace_tab(snapshot, simulation)
    with tab_simulation:
        render_simulation_tab(snapshot, simulation)
    with tab_autorun:
        render_autorun_tab(model)
    with tab_evaluation:
        render_evaluation_tab(model)


main()
