"""Entry point Streamlit: page config, cache model, dan inisialisasi session."""

from __future__ import annotations

import streamlit as st

from hotel_demo import ml
from hotel_demo.ui import (
    render_autorun_tab,
    render_header,
    render_sidebar,
    render_simulation_center,
    render_staff_portal,
    render_unified_evaluation_audit,
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

    # Clean Navigation
    st.markdown(
        """
        <style>
        [data-testid="stMainBlockContainer"]:has([data-testid="stTabs"]) {
            padding-bottom: 3rem !important;
        }
        [data-testid="stTabs"] div:has(> [data-baseweb="tab-list"]) {
            position: sticky;
            top: 3.75rem;
            z-index: 999;
            background: var(--background-color, #ffffff);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    tab_sim, tab_autorun, tab_staff, tab_eval = st.tabs(
        [
            "🎯 Simulasi & Layanan Tamu (Live Demo)",
            "⚡ Uji Otomatis Skenario (Autorun)",
            "👔 Meja Kerja Staf Hotel",
            "📊 Evaluasi, Bisnis & Audit DB",
        ]
    )

    with tab_sim:
        render_simulation_center(snapshot, simulation, model)

    with tab_autorun:
        render_autorun_tab(model)

    with tab_staff:
        render_staff_portal(snapshot, simulation)

    with tab_eval:
        render_unified_evaluation_audit(snapshot, simulation, model)


main()
