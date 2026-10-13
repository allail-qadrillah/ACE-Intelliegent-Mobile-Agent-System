"""Skrip untuk membuat diagram visual arsitektur database ACE System (Dual-Node SQLite).
Menghasilkan format gambar resolusi tinggi (PNG) dan dokumen Mermaid Markdown di folder `docs/diagrams/`.
"""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

DIAGRAM_DIR = Path(__file__).resolve().parent / "docs" / "diagrams"
DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)


def generate_mermaid_markdown() -> Path:
    mermaid_content = """# Diagram Struktur Database Dual-Node SQLite
## ACE — Intelligent Mobile Agent System

Diagram relasi entitas (*Entity-Relationship Diagram*) berikut menunjukkan pemisahan dua basis data SQLite in-memory:
1. **Node FRONT_OFFICE**: Basis data untuk administrasi tamu, reservasi, tarif kamar, penagihan folio, dan status kasus.
2. **Node OPERATIONS**: Basis data operasional kamar fisik (kebersihan, blokir maintenance) dan tiket staf.

```mermaid
erDiagram
    %% Node FRONT_OFFICE
    GUESTS ||--o{ RESERVATIONS : "has"
    ROOMS ||--o| RESERVATIONS : "occupied_by"
    RESERVATIONS ||--o{ FOLIO_ENTRIES : "contains"
    CASES ||--o{ AUDIT_EVENTS : "tracks"
    APPLIED_OPERATIONS_FO ||--|| ROOMS : "atomically mutates"

    %% Node OPERATIONS
    ROOM_READINESS ||--o{ TICKETS : "room_reference"
    APPLIED_OPERATIONS_OPS ||--|| TICKETS : "idempotency_guard"

    %% Entitas Node FRONT_OFFICE
    GUESTS {
        TEXT id PK "ID Tamu (cth: G001)"
        TEXT name "Nama Tamu"
    }
    ROOMS {
        TEXT id PK "ID Kamar (cth: R101)"
        TEXT room_type "standard / deluxe"
        INTEGER nightly_rate "Tarif per malam"
        TEXT occupied_by FK "ID Reservasi (nullable)"
        INTEGER version "Optimistic Locking"
    }
    RESERVATIONS {
        TEXT id PK "ID Reservasi (cth: RES001)"
        TEXT guest_id FK "Relasi ke guests.id"
        TEXT room_id FK "Relasi ke rooms.id"
        TEXT room_type "Tipe kamar yang dipesan"
        INTEGER nightly_rate "Tarif terkonfirmasi"
        TEXT status "checked_in / checked_out"
        INTEGER version "Optimistic Locking"
    }
    FOLIO_ENTRIES {
        TEXT id PK "ID Folio (cth: F01, F02)"
        TEXT reservation_id FK "Relasi ke reservations.id"
        TEXT description "Keterangan biaya"
        INTEGER amount "Nominal Rupiah"
    }
    FAQ {
        TEXT key PK "Kata kunci (check_in, wifi)"
        TEXT answer "Jawaban resmi hotel"
    }
    CASES {
        TEXT id PK "ID Kasus (cth: CASE-001)"
        TEXT scenario_id "S01 s.d S09"
        TEXT status "PROCESSING, WAITING_GUEST, dll"
        INTEGER human_required "1 jika butuh intervensi manusia"
        TEXT reason_codes_json "Alasan penolakan / eskalasi"
        TEXT proposed_room_id "Kamar yang ditawarkan"
        INTEGER proposal_version "Versi proposal"
        TEXT consent_json "Rekaman persetujuan tamu"
        TEXT priority "NORMAL / URGENT"
        TEXT state_json "State lengkap kasus"
    }
    AUDIT_EVENTS {
        INTEGER seq PK "Nomor urut audit autoincrement"
        TEXT event_type "Tipe aksi / peristiwa"
        TEXT payload_json "Snapshot payload peristiwa"
    }
    APPLIED_OPERATIONS_FO {
        TEXT operation_key PK "Kunci idempotensi transaksi"
        TEXT result_json "Hasil commit sebelumnya"
    }

    %% Entitas Node OPERATIONS
    ROOM_READINESS {
        TEXT room_id PK "ID Kamar (cth: R101, R102)"
        TEXT cleanliness "clean / dirty"
        INTEGER maintenance_blocked "1 jika AC rusak / perbaikan"
        INTEGER evidence_version "Versi bukti fisik"
    }
    TICKETS {
        TEXT id PK "ID Tiket (cth: TICKET-S01-001)"
        TEXT operation_key UK "Kunci unik pencegah tiket ganda"
        TEXT case_id "ID Kasus terkait"
        TEXT room_id "Kamar tujuan perbaikan"
        TEXT department "MAINTENANCE / HOUSEKEEPING"
        TEXT description "Deskripsi tugas staf"
        TEXT status "PENDING, IN_PROGRESS, DONE"
    }
    APPLIED_OPERATIONS_OPS {
        TEXT operation_key PK "Kunci idempotensi tiket fisik"
        TEXT result_json "Hasil pembuatan tiket"
    }
```
"""
    md_file = DIAGRAM_DIR / "database_schema_diagram.md"
    md_file.write_text(mermaid_content, encoding="utf-8")
    print(f"Diagram Mermaid tersimpan di: {md_file}")
    return md_file


def generate_png_diagram() -> Path:
    fig, ax = plt.subplots(figsize=(16, 11), dpi=200)
    fig.patch.set_facecolor("#0F172A")  # Slate Navy background
    ax.set_facecolor("#0F172A")
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11)
    ax.axis("off")

    # Title & Subtitle
    ax.text(
        8.0, 10.4,
        "STRUKTUR DATABASE DUAL-NODE SQLITE",
        fontsize=20, fontweight="bold", color="#F8FAFC", ha="center"
    )
    ax.text(
        8.0, 10.0,
        "ACE — Intelligent Mobile Agent System (Isolasi Data Front Office vs Operations)",
        fontsize=12, color="#38BDF8", ha="center"
    )

    # -------------------------------------------------------------
    # Container Node 1: FRONT_OFFICE (Left)
    # -------------------------------------------------------------
    fo_box = FancyBboxPatch(
        (0.6, 0.6), 7.0, 9.0,
        boxstyle="round,pad=0.2,rounding_size=0.3",
        linewidth=2, edgecolor="#2563EB", facecolor="#1E293B"
    )
    ax.add_patch(fo_box)
    ax.text(4.1, 9.2, "NODE: FRONT_OFFICE", fontsize=14, fontweight="bold", color="#60A5FA", ha="center")
    ax.text(4.1, 8.85, "(SQLite In-Memory: Administrasi & Tamu)", fontsize=10, color="#94A3B8", ha="center")

    # Tables inside FRONT_OFFICE
    fo_tables = [
        ("guests", ["id (PK)", "name"], (1.0, 7.3), (2.8, 1.2)),
        ("rooms", ["id (PK)", "room_type", "nightly_rate", "occupied_by (FK)", "version"], (4.4, 6.7), (2.8, 1.8)),
        ("reservations", ["id (PK)", "guest_id (FK)", "room_id (FK)", "status", "version"], (1.0, 5.0), (2.8, 1.8)),
        ("folio_entries", ["id (PK)", "reservation_id (FK)", "description", "amount"], (4.4, 4.6), (2.8, 1.6)),
        ("cases", ["id (PK)", "scenario_id", "status", "human_required", "consent_json"], (1.0, 2.7), (2.8, 1.8)),
        ("faq", ["key (PK)", "answer"], (4.4, 3.0), (2.8, 1.2)),
        ("audit_events", ["seq (PK-Auto)", "event_type", "payload_json"], (1.0, 1.0), (2.8, 1.3)),
        ("applied_operations", ["operation_key (PK)", "result_json (Idempotency)"], (4.4, 1.3), (2.8, 1.3)),
    ]

    for tname, cols, (x, y), (w, h) in fo_tables:
        t_patch = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.08,rounding_size=0.15",
            linewidth=1.2, edgecolor="#3B82F6", facecolor="#0F172A"
        )
        ax.add_patch(t_patch)
        ax.text(x + w / 2, y + h - 0.28, tname.upper(), fontsize=10, fontweight="bold", color="#93C5FD", ha="center")
        for idx, col in enumerate(cols):
            ax.text(x + 0.15, y + h - 0.55 - (idx * 0.22), f"• {col}", fontsize=8, color="#E2E8F0")

    # -------------------------------------------------------------
    # Container Node 2: OPERATIONS (Right)
    # -------------------------------------------------------------
    ops_box = FancyBboxPatch(
        (8.4, 0.6), 7.0, 9.0,
        boxstyle="round,pad=0.2,rounding_size=0.3",
        linewidth=2, edgecolor="#0D9488", facecolor="#1E293B"
    )
    ax.add_patch(ops_box)
    ax.text(11.9, 9.2, "NODE: OPERATIONS", fontsize=14, fontweight="bold", color="#2DD4BF", ha="center")
    ax.text(11.9, 8.85, "(SQLite In-Memory: Kesiapan Fisik & Staf)", fontsize=10, color="#94A3B8", ha="center")

    # Tables inside OPERATIONS
    ops_tables = [
        ("room_readiness", ["room_id (PK)", "cleanliness (clean/dirty)", "maintenance_blocked (0/1)", "evidence_version"], (8.8, 6.2), (6.2, 2.0)),
        ("tickets", ["id (PK)", "operation_key (UK)", "case_id", "room_id", "department", "description", "status (PENDING/DONE)"], (8.8, 3.4), (6.2, 2.3)),
        ("applied_operations", ["operation_key (PK)", "result_json (Idempotency Tiket Fisik)"], (8.8, 1.3), (6.2, 1.5)),
    ]

    for tname, cols, (x, y), (w, h) in ops_tables:
        t_patch = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.08,rounding_size=0.15",
            linewidth=1.2, edgecolor="#14B8A6", facecolor="#0F172A"
        )
        ax.add_patch(t_patch)
        ax.text(x + w / 2, y + h - 0.32, tname.upper(), fontsize=10.5, fontweight="bold", color="#5EEAD4", ha="center")
        for idx, col in enumerate(cols):
            ax.text(x + 0.25, y + h - 0.65 - (idx * 0.23), f"• {col}", fontsize=8.5, color="#E2E8F0")

    # -------------------------------------------------------------
    # Migration & Isolation Arrow in between
    # -------------------------------------------------------------
    arrow = FancyArrowPatch(
        (7.7, 5.0), (8.3, 5.0),
        connectionstyle="arc3,rad=0",
        arrowstyle="-|>",
        mutation_scale=20,
        linewidth=2.5,
        color="#F59E0B"
    )
    ax.add_patch(arrow)
    ax.text(8.0, 5.3, "MIGRASI STATE\n(Mobile Agent)", fontsize=8, fontweight="bold", color="#FBBF24", ha="center")
    ax.text(8.0, 4.3, "Dilarang Query\nSilang Node!", fontsize=7.5, color="#F87171", ha="center")

    plt.tight_layout()
    png_file = DIAGRAM_DIR / "database_schema_diagram.png"
    plt.savefig(png_file, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Gambar Diagram PNG tersimpan di: {png_file}")
    return png_file


if __name__ == "__main__":
    generate_mermaid_markdown()
    generate_png_diagram()

