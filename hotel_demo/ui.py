"""Rendering Streamlit. Hanya memanggil public method Simulation, tidak menulis DB."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import streamlit as st

from .evaluation import comparison_table_rows, run_comparison
from .ml import DATASET_NOTE
from .simulation import SCENARIO_ORDER, Simulation, load_scenarios

MODE_LABELS = {"mobile": "Mobile Agent", "static": "Static Agent"}


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
            return f"Rincian tagihan total Rp{folio.get('total', 0):,}".replace(",", ".")
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
    columns[1].metric("Threshold", f"{snapshot['scenario'].get('threshold', 0.80)}")
    columns[2].metric("Model recommends human", "Ya" if case["model_recommends_human"] else "Tidak")
    columns[3].metric("human_required", "Ya" if case["human_required"] else "Tidak")
    st.caption(
        f"mandatory_reasons: {case['mandatory_reasons'] or '-'} · "
        f"final_decision: {'REVIEW' if case['human_required'] else 'ALLOW'} · "
        f"decision_source: {case['decision_source']} · priority: {case['priority']} · "
        f"reason_codes: {case['human_reason_codes'] or '-'}"
    )


def render_simulation_tab(snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation]) -> None:
    if snapshot is None or simulation is None:
        st.info("Pilih salah satu skenario di sidebar untuk memulai run baru.")
        return

    st.markdown(f"**Mode aktif:** `{snapshot['active_mode']}` · **Run:** `{snapshot['run_id']}`")
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
                st.warning("Agen berada di jalur transfer; tidak ada instance aktif pada node mana pun.")

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


def render_trace_tab(snapshot: Optional[Dict[str, Any]], simulation: Optional[Simulation]) -> None:
    if snapshot is None or simulation is None:
        st.info("Belum ada run.")
        return

    st.markdown("#### Metrik")
    metrics = snapshot["metrics"]
    total_payload = metrics["inter_node_message_bytes"] + metrics["transferred_checkpoint_bytes"]
    columns = st.columns(4)
    columns[0].metric("Pesan (MESSAGE_SENT)", metrics["messages_sent"])
    columns[1].metric("Pesan antar-node", metrics["inter_node_messages"])
    columns[2].metric("Migrasi sukses/gagal", f"{metrics['migrations_succeeded']}/{metrics['migrations_failed']}")
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
        st.json({"manifest": report["manifest"], "test_predictions": report["test_predictions"]})


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
