"""Entry point Streamlit: page config, cache model, dan inisialisasi session."""

from __future__ import annotations

import streamlit as st

from hotel_demo import ml
from hotel_demo.ui import (
    render_autorun_tab,
    render_comprehension_tab,
    render_executive_dashboard,
    render_guest_portal,
    render_header,
    render_sidebar,
    render_staff_portal,
    render_technical_suite,
    render_universal_action_bar,
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

    # Universal Action Bar & Next Action Guide on top of all views
    render_universal_action_bar(snapshot, simulation)

    # Clean Business-First Navigation with Dedicated Comprehension Suite
    tab_executive, tab_comprehension, tab_guest, tab_staff, tab_autorun, tab_technical = st.tabs(
        [
            "🏨 Dasbor Eksekutif & Cerita Kasus",
            "📖 Cara Kerja & Analogi Nyata",
            "🛎️ HP Tamu (Layanan Tamu)",
            "👔 Meja Kerja Staf Hotel",
            "🎬 Uji Seluruh Skenario",
            "🛠️ Mode Pengembang (Khusus IT)",
        ]
    )

    with tab_executive:
        render_executive_dashboard(snapshot, simulation, model)

    with tab_comprehension:
        render_comprehension_tab()

    with tab_guest:
        render_guest_portal(snapshot, simulation, model)

    with tab_staff:
        render_staff_portal(snapshot, simulation)

    with tab_autorun:
        render_autorun_tab(model)

    with tab_technical:
        render_technical_suite(snapshot, simulation, model)


main()
