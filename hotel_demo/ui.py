"""Rendering Streamlit. Hanya memanggil public method Simulation, tidak menulis DB."""

from __future__ import annotations

import json
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
            "Buka **sidebar** (kiri) dan klik salah satu skenario S01–S06.",
        ),
        (
            "🔄",
            "2. Jalankan Simulasi",
            'Tekan **"Langkah Berikutnya"** di tab Simulasi untuk maju step-by-step.',
        ),
        (
            "🔍",
            "3. Lihat Jejak",
            'Buka tab **"Jejak & State"** untuk melihat pesan, event, dan checkpoint migrasi.',
        ),
        (
            "📊",
            "4. Evaluasi",
            'Buka tab **"Evaluasi"** dan klik **"Jalankan Perbandingan"** untuk membandingkan Mobile vs Static.',
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
    st.markdown("## 🎬 6 Skenario Demo")
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
    st.title("Demo Mobile Agent Hotel")
    st.caption(
        "Simulasi multi-agent customer service hotel dengan migrasi state mobile agent "
        "antar-node logis dalam satu proses Python."
    )
    st.markdown(
        "`Lokal` · `Data Simulasi` · `Tanpa API` · Dua node logis: "
        "**FRONT_OFFICE** dan **OPERATIONS**"
    )
    st.caption(
        "Simulasi migrasi state agen antar-node logis dalam satu proses Python; "
        "kode agen tersedia di kedua node."
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


def render_sidebar(model: Any) -> None:
    scenarios = load_scenarios()
    with st.sidebar:
        st.subheader("Kontrol Demo")
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

        st.markdown("**Skenario**")
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
        with st.expander("Aturan otonomi agen", expanded=False):
            st.markdown(
                "- Agen boleh memindahkan tamu ke kamar **setara, bersih, kosong, "
                "tanpa biaya tambahan** hanya setelah persetujuan tamu dan semua aturan terpenuhi.\n"
                "- Refund/kompensasi, upgrade di luar aturan, sengketa tagihan, permintaan manusia, "
                "dan darurat **wajib diteruskan ke staf**.\n"
                "- Policy wajib selalu menang atas prediksi ML."
            )
        with st.expander("Tentang Demo", expanded=False):
            st.markdown(
                "**Kelompok 5**\n\n"
                "- M. Al lail Qadrillah\n"
                "- Dimas Prabowo\n"
                "- Monanta Alfiareza\n"
                "- Frans Alwan\n\n"
                "Hotel fiktif **Hotel Nusantara Demo**. Seluruh data sintetis dan lokal. "
                "NIM/PIC belum diisi. DL/RL/GNN tidak diimplementasikan pada MVP."
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


def render_simulation_tab(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation]
) -> None:
    if snapshot is None or simulation is None:
        st.info("Pilih salah satu skenario di sidebar untuk memulai run baru.")
        return

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
                st.rerun()
            if guest_columns[1].button(
                "Tamu: Tolak perpindahan", key="guest_decline", use_container_width=True
            ):
                simulation.submit_guest_choice(False, actor="GUEST")
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


def render_trace_tab(
    snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation]
) -> None:
    if snapshot is None or simulation is None:
        st.info("Belum ada run.")
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

    st.markdown("#### Snapshot Database")
    db_columns = st.columns(2)
    with db_columns[0]:
        with st.expander("Front Office DB", expanded=False):
            st.json(simulation.front_office.dump())
    with db_columns[1]:
        with st.expander("Operations DB", expanded=False):
            st.json(simulation.operations.dump())

    st.download_button(
        "Unduh Log JSON",
        data=simulation.export_json(),
        file_name=f"{snapshot['run_id']}-{snapshot['scenario_id']}-{snapshot['active_mode']}.json",
        mime="application/json",
        key="download_log",
    )


def render_ml_report(model: Any) -> None:
    st.markdown("#### Report ML Sintetis")
    st.info(DATASET_NOTE)
    report = model.report
    metrics = report["metrics"]
    columns = st.columns(5)
    columns[0].metric("Accuracy", f"{metrics['accuracy']:.3f}")
    columns[1].metric("Precision", f"{metrics['precision']:.3f}")
    columns[2].metric("Recall", f"{metrics['recall']:.3f}")
    columns[3].metric("F1", f"{metrics['f1']:.3f}")
    columns[4].metric("n test", metrics["n_test"])
    st.caption(
        f"Threshold {report['threshold']} · train {report['dataset']['n_train']} · "
        f"test {report['dataset']['n_test']} · hash dataset `{report['dataset']['sha256'][:16]}` · "
        f"confusion matrix {metrics['confusion_matrix']['matrix']}"
    )
    with st.expander("Manifest & prediksi uji", expanded=False):
        st.json(
            {
                "manifest": report["manifest"],
                "test_predictions": report["test_predictions"],
            }
        )


def render_evaluation_tab(model: Any) -> None:
    st.markdown("#### Perbandingan Static vs Mobile (S01 & S02)")
    st.caption(
        "Perbandingan simulator lokal. Waktu komputasi dan ukuran payload bukan "
        "benchmark jaringan/produksi."
    )
    if st.button("Jalankan Perbandingan", key="run_comparison"):
        st.session_state["evaluation_result"] = run_comparison(model=model)
    result = st.session_state.get("evaluation_result")
    if result is None:
        st.caption("Belum dijalankan. Run aktif tidak akan berubah.")
    else:
        st.dataframe(comparison_table_rows(result), use_container_width=True)
        assertions = result["assertions"]
        failures = [item for item in assertions if not item["passed"]]
        if failures:
            st.error(f"{len(failures)} assertion gagal: {failures}")
        else:
            st.success(f"Semua {len(assertions)} assertion kesetaraan lulus.")
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
