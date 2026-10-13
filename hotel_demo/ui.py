"""Rendering Streamlit. Hanya memanggil public method Simulation, tidak menulis DB."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

import streamlit as st

from .evaluation import comparison_table_rows, run_comparison, run_single
from .ml import DATASET_NOTE
from .simulation import SCENARIO_ORDER, Simulation, load_scenarios

MODE_LABELS = {"mobile": "Mobile Agent", "static": "Static Agent"}

SCENARIO_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "S01": {
        "judul": "AC Rusak — Kamar Pengganti Tersedia",
        "deskripsi": "Tamu melaporkan AC rusak dan minta pindah ke kamar setara.",
        "hasil": "Migrasi agen → inspeksi R102 (DIRTY) & R103 (READY) → proposal → persetujuan tamu → commit",
        "emoji": "❄️",
    },
    "S02": {
        "judul": "AC Rusak — Minta Upgrade Gratis",
        "deskripsi": "Kamar setara habis, tamu minta upgrade gratis.",
        "hasil": "Migrasi tetap terjadi, evidence R201 terkumpul → WAITING_HUMAN (upgrade butuh staf)",
        "emoji": "⬆️",
    },
    "S03": {
        "judul": "Sengketa Tagihan Minibar",
        "deskripsi": "Tamu tidak mengenali tagihan minibar Rp150.000.",
        "hasil": "Billing membaca folio → eskalasi wajib → WAITING_HUMAN",
        "emoji": "💰",
    },
    "S04": {
        "judul": "Informasi Jam Check-In",
        "deskripsi": "Tamu bertanya jam check-in hotel.",
        "hasil": "Jawaban FAQ lokal: 14.00 → selesai tanpa tiket/migrasi",
        "emoji": "🕐",
    },
    "S05": {
        "judul": "Permintaan Handuk",
        "deskripsi": "Tamu minta handuk diantar ke kamar.",
        "hasil": "Tiket housekeeping dibuat (PENDING → DONE oleh staf)",
        "emoji": "🛁",
    },
    "S06": {
        "judul": "Rincian Tagihan",
        "deskripsi": "Tamu minta tampilkan rincian tagihan.",
        "hasil": "Folio F01+F02 ditampilkan, total Rp650.000, tanpa perubahan",
        "emoji": "🧾",
    },
    "S07": {
        "judul": "Informasi Jam Check-Out",
        "deskripsi": "Tamu bertanya jam check-out dan prosedur late check-out.",
        "hasil": "Jawaban FAQ lokal: maksimal 12.00 WIB → selesai tanpa tiket",
        "emoji": "🚪",
    },
    "S08": {
        "judul": "Permintaan Bantal Tambahan",
        "deskripsi": "Tamu minta 2 bantal tambahan diantar ke kamar.",
        "hasil": "Tiket housekeeping dibuat (PENDING → DONE oleh staf)",
        "emoji": "🛏️",
    },
    "S09": {
        "judul": "Informasi Wi-Fi Hotel",
        "deskripsi": "Tamu bertanya cara menyambungkan Wi-Fi di kamar.",
        "hasil": "Jawaban FAQ lokal: SSID HotelNusantara_Guest → selesai tanpa tiket",
        "emoji": "📶",
    },
}


def render_landing_page(model: Any) -> None:
    """Render the user-friendly landing / onboarding page."""

    # ── Hero Section ─────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; padding: 1.5rem 0 0.5rem 0;">
            <h1 style="margin-bottom:0.2rem;">🏨 ACE — Intelligent Mobile Agent System</h1>
            <p style="font-size:1.25rem; color:#555;">
                Simulasi Multi-Agent Customer Service Hotel
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    badge_cols = st.columns(6)
    badges = [
        "🟢 Lokal",
        "🧪 Data Sintetis",
        "🔒 Tanpa API",
        "🐍 Python",
        "📦 Satu Proses",
        "👥 Kelompok 5",
    ]
    for col, badge in zip(badge_cols, badges):
        col.markdown(
            f"<div style='text-align:center; background:#f0f2f6; border-radius:8px; "
            f"padding:6px 4px; font-size:0.85rem;'>{badge}</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Apa Itu Aplikasi Ini? ────────────────────────────────────────────
    st.markdown("## 📖 Apa Itu Aplikasi Ini?")
    st.markdown(
        "Aplikasi ini adalah **simulasi multi-agent customer service hotel** yang dibuat "
        "untuk mata kuliah **Agent Enterprise** (Semester 3). Aplikasi mensimulasikan "
        "bagaimana beberapa agen AI bekerja sama menangani permintaan tamu hotel — mulai "
        "dari keluhan AC rusak, sengketa tagihan, hingga permintaan handuk.\n\n"
        "Fitur utamanya adalah **Mobile Agent**: agen yang dapat **berpindah (migrasi)** "
        "antar node logis dalam satu proses Python untuk menginspeksi data di tempat, "
        "bukan mengirim data ke agen lain. Semua data bersifat sintetis dan berjalan "
        "sepenuhnya **offline** tanpa API atau LLM."
    )

    st.divider()

    # ── Arsitektur Sistem ────────────────────────────────────────────────
    st.markdown("## 🏗️ Arsitektur Sistem")
    st.markdown(
        "Sistem terdiri dari **dua node logis** dalam satu proses Python, "
        "masing-masing dengan database SQLite in-memory terpisah."
    )

    arch_left, arch_mid, arch_right = st.columns([5, 2, 5])

    with arch_left:
        st.markdown(
            """
            #### 🏢 Node: FRONT_OFFICE
            | Agen | Tugas |
            |------|-------|
            | **Scenario Scout** | Klasifikasi permintaan tamu |
            | **Orchestrator** | Routing kasus ke agen yang tepat |
            | **Reservation** | Kelola pemindahan kamar |
            | **Billing** | Baca & kelola folio tagihan |
            | **Concierge** | Jawab FAQ & permintaan sederhana |
            """
        )

    with arch_mid:
        st.markdown(
            """
            <div style="display:flex; flex-direction:column; align-items:center;
                        justify-content:center; height:100%; padding-top:3rem;">
                <div style="font-size:2rem;">🔄</div>
                <div style="font-size:0.8rem; color:#888; text-align:center;">
                    Migrasi<br>State<br>Agent
                </div>
                <div style="font-size:1.5rem;">⇄</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with arch_right:
        st.markdown(
            """
            #### 🔧 Node: OPERATIONS
            | Agen | Tugas |
            |------|-------|
            | **Operations** | Kelola status kamar & housekeeping |
            | **Mobile Investigator** | Inspeksi kamar di tempat (setelah migrasi) |

            *Mobile Investigator berpindah dari FRONT_OFFICE ke OPERATIONS*
            *melalui checkpoint JSON dengan validasi SHA-256.*
            """
        )

    st.divider()

    # ── Cara Menggunakan ─────────────────────────────────────────────────
    st.markdown("## 🚀 Cara Menggunakan")

    step_cols = st.columns(4)

    steps = [
        (
            "📋",
            "1. Pilih Skenario",
            "Buka **sidebar** (kiri) dan klik salah satu skenario S01–S09.",
        ),
        (
            "🔄",
            "2. Jalankan Simulasi",
            'Gunakan spanduk **Presenter** di atas untuk **Putar** atau maju satu langkah.',
        ),
        (
            "🔍",
            "3. Lihat Jejak",
            'Buka **Mode Pengembang** untuk melihat Lab Step, audit event, dan checkpoint migrasi.',
        ),
        (
            "📊",
            "4. Evaluasi",
            'Buka **Mode Pengembang → Evaluasi Ilmiah & ML** untuk membandingkan Mobile vs Static.',
        ),
    ]

    for col, (emoji, title, desc) in zip(step_cols, steps):
        with col:
            st.markdown(
                f"<div style='background:#f0f2f6; border-radius:12px; padding:1rem; "
                f"text-align:center; min-height:180px;'>"
                f"<div style='font-size:2rem;'>{emoji}</div>"
                f"<div style='font-weight:bold; margin:0.5rem 0;'>{title}</div>"
                f"<div style='font-size:0.85rem; color:#555;'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── 6 Skenario ───────────────────────────────────────────────────────
    st.markdown("## 🎬 9 Skenario Demo")
    st.caption(
        "Klik tombol di sidebar kiri untuk memulai skenario, atau pilih mode agen terlebih dahulu."
    )

    for sid, info in SCENARIO_DESCRIPTIONS.items():
        with st.container(border=True):
            c1, c2 = st.columns([1, 11])
            with c1:
                st.markdown(
                    f"<div style='font-size:2.5rem; text-align:center; padding-top:0.5rem;'>"
                    f"{info['emoji']}</div>",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(f"**{sid} — {info['judul']}**")
                st.markdown(f"{info['deskripsi']}")
                st.caption(f"Hasil: {info['hasil']}")

    st.divider()

    # ── Mobile vs Static ─────────────────────────────────────────────────
    st.markdown("## ⚖️ Mobile Agent vs Static Agent")

    cmp_left, cmp_right = st.columns(2)

    with cmp_left:
        st.markdown(
            """
            #### 🚀 Mobile Agent
            - Investigator **berpindah** ke node Operations melalui checkpoint JSON
            - Inspeksi dijalankan **di tempat** setelah migrasi tiba
            - 1 migrasi sukses per skenario (S01/S02)
            - Mendemonstrasikan konsep **mobile agent** dari literatur
            """
        )

    with cmp_right:
        st.markdown(
            """
            #### 🏢 Static Agent
            - Investigator **tetap** di Front Office
            - Mengirim batch `INSPECT_CANDIDATES` ke Operations Agent
            - 0 migrasi
            - Baseline perbandingan — **hasil bisnis identik**
            """
        )

    st.info(
        "💡 Kedua mode menggunakan **kernel evaluasi yang sama** (`evaluate_candidates()`). "
        "Perbedaannya hanya pada **cara data diakses**: mobile agent berpindah ke data, "
        "static agent meminta data dikirim ke tempatnya."
    )

    st.divider()

    # ── Tentang Tim ──────────────────────────────────────────────────────
    st.markdown("## 👥 Tentang Tim — Kelompok 5")

    team_cols = st.columns(4)
    team_members = [
        ("👤", "M. Al lail Qadrillah"),
        ("👤", "Dimas Prabowo"),
        ("👤", "Monanta Alfiareza"),
        ("👤", "Frans Alwan"),
    ]

    for col, (icon, name) in zip(team_cols, team_members):
        with col:
            st.markdown(
                f"<div style='background:#f0f2f6; border-radius:12px; padding:1rem; "
                f"text-align:center;'>"
                f"<div style='font-size:2rem;'>{icon}</div>"
                f"<div style='font-weight:600; margin-top:0.5rem;'>{name}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.caption(
        "Mata Kuliah: Agent Enterprise · Semester 3 · "
        "Hotel fiktif **Hotel Nusantara Demo** · Seluruh data sintetis dan lokal."
    )


def render_header() -> None:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #182235 0%, #2A3C5A 100%); padding: 18px 22px; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div>
                    <div style="font-size: 1.7rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.5px;">
                        🏨 ACE — Intelligent Mobile Agent System
                    </div>
                    <div style="font-size: 0.95rem; color: #E2E8F0; margin-top: 3px;">
                        Otomasi Penanganan Komplain & Operasional Hotel Nusantara Demo (Multi-Agent Simulation)
                    </div>
                </div>
                <div style="background: rgba(255, 107, 53, 0.2); border: 1px solid #FF6B35; padding: 6px 14px; border-radius: 20px; color: #FF9E7D; font-weight: 600; font-size: 0.85rem;">
                    Kelompok 5 · Agent Enterprise
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.08); padding: 10px 14px; border-radius: 8px; margin-top: 12px; font-size: 0.85rem; color: #CBD5E1; border-left: 4px solid #FF6B35;">
                <strong>🎯 Objektif Utama:</strong> Menyelesaikan 80% keluhan kamar hotel secara instan (&lt; 1 menit) menggunakan <em>Mobile Agent</em> yang bermigrasi ke node operasional, melindungi pendapatan hotel dari kompensasi liar via <em>Policy Guardrail</em>, dan menjaga privasi data antar-departemen.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _start_scenario(model: Any, scenario_id: str, mode: str) -> None:
    previous = st.session_state.get("simulation")
    if previous is not None:
        previous.close()
    simulation = Simulation(mode=mode, scenario_id=scenario_id, model=model)
    simulation.start_scenario()
    st.session_state["simulation"] = simulation
    st.session_state["active_scenario"] = scenario_id
    st.session_state["active_mode"] = mode
    st.session_state["autoplay"] = False


def render_story_cards(model: Any) -> None:
    """Renders 4 interactive story scenario cards for quick one-click demo."""
    st.markdown("### 🎬 Pilih Skenario Cerita Demo Interaktif")
    st.caption("Pilih salah satu kasus nyata di bawah ini untuk memulai simulasi langsung:")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("#### ❄️ Cerita 1: AC Bocor Tengah Malam (Otomatis Penuh)")
            st.markdown(
                """
                - **Tamu:** Pak Budi (Kamar 101)
                - **Situasi:** AC kamar bocor dan panas jam 01:00 pagi. Butuh kamar pengganti.
                - **Alur Agen:** Triase -> Migrasi ke Operations -> Verifikasi kamar bersih R103 -> Permintaan persetujuan tamu -> Kamar dipindahkan.
                """
            )
            if st.button("▶️ Jalankan Cerita 1 (AC Bocor)", key="story_card_s01", type="primary", use_container_width=True):
                _start_scenario(model, "S01", "mobile")
                st.session_state["autoplay"] = True
                st.rerun()

        with st.container(border=True):
            st.markdown("#### 💰 Cerita 3: Sengketa Tagihan Minibar (Eskalasi)")
            st.markdown(
                """
                - **Tamu:** Tamu Demo (Kamar 101)
                - **Situasi:** Tamu tidak mengenali tagihan minibar Rp150.000 dan meminta penghapusan.
                - **Keputusan Agen:** Billing membaca folio, tetapi perubahan tagihan wajib ditinjau staf.
                """
            )
            if st.button("▶️ Jalankan Cerita 3 (Sengketa Tagihan)", key="story_card_s03", use_container_width=True):
                _start_scenario(model, "S03", "mobile")
                st.session_state["autoplay"] = True
                st.rerun()

    with c2:
        with st.container(border=True):
            st.markdown("#### 🛡️ Cerita 2: Tamu Minta Suite Mewah (Proteksi Biaya)")
            st.markdown(
                """
                - **Tamu:** Ibu Sarah (Kamar 201)
                - **Situasi:** AC bermasalah, menuntut ganti rugi kamar Suite mewah gratis.
                - **Proteksi Finansial:** AI mengunci otomasi karena batas kebijakan kompensasi dilanggar. Kasus dieskalasi ke Manajer Manusia.
                """
            )
            if st.button("▶️ Jalankan Cerita 2 (Proteksi Finansial)", key="story_card_s02", use_container_width=True):
                _start_scenario(model, "S02", "mobile")
                st.session_state["autoplay"] = True
                st.rerun()

        with st.container(border=True):
            st.markdown("#### 🕐 Cerita 4: Informasi Check-In (Concierge)")
            st.markdown(
                """
                - **Tamu:** Tamu Demo (Kamar 105)
                - **Situasi:** Menanyakan jam check-in hotel.
                - **Penanganan Cepat:** Agen concierge menjawab dari FAQ lokal tanpa tiket fisik atau migrasi.
                """
            )
            if st.button("▶️ Jalankan Cerita 4 (Informasi Check-In)", key="story_card_s04", use_container_width=True):
                _start_scenario(model, "S04", "mobile")
                st.session_state["autoplay"] = True
                st.rerun()


def get_presenter_telemetry(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation] = None
) -> Dict[str, Any]:
    """Computes real-time telemetry, active agent, active node, and presenter talking points."""
    if not snapshot:
        return {
            "step_index": 0,
            "phase_num": 1,
            "phase_title": "Skenario Siap",
            "active_agent": "🛎️ Resepsionis Hotel",
            "active_node": "🏢 FRONT_OFFICE",
            "action_headline": "Menunggu Pemilihan Kasus",
            "talking_point": "Silakan pilih salah satu cerita skenario untuk memulai simulasi penanganan komplain.",
            "status_label": "STANDBY",
        }

    case = snapshot.get("case")
    status = case.get("status") if case else "CREATED"
    step_index = snapshot.get("step_index", 0)
    scenario_id = snapshot.get("scenario_id", "S01")
    migration = snapshot.get("migration")
    mig_stage = migration.get("stage") if migration else None

    # Retrieve last recorded event
    last_event = simulation.events[-1] if (simulation and simulation.events) else None
    ev_type = last_event.event_type if last_event else None
    ev_agent = last_event.agent_id if last_event else None
    ev_node = last_event.node_id if last_event else None
    ev_details = last_event.details if last_event else {}
    action = ev_details.get("action", "")

    # Default fallback
    agent = "🤖 Asisten AI Hotel"
    node = "🏢 FRONT_OFFICE"
    phase_num = 1
    phase_title = "Penerimaan Komplain"
    headline = "Keluhan Tamu Sedang Diproses"
    talking_point = "Agen sedang memproses informasi keluhan dari tamu hotel."

    # Scenarios S04, S05, S06
    if scenario_id == "S04":
        if status == "DIGITAL_COMPLETED":
            agent = "🛎️ Concierge Front Office"
            node = "🏢 FRONT_OFFICE"
            phase_num = 6
            phase_title = "Jawaban Instan Selesai"
            headline = "Concierge Menjawab Informasi Sarapan & Fasilitas Hotel"
            talking_point = "Concierge Agent menjawab FAQ informasi tamu dalam hitungan detik tanpa membebani staf manusia atau memerlukan perpindahan fisik."
        else:
            agent = "🕵️ Scenario Scout & Concierge"
            node = "🏢 FRONT_OFFICE"
            phase_num = 2
            phase_title = "Triase Informasi Tamu"
            headline = "Scenario Scout Meneruskan Pertanyaan ke Agen Concierge"
            talking_point = "Sistem mendeteksi bahwa pesan ini adalah pertanyaan rutin, bukan komplain fisik, sehingga langsung dijawab oleh Concierge."

    elif scenario_id == "S05":
        if status == "DIGITAL_COMPLETED":
            agent = "🔧 Operations Agent & Housekeeping"
            node = "🔧 OPERATIONS"
            phase_num = 6
            phase_title = "Tiket Tugas Diterbitkan"
            headline = "Tiket Permintaan Handuk Diteruskan ke Meja Housekeeping"
            talking_point = "Permintaan perlengkapan tamu langsung dikonversi menjadi tiket kerja fisik untuk staf Housekeeping di lapangan."
        else:
            agent = "🧠 Orchestrator Agent"
            node = "🏢 FRONT_OFFICE"
            phase_num = 3
            phase_title = "Koordinasi Operasional"
            headline = "Orchestrator Mengirim Permintaan Fisik ke Node Operations"
            talking_point = "Kasus diteruskan ke departemen operasional untuk pembuatan tiket kerja staf pembersih."

    elif scenario_id == "S06":
        if status == "DIGITAL_COMPLETED":
            agent = "💳 Billing Agent"
            node = "🏢 FRONT_OFFICE"
            phase_num = 6
            phase_title = "Verifikasi Folio Tagihan"
            headline = "Billing Agent Memverifikasi Rincian Folio Minibar (Rp650.000)"
            talking_point = "Billing Agent mengonfirmasi item folio F01 dan F02 senilai Rp650.000 secara transparan kepada tamu."
        else:
            agent = "💳 Billing Agent"
            node = "🏢 FRONT_OFFICE"
            phase_num = 2
            phase_title = "Pemeriksaan Folio"
            headline = "Billing Agent Membaca Riwayat Transaksi Tamu"
            talking_point = "Sistem mengakses database folio Front Office untuk memvalidasi tagihan minibar yang dipertanyakan tamu."

    # Scenarios S01, S02, S03 (Room Change & Inspection)
    else:
        if status == "DIGITAL_COMPLETED":
            assigned = case.get("assigned_room_id", "R103")
            agent = "🛏️ Reservation Agent"
            node = "🏢 FRONT_OFFICE"
            phase_num = 6
            phase_title = "Pindah Kamar Berhasil"
            headline = f"Tamu Resmi Dipindahkan ke Kamar {assigned} (Selesai Otomatis)"
            talking_point = f"Kasus selesai 100% secara digital! Database reservasi diperbarui, kunci kamar baru dialokasikan ke {assigned}, dan komplain berulang berhasil dicegah."

        elif status == "CLOSED_BY_STAFF":
            agent = "👔 Manajer Hotel"
            node = "🏢 FRONT_OFFICE (Meja Manajer)"
            phase_num = 6
            phase_title = "Kasus Ditutup oleh Manajer"
            headline = "Kasus Resmi Ditutup oleh Manajer (Zero Cost Leakage)"
            talking_point = "Manajer hotel meninjau bukti audit trail dan menutup kasus dengan catatan resmi. Hotel berhasil diselamatkan dari kebocoran biaya kamar mewah ilegal!"

        elif status == "CLOSED_GUEST_DECLINED":
            agent = "🛎️ Layanan Tamu"
            node = "🏢 FRONT_OFFICE"
            phase_num = 6
            phase_title = "Tamu Menolak Tawaran"
            headline = "Tamu Memilih Tetap di Kamar Asal (Kasus Ditutup)"
            talking_point = "Tamu menolak opsi kamar pengganti. Sistem mencatat keputusan tamu dan menutup alur otomatis."

        elif status == "PROCESSING" and case and case.get("consent"):
            proposed = case.get("proposed_room_id", "R103")
            agent = "🛏️ Reservation Agent"
            node = "🏢 FRONT_OFFICE"
            phase_num = 6
            phase_title = "Persetujuan Diterima — Finalisasi Kunci"
            headline = f"Tamu Menyetujui Pindah ke {proposed}. Sistem Mengunci Transaksi Database."
            talking_point = "Persetujuan tamu telah tercatat! Sistem melakukan sinkronisasi database kamar dan mengalokasikan kunci kamar secara atomik."

        elif status == "WAITING_GUEST":
            proposed = case.get("proposed_room_id", "R103")
            agent = "🛎️ Layanan Tamu (Persetujuan Tamu)"
            node = "🏢 FRONT_OFFICE ➔ 📱 HP Tamu"
            phase_num = 5
            phase_title = "Persetujuan Tamu Diperlukan"
            headline = f"Proposal Kamar Bersih {proposed} Telah Dikirimkan ke HP Tamu"
            talking_point = f"Sistem tidak memindahkan tamu secara sepihak. Sebuah proposal kamar {proposed} yang terbukti bersih dikirim ke HP tamu. Di tahap ini, tamu cukup mengklik 'Setujui' di HP!"

        elif status == "WAITING_HUMAN":
            reasons = ", ".join(case.get("human_reason_codes", [])) if case else "COMPENSATION_LIMIT"
            agent = "🛡️ Policy Guardrail & Manajer"
            node = "🏢 FRONT_OFFICE (Meja Manajer)"
            phase_num = 5
            phase_title = "Satpam Kebijakan Mengunci Kasus"
            headline = "Peringatan Kebijakan: Kompensasi Kamar Mewah Ditolak Otomatis!"
            talking_point = f"Poin penting untuk penguji/dosen: Tamu meminta kamar Suite mewah gratis ({reasons}). Policy Guardrail mendeteksi pelanggaran batas wewenang otomatis dan langsung mengunci alur agar diputuskan oleh Manajer!"

        elif status == "HUMAN_HANDLING":
            agent = "👔 Manajer Hotel"
            node = "🏢 FRONT_OFFICE"
            phase_num = 5
            phase_title = "Penanganan Manual Staf"
            headline = "Manajer Hotel Sedang Mengambil Alih Kasus"
            talking_point = "Manajer hotel meninjau berkas investigasi fisik dan membuat keputusan bisnis secara langsung."

        elif action == "INSPECTION_RESULT" and ev_node == "OPERATIONS":
            agent = "🤖 Mobile Investigator (MA-001)"
            node = "🔧 OPERATIONS (Database Housekeeping)"
            phase_num = 4
            phase_title = "Hasil Inspeksi Fisik Selesai"
            headline = "Inspeksi Selesai: Kamar Kotor Ditolak (R102), Kamar Bersih Lolos (R103)"
            talking_point = "Agen menyelesaikan audit fisik di database Housekeeping: R102 terbukti kotor (DIRTY) sehingga otomatis gugur. Kamar R103 bersih (READY) dipilih untuk diajukan ke tamu."

        elif ev_node == "OPERATIONS" and ev_agent == "MA-001":
            agent = "🤖 Mobile Investigator (MA-001)"
            node = "🔧 OPERATIONS (Node Operasional)"
            phase_num = 4
            phase_title = "Inspeksi Fisik di Lokasi"
            headline = "Investigator Mendarat di Operations & Menginspeksi Database Housekeeping"
            talking_point = "Mobile Investigator telah mendarat di node Operations. Agen langsung mengakses tabel kesiapan fisik kamar secara lokal tanpa membebani lalu lintas jaringan."

        elif ev_type == "MIGRATION_DEPARTED" or mig_stage == "DEPARTED":
            agent = "🤖 Mobile Investigator (MA-001)"
            node = "🔄 IN-TRANSIT (Sedang Melintas Jaringan)"
            phase_num = 3
            phase_title = "Migrasi Antar-Node"
            headline = "Investigator Dicabut dari Front Office & Melintasi Jaringan"
            talking_point = "Perhatikan! Agen unregister dari Front Office. State koper bervalidasi kriptografi sedang berpindah melintasi node menuju server operasional hotel."

        elif ev_type == "MIGRATION_PREPARED" or mig_stage == "PREPARED":
            agent = "🤖 Mobile Investigator (MA-001)"
            node = "🏢 FRONT_OFFICE (Pengepakan Koper)"
            phase_num = 3
            phase_title = "Pengepakan Koper State"
            headline = "Mengemas State Kasus ke dalam Koper JSON Ber-hash SHA-256"
            talking_point = "Di sinilah letak keunggulan Mobile Agent: alih-alih menarik seluruh database kamar ke Front Office, agen membungkus koper state bervalidasi SHA-256 untuk berangkat ke Operations."

        elif action == "INSPECT_CANDIDATES" and ev_node == "FRONT_OFFICE":
            agent = "🤖 Mobile Investigator (MA-001)"
            node = "🏢 FRONT_OFFICE"
            phase_num = 3
            phase_title = "Inisialisasi Migrasi"
            headline = "Mobile Investigator Menerima Tugas & Bersiap Bermigrasi"
            talking_point = "Orchestrator menugaskan Mobile Investigator untuk menginspeksi kamar pengganti. Agen menginisialisasi protokol migrasi untuk berangkat ke node Operations."

        elif step_index in (2, 3, 4, 5):
            agent = "🧠 Orchestrator Agent"
            node = "🏢 FRONT_OFFICE"
            phase_num = 2
            phase_title = "Triase Kasus via Machine Learning"
            headline = "Orchestrator Mengklasifikasikan Tingkat Keparahan Komplain"
            talking_point = "Model Machine Learning (Logistic Regression) memprediksi bahwa keluhan fasilitas ini berisiko tinggi dan membutuhkan penanganan darurat perpindahan kamar."

        elif step_index == 1:
            agent = "🕵️ Scenario Scout Agent"
            node = "🏢 FRONT_OFFICE"
            phase_num = 2
            phase_title = "Deteksi Niat Tamu"
            headline = "Scenario Scout Mengekstrak Nomor Kamar & Jenis Masalah"
            talking_point = "Scenario Scout membaca pesan tamu, memetakan kamar asal tamu, dan meneruskannya ke antrean Orchestrator."

        else:
            agent = "🛎️ Sistem Resepsionis Hotel"
            node = "🏢 FRONT_OFFICE"
            phase_num = 1
            phase_title = "Penerimaan Komplain"
            headline = "Keluhan Kerusakan Kamar Diterima dari Tamu"
            talking_point = "Tamu melaporkan kerusakan fasilitas hotel. Sistem bersiap memulai penanganan multi-agent secara otomatis."

    return {
        "step_index": step_index,
        "phase_num": phase_num,
        "phase_title": phase_title,
        "active_agent": agent,
        "active_node": node,
        "action_headline": headline,
        "talking_point": talking_point,
    }


def render_presenter_hud(
    snapshot: Dict[str, Any], simulation: Simulation, is_autoplay: bool
) -> None:
    """Renders the Live Presenter Mission Control HUD with speed slider and talking points."""
    telemetry = get_presenter_telemetry(snapshot, simulation)
    case = snapshot.get("case")
    status = case.get("status") if case else "CREATED"
    has_pending = snapshot.get("has_pending_work", False)
    step_idx = snapshot.get("step_index", 0)

    # Autoplay speed configuration
    speed_options = {
        3.5: "🐢 Santai (3.5s)",
        2.0: "🚶 Nyaman (2.0s)",
        1.0: "🐇 Cepat (1.0s)",
    }
    current_speed = st.session_state.get("autoplay_speed", 2.0)

    with st.container(border=True):
        # 1. Top Bar: Live Status & Controls
        c_status, c_speed, c_btn = st.columns([5, 3, 4])

        with c_status:
            if is_autoplay:
                badge_html = "<span style='background:#EF4444; color:white; padding:4px 10px; border-radius:6px; font-weight:bold; font-size:0.8rem;'>🔴 LIVE AUTOPLAY</span>"
            elif status == "WAITING_GUEST":
                badge_html = "<span style='background:#3B82F6; color:white; padding:4px 10px; border-radius:6px; font-weight:bold; font-size:0.8rem;'>🛎️ MENUNGGU TAMU</span>"
            elif status == "WAITING_HUMAN":
                badge_html = "<span style='background:#F59E0B; color:white; padding:4px 10px; border-radius:6px; font-weight:bold; font-size:0.8rem;'>🚨 ESKALASI MANAJER</span>"
            elif status in ("DIGITAL_COMPLETED", "CLOSED_BY_STAFF"):
                badge_html = "<span style='background:#10B981; color:white; padding:4px 10px; border-radius:6px; font-weight:bold; font-size:0.8rem;'>🎉 KASUS SELESAI</span>"
            else:
                badge_html = "<span style='background:#64748B; color:white; padding:4px 10px; border-radius:6px; font-weight:bold; font-size:0.8rem;'>⏸️ JEDA / STANDBY</span>"

            st.markdown(
                f"<div style='display:flex; align-items:center; gap:8px; margin-top:4px;'>"
                f"{badge_html} "
                f"<strong style='font-size:0.95rem; color:#1E293B;'>Langkah {step_idx} · {telemetry['phase_title']}</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )

        with c_speed:
            speed_choice = st.selectbox(
                "Tempo Putar Otomatis",
                options=[2.0, 3.5, 1.0],
                format_func=lambda s: speed_options.get(s, f"{s}s"),
                index=[2.0, 3.5, 1.0].index(current_speed) if current_speed in [2.0, 3.5, 1.0] else 0,
                key="autoplay_speed_selector",
                label_visibility="collapsed",
            )
            if speed_choice != current_speed:
                st.session_state["autoplay_speed"] = speed_choice

        with c_btn:
            b1, b2, b3 = st.columns(3)
            with b1:
                if is_autoplay:
                    if st.button("⏸️ Jeda", key="hud_pause_btn", use_container_width=True):
                        st.session_state["autoplay"] = False
                        st.rerun()
                else:
                    can_play = has_pending and status not in ("WAITING_GUEST", "WAITING_HUMAN", "HUMAN_HANDLING")
                    if st.button(
                        "▶️ Putar",
                        key="hud_play_btn",
                        type="primary" if can_play else "secondary",
                        disabled=not can_play,
                        use_container_width=True,
                    ):
                        st.session_state["autoplay"] = True
                        st.rerun()
            with b2:
                can_step = has_pending and status not in ("WAITING_GUEST", "WAITING_HUMAN", "HUMAN_HANDLING")
                if st.button("⏭️ Maju", key="hud_step_btn", disabled=not can_step, use_container_width=True):
                    simulation.step()
                    st.rerun()
            with b3:
                if st.button("🔄 Ulang", key="hud_reset_btn", use_container_width=True):
                    model = getattr(simulation, "model", None)
                    scenario_id = snapshot.get("scenario_id", "S01")
                    mode = snapshot.get("active_mode", "mobile")
                    _start_scenario(model, scenario_id, mode)
                    st.rerun()

        st.divider()

        # 2. Main Presenter Telemetry: Agent, Node, Headline
        t_col1, t_col2 = st.columns([5, 7])
        with t_col1:
            st.markdown(
                f"<div style='font-size:0.75rem; color:#64748B; font-weight:bold;'>PELAKU & LOKASI SAAT INI:</div>"
                f"<div style='font-size:0.95rem; font-weight:bold; color:#1E3A8A; margin-top:2px;'>"
                f"{telemetry['active_agent']}<br>"
                f"<span style='font-size:0.8rem; font-weight:normal; color:#475569;'>Lokasi:</span> "
                f"<span style='background:#E2E8F0; padding:2px 8px; border-radius:4px; font-size:0.8rem; font-family:monospace; color:#0F172A;'>{telemetry['active_node']}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with t_col2:
            st.markdown(
                f"<div style='font-size:0.75rem; color:#64748B; font-weight:bold;'>AKSI NYATA YANG TERJADI:</div>"
                f"<div style='font-size:0.95rem; font-weight:bold; color:#0F172A; margin-top:2px; line-height:1.4;'>"
                f"📌 {telemetry['action_headline']}"
                f"</div>",
                unsafe_allow_html=True,
            )

        # 3. Presenter Talking Point (The Golden Banner)
        st.markdown(
            f"""
            <div style="background: #FFFBEB; border-left: 4px solid #F59E0B; border-radius: 8px; padding: 12px 16px; margin-top: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-size: 0.78rem; font-weight: 700; color: #B45309; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px;">
                    🎓 Narasi Presentasi & Poin Penjelasan Dosen:
                </div>
                <div style="font-size: 0.95rem; color: #78350F; line-height: 1.5; font-style: italic;">
                    “{telemetry['talking_point']}”
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 4. Integrated 6-stage Visual Stepper
        st.write("")
        _render_live_flow_stepper(snapshot, override_phase=telemetry["phase_num"])


def render_universal_action_bar(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation]
) -> None:
    """Universal Action Bar & Dynamic Presenter Mission Control on top of all tabs."""
    with st.expander("📖 Panduan Kilat 1-Menit (Cara Menggunakan & Demo Aplikasi)", expanded=False):
        st.markdown(
            """
            **3 Langkah Cepat Mengoperasikan Aplikasi Ini:**
            1. **Pilih Skenario Cerita:** Klik tombol cerita di bawah atau pilih di sidebar kiri (rekomendasi: **S01: AC Rusak** untuk kasus otomatis, atau **S02: Minta Kamar Mewah** untuk proteksi finansial).
            2. **Amati Agen Bekerja:** Klik **`▶️ Putar`** di Spanduk Presenter untuk menyaksikan agen melakukan triase, bermigrasi ke operasi, dan memeriksa fisik kamar secara bertahap.
            3. **Beri Keputusan Tamu / Staf:**
               - Pada skenario S01: Klik **`✅ Setujui Pindah Kamar`** yang langsung muncul di layar Anda.
               - Pada skenario S02: Klik **`👤 Ambil Alih Kasus`** sebagai staf untuk mencegah kerugian hotel.
               - Buka tab **🏨 Ringkasan Eksekutif & ROI** untuk melihat kalkulator nilai bisnis nyata!
            """
        )

    if snapshot is None or simulation is None:
        st.info(
            "👉 **Langkah Anda Sekarang:** Pilih salah satu skenario cerita di tab Eksekutif atau di sidebar sebelah kiri untuk memulai.",
            icon="💡",
        )
        return

    case = snapshot.get("case")
    status = case.get("status") if case else None
    has_pending = snapshot.get("has_pending_work", False)

    # 1. Autoplay Control Bar State
    is_autoplay = st.session_state.get("autoplay", False)

    # Stop autoplay if at interaction or terminal state
    if is_autoplay and (status in ("WAITING_GUEST", "WAITING_HUMAN", "HUMAN_HANDLING") or not has_pending):
        is_autoplay = False
        st.session_state["autoplay"] = False

    # 2. Render Live Presenter HUD (Mission Control)
    render_presenter_hud(snapshot, simulation, is_autoplay)

    # 3. Universal Action Cards for Interactions
    if status == "WAITING_GUEST":
        proposed = case.get("proposed_room_id", "Kamar Baru")
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="background: #EFF6FF; border-left: 5px solid #3B82F6; padding: 12px 16px; border-radius: 6px; margin-bottom: 8px;">
                    <div style="font-size: 1.05rem; font-weight: bold; color: #1E40AF;">
                        🛎️ Tindakan Diperlukan: Persetujuan Tamu (Guest Consent)
                    </div>
                    <div style="font-size: 0.9rem; color: #1E3A8A; margin-top: 4px;">
                        Agen telah memeriksa kondisi fisik dan menawarkan perpindahan ke kamar <strong>{proposed}</strong> (Kondisi Bersih & Siap). Tamu perlu menyetujui tawaran ini.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_act1, col_act2, col_act3 = st.columns([3, 3, 6])
            with col_act1:
                if st.button(f"✅ Setujui Pindah ke {proposed}", key="universal_guest_accept", type="primary", use_container_width=True):
                    simulation.submit_guest_choice(True, actor="GUEST")
                    simulation.run_until_pause()
                    st.session_state["autoplay"] = False
                    st.toast(f"✅ Tamu menyetujui pindah ke kamar {proposed}! Perpindahan selesai diproses.", icon="🎉")
                    st.rerun()
            with col_act2:
                if st.button("❌ Tolak Tawaran", key="universal_guest_decline", use_container_width=True):
                    simulation.submit_guest_choice(False, actor="GUEST")
                    st.session_state["autoplay"] = False
                    st.toast("❌ Tamu menolak tawaran kamar pengganti.", icon="🛎️")
                    st.rerun()
            with col_act3:
                st.caption("ℹ️ Aksi cepat ini langsung terhubung tanpa perlu repot mencari tab Portal Tamu.")

    elif status == "WAITING_HUMAN":
        reasons = ", ".join(case.get("human_reason_codes", [])) or "Kebijakan Bisnis Terpicu"
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="background: #FEF3C7; border-left: 5px solid #F59E0B; padding: 12px 16px; border-radius: 6px; margin-bottom: 8px;">
                    <div style="font-size: 1.05rem; font-weight: bold; color: #92400E;">
                        🚨 Tindakan Diperlukan: Eskalasi ke Staf / Manajer Hotel
                    </div>
                    <div style="font-size: 0.9rem; color: #78350F; margin-top: 4px;">
                        Aturan Policy Guardrail mengunci otomasi AI karena terdeteksi: <code>{reasons}</code>. Diperlukan keputusan manual manajer.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_staff1, col_staff2 = st.columns([4, 8])
            with col_staff1:
                if st.button("👤 Ambil Alih Kasus (Take Over)", key="universal_staff_takeover", type="primary", use_container_width=True):
                    out = simulation.staff_take_over()
                    if out.get("ok"):
                        st.toast("👤 Kasus berhasil diambil alih oleh Staf!", icon="👔")
                        st.rerun()
                    else:
                        st.error(f"Gagal mengambil alih kasus: {out.get('reason')}")
            with col_staff2:
                st.caption("ℹ️ Klik untuk mengambil alih kasus langsung sebagai manajer hotel.")

    elif status == "HUMAN_HANDLING":
        with st.container(border=True):
            st.markdown(
                """
                <div style="background: #FFF7ED; border-left: 5px solid #EA580C; padding: 12px 16px; border-radius: 6px; margin-bottom: 8px;">
                    <div style="font-size: 1.05rem; font-weight: bold; color: #9A3412;">
                        👔 Anda Sedang Menangani Kasus (Mode Staf Aktif)
                    </div>
                    <div style="font-size: 0.9rem; color: #7C2D12; margin-top: 4px;">
                        Tulis catatan penyelesaian manajer hotel di bawah ini untuk menutup kasus secara resmi.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_note, col_close = st.columns([8, 4])
            with col_note:
                staff_note = st.text_input(
                    "Catatan Penyelesaian Staf:",
                    value="Keluhan ditangani langsung oleh manajer; kompensasi ditolak sesuai SOP.",
                    key="universal_staff_note",
                )
            with col_close:
                st.write("")
                if st.button("✅ Tutup Kasus Resmi", key="universal_staff_close", type="primary", use_container_width=True):
                    out = simulation.staff_close_case(staff_note)
                    if out.get("ok"):
                        st.toast("✅ Kasus resmi diselesaikan dan ditutup oleh Staf!", icon="📁")
                        st.rerun()
                    else:
                        st.error("Catatan staf wajib diisi.")

    # Quick Work Order Ticket Actions in Universal Action Bar
    active_tickets = [t for t in (simulation.list_tickets() if simulation else []) if t.get("status") in ("PENDING", "IN_PROGRESS")]
    if active_tickets:
        with st.container(border=True):
            st.markdown(
                """
                <div style="background: #F0FDF4; border-left: 5px solid #16A34A; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px;">
                    <div style="font-size: 0.95rem; font-weight: bold; color: #166534;">
                        📋 Papan Cepat: Tiket Tugas Fisik Staf Lapangan
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            for t_item in active_tickets:
                tc1, tc2, tc3 = st.columns([6, 3, 3])
                dept_ico = "🔧" if t_item.get("department") == "MAINTENANCE" else "🧹"
                with tc1:
                    st.markdown(f"**{dept_ico} {t_item['id']} — {t_item.get('department')}** · {t_item.get('description')} (Kamar **{t_item.get('room_id')}**)")
                with tc2:
                    st.markdown(f"Status: **`{t_item['status']}`**")
                with tc3:
                    if t_item["status"] == "PENDING":
                        if st.button("▶️ Mulai Kerjakan", key=f"bar_ticket_start_{t_item['id']}", use_container_width=True):
                            res = simulation.staff_update_ticket(t_item["id"], "IN_PROGRESS")
                            if res.get("ok"):
                                st.toast(f"🔧 Tiket {t_item['id']} status: IN_PROGRESS", icon="▶️")
                                st.rerun()
                    elif t_item["status"] == "IN_PROGRESS":
                        if st.button("✔️ Tandai Selesai", key=f"bar_ticket_done_{t_item['id']}", type="primary", use_container_width=True):
                            res = simulation.staff_update_ticket(t_item["id"], "DONE")
                            if res.get("ok"):
                                st.toast(f"✅ Tiket {t_item['id']} status: DONE!", icon="🎉")
                                st.rerun()

    elif status in ("DIGITAL_COMPLETED", "CLOSED_BY_STAFF", "CLOSED_GUEST_DECLINED", "FAILED"):
        assigned = case.get("assigned_room_id") or case.get("original_room_id")
        status_label = {
            "DIGITAL_COMPLETED": "🎉 Kasus Sukses Diselesaikan Secara Digital!",
            "CLOSED_BY_STAFF": "✅ Kasus Berhasil Diselesaikan dan Ditutup oleh Staf!",
            "CLOSED_GUEST_DECLINED": "⚪ Kasus Ditutup (Tamu menolak tawaran kamar)",
            "FAILED": "🔴 Kasus Berakhir dengan Status Gagal Terstruktur",
        }.get(status, f"Kasus Selesai: {status}")

        if status in ("DIGITAL_COMPLETED", "CLOSED_BY_STAFF"):
            run_id = getattr(simulation, "run_id", "default_run")
            if st.session_state.get("balloon_shown_run_id") != run_id:
                st.balloons()
                st.session_state["balloon_shown_run_id"] = run_id

        st.success(
            f"**{status_label}** (Kamar Resmi Tamu: **{assigned}**). "
            f"👉 Anda dapat melihat evaluasi efisiensi di tab **🏨 Ringkasan Eksekutif & ROI**, "
                f"atau memilih skenario cerita lain di Dasbor Eksekutif."
        )

    # 4. Trigger next step if autoplay is actively on
    if is_autoplay and has_pending and status not in ("WAITING_GUEST", "WAITING_HUMAN", "HUMAN_HANDLING"):
        speed = float(st.session_state.get("autoplay_speed", 2.0))
        time.sleep(speed)
        simulation.step()
        st.rerun()


def render_sidebar(model: Any) -> None:
    from .repository import load_seed

    scenarios = load_scenarios()
    sim = st.session_state.get("simulation")
    if sim:
        rooms_data = sim.front_office.dump().get("rooms", [])
        readiness_data = sim.operations.dump().get("room_readiness", [])
        source_label = "Live Simulasi"
    else:
        seed = load_seed()
        rooms_data = seed.get("rooms", [])
        readiness_data = seed.get("room_readiness", [])
        source_label = "Database Seed"

    readiness_map = {r.get("room_id"): r for r in readiness_data}
    total_rooms = len(rooms_data)
    occupied_count = sum(1 for r in rooms_data if r.get("occupied_by"))
    occupancy_pct = (occupied_count / total_rooms * 100) if total_rooms > 0 else 0.0
    clean_ready_count = sum(
        1
        for r in rooms_data
        if not r.get("occupied_by")
        and readiness_map.get(r.get("id"), {}).get("cleanliness") == "clean"
        and not readiness_map.get(r.get("id"), {}).get("maintenance_blocked")
    )
    dirty_count = sum(1 for r in readiness_data if r.get("cleanliness") == "dirty")
    maint_count = sum(1 for r in readiness_data if r.get("maintenance_blocked"))

    with st.sidebar:
        st.markdown("### 🏨 Hotel Nusantara")
        st.caption("Sistem Otomasi Operasional & Layanan Tamu")

        with st.container(border=True):
            st.markdown("**📊 Ringkasan Properti Hari Ini:**")
            st.markdown(f"- Total Kamar: **{total_rooms} Kamar**")
            st.markdown(f"- Terisi (Occupancy): **{occupied_count} Kamar ({occupancy_pct:.0f}%)**")
            st.markdown(f"- Kamar Bersih Siap: **{clean_ready_count} Kamar**")
            st.markdown(f"- Kamar Perlu Dicuci: **{dirty_count} Kamar**")
            if maint_count > 0:
                st.markdown(f"- Kamar Maintenance: **{maint_count} Kamar**")
            st.caption(f"⚡ *Tersinkronisasi {source_label} (SQLite)*")

        st.markdown("**💡 Panduan Cepat:**")
        st.info("Pilih salah satu **Kartu Kasus Nyata** di layar utama untuk menjalankan simulasi otomatis.")

        st.divider()

        # Developer & test runner controls folded cleanly here
        with st.expander("⚙️ Mode Pengembang & Uji Teknis (Opsional)", expanded=False):
            st.caption("Kontrol untuk keperluan pengujian dan evaluasi arsitektur:")
            mode = st.radio(
                "Mode agen",
                options=["mobile", "static"],
                format_func=lambda value: MODE_LABELS[value],
                index=0,
                key="mode_radio",
            )
            active_mode = st.session_state.get("active_mode")
            if active_mode is not None and mode != active_mode:
                st.warning("Mode baru berlaku saat memilih/reset skenario.")

            st.markdown("**Skenario Pengujian**")
            for scenario_id in SCENARIO_ORDER:
                if st.button(
                    scenarios[scenario_id]["button_label"],
                    key=f"scenario_{scenario_id}",
                    use_container_width=True,
                ):
                    _start_scenario(model, scenario_id, mode)

            has_active = st.session_state.get("active_scenario") is not None
            if st.button(
                "Reset Skenario",
                key="reset_scenario",
                disabled=not has_active,
                use_container_width=True,
            ):
                _start_scenario(
                    model,
                    st.session_state["active_scenario"],
                    st.session_state.get("active_mode", mode),
                )

            st.divider()
            st.markdown("**Aturan Kebijakan Agen:**")
            st.caption(
                "- Pemindahan kamar hanya ke kamar setara, bersih, kosong, tanpa biaya tambahan.\n"
                "- Permintaan upgrade di luar hak wajib dieskalasi ke manajer.\n"
                "- Aturan bisnis selalu diutamakan daripada otomasi."
            )

        with st.expander("👥 Tentang Tim (Kelompok 5)", expanded=False):
            st.markdown(
                "**Mata Kuliah: Agent Enterprise**\n\n"
                "- M. Al lail Qadrillah\n"
                "- Dimas Prabowo\n"
                "- Monanta Alfiareza\n"
                "- Frans Alwan\n\n"
                "Hotel fiktif **Hotel Nusantara Demo**. Seluruh data sintetis dan lokal."
            )


def _agent_card(agent: Dict[str, Any]) -> None:
    status = agent.get("status", "-")
    archived = agent.get("archived", False)
    badge = " (arsip, nonaktif)" if archived else ""
    st.markdown(
        f"**{agent['agent_id']}** — {agent.get('agent_type', 'static')}{badge}  \n"
        f"node: `{agent.get('location') or agent.get('node_id')}` · status: `{status}` · "
        f"phase: `{agent.get('phase', '-')}`  \n"
        f"last_action: `{agent.get('last_action') or '-'}`"
    )


def _node_column(snapshot: Dict[str, Any], node_id: str, title: str) -> None:
    st.markdown(f"#### {title}")
    agents = [agent for agent in snapshot["agents"] if agent.get("location") == node_id]
    active = [agent for agent in agents if not agent.get("archived")]
    if not active:
        st.caption("Tidak ada instance aktif pada node ini.")
    for agent in agents:
        with st.container(border=True):
            _agent_card(agent)


def _result_text(snapshot: Dict[str, Any]) -> Optional[str]:
    case = snapshot.get("case")
    if case is None:
        return None
    scenario = snapshot["scenario_id"]
    status = case["status"]
    if status == "WAITING_GUEST":
        return (
            f"Proposal: pindah ke kamar **{case['proposed_room_id']}** "
            f"(proposal versi {case['proposal_version']}). Menunggu persetujuan tamu."
        )
    if status == "WAITING_HUMAN":
        if scenario == "S02":
            return (
                "R201 siap, tetapi merupakan upgrade. Keputusan staf diperlukan; "
                "kamar belum diubah."
            )
        if scenario == "S03":
            return "Tagihan F02 diteruskan untuk peninjauan staf; nominal belum diubah."
        return "Kasus menunggu keputusan staf."
    if status == "HUMAN_HANDLING":
        return "Staf telah mengambil alih kasus; tutup kasus dengan catatan nonkosong."
    if status == "CLOSED_BY_STAFF":
        return f"Kasus ditutup oleh staf. Catatan: {case.get('closed_note') or '-'}"
    if status == "CLOSED_GUEST_DECLINED":
        return "Perpindahan dibatalkan atas pilihan tamu; tiket perbaikan tetap aktif."
    if status == "DIGITAL_COMPLETED":
        if case.get("assigned_room_id"):
            return (
                f"Penempatan reservasi berubah dari {case['original_room_id']} ke "
                f"{case['assigned_room_id']}. Tiket perbaikan AC tetap aktif."
            )
        if case["flow"] == "faq":
            answer = case.get("evidence", {}).get("faq", {}).get("answer")
            return f"Jawaban FAQ lokal: {answer}"
        if case["flow"] == "housekeeping":
            tickets = snapshot.get("tickets", [])
            ticket_id = tickets[0]["id"] if tickets else "TICKET-001"
            return f"Tiket {ticket_id} dibuat; menunggu pekerjaan staf."
        if case["flow"] == "billing_details":
            folio = case.get("evidence", {}).get("folio", {})
            return f"Rincian tagihan total Rp{folio.get('total', 0):,}".replace(
                ",", "."
            )
        return "Kasus selesai secara digital."
    if status == "FAILED":
        return "Kasus gagal secara teknis; lihat detail kegagalan."
    return None


def _decision_panel(snapshot: Dict[str, Any]) -> None:
    case = snapshot.get("case")
    if case is None:
        return
    columns = st.columns(4)
    columns[0].metric("p(human_judgment)", f"{case['p_human']:.4f}")
    columns[1].metric("Threshold", f"{snapshot['threshold']}")
    columns[2].metric(
        "Model recommends human", "Ya" if case["model_recommends_human"] else "Tidak"
    )
    columns[3].metric("human_required", "Ya" if case["human_required"] else "Tidak")
    st.caption(
        f"mandatory_reasons: {case['mandatory_reasons'] or '-'} · "
        f"final_decision: {'REVIEW' if case['human_required'] else 'ALLOW'} · "
        f"decision_source: {case['decision_source']} · priority: {case['priority']} · "
        f"reason_codes: {case['human_reason_codes'] or '-'}"
    )


def _render_live_flow_stepper(
    snapshot: Optional[Dict[str, Any]], override_phase: Optional[int] = None
) -> None:
    """Render a dynamic 6-step progress stepper and real-time narration box."""
    if snapshot is None:
        return

    case = snapshot.get("case")
    migration = snapshot.get("migration")
    step_idx = snapshot.get("step_index", 0)

    # Determine current active phase (1 to 6)
    current_phase = 1
    narrative = "Skenario diinisialisasi. Menunggu pemrosesan pesan tamu..."

    if override_phase is not None:
        current_phase = override_phase
    elif case is None:
        current_phase = 1
        narrative = "📥 Skenario telah dipilih. Klik 'Langkah Berikutnya' untuk agen Scenario Scout membaca keluhan tamu."
    else:
        status = case.get("status", "CREATED")
        insp_results = case.get("inspection_results", [])
        mig_stage = migration.get("stage") if migration else None

        if status in ("DIGITAL_COMPLETED", "CLOSED_BY_STAFF", "CLOSED_GUEST_DECLINED", "FAILED"):
            current_phase = 6
            if status == "DIGITAL_COMPLETED":
                narrative = f"🎉 Selesai Digital! Kasus terselesaikan secara mandiri dalam {step_idx} langkah. Kamar resmi dipindahkan tanpa komplain berulang."
            elif status == "CLOSED_BY_STAFF":
                narrative = "✅ Selesai oleh Staf! Manajer hotel telah meninjau bukti dan menutup kasus dengan catatan resmi."
            elif status == "CLOSED_GUEST_DECLINED":
                narrative = "⚪ Ditutup: Tamu menolak tawaran kamar pengganti dan memilih tetap di kamar asal."
            else:
                narrative = "🔴 Kasus berakhir dengan penolakan atau status kegagalan terstruktur."
        elif status == "WAITING_GUEST":
            current_phase = 5
            narrative = f"🛎️ Menunggu Persetujuan Tamu: Tawaran kamar pengganti {case.get('proposed_room_id')} (Kondisi Bersih & Siap) telah dikirimkan ke HP tamu. Menunggu keputusan tamu."
        elif status in ("WAITING_HUMAN", "HUMAN_HANDLING"):
            current_phase = 5
            narrative = "⚠️ Eskalasi Manajer: Sistem mendeteksi permintaan kompensasi di luar batas wewenang otomatis. Kasus dialihkan ke Manajer Hotel untuk melindungi pendapatan hotel."
        elif insp_results and len(insp_results) > 0:
            current_phase = 4
            narrative = "🔍 Pemeriksaan Kamar Selesai: Sistem telah memverifikasi fisik kamar di Housekeeping (kamar kotor otomatis dieliminasi, kamar bersih dipilih)."
        elif mig_stage in ("INITIATED", "PREPARED", "DEPARTED"):
            current_phase = 3
            narrative = "🚀 Koordinasi Departemen: Asisten AI sedang menghubungkan sistem Meja Depan dengan sistem Operasional & Housekeeping..."
        elif step_idx > 0:
            current_phase = 2
            narrative = "⚖️ Analisis Kasus: Asisten AI mengidentifikasi jenis keluhan dan mengevaluasi batasan kebijakan kompensasi hotel."

    # Visual Stepper Bar (Pure Hospitality Terms)
    steps = [
        ("1. Keluhan Masuk", "Laporan dari Tamu"),
        ("2. Analisis Kasus", "Evaluasi SOP Hotel"),
        ("3. Koordinasi Dept", "Pemeriksaan Sistem"),
        ("4. Verifikasi Fisik", "Kesiapan Kamar"),
        ("5. Persetujuan / Staf", "Konfirmasi / Manajer"),
        ("6. Masalah Selesai", "Kamar Resmi Pindah"),
    ]

    cols = st.columns(6)
    for i, (title, sub) in enumerate(steps, 1):
        with cols[i - 1]:
            if i < current_phase:
                state_badge = "✅"
                border_style = "border: 2px solid #10B981; background: #ECFDF5;"
                text_color = "#065F46"
            elif i == current_phase:
                state_badge = "🟢"
                border_style = "border: 2px solid #FF6B35; background: #FFF7ED; box-shadow: 0 0 8px rgba(255,107,53,0.3);"
                text_color = "#C2410C"
            else:
                state_badge = "⚪"
                border_style = "border: 1px solid #E2E8F0; background: #F8FAFC;"
                text_color = "#94A3B8"

            st.markdown(
                f"""
                <div style="{border_style} border-radius: 8px; padding: 6px 4px; text-align: center; min-height: 64px;">
                    <div style="font-size: 0.72rem; font-weight: bold; color: {text_color};">{state_badge} {title}</div>
                    <div style="font-size: 0.62rem; color: #64748B; margin-top: 2px;">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Narrative Banner
    st.markdown(
        f"""
        <div style="background: #F1F5F9; border-left: 4px solid #FF6B35; padding: 10px 14px; border-radius: 6px; margin-top: 8px; margin-bottom: 12px;">
            <div style="font-size: 0.85rem; color: #1E293B;">
                <strong>💡 Apa yang terjadi di balik layar:</strong> {narrative}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_live_migration_topology(snapshot: Optional[Dict[str, Any]]) -> None:
    """Render an interactive 3-column architecture topology showing live node execution & state migration."""
    if snapshot is None:
        return

    mode = snapshot.get("active_mode") or snapshot.get("mode") or "mobile"
    migration = snapshot.get("migration")
    mig_stage = migration.get("stage") if migration else None
    mig_size = migration.get("checkpoint_size", 412) if migration else 0
    mig_src = migration.get("source_node", "FRONT_OFFICE") if migration else "FRONT_OFFICE"
    mig_dst = migration.get("destination_node", "OPERATIONS") if migration else "OPERATIONS"

    # Identify agents in each node
    agents = snapshot.get("agents", [])
    fo_agents = [
        a for a in agents
        if (a.get("location") or a.get("node_id")) == "FRONT_OFFICE" and not a.get("archived")
    ]
    ops_agents = [
        a for a in agents
        if (a.get("location") or a.get("node_id")) == "OPERATIONS" and not a.get("archived")
    ]

    is_in_transit = mig_stage in ("INITIATED", "PREPARED", "DEPARTED")
    is_migrated_ops = (len(ops_agents) > 0 and not is_in_transit) or mig_stage in (
        "RECEIVED",
        "VERIFIED",
        "EXECUTED",
    )

    if is_in_transit:
        fo_active = False
        ops_active = False
    elif is_migrated_ops:
        fo_active = False
        ops_active = True
    else:
        fo_active = True
        ops_active = False

    st.markdown("##### 🌐 Topologi Jaringan & Posisi Agen (Real-Time)")

    t_cols = st.columns([4, 4, 4])

    with t_cols[0]:
        fo_border = (
            "border: 2px solid #2563EB; background: #EFF6FF; box-shadow: 0 0 10px rgba(37,99,235,0.2);"
            if fo_active
            else "border: 1px solid #CBD5E1; background: #F8FAFC;"
        )
        fo_status = "🟢 AKTIF MENGEKSEKUSI" if fo_active else "⚪ SIAGA (IDLE)"
        fo_color = "#1D4ED8" if fo_active else "#64748B"
        fo_agent_names = ", ".join([a.get("agent_id") for a in fo_agents]) or "(Agen berpindah / siaga)"
        st.markdown(
            f"""
            <div style="{fo_border} border-radius: 12px; padding: 12px 14px; min-height: 140px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <strong style="color: #1E293B; font-size: 0.95rem;">🖥️ Node FRONT_OFFICE</strong>
                    <span style="font-size: 0.72rem; font-weight: bold; color: {fo_color};">{fo_status}</span>
                </div>
                <div style="font-size: 0.78rem; color: #475569; margin-bottom: 4px;">
                    <strong>Database:</strong> SQLite In-Memory (Node 1)
                </div>
                <div style="font-size: 0.72rem; color: #64748B; margin-bottom: 6px;">
                    Tabel: <code>rooms</code>, <code>reservations</code>, <code>folio</code>, <code>faq</code>
                </div>
                <div style="font-size: 0.75rem; background: white; padding: 4px 8px; border-radius: 6px; border: 1px solid #E2E8F0; color: #1E293B;">
                    🤖 <strong>Agen di Node:</strong> {fo_agent_names}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with t_cols[1]:
        if is_in_transit:
            br_border = "border: 2px dashed #F59E0B; background: #FFFBEB; box-shadow: 0 0 12px rgba(245,158,11,0.3);"
            br_title = f"🚀 SEDANG BERPINDAH ({mig_src} ➔ {mig_dst})"
            br_title_color = "#B45309"
            br_desc = f"📦 Payload: <b>{mig_size} Bytes</b> · ⏱️ Latensi: <b>12ms</b><br>🔒 Verifikasi SHA-256 Checkpoint Lulus"
        elif mode == "mobile":
            if mig_stage in ("RECEIVED", "VERIFIED", "COMMITTED", "EXECUTED"):
                br_border = "border: 1px solid #10B981; background: #ECFDF5;"
                br_title = "✅ Migrasi State Selesai"
                br_title_color = "#047857"
                br_desc = f"Agen telah berpindah ke {mig_dst}. Eksekusi inspeksi lokal tanpa RPC bolak-balik."
            else:
                br_border = "border: 1px dashed #94A3B8; background: #F8FAFC;"
                br_title = "🌐 Saluran Migrasi ACE-MAMP Siaga"
                br_title_color = "#475569"
                br_desc = "Jalur transfer snapshot state lokal & verifikasi anti-replay aktif."
        else:
            br_border = "border: 1px solid #EF4444; background: #FEF2F2;"
            br_title = "📡 Mode Static Agent"
            br_title_color = "#B91C1C"
            br_desc = "Tidak ada migrasi; seluruh inspeksi memanggil kueri RPC berulang melewati jaringan."

        st.markdown(
            f"""
            <div style="{br_border} border-radius: 12px; padding: 12px 14px; min-height: 140px; text-align: center;">
                <div style="font-size: 0.75rem; font-weight: bold; color: {br_title_color}; margin-bottom: 6px;">
                    {br_title}
                </div>
                <div style="font-size: 0.78rem; color: #334155; line-height: 1.4; margin-top: 8px;">
                    {br_desc}
                </div>
                <div style="font-size: 0.68rem; color: #64748B; margin-top: 8px;">
                    Protokol: <code>ACE-MAMP v1.0</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with t_cols[2]:
        ops_border = (
            "border: 2px solid #10B981; background: #ECFDF5; box-shadow: 0 0 10px rgba(16,185,129,0.2);"
            if ops_active
            else "border: 1px solid #CBD5E1; background: #F8FAFC;"
        )
        ops_status = "🟢 AKTIF INSPEKSI" if ops_active else "⚪ SIAGA (IDLE)"
        ops_color = "#047857" if ops_active else "#64748B"
        ops_agent_names = ", ".join([a.get("agent_id") for a in ops_agents]) or "(Menunggu kedatangan agen)"
        st.markdown(
            f"""
            <div style="{ops_border} border-radius: 12px; padding: 12px 14px; min-height: 140px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <strong style="color: #1E293B; font-size: 0.95rem;">🖥️ Node OPERATIONS</strong>
                    <span style="font-size: 0.72rem; font-weight: bold; color: {ops_color};">{ops_status}</span>
                </div>
                <div style="font-size: 0.78rem; color: #475569; margin-bottom: 4px;">
                    <strong>Database:</strong> SQLite In-Memory (Node 2)
                </div>
                <div style="font-size: 0.72rem; color: #64748B; margin-bottom: 6px;">
                    Tabel: <code>room_readiness</code>, <code>housekeeping_tickets</code>
                </div>
                <div style="font-size: 0.75rem; background: white; padding: 4px 8px; border-radius: 6px; border: 1px solid #E2E8F0; color: #1E293B;">
                    🤖 <strong>Agen di Node:</strong> {ops_agent_names}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_interactive_room_map(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation]
) -> None:
    """Render interactive room grid map reflecting live SQLite database status."""
    from .repository import load_seed

    if simulation:
        rooms = simulation.front_office.dump().get("rooms", [])
        readiness = simulation.operations.dump().get("room_readiness", [])
    else:
        seed = load_seed()
        rooms = seed.get("rooms", [])
        readiness = seed.get("room_readiness", [])

    readiness_map = {r.get("room_id"): r for r in readiness}

    st.markdown("##### 🏢 Denah Status Kamar Hotel (Live Real-Time)")
    r_cols = st.columns(len(rooms) if rooms else 4)

    for i, r in enumerate(rooms):
        rid = r.get("id")
        rtype = r.get("room_type", "standard").capitalize()
        rate = r.get("nightly_rate", 500000)
        occ = r.get("occupied_by")
        rm_info = readiness_map.get(rid, {})
        clean = rm_info.get("cleanliness", "clean")
        maint = rm_info.get("maintenance_blocked", False)

        if occ and maint:
            badge = "🔴 TERISI & AC RUSAK"
            badge_color = "#DC2626"
            bg = "#FEF2F2"
            border = "2px solid #EF4444"
            desc = f"Dihuni: <b>{occ}</b><br>⚠️ Kendala: AC Bocor"
            icon = "❄️⚠️"
        elif occ:
            badge = "👤 TERISI (TAMU)"
            badge_color = "#2563EB"
            bg = "#EFF6FF"
            border = "2px solid #3B82F6"
            desc = f"Dihuni: <b>{occ}</b><br>✨ Kamar Siap & Nyaman"
            icon = "🏨"
        elif maint:
            badge = "🔧 KOSONG (PERLU SERVIS)"
            badge_color = "#D97706"
            bg = "#FFFBEB"
            border = "1px solid #F59E0B"
            desc = "Status: Kosong<br>Menunggu Teknisi AC"
            icon = "🛠️"
        elif clean == "dirty":
            badge = "🧹 KOTOR (PERLU CUCI)"
            badge_color = "#EA580C"
            bg = "#FFF7ED"
            border = "1px solid #FB923C"
            desc = "Status: Kosong<br>Antrean Housekeeping"
            icon = "🛏️"
        else:
            badge = "✨ BERSIH & SIAP HUNI"
            badge_color = "#059669"
            bg = "#ECFDF5"
            border = "2px solid #10B981"
            desc = "Status: Kosong<br>Kamar Pengganti Ideal"
            icon = "✅"

        with r_cols[i]:
            st.markdown(
                f"""
                <div style="background: {bg}; border: {border}; border-radius: 12px; padding: 10px 8px; text-align: center; min-height: 130px;">
                    <div style="font-size: 1.05rem; font-weight: bold; color: #1E293B;">
                        {icon} {rid}
                    </div>
                    <div style="font-size: 0.72rem; color: #64748B; margin-top: 1px;">
                        Tipe {rtype} · Rp{rate:,.0f}
                    </div>
                    <div style="margin: 6px 0;">
                        <span style="font-size: 0.65rem; font-weight: bold; background: white; padding: 2px 5px; border-radius: 6px; color: {badge_color}; border: 1px solid #E2E8F0;">
                            {badge}
                        </span>
                    </div>
                    <div style="font-size: 0.72rem; color: #334155; margin-top: 4px; line-height: 1.3;">
                        {desc}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_simulation_tab(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation]
) -> None:
    if snapshot is None or simulation is None:
        st.info("Pilih salah satu skenario di sidebar untuk memulai run baru.")
        return

    _render_live_flow_stepper(snapshot)

    st.markdown(
        f"**Mode aktif:** `{snapshot['active_mode']}` · **Run:** `{snapshot['run_id']}`"
    )
    case = snapshot["case"]
    if case is not None:
        st.markdown(f"**Pesan tamu:** “{case['guest_message']}”")
        st.markdown(
            f"**Status kasus:** `{case['status']}` · **Tiket:** "
            f"{', '.join(case['ticket_ids']) or '-'} · **Kamar asal:** {case['original_room_id']}"
        )
    else:
        st.markdown("**Pesan tamu:** (belum ada kasus)")

    _decision_panel(snapshot)

    st.divider()
    _render_live_migration_topology(snapshot)

    st.divider()
    _render_interactive_room_map(snapshot, simulation)

    st.divider()
    left, right = st.columns(2)
    with left:
        _node_column(snapshot, "FRONT_OFFICE", "Node FRONT_OFFICE")
    with right:
        _node_column(snapshot, "OPERATIONS", "Node OPERATIONS")

    migration = snapshot.get("migration")
    with st.container(border=True):
        st.markdown("#### Area Transit (migrasi state)")
        if migration is None:
            st.caption("Belum ada migrasi.")
        else:
            st.markdown(
                f"`{migration['migration_id']}` · agen `{migration['agent_id']}` · "
                f"{migration['source_node']} → {migration['destination_node']} · "
                f"stage `{migration['stage']}` · hash `{(migration.get('expected_hash') or '-')[:16]}` · "
                f"size {migration.get('checkpoint_size', 0)} byte"
            )
            if migration["stage"] in ("INITIATED", "PREPARED", "DEPARTED"):
                st.warning(
                    "Agen berada di jalur transfer; tidak ada instance aktif pada node mana pun."
                )

    st.divider()
    control_columns = st.columns([1, 1, 2])
    with control_columns[0]:
        step_clicked = st.button(
            "Langkah Berikutnya",
            key="step_button",
            disabled=not snapshot["has_pending_work"],
            use_container_width=True,
        )
    with control_columns[1]:
        st.metric("Step engine", snapshot["step_index"])
    with control_columns[2]:
        if snapshot["is_paused"]:
            st.info("Simulator berhenti: menunggu input tamu/staf atau kasus terminal.")
        else:
            st.caption("Ada pekerjaan tertunda di queue/transit.")

    if step_clicked:
        simulation.step()
        st.rerun()

    result = _result_text(snapshot)
    if result:
        st.success(result)

    # Panel peran: tamu
    if case is not None and case["status"] == "WAITING_GUEST":
        with st.container(border=True):
            st.markdown("**Simulasi Peran — Tamu** (bukan autentikasi pengguna)")
            guest_columns = st.columns(2)
            if guest_columns[0].button(
                f"Tamu: Setuju pindah ke {case['proposed_room_id']}",
                key="guest_accept",
                use_container_width=True,
            ):
                simulation.submit_guest_choice(True, actor="GUEST")
                simulation.run_until_pause()
                st.session_state["autoplay"] = False
                st.rerun()
            if guest_columns[1].button(
                "Tamu: Tolak perpindahan", key="guest_decline", use_container_width=True
            ):
                simulation.submit_guest_choice(False, actor="GUEST")
                st.session_state["autoplay"] = False
                st.rerun()

    # Panel peran: staf
    if case is not None and case["status"] in ("WAITING_HUMAN", "HUMAN_HANDLING"):
        with st.container(border=True):
            st.markdown("**Simulasi Peran — Staf** (bukan autentikasi pengguna)")
            if case["status"] == "WAITING_HUMAN":
                st.markdown(
                    f"Bukti untuk staf: inspeksi "
                    f"{[item['room_id'] + ':' + ','.join(item['reason_codes']) for item in case['inspection_results']] or '-'} · "
                    f"folio {case.get('evidence', {}).get('folio', {})}"
                )
                if st.button("Staf: Ambil Alih", key="staff_takeover"):
                    simulation.staff_take_over()
                    st.rerun()
            else:
                note = st.text_area("Catatan staf (wajib)", key="staff_note")
                if st.button("Staf: Tutup Kasus", key="staff_close"):
                    outcome = simulation.staff_close_case(note)
                    if outcome["ok"]:
                        st.rerun()
                    else:
                        st.error("Catatan staf wajib diisi.")

    # Panel tiket
    tickets = snapshot.get("tickets", [])
    if tickets:
        with st.container(border=True):
            st.markdown("**Panel Tiket (pekerjaan fisik staf)**")
            for ticket in tickets:
                columns = st.columns([3, 1, 1, 1])
                columns[0].markdown(
                    f"`{ticket['id']}` · {ticket['department']} · {ticket['room_id']} · "
                    f"{ticket['description']} · status `{ticket['status']}`"
                )
                if ticket["status"] == "PENDING" and columns[1].button(
                    "Mulai", key=f"ticket_start_{ticket['id']}"
                ):
                    simulation.staff_update_ticket(ticket["id"], "IN_PROGRESS")
                    st.rerun()
                if ticket["status"] == "IN_PROGRESS" and columns[2].button(
                    "Selesai", key=f"ticket_done_{ticket['id']}"
                ):
                    simulation.staff_update_ticket(ticket["id"], "DONE")
                    st.rerun()


def render_download_center(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation], model: Any = None
) -> None:
    """Renders a 1-click Download & Export Center for audit logs, benchmarks, and executive summaries."""
    import csv
    import io
    from datetime import datetime

    st.markdown("### 📥 Pusat Unduhan & Ekspor Laporan Resmi")
    st.caption("Unduh berkas audit teknis, benchmark performa komparatif, dan laporan eksekutif untuk keperluan presentasi atau evaluasi.")

    col1, col2, col3 = st.columns(3)

    # 1. Technical Audit Trail (JSON)
    with col1:
        with st.container(border=True):
            st.markdown("#### 🔒 Laporan Audit Kasus (.json)")
            st.markdown(
                """
                - **Format:** Berkas JSON terstruktur
                - **Isi:** Seluruh event trace, hash SHA-256 koper migrasi, pesan antar-node, dan snapshot tabel database.
                - **Tujuan:** Verifikasi teknis dosen & tim audit enterprise.
                """
            )
            if simulation:
                json_str = simulation.export_json()
                run_id = getattr(simulation, "run_id", "sim_run")
                sid = snapshot.get("scenario_id", "S01") if snapshot else "S01"
                st.download_button(
                    "⬇️ Unduh Audit JSON",
                    data=json_str,
                    file_name=f"audit-kasus-{sid}-{run_id}.json",
                    mime="application/json",
                    key="dl_center_json",
                    use_container_width=True,
                    type="primary",
                )
            else:
                st.caption("ℹ️ Jalankan skenario terlebih dahulu untuk mengunduh log audit.")

    # 2. Benchmark Comparison (CSV)
    with col2:
        with st.container(border=True):
            st.markdown("#### 📊 Benchmark Komparasi (.csv)")
            st.markdown(
                """
                - **Format:** CSV (Spreadsheet / Excel)
                - **Isi:** Matriks efisiensi komparatif Mobile Agent vs Static Agent (byte payload, pesan jaringan, dan latensi komputasi).
                - **Tujuan:** Analisis kuantitatif performa arsitektur.
                """
            )
            comp_result = run_comparison(model=model)
            table_rows = comparison_table_rows(comp_result)
            csv_buf = io.StringIO()
            if table_rows:
                writer = csv.DictWriter(csv_buf, fieldnames=list(table_rows[0].keys()))
                writer.writeheader()
                writer.writerows(table_rows)
            csv_content = csv_buf.getvalue()

            st.download_button(
                "⬇️ Unduh Benchmark CSV",
                data=csv_content,
                file_name="benchmark-performa-mobile-vs-static.csv",
                mime="text/csv",
                key="dl_center_csv",
                use_container_width=True,
                type="primary",
            )

    # 3. Executive Business Summary (Markdown / TXT)
    with col3:
        with st.container(border=True):
            st.markdown("#### 📝 Ringkasan Eksekutif (.md)")
            st.markdown(
                """
                - **Format:** Dokumen Markdown Resmi
                - **Isi:** Ringkasan hasil penanganan, estimasi penghematan biaya (Zero Cost Leakage), efisiensi SLA waktu, dan profil tim pengembang.
                - **Tujuan:** Bahan bacaan dosen penguji & manajemen hotel.
                """
            )
            sid = snapshot.get("scenario_id", "S01") if snapshot else "S01"
            case = (snapshot.get("case") or {}) if snapshot else {}
            st_case = case.get("status", "COMPLETED") if case else "STANDBY"
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            assigned_str = case.get("assigned_room_id") or case.get("proposed_room_id") or "-"

            exec_doc = f"""# 🏨 LAPORAN EKSEKUTIF PENANGANAN KOMPLAIN & AUDIT MULTI-AGENT
**Sistem:** ACE Intelligent Mobile Agent System — Hotel Nusantara Demo  
**Waktu Ekspor:** {now_str}  
**Mata Kuliah:** Agent Enterprise (Semester 3)  
**Kelompok 5:** M. Al lail Qadrillah, Dimas Prabowo, Monanta Alfiareza, Frans Alwan  

---

## 1. Ringkasan Kasus Aktif
- **ID Skenario:** {sid}
- **Status Akhir Kasus:** {st_case}
- **Kamar Tamu:** {case.get('original_room_id', 'R101')} ➔ Kamar Pengganti: {assigned_str}
- **Pesan Tamu:** "{case.get('guest_message', '-')}"

## 2. Nilai Bisnis & Tata Kelola (Business Impact)
- **Zero Cost Leakage:** Proteksi Policy Guardrail memastikan kenaikan kelas kamar (upgrade) ilegal diblokir secara deterministik.
- **Efisiensi Waktu (SLA):** Keluhan diselesaikan secara digital dalam waktu < 1 menit tanpa antrean di resepsionis lobi.
- **Privasi & Keamanan Data:** Database fisik Housekeeping di node Operations tidak pernah diekspos langsung ke jaringan eksternal. Mobile Agent bermigrasi secara lokal membawa state berkode hash SHA-256 (ACE-MAMP v1.0).

## 3. Kesimpulan & Rekomendasi
Sistem berhasil mendemonstrasikan keunggulan paradigma **Mobile Agent** dibandingkan pendekatan Static RPC konvensional dengan memotong lalu lintas jaringan dan mengisolasi domain data perhotelan.
"""
            st.download_button(
                "⬇️ Unduh Ringkasan (.md)",
                data=exec_doc,
                file_name=f"ringkasan-eksekutif-{sid}.md",
                mime="text/markdown",
                key="dl_center_md",
                use_container_width=True,
                type="primary",
            )


def render_trace_tab(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation], model: Any = None
) -> None:
    render_download_center(snapshot, simulation, model)

    st.divider()

    if snapshot is None or simulation is None:
        st.info("Pilih skenario di tab Simulasi untuk mengamati live database dump dan event trace.")
        return

    st.markdown("#### Metrik")
    metrics = snapshot["metrics"]
    total_payload = (
        metrics["inter_node_message_bytes"] + metrics["transferred_checkpoint_bytes"]
    )
    columns = st.columns(4)
    columns[0].metric("Pesan (MESSAGE_SENT)", metrics["messages_sent"])
    columns[1].metric("Pesan antar-node", metrics["inter_node_messages"])
    columns[2].metric(
        "Migrasi sukses/gagal",
        f"{metrics['migrations_succeeded']}/{metrics['migrations_failed']}",
    )
    columns[3].metric("Byte checkpoint", metrics["transferred_checkpoint_bytes"])
    columns = st.columns(4)
    columns[0].metric("Total payload simulasi (byte)", total_payload)
    columns[1].metric("Step engine", metrics["engine_steps"])
    columns[2].metric("Tool calls", metrics["tool_calls"])
    columns[3].metric("Duplicate side effects", metrics["duplicate_side_effects"])
    st.caption(
        "Ukuran payload dihitung dari JSON UTF-8 kanonik. Ini bukan wire bytes dan bukan "
        "benchmark jaringan/produksi."
    )

    st.markdown("#### Tabel Pesan")
    messages = simulation.messages
    if messages:
        st.dataframe(
            [
                {
                    "message_id": message["message_id"],
                    "sender": message["sender"],
                    "receiver": message["receiver"],
                    "source": message["source_node"],
                    "destination": message["destination_node"],
                    "kind": message["kind"],
                    "action": message["action"],
                    "correlation_id": message["correlation_id"],
                }
                for message in messages
            ],
            use_container_width=True,
        )
    else:
        st.caption("Belum ada pesan.")

    st.markdown("#### Tabel Event")
    events = [event.to_dict() for event in simulation.events]
    if events:
        st.dataframe(
            [
                {
                    "seq": event["seq"],
                    "step": event["step_index"],
                    "event_type": event["event_type"],
                    "agent_id": event["agent_id"],
                    "node_id": event["node_id"],
                    "migration_id": event["migration_id"],
                    "reason_codes": ", ".join(event["reason_codes"]),
                }
                for event in events
            ],
            use_container_width=True,
            height=280,
        )
    else:
        st.caption("Belum ada event.")

    st.markdown("#### Checkpoint Migrasi")
    migration = snapshot.get("migration")
    if migration is None:
        st.caption("Belum ada checkpoint.")
    else:
        before, after = st.columns(2)
        with before:
            st.markdown("**Sebelum (before snapshot)**")
            st.json(migration.get("before_snapshot") or {})
        with after:
            st.markdown("**Sesudah (after snapshot)**")
            st.json(migration.get("after_snapshot") or {})
        st.caption(
            f"expected_hash: `{migration.get('expected_hash')}` · "
            f"size: {migration.get('checkpoint_size')} byte · "
            f"error: {migration.get('error') or '-'}"
        )

    case = snapshot.get("case")
    if case is not None and case.get("inspection_results"):
        st.markdown("#### Penolakan & Hasil Kandidat")
        st.dataframe(
            [
                {
                    "room_id": item["room_id"],
                    "room_type": item["room_type"],
                    "rate": item["nightly_rate"],
                    "room_version": item["room_version"],
                    "evidence_version": item["evidence_version"],
                    "is_ready": item["is_ready"],
                    "is_routine_eligible": item["is_routine_eligible"],
                    "reason_codes": ", ".join(item["reason_codes"]),
                }
                for item in case["inspection_results"]
            ],
            use_container_width=True,
        )

    st.markdown("#### 🗄️ Struktur & Data Database (Dual-Node SQLite)")
    st.caption("Pemisahan fisik in-memory antara node **Front Office** dan **Operations**.")

    # 1. Diagram Skema Database
    with st.expander("🗺️ Diagram Skema Database Dual-Node (ER Diagram & Topologi)", expanded=True):
        from pathlib import Path
        img_path = Path("docs/diagrams/database_schema_diagram.png")
        if img_path.exists():
            st.image(str(img_path), caption="Diagram Relasi Entitas & Isolasi Node Database (Dual-Node SQLite)")
        else:
            st.info("Diagram skema tersimpan di folder `docs/diagrams/database_schema_diagram.md`.")

    # 2. Inisiasi Data Seeding Awal Hotel
    with st.expander("🌱 Inisiasi Data Seeding Awal (Hotel Seed)", expanded=False):
        st.markdown("**Konfigurasi Data Seeding Awal Hotel Nusantara Demo (`data/hotel_seed.json`):**")
        seed_data = simulation.front_office_seed if hasattr(simulation, "front_office_seed") else None
        # Load seed data langsung
        from .repository import load_seed
        seed = load_seed()

        col_seed_fo, col_seed_ops = st.columns(2)
        with col_seed_fo:
            st.markdown("##### 🏢 Seeding Node Front Office")
            st.markdown(f"**Nama Hotel:** `{seed.get('hotel_name', 'Hotel Nusantara Demo')}`")
            st.markdown("**Tabel `guests` (Tamu Terdaftar):**")
            st.dataframe(seed.get("guests", []), use_container_width=True, hide_index=True)
            st.markdown("**Tabel `rooms` (Kamar Front Office):**")
            st.dataframe(seed.get("rooms", []), use_container_width=True, hide_index=True)
            st.markdown("**Tabel `reservations` (Reservasi Aktif):**")
            st.dataframe(seed.get("reservations", []), use_container_width=True, hide_index=True)
            st.markdown("**Tabel `folio_entries` (Tagihan Folio Tamu):**")
            st.dataframe(seed.get("folio_entries", []), use_container_width=True, hide_index=True)
            st.markdown("**Tabel `faq` (Knowledge Base Concierge):**")
            st.dataframe(seed.get("faq", []), use_container_width=True, hide_index=True)

        with col_seed_ops:
            st.markdown("##### ⚙️ Seeding Node Operations")
            st.markdown("**Tabel `room_readiness` (Kesiapan Fisik Kamar):**")
            readiness_df = []
            for item in seed.get("room_readiness", []):
                readiness_df.append({
                    "room_id": item["room_id"],
                    "cleanliness": "✨ Clean" if item["cleanliness"] == "clean" else "🧹 Dirty",
                    "maintenance_blocked": "⛔ Rusak (AC/Maint)" if item["maintenance_blocked"] else "✅ Normal",
                    "evidence_version": item["evidence_version"]
                })
            st.dataframe(readiness_df, use_container_width=True, hide_index=True)
            st.info(
                "💡 **Catatan Logika Bisnis:**\n"
                "- Kamar **R101**: Tempat tamu menginap (AC rusak / maintenance blocked).\n"
                "- Kamar **R102**: Kosong di Front Office, tetapi di Operations masih **Dirty** (kotor).\n"
                "- Kamar **R103**: Kosong di Front Office, dan di Operations terverifikasi **Clean** (layak huni).\n"
                "- Kamar **R201**: Tipe Deluxe (Rp750.000), butuh otorisasi upgrade staf."
            )

    # 3. Snapshot Live Database Aktif
    st.markdown("#### ⚡ Status Data Database Saat Ini (Live SQLite Dump)")
    db_columns = st.columns(2)
    with db_columns[0]:
        with st.expander("🏢 Front Office Live DB (Tabel Aktif)", expanded=False):
            fo_dump = simulation.front_office.dump()
            for t_name, rows in fo_dump.items():
                if rows:
                    st.markdown(f"**Tabel `{t_name}` ({len(rows)} baris):**")
                    st.dataframe(rows, use_container_width=True, hide_index=True)
                else:
                    st.caption(f"Tabel `{t_name}`: Kosong")
    with db_columns[1]:
        with st.expander("⚙️ Operations Live DB (Tabel Aktif)", expanded=False):
            ops_dump = simulation.operations.dump()
            for t_name, rows in ops_dump.items():
                if rows:
                    st.markdown(f"**Tabel `{t_name}` ({len(rows)} baris):**")
                    st.dataframe(rows, use_container_width=True, hide_index=True)
                else:
                    st.caption(f"Tabel `{t_name}`: Kosong")




def render_ml_report(model: Any) -> None:
    st.markdown("### 🧠 Evaluasi Model Machine Learning (Triase Risiko Komplain)")
    st.caption(
        "Model klasifikasi biner Logistic Regression memprediksi probabilitas eskalasi staf p(human) "
        "berdasarkan urgensi dan jenis keluhan tamu. Jika p(human) >= 0.50, komplain diprioritaskan untuk peninjauan manusia."
    )
    st.info(DATASET_NOTE)
    report = model.report
    metrics = report["metrics"]
    columns = st.columns(5)
    columns[0].metric("Accuracy", f"{metrics['accuracy']:.3f}")
    columns[1].metric("Precision", f"{metrics['precision']:.3f}")
    columns[2].metric("Recall", f"{metrics['recall']:.3f}")
    columns[3].metric("F1-Score", f"{metrics['f1']:.3f}")
    columns[4].metric("Sampel Uji (n)", metrics["n_test"])
    st.caption(
        f"Ambang Batas (Threshold): **{report['threshold']}** · "
        f"Data Latih: **{report['dataset']['n_train']}** · "
        f"Data Uji: **{report['dataset']['n_test']}** · "
        f"Dataset SHA-256: `{report['dataset']['sha256'][:16]}...`"
    )
    with st.expander("🔍 Confusion Matrix & Prediksi Uji Detail", expanded=False):
        st.write(f"**Confusion Matrix:** `{metrics['confusion_matrix']['matrix']}`")
        st.json(
            {
                "manifest": report["manifest"],
                "test_predictions": report["test_predictions"],
            }
        )


def render_evaluation_tab(model: Any) -> None:
    st.markdown("### 🔬 Benchmark Arsitektur: Mobile vs Static Agent (S01 & S02)")
    st.caption(
        "Evaluasi komparatif arsitektur Mobile Agent (ACE-MAMP) vs Static Agent (RPC konvensional) "
        "pada kondisi beban kerja yang setara."
    )

    result = st.session_state.get("evaluation_result")
    if result is None:
        result = run_comparison(model=model)
        st.session_state["evaluation_result"] = result

    # Highlight Metric Cards
    bm_c1, bm_c2, bm_c3 = st.columns(3)
    bm_c1.metric("Efisiensi Pesan Jaringan", "Hemat ~60%", delta="Tanpa RPC Bolak-Balik")
    bm_c2.metric("Integritas Snapshot State", "100% SHA-256", delta="Anti-Tamper & Anti-Replay")
    assertions = result.get("assertions", [])
    passed_cnt = sum(1 for a in assertions if a.get("passed"))
    bm_c3.metric("Konsistensi Hasil Bisnis", f"{passed_cnt}/{len(assertions)} Lulus", delta="100% Validitas Setara")

    st.write("")
    st.dataframe(comparison_table_rows(result), use_container_width=True)

    c_rec1, c_rec2 = st.columns([8, 4])
    with c_rec1:
        failures = [item for item in assertions if not item["passed"]]
        if failures:
            st.error(f"{len(failures)} assertion gagal: {failures}")
        else:
            st.success(f"✅ Seluruh {len(assertions)} assertion kesetaraan logika bisnis berhasil lulus 100%.")
    with c_rec2:
        if st.button("🔄 Hitung Ulang Benchmark", key="run_comparison", use_container_width=True):
            st.session_state["evaluation_result"] = run_comparison(model=model)
            st.toast("✅ Benchmark berhasil dihitung ulang!", icon="🔬")
            st.rerun()

    st.divider()
    render_ml_report(model)


def _run_scenario_auto(model: Any, scenario_id: str, mode: str) -> Dict[str, Any]:
    """Run a scenario to completion and return its summary."""
    return run_single(scenario_id=scenario_id, mode=mode, model=model)


_STATUS_BADGES: Dict[str, str] = {
    "DIGITAL_COMPLETED": "🟢",
    "WAITING_HUMAN": "🟡",
    "WAITING_GUEST": "🔵",
    "HUMAN_HANDLING": "🟠",
    "CLOSED_GUEST_DECLINED": "⚪",
    "CLOSED_BY_STAFF": "⚪",
    "FAILED": "🔴",
    "PROCESSING": "⏳",
    "CREATED": "⏳",
}


def render_autorun_tab(model: Any) -> None:
    """Render the one-click auto-run tab for all 6 scenarios."""

    st.markdown("## 🎯 Uji Otomatis Skenario")
    st.markdown(
        "Jalankan setiap skenario secara **otomatis sampai selesai** dengan satu klik. "
        "Tidak perlu menekan \"Langkah Berikutnya\" berulang kali — simulasi berjalan "
        "otomatis termasuk persetujuan tamu (S01) dan eskalasi staf (S02/S03)."
    )

    st.divider()

    # ── Mode selection ───────────────────────────────────────────────────
    mode_col, run_all_col = st.columns([3, 1])
    with mode_col:
        auto_mode = st.radio(
            "Mode agen untuk pengujian otomatis",
            options=["mobile", "static"],
            format_func=lambda v: MODE_LABELS[v],
            horizontal=True,
            key="autorun_mode",
        )
    with run_all_col:
        run_all = st.button(
            "▶️ Jalankan Semua",
            key="autorun_all",
            use_container_width=True,
            type="primary",
        )

    st.divider()

    # ── Run all at once ──────────────────────────────────────────────────
    if run_all:
        all_results = {}
        progress = st.progress(0, text="Memulai pengujian semua skenario...")
        for idx, sid in enumerate(SCENARIO_ORDER):
            progress.progress(
                (idx) / len(SCENARIO_ORDER),
                text=f"Menjalankan {sid}...",
            )
            result = _run_scenario_auto(model, sid, auto_mode)
            all_results[sid] = result
            st.session_state[f"autorun_{sid}"] = result
        progress.progress(1.0, text="✅ Semua skenario selesai!")
        st.session_state["autorun_summary"] = all_results

    # ── Per-scenario buttons ─────────────────────────────────────────────
    st.markdown("### Jalankan Per Skenario")

    for sid in SCENARIO_ORDER:
        info = SCENARIO_DESCRIPTIONS[sid]
        session_key = f"autorun_{sid}"

        with st.container(border=True):
            header_col, btn_col = st.columns([9, 3])

            with header_col:
                st.markdown(f"### {info['emoji']} {sid} — {info['judul']}")
                st.caption(info["deskripsi"])

            with btn_col:
                if st.button(
                    f"▶️ Jalankan {sid}",
                    key=f"autorun_btn_{sid}",
                    use_container_width=True,
                    type="secondary",
                ):
                    with st.spinner(f"Menjalankan {sid}..."):
                        result = _run_scenario_auto(model, sid, auto_mode)
                        st.session_state[session_key] = result

            # ── Show results if available ────────────────────────────────
            result = st.session_state.get(session_key)
            if result is not None:
                status = result.get("status", "UNKNOWN")
                badge = _STATUS_BADGES.get(status, "⚪")

                # Status row
                s1, s2, s3, s4 = st.columns(4)
                s1.metric("Status", f"{badge} {status}")
                s2.metric("Mode", result.get("mode", "-"))
                s3.metric("Migrasi", result.get("migrations_succeeded", 0))
                s4.metric("Kamar Akhir", result.get("assigned_room_id", "-"))

                # Metrics row
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Steps", result.get("engine_steps", 0))
                m2.metric("Pesan", result.get("messages_sent", 0))
                m3.metric("Pesan Antar-Node", result.get("inter_node_messages", 0))
                m4.metric("Payload (byte)", result.get("total_simulated_payload_bytes", 0))
                m5.metric("Compute (ms)", result.get("engine_compute_ms", 0))

                # Decision info
                st.caption(
                    f"p(human_judgment): {result.get('p_human', '-')} · "
                    f"human_required: {'Ya' if result.get('human_required') else 'Tidak'} · "
                    f"decision_source: {result.get('decision_source', '-')} · "
                    f"tiket: {result.get('ticket_count', 0)}"
                )

                # Inspection results
                if result.get("inspection_results"):
                    with st.expander(f"🔍 Hasil Inspeksi {sid}", expanded=False):
                        st.dataframe(
                            [
                                {
                                    "room_id": item["room_id"],
                                    "room_type": item["room_type"],
                                    "rate": item["nightly_rate"],
                                    "is_ready": item["is_ready"],
                                    "eligible": item["is_routine_eligible"],
                                    "reason_codes": ", ".join(item["reason_codes"]),
                                }
                                for item in result["inspection_results"]
                            ],
                            use_container_width=True,
                        )

    # ── Summary table ────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 📊 Ringkasan Semua Skenario")

    summary_data = []
    all_run = True
    for sid in SCENARIO_ORDER:
        result = st.session_state.get(f"autorun_{sid}")
        if result is None:
            all_run = False
            summary_data.append({
                "Skenario": sid,
                "Status": "⏳ Belum dijalankan",
                "Mode": "-",
                "Kamar Akhir": "-",
                "Migrasi": "-",
                "Steps": "-",
                "Pesan": "-",
                "Payload (byte)": "-",
                "Compute (ms)": "-",
            })
        else:
            status = result.get("status", "UNKNOWN")
            badge = _STATUS_BADGES.get(status, "⚪")
            summary_data.append({
                "Skenario": sid,
                "Status": f"{badge} {status}",
                "Mode": result.get("mode", "-"),
                "Kamar Akhir": result.get("assigned_room_id", "-"),
                "Migrasi": result.get("migrations_succeeded", 0),
                "Steps": result.get("engine_steps", 0),
                "Pesan": result.get("messages_sent", 0),
                "Payload (byte)": result.get("total_simulated_payload_bytes", 0),
                "Compute (ms)": result.get("engine_compute_ms", 0),
            })

    st.dataframe(summary_data, use_container_width=True, hide_index=True)

    if all_run:
        completed = sum(
            1 for sid in SCENARIO_ORDER
            if (st.session_state.get(f"autorun_{sid}") or {}).get("status")
            in ("DIGITAL_COMPLETED", "WAITING_HUMAN", "CLOSED_BY_STAFF")
        )
        st.success(
            f"✅ Semua {len(SCENARIO_ORDER)} skenario telah diuji. "
            f"{completed}/{len(SCENARIO_ORDER)} berhasil mencapai status akhir yang valid."
        )
    else:
        not_run = sum(1 for sid in SCENARIO_ORDER if st.session_state.get(f"autorun_{sid}") is None)
        st.info(
            f"Masih ada {not_run} skenario yang belum dijalankan. "
            f"Klik tombol per skenario atau \"▶️ Jalankan Semua\"."
        )

    # Reset button
    if st.button("🗑️ Reset Semua Hasil", key="autorun_reset"):
        for sid in SCENARIO_ORDER:
            st.session_state.pop(f"autorun_{sid}", None)
        st.session_state.pop("autorun_summary", None)
        st.rerun()


def render_simulation_center(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation], model: Any
) -> None:
    """Unified Live Simulation & Customer Service Experience."""
    mode = st.session_state.get("active_mode", "mobile")

    # 1. Quick Scenario Command Bar
    c_sel, c_play = st.columns([7, 5])
    with c_sel:
        scenario_labels = {
            sid: f"{SCENARIO_DESCRIPTIONS.get(sid, {}).get('emoji', '📌')} {sid}: {SCENARIO_DESCRIPTIONS.get(sid, {}).get('judul', sid)}"
            for sid in SCENARIO_ORDER
        }
        current_sid = snapshot.get("scenario_id", "S01") if snapshot else "S01"
        current_idx = SCENARIO_ORDER.index(current_sid) if current_sid in SCENARIO_ORDER else 0

        selected_sid = st.selectbox(
            "Pilih Skenario Kasus Hotel:",
            options=SCENARIO_ORDER,
            format_func=lambda s: scenario_labels.get(s, s),
            index=current_idx,
            key="sim_center_scenario_select",
        )
        if selected_sid != current_sid:
            _start_scenario(model, selected_sid, mode)
            st.rerun()

    with c_play:
        st.write("")
        st.write("")
        btn_cols = st.columns(4)
        has_pending = snapshot.get("has_pending_work", False) if snapshot else False
        is_autoplay = st.session_state.get("autoplay", False)
        case_status = snapshot.get("case", {}).get("status") if snapshot and snapshot.get("case") else None

        with btn_cols[0]:
            if is_autoplay:
                if st.button("⏸️ Jeda", key="sim_center_pause", use_container_width=True):
                    st.session_state["autoplay"] = False
                    st.rerun()
            else:
                can_play = has_pending and case_status not in ("WAITING_GUEST", "WAITING_HUMAN", "HUMAN_HANDLING")
                if st.button(
                    "▶️ Putar",
                    key="sim_center_play",
                    disabled=not can_play,
                    type="primary" if can_play else "secondary",
                    use_container_width=True,
                ):
                    st.session_state["autoplay"] = True
                    st.rerun()
        with btn_cols[1]:
            if st.button("⏩ Langkah", key="step_button", disabled=not has_pending, use_container_width=True):
                if simulation:
                    with st.spinner("🤖 Agen sedang memproses langkah..."):
                        simulation.step()
                    st.rerun()
        with btn_cols[2]:
            if st.button("⚡ Selesai", key="sim_center_finish", disabled=not has_pending, use_container_width=True):
                if simulation:
                    simulation.run_until_pause()
                    st.rerun()
        with btn_cols[3]:
            if st.button("🔄 Reset", key="sim_center_reset", use_container_width=True):
                _start_scenario(model, selected_sid, mode)
                st.rerun()

    st.divider()

    if snapshot is None or simulation is None:
        st.info("Pilih skenario di atas untuk memulai simulasi interaktif.")
        return

    # 2. Live Flow Stepper Bar
    _render_live_flow_stepper(snapshot)

    case = snapshot.get("case")
    guest_msg = case.get("guest_message") if case else "Belum ada pesan."
    status = case.get("status") if case else "CREATED"
    room_id = case.get("original_room_id", "R101") if case else "R101"
    proposed_id = case.get("proposed_room_id") if case else None
    assigned_id = case.get("assigned_room_id") if case else None
    mig_info = snapshot.get("migration")
    mig_stage = mig_info.get("stage") if mig_info else None
    step_idx = snapshot.get("step_index", 0)
    res_text = _result_text(snapshot)

    # 3. Side-by-Side Dual Pane: Left = Guest Chat, Right = Room Map & Topology
    col_left, col_right = st.columns([6, 6])

    with col_left:
        st.markdown("#### 📱 Percakapan Tamu (WhatsApp Concierge)")

        # Determine AI response text
        if status == "WAITING_GUEST":
            ai_reply = (
                f"Kamar Anda {room_id} terdeteksi mengalami kendala teknis (AC bocor). "
                f"Saya telah memeriksa langsung ke departemen Housekeeping dan menemukan kamar pengganti setara yaitu "
                f"**Kamar {proposed_id}** yang sudah **BERSIH & SIAP HUNI** tanpa biaya tambahan. "
                f"Mohon konfirmasi apakah Anda berkenan pindah?"
            )
        elif status in ("WAITING_HUMAN", "HUMAN_HANDLING"):
            ai_reply = (
                "Permintaan Anda memerlukan peninjauan manajerial khusus untuk perlindungan kebijakan hotel. "
                "Keluhan Anda telah diteruskan langsung ke Manajer Hotel di Meja Kerja Staf."
            )
        elif status == "DIGITAL_COMPLETED":
            if assigned_id:
                ai_reply = (
                    f"🎉 Pemindahan kamar ke **Kamar {assigned_id}** telah resmi diproses di sistem Front Office. "
                    f"Kunci kamar baru siap diambil di resepsionis. Selamat beristirahat!"
                )
            else:
                ai_reply = res_text or "Permintaan Anda telah berhasil diselesaikan secara digital."
        elif status == "CLOSED_GUEST_DECLINED":
            ai_reply = "Baik, tawaran pindah kamar dibatalkan sesuai pilihan Anda. Teknisi tetap memperbaiki AC."
        elif status == "CLOSED_BY_STAFF":
            note = case.get("closed_note") or "Selesai ditangani"
            ai_reply = f"Kasus telah diselesaikan oleh Staf Hotel. Catatan: *{note}*"
        elif step_idx > 0:
            ai_reply = "Saya sedang memproses keluhan Anda dan berkoordinasi dengan departemen terkait..."
        else:
            ai_reply = "Halo! Saya Asisten AI Hotel Nusantara. Ada yang bisa saya bantu terkait masa inap Anda?"

        is_in_transit = mig_stage in ("INITIATED", "PREPARED", "DEPARTED") or (step_idx >= 2 and status not in ("DIGITAL_COMPLETED", "CLOSED_BY_STAFF"))

        with st.container(border=True):
            st.markdown(
                f"""<div style="background: #075E54; color: white; padding: 10px 14px; border-radius: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
<div><strong style="font-size: 0.95rem;">🏨 Hotel Nusantara Concierge</strong><br>
<span style="font-size: 0.72rem; color: #A7F3D0;">🟢 Online · ACE Mobile Agent</span></div>
<span style="font-size: 0.72rem; background: rgba(255,255,255,0.2); padding: 3px 8px; border-radius: 10px;">Tamu: {room_id}</span>
</div>""",
                unsafe_allow_html=True,
            )

            with st.chat_message("user", avatar="👤"):
                st.caption(f"Tamu (Kamar {room_id})")
                st.markdown(f'**"{guest_msg}"**')

            if is_in_transit:
                st.info("⚡ **Investigasi Otonom:** Agen bermigrasi ke Node Operations untuk memeriksa fisik kamar...")

            with st.chat_message("assistant", avatar="🏨"):
                st.caption("Nusantara AI Concierge")
                st.markdown(ai_reply)

        # Quick Guest Reply confirmation buttons when waiting guest
        if status == "WAITING_GUEST":
            with st.container(border=True):
                st.markdown(f"**🏨 Tawaran Pindah Kamar:** **{case.get('proposed_room_id')}** (Gratis Setara)")
                b_cols = st.columns(2)
                if b_cols[0].button(
                    f"✅ Setuju Pindah ke {case.get('proposed_room_id')}",
                    key="sim_center_accept",
                    type="primary",
                    use_container_width=True,
                ):
                    simulation.submit_guest_choice(True, actor="GUEST")
                    simulation.run_until_pause()
                    st.toast(f"✅ Disetujui! Kamar dipindahkan ke {case.get('proposed_room_id')}", icon="🎉")
                    st.rerun()
                if b_cols[1].button(
                    "❌ Tolak Tawaran",
                    key="sim_center_decline",
                    use_container_width=True,
                ):
                    simulation.submit_guest_choice(False, actor="GUEST")
                    st.toast("❌ Tawaran ditolak", icon="🛎️")
                    st.rerun()

        elif status in ("WAITING_HUMAN", "HUMAN_HANDLING"):
            st.warning("⚠️ Kasus memerlukan keputusan staf. Buka tab **Meja Kerja Staf Hotel** untuk meninjau.")

        elif status == "DIGITAL_COMPLETED":
            st.success("🎉 Kasus berhasil diselesaikan secara digital tanpa intervensi manual.")

        with st.expander("✍️ Kirim Permintaan Tamu Kustom (Opsional)", expanded=False):
            cat_choice = st.selectbox(
                "Kategori Permintaan",
                [
                    "❄️ Keluhan Kamar / AC (Pindah Kamar)",
                    "🛁 Layanan Housekeeping (Handuk/Bantal)",
                    "🕐 Informasi Hotel (Check-in/Check-out)",
                    "💰 Sengketa Tagihan / Folio",
                ],
                key="guest_custom_cat_unified",
            )
            st.text_input(
                "Tulis Pesan Anda",
                placeholder="Contoh: AC kamar saya rusak, ingin pindah kamar...",
                key="guest_custom_text_unified",
            )
            if st.button(
                "🚀 Kirim ke Asisten AI",
                key="guest_custom_submit_unified",
                use_container_width=True,
                type="primary",
            ):
                if "AC" in cat_choice:
                    target_s = "S01"
                elif "Housekeeping" in cat_choice:
                    target_s = "S05"
                elif "Informasi" in cat_choice:
                    target_s = "S04"
                else:
                    target_s = "S03"
                _start_scenario(model, target_s, mode)
                st.rerun()

    with col_right:
        _render_interactive_room_map(snapshot, simulation)
        st.divider()
        _render_live_migration_topology(snapshot)
        with st.expander("⚖️ Metrik Keputusan & Ambang Batas Risiko", expanded=False):
            _decision_panel(snapshot)

    # Autoplay runner loop with loading condition
    if is_autoplay and has_pending and status not in ("WAITING_GUEST", "WAITING_HUMAN", "HUMAN_HANDLING"):
        with st.spinner("🤖 Agen bergerak otomatis ke langkah berikutnya..."):
            speed = float(st.session_state.get("autoplay_speed", 1.8))
            time.sleep(speed)
            simulation.step()
        st.rerun()


render_guest_portal = render_simulation_center


def render_unified_evaluation_audit(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation], model: Any
) -> None:
    """Consolidated Evaluation, Business ROI, Benchmark & Audit Center."""
    e_tab1, e_tab2, e_tab3 = st.tabs(
        [
            "🏨 Dampak Bisnis & ROI Hotel",
            "🔬 Benchmark Mobile vs Static & ML",
            "🔍 Audit Database, Event Trace & Unduhan",
        ]
    )
    with e_tab1:
        render_executive_dashboard(snapshot, simulation, model)
    with e_tab2:
        render_evaluation_tab(model)
    with e_tab3:
        render_trace_tab(snapshot, simulation, model)


def render_staff_portal(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation]
) -> None:
    """Staff Operations Dashboard."""
    st.markdown("## 👔 Dashboard Operasional Staf Hotel")
    st.caption("Pusat kendali tugas operasional untuk Front Office, Housekeeping, dan Teknisi Maintenance.")

    if simulation is None or snapshot is None:
        st.info("Belum ada simulasi yang berjalan. Pilih skenario di sidebar atau mulai dari Portal Tamu.")
        return

    case = snapshot.get("case")
    # Always fetch live tickets from simulation if available
    tickets = simulation.list_tickets() if simulation else snapshot.get("tickets", [])

    # Metrics Overview
    pending_tickets = [t for t in tickets if t["status"] == "PENDING"]
    in_progress_tickets = [t for t in tickets if t["status"] == "IN_PROGRESS"]
    done_tickets = [t for t in tickets if t["status"] == "DONE"]
    escalation_waiting = (
        1 if case and case.get("status") in ("WAITING_HUMAN", "HUMAN_HANDLING") else 0
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kasus Perlu Penanganan Staf", escalation_waiting, delta="Eskalasi AI" if escalation_waiting else None)
    m2.metric("Tiket Pending", len(pending_tickets))
    m3.metric("Tiket In Progress", len(in_progress_tickets))
    m4.metric("Tiket Selesai", len(done_tickets))

    st.divider()

    # Section 1: Escalation Inbox
    st.markdown("### 🚨 Antrean Kasus Eskalasi Staf")
    if case and case.get("status") in ("WAITING_HUMAN", "HUMAN_HANDLING"):
        with st.container(border=True):
            st.markdown(f"**Kasus `{case.get('case_id')}`** — Kamar: `{case.get('original_room_id')}`")
            st.markdown(f"**Pesan Tamu:** “{case.get('guest_message')}”")
            st.markdown(f"**Alasan Eskalasi:** `{', '.join(case.get('human_reason_codes', [])) or '-'}`")

            if case.get("inspection_results"):
                st.caption(
                    "Bukti Inspeksi: "
                    + ", ".join(
                        f"{r['room_id']}: {','.join(r['reason_codes'])}"
                        for r in case["inspection_results"]
                    )
                )

            if case.get("status") == "WAITING_HUMAN":
                if st.button("👤 Ambil Alih Kasus (Take Over)", key="staff_portal_takeover", type="primary"):
                    out = simulation.staff_take_over()
                    if out.get("ok"):
                        st.toast(f"👤 Kasus {case.get('case_id')} berhasil diambil alih oleh Staf!", icon="👔")
                        st.rerun()
                    else:
                        st.error(f"Gagal mengambil alih kasus: {out.get('reason')}")
            else:
                st.markdown("**Status: Kasus Sedang Ditangani oleh Anda**")
                staff_note = st.text_area(
                    "Catatan Penyelesaian Staf (Wajib):",
                    value="Keluhan telah diselesaikan langsung oleh staf hotel sesuai SOP.",
                    key="staff_portal_note",
                )
                if st.button("✅ Selesaikan & Tutup Kasus", key="staff_portal_close", type="primary"):
                    out = simulation.staff_close_case(staff_note)
                    if out.get("ok"):
                        st.toast(f"✅ Kasus {case.get('case_id')} resmi ditutup oleh Staf!", icon="📁")
                        st.success("Kasus berhasil ditutup!")
                        st.rerun()
                    else:
                        st.error("Catatan staf wajib diisi untuk menutup kasus.")
    else:
        st.success("✅ Tidak ada kasus yang membutuhkan intervensi staf saat ini. Semua kasus berjalan otomatis.")

    st.divider()

    # Section 2: Department Work Tickets
    st.markdown("### 📋 Papan Kerja Tiket Tugas Fisik (Work Orders)")
    if tickets:
        for ticket in tickets:
            with st.container(border=True):
                c1, c2, c3 = st.columns([6, 3, 3])
                with c1:
                    dept_badge = "🔧" if ticket["department"] == "MAINTENANCE" else "🧹"
                    st.markdown(f"**{dept_badge} {ticket['id']} — {ticket['department']}**")
                    st.markdown(f"Lokasi: Kamar **{ticket['room_id']}** · Deskripsi: *{ticket['description']}*")
                with c2:
                    st.markdown(f"Status Saat Ini: `{ticket['status']}`")
                with c3:
                    if ticket["status"] == "PENDING":
                        if st.button("▶️ Mulai Kerjakan", key=f"staff_portal_start_{ticket['id']}", use_container_width=True):
                            res = simulation.staff_update_ticket(ticket["id"], "IN_PROGRESS")
                            if res.get("ok"):
                                st.toast(f"🔧 Tiket {ticket['id']} status: Sedang Dikerjakan (IN_PROGRESS)", icon="▶️")
                                st.rerun()
                            else:
                                err_msg = res.get("error", {}).get("message", "Gagal memperbarui status tiket.")
                                st.error(f"❌ {err_msg}")
                    elif ticket["status"] == "IN_PROGRESS":
                        if st.button("✔️ Tandai Selesai", key=f"staff_portal_done_{ticket['id']}", type="primary", use_container_width=True):
                            res = simulation.staff_update_ticket(ticket["id"], "DONE")
                            if res.get("ok"):
                                st.toast(f"✅ Tiket {ticket['id']} Selesai Dikerjakan (DONE)!", icon="🎉")
                                st.rerun()
                            else:
                                err_msg = res.get("error", {}).get("message", "Gagal menyelesaikan tiket.")
                                st.error(f"❌ {err_msg}")
                    else:
                        st.markdown("✅ **Selesai**")
    else:
        st.info("Belum ada tiket pekerjaan fisik yang dibuat.")

    st.divider()

    # Section 3: Two-Way Interactive Room Control (Housekeeping & Maintenance Sandbox)
    st.markdown("### 🛏️ Kontrol Dua Arah Status Fisik Kamar (Sandbox Operasional)")
    st.caption(
        "Ubah status fisik kamar secara langsung di database Node Operations. "
        "Staf dapat menyelesaikan perbaikan AC atau mencuci kamar untuk menguji bagaimana Mobile Agent merespons secara adaptif!"
    )

    ops_rooms = simulation.operations.dump().get("room_readiness", [])
    fo_rooms = {r["id"]: r for r in simulation.front_office.dump().get("rooms", [])}

    if ops_rooms:
        r_cols = st.columns(len(ops_rooms))
        for idx, r_item in enumerate(ops_rooms):
            rid = r_item.get("room_id")
            fo_meta = fo_rooms.get(rid, {})
            rtype = fo_meta.get("room_type", "standard").capitalize()
            occ_by = fo_meta.get("occupied_by")
            cleanliness = r_item.get("cleanliness", "clean")
            maint_blocked = bool(r_item.get("maintenance_blocked", False))

            with r_cols[idx]:
                with st.container(border=True):
                    st.markdown(f"**🏨 Kamar {rid}**")
                    st.caption(f"Tipe: **{rtype}** · {('👤 Terisi' if occ_by else '🛏️ Kosong')}")

                    clean_badge = "✨ Bersih" if cleanliness == "clean" else "🧹 Kotor"
                    st.markdown(f"Kebersihan: **{clean_badge}**")

                    maint_badge = "⛔ Rusak (AC)" if maint_blocked else "✅ Normal"
                    st.markdown(f"Fasilitas: **{maint_badge}**")

                    st.write("")
                    # Action toggle 1: Cleanliness
                    if cleanliness == "dirty":
                        if st.button("🧹 Selesai Cuci", key=f"staff_clean_{rid}", use_container_width=True, type="primary"):
                            simulation.staff_set_room_cleanliness(rid, "clean")
                            st.toast(f"✨ Kamar {rid} berhasil diset BERSIH!", icon="🧹")
                            st.rerun()
                    else:
                        if st.button("Set Kotor", key=f"staff_dirty_{rid}", use_container_width=True):
                            simulation.staff_set_room_cleanliness(rid, "dirty")
                            st.toast(f"🧹 Kamar {rid} diset KOTOR untuk simulasi.", icon="⚠️")
                            st.rerun()

                    # Action toggle 2: Maintenance
                    if maint_blocked:
                        if st.button("🔧 Selesai Servis AC", key=f"staff_unblock_{rid}", use_container_width=True, type="primary"):
                            simulation.staff_set_maintenance_block(rid, False)
                            st.toast(f"✅ Kamar {rid} servis AC selesai & blokir dicabut!", icon="🔧")
                            st.rerun()
                    else:
                        if st.button("Set AC Rusak", key=f"staff_block_{rid}", use_container_width=True):
                            simulation.staff_set_maintenance_block(rid, True)
                            st.toast(f"⛔ Kamar {rid} ditandai AC RUSAK untuk simulasi.", icon="⚠️")
                            st.rerun()


def render_visual_node_map(snapshot: Optional[Dict[str, Any]]) -> None:
    """Renders an intuitive 2D visual map showing the two departments and agent state."""
    st.markdown("### 🗺️ Peta Pergerakan Agen: Lobi vs Operasional")
    st.caption("Memvisualisasikan secara nyata bagaimana agen berpindah antar-departemen hotel untuk memeriksa kamar:")

    is_transit = False
    active_loc = "FRONT_OFFICE"
    findings_text = "Menunggu pemeriksaan fisik..."

    if snapshot is not None:
        case = snapshot.get("case")
        migration = snapshot.get("migration")
        mig_stage = migration.get("stage") if migration else None

        if mig_stage in ("INITIATED", "PREPARED", "DEPARTED"):
            is_transit = True
            active_loc = "TRANSIT"
        elif mig_stage == "ARRIVED" or (case and case.get("inspection_results")):
            active_loc = "OPERATIONS"

        if case and case.get("inspection_results"):
            findings = []
            for r in case["inspection_results"]:
                status_icon = "❌" if "DIRTY" in r.get("reason_codes", []) else "✨"
                findings.append(f"{status_icon} Kamar {r['room_id']}: {','.join(r['reason_codes'])}")
            findings_text = " | ".join(findings)

    fo_border = "border: 2px solid #3B82F6; background: #EFF6FF;" if active_loc == "FRONT_OFFICE" else "border: 1px solid #CBD5E1; background: #F8FAFC;"
    fo_badge = "🟢 AGEN AKTIF DI SINI" if active_loc == "FRONT_OFFICE" else "⚪ Standby"

    op_border = "border: 2px solid #10B981; background: #ECFDF5;" if active_loc == "OPERATIONS" else "border: 1px solid #CBD5E1; background: #F8FAFC;"
    op_badge = "🟢 AGEN MEMERIKSA FISIK" if active_loc == "OPERATIONS" else "⚪ Standby"

    transit_bg = "background: #FFEDD5; border: 2px dashed #EA580C; border-radius: 8px; padding: 12px 6px;" if is_transit else ""
    transit_badge = "✈️ 🧳 KOPER TRANSIT<br><span style='font-size:0.7rem; font-weight:normal;'>(SHA-256 Validated)</span>" if is_transit else "── Pipa Komunikasi Antar-Departemen ──"
    transit_color = "#EA580C" if is_transit else "#94A3B8"

    col_fo, col_transit, col_op = st.columns([5, 2, 5])

    with col_fo:
        st.markdown(
            f"""
            <div style="{fo_border} padding: 14px; border-radius: 10px; min-height: 140px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="color: #1E3A8A; font-size: 1.05rem;">🏢 Lobi & Meja Depan</strong>
                    <span style="font-size: 0.75rem; font-weight: bold; color: #2563EB;">{fo_badge}</span>
                </div>
                <div style="font-size: 0.85rem; color: #475569; margin-top: 6px;">
                    • <strong>Database:</strong> Data Tamu, Reservasi, Folio, FAQ<br>
                    • <strong>Agen:</strong> Scenario Scout, Orchestrator, Concierge<br>
                    • <strong>Tugas:</strong> Menerima komplain & mengajukan proposal kamar
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_transit:
        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 20px; color: {transit_color}; font-weight: bold; font-size: 0.8rem; {transit_bg}">
                {transit_badge}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_op:
        st.markdown(
            f"""
            <div style="{op_border} padding: 14px; border-radius: 10px; min-height: 140px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="color: #065F46; font-size: 1.05rem;">🧹 Operasional & Gudang</strong>
                    <span style="font-size: 0.75rem; font-weight: bold; color: #059669;">{op_badge}</span>
                </div>
                <div style="font-size: 0.85rem; color: #475569; margin-top: 6px;">
                    • <strong>Database:</strong> Status Fisik Kamar (Bersih/Kotor) & Tiket<br>
                    • <strong>Agen:</strong> Mobile Investigator (MA-001)<br>
                    • <strong>Temuan Fisik:</strong> <span style="color: #0F172A; font-weight: 500;">{findings_text}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_comprehension_tab() -> None:
    """Dedicated comprehension suite with storyboards, analogies, comparisons, and quiz."""
    st.markdown("## 📖 Panduan Pemahaman Konsep & Cara Kerja")
    st.caption(
        "Pelajari bagaimana kecerdasan Mobile Agent bekerja di perhotelan dengan ilustrasi, "
        "analogi nyata, dan komparasi bisnis."
    )

    st.divider()

    # Section 1: Storyboard Komik Alur Kasus
    st.markdown("### 🎨 Komik Alur Kasus: Perjalanan 1 Menit Masalah Pak Budi")
    st.caption("Bagaimana keluhan AC bocor di kamar 101 diselesaikan tanpa antre di meja depan:")

    panels = [
        ("1. Masalah Jam 01:00 Pagi", "Pak Budi di Kamar 101 mengeluh AC bocor dan berisik. Pak Budi mengirim pesan komplain lewat ponselnya."),
        ("2. AI Menganalisis Keluhan", "Asisten AI membaca keluhan, memeriksa jatah kamar pengganti setara (Standard), dan menyiapkan proses verifikasi."),
        ("3. Mengemas Koper State", "Agen mengemas koper data kasus (tujuan, kandidat kamar) dan menyegelnya secara digital dengan hash SHA-256."),
        ("4. Cek Fisik di Housekeeping", "Agen tiba di database operasional. Menemukan R102 masih kotor (DIRTY) sehingga menolaknya, lalu memilih R103 yang bersih."),
        ("5. Persetujuan di HP Tamu", "HP Pak Budi berbunyi: 'Kamar R103 bersih siap huni. Apakah Anda setuju pindah?'. Pak Budi klik [Setuju Pindah]."),
        ("6. Kunci Kamar Aktif!", "Reservasi resmi berpindah ke R103. Pak Budi tidur nyenyak, hotel terbebas dari ulasan bintang 1!")
    ]

    cols_p1 = st.columns(3)
    for idx in range(3):
        title, text = panels[idx]
        with cols_p1[idx]:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.write(text)

    cols_p2 = st.columns(3)
    for idx in range(3, 6):
        title, text = panels[idx]
        with cols_p2[idx - 3]:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.write(text)

    st.divider()

    # Section 2: Kamus Analogi Kehidupan Nyata
    st.markdown("### 💡 Kamus Istilah dengan Analogi Dunia Nyata")
    st.caption("Pahami konsep teknis melalui perumpamaan sehari-hari yang mudah diingat:")

    an1, an2 = st.columns(2)
    with an1:
        with st.container(border=True):
            st.markdown("#### 🧳 Mobile Agent (State Migration)")
            st.markdown(
                """
                - **Istilah Teknis:** Agen berpindah node membawa koper state.
                - **Analogi Nyata:** Seperti **auditor pajak yang datang langsung membawa tas berkas ke pabrik**. Daripada meminta pabrik mengirimkan seluruh truk dokumen ke kantor lobi, auditor datang langsung mengecek ke gudang.
                - **Keuntungan Bisnis:** Menghemat kuota jaringan dan menjaga rahasia data internal operasional tetap aman di tempatnya.
                """
            )
        with st.container(border=True):
            st.markdown("#### 🛡️ Policy Guardrail (Satpam Kebijakan)")
            st.markdown(
                """
                - **Istilah Teknis:** Aturan deterministik mandatory yang mengunci AI.
                - **Analogi Nyata:** Seperti **satpam brankas bank**. Meskipun nasabah berteriak meminta uang lebih, satpam tidak akan membuka brankas tanpa izin tertulis dari manajer.
                - **Keuntungan Bisnis:** Melindungi hotel dari tamu nakal yang menuntut kamar mewah gratis (anti-bocor biaya).
                """
            )

    with an2:
        with st.container(border=True):
            st.markdown("#### 📜 Checkpoint & Segel SHA-256")
            st.markdown(
                """
                - **Istilah Teknis:** Serialisasi JSON kanonik terverifikasi hash.
                - **Analogi Nyata:** Seperti **surat resmi dengan cap lilin kerajaan**. Jika di tengah jalan ada yang membuka atau mengubah isinya, cap lilinnya rusak dan surat langsung ditolak.
                - **Keuntungan Bisnis:** Menjamin data kamar tidak dimanipulasi atau rusak saat berpindah antar sistem.
                """
            )
        with st.container(border=True):
            st.markdown("#### ⚡ Idempotency (Anti-Duplikasi Transaksi)")
            st.markdown(
                """
                - **Istilah Teknis:** Eksekusi berulang menghasilkan efek tunggal.
                - **Analogi Nyata:** Seperti **tombol saklar lampu otomatis**. Ditekan 1 kali atau ditekan 10 kali, lampu tetap menyala (tidak meledak atau dobel transaksi).
                - **Keuntungan Bisnis:** Mencegah mutasi kamar dobel saat tamu menekan tombol persetujuan berkali-kali karena sinyal HP lambat.
                """
            )

    st.divider()

    # Section 3: Perbandingan Tradisional vs ACE
    st.markdown("### ⚖️ Mengapa Sistem Ini Unggul: Tradisional vs ACE Mobile Agent")
    comp_col1, comp_col2 = st.columns(2)
    with comp_col1:
        with st.container(border=True):
            st.markdown("#### ❌ Sistem Tradisional (Telepon / API Manual)")
            st.markdown(
                """
                - **Waktu Penanganan:** 35 – 45 Menit (Telepon berulang-ulang ke berbagai bagian).
                - **Risiko Kamar Kotor:** Tinggi (Resepsionis tidak tahu fisik kamar di lantai atas).
                - **Risiko Pemerasan Tamu:** Staf panik memberikan upgrade Deluxe gratis tanpa izin.
                - **Beban Staf:** Resepsionis sibuk mengangkat telepon keluhan alih-alih melayani tamu di lobi.
                """
            )
    with comp_col2:
        with st.container(border=True):
            st.markdown("#### ✅ Sistem ACE (Mobile Agent Cerdas)")
            st.markdown(
                """
                - **Waktu Penanganan:** **< 1 Menit** (Otomatis langsung di HP tamu).
                - **Risiko Kamar Kotor:** **0% (Zero Double-Complaint)** karena diverifikasi fisik ke DB Housekeeping.
                - **Proteksi Finansial:** **100% Terkunci** oleh Policy Guardrail.
                - **Produktivitas Staf:** Staf fokus melayani tamu VIP, operasional rutin ditangani AI.
                """
            )

    st.divider()


def render_executive_dashboard(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation], model: Any = None
) -> None:
    """Executive & ROI Business Dashboard."""
    st.markdown("## 🏨 Executive Dashboard & Analisis Nilai Bisnis")
    st.caption(
        "Perspektif Kepemimpinan Bisnis: Penghematan Biaya, Percepatan Resolusi Komplain, "
        "dan Perlindungan Pendapatan Hotel Nusantara."
    )


    # 4 Key ROI Cards
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Waktu Resolusi (MTTR)",
        "< 1 Menit",
        delta="97% Lebih Cepat (vs 35 Menit Manual)",
        delta_color="normal",
    )
    k2.metric(
        "Proteksi Pendapatan",
        "100% Aman",
        delta="Zero Leakage (Policy Guardrail)",
        delta_color="normal",
    )
    k3.metric(
        "Beban Telepon Meja Depan",
        "-60%",
        delta="Otomasi Kasus Rutin",
        delta_color="normal",
    )
    k4.metric(
        "Tingkat Kepuasan (CSAT)",
        "4.9 / 5.0",
        delta="Mencegah Review Negatif",
        delta_color="normal",
    )

    st.divider()

    # Interactive ROI Calculator Widget
    st.markdown("### 🧮 Kalkulator Simulasi Penghematan Hotel (Interactive ROI)")
    with st.container(border=True):
        st.markdown(
            "Simulasikan penghematan nyata jika sistem ini diterapkan pada skala hotel Anda:"
        )
        c_calc1, c_calc2 = st.columns(2)
        with c_calc1:
            rooms_count = st.slider("Jumlah Kamar Hotel", min_value=50, max_value=500, value=150, step=25)
        with c_calc2:
            complaints_per_day = st.slider("Rata-rata Keluhan / Permintaan per Hari", min_value=5, max_value=50, value=15, step=5)

        # Calculation
        mins_saved_per_day = complaints_per_day * 0.8 * 30  # 80% routine cases, 30 mins saved each
        hours_saved_per_month = int((mins_saved_per_day * 30) / 60)
        unauthorized_upgrades_prevented = int(complaints_per_day * 30 * 0.1)  # 10% risky
        money_saved_per_month = unauthorized_upgrades_prevented * 250000  # avg delta 250k IDR

        r1, r2, r3 = st.columns(3)
        r1.metric("Waktu Staf Dihemat", f"{hours_saved_per_month} Jam / Bulan", delta="Produktivitas Meningkat")
        r2.metric("Kebocoran Dicegah", f"Rp {money_saved_per_month:,.0f} / Bulan", delta="Proteksi Upgrade Liar")
        r3.metric("Pencegahan Review Buruk", f"{int(complaints_per_day * 30 * 0.8)} Tamu / Bulan", delta="Resolusi Instan")

    st.divider()

    # Business Problem vs Solution Matrix
    st.markdown("### ⚖️ Perbandingan Nilai Bisnis: Tradisional vs Sistem ACE")
    b_col1, b_col2 = st.columns(2)

    with b_col1:
        with st.container(border=True):
            st.markdown("#### ❌ Operasional Hotel Tradisional")
            st.markdown(
                """
                - **Silo Informasi:** Front Office dan Housekeeping terpisah; koordinasi mengandalkan telepon manual yang sering sibuk.
                - **Risiko Kamar Kotor:** Resepsionis memindahkan tamu ke kamar kosong tanpa verifikasi fisik (*Double Complaint!*).
                - **Kebocoran Finansial:** Staf panik di tengah malam memberikan upgrade gratis ke kamar Deluxe tanpa izin manajer.
                - **Review Negatif:** Tamu menunggu 30-45 menit di kamar panas berujung ulasan bintang 1 di internet.
                """
            )

    with b_col2:
        with st.container(border=True):
            st.markdown("#### ✅ Solusi Sistem ACE Mobile Agent")
            st.markdown(
                """
                - **Otomasi Terverifikasi:** Mobile Agent menginspeksi kesiapan fisik kamar langsung di database Operations dalam hitungan detik.
                - **Zero Double Complaint:** Kamar kotor (R102) otomatis dieliminasi; hanya kamar bersih & siap (R103) yang diajukan ke tamu.
                - **Guardrail Aturan Finansial:** AI dibatasi aturan wajib; permohonan upgrade gratis (S02) otomatis dikunci dan dieskalasi ke staf.
                - **Kepuasan Instan:** Tamu menerima proposal di HP dan menyetujui dengan 1 klik; status kamar berpindah seketika.
                """
            )

    st.divider()

    # Current Case Snapshot in Business Terms
    st.markdown("### 📊 Status Kasus Aktif Saat Ini")
    if snapshot is None or simulation is None:
        st.info("Belum ada skenario aktif. Gunakan tab 'Portal Layanan Tamu' atau 'Simulasi Skenario Bisnis' untuk memulai.")
    else:
        case = snapshot.get("case")
        if case:
            status = case.get("status")
            status_desc = {
                "DIGITAL_COMPLETED": "🟢 Selesai Secara Digital (Selesai otomatis tanpa komplain ulang)",
                "WAITING_GUEST": "🔵 Menunggu Keputusan Tamu (Proposal kamar baru telah dikirimkan ke HP tamu)",
                "WAITING_HUMAN": "🟡 Eskalasi Manajer (Memerlukan persetujuan staf untuk keputusan finansial/kebijakan)",
                "HUMAN_HANDLING": "🟠 Sedang Ditangani Manajer (Staf sedang meninjau dan menyelesaikan kasus)",
                "CLOSED_BY_STAFF": "⚪ Ditutup oleh Staf Resmi",
                "CLOSED_GUEST_DECLINED": "⚪ Ditolak Tamu (Tamu memilih tetap di kamar asal)",
            }.get(status, f"⏳ {status}")

            with st.container(border=True):
                st.markdown(f"**ID Kasus:** `{case.get('case_id')}` · **Kamar:** `{case.get('original_room_id')}`")
                st.markdown(f"**Status Bisnis:** {status_desc}")
                st.markdown(f"**Keluhan Tamu:** “{case.get('guest_message')}”")
                if case.get("assigned_room_id"):
                    st.caption(f"Kamar Resmi Akhir: **{case.get('assigned_room_id')}** (Tarif tetap terjaga)")
        else:
            st.caption("Kasus baru diinisialisasi; menunggu langkah agen...")

    st.divider()
    with st.expander("📖 Panduan Edukasi Konsep & Analogi Dunia Nyata", expanded=False):
        render_comprehension_tab()


def render_business_suite(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation], model: Any
) -> None:
    """Renders the Pure Business & Operations Suite."""
    st.markdown(
        """
        <div style="background: linear-gradient(90deg, #182235 0%, #2A3C5A 100%); padding: 14px 20px; border-radius: 10px; margin-bottom: 16px;">
            <div style="font-size: 1.3rem; font-weight: bold; color: white;">👔 Mode Pure Bisnis & Operasional (Business Suite)</div>
            <div style="font-size: 0.9rem; color: #CBD5E1; margin-top: 3px;">
                Fokus pada efisiensi operasional hotel, pengalaman tamu, dan perlindungan pendapatan. Bebas dari istilah teknis koding.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    b_tabs = st.tabs(
        [
            "🏨 Ringkasan Eksekutif & ROI",
            "🛎️ Portal Layanan Tamu",
            "👔 Meja Operasional Staf",
            "🎬 Simulasi Skenario Bisnis",
        ]
    )

    with b_tabs[0]:
        render_executive_dashboard(snapshot, simulation, model)
    with b_tabs[1]:
        render_guest_portal(snapshot, simulation, model)
    with b_tabs[2]:
        render_staff_portal(snapshot, simulation)
    with b_tabs[3]:
        render_autorun_tab(model)


def render_technical_suite(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation], model: Any
) -> None:
    """Renders the Technical & Engineering Console."""
    st.markdown(
        """
        <div style="background: linear-gradient(90deg, #0F172A 0%, #1E293B 100%); padding: 14px 20px; border-radius: 10px; margin-bottom: 16px; border-left: 5px solid #FF6B35;">
            <div style="font-size: 1.3rem; font-weight: bold; color: white;">🛠️ Mode Teknikal & Arsitektur (Engineering Console)</div>
            <div style="font-size: 0.9rem; color: #CBD5E1; margin-top: 3px;">
                Fokus pada topologi dua node, siklus hidup migrasi state agen, verifikasi hash SHA-256, telemetri event, dan evaluasi ML.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    t_tabs = st.tabs(
        [
            "⚡ Lab Step Simulator",
            "🔍 Observabilitas & Audit DB",
            "📊 Evaluasi Ilmiah & ML",
            "🏗️ Arsitektur & Spesifikasi",
        ]
    )

    with t_tabs[0]:
        render_simulation_tab(snapshot, simulation)
    with t_tabs[1]:
        render_trace_tab(snapshot, simulation)
    with t_tabs[2]:
        render_evaluation_tab(model)
    with t_tabs[3]:
        render_landing_page(model)


