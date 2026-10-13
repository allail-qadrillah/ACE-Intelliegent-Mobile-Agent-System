# Diagram Struktur Database Dual-Node SQLite
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
