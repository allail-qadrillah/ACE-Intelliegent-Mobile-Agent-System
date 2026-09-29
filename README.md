# 🏨 ACE — Intelligent Mobile Agent System
### Otomasi Penanganan Komplain & Operasional Hotel Nusantara (Multi-Agent Simulation)

Simulasi *multi-agent customer service* dan operasional hotel berbasis **migrasi state mobile agent** antar-node logis di dalam **satu proses Python**.

> **Label Ilmiah Jujur:** Simulasi ini berfokus pada migrasi **state** agen antar-node logis (`FRONT_OFFICE` dan `OPERATIONS`) dalam satu proses Python; kode agen tersedia di kedua node. Ini **bukan** perpindahan kode/call stack atau transfer server fisik. Seluruh data bersifat sintetis dan lokal. Tidak ada ketergantungan API eksternal, LLM berbayar, atau unduhan model saat runtime.

**Mata Kuliah:** Agent Enterprise · Semester 3  
**Kelompok 5:**
- M. Al lail Qadrillah
- Dimas Prabowo
- Monanta Alfiareza
- Frans Alwan

---

## 🎯 1. Objektif & Nilai Bisnis Utama

Sistem ini dirancang untuk menjawab 3 tantangan utama operasional hotel:
1. **Penyelesaian Komplain Super Cepat (< 1 Menit vs 35 Menit Manual):**  
   Menyelesaikan komplain kamar rutin secara otomatis tanpa membuat tamu menunggu lama di kamar yang rusak.
2. **Verifikasi Kesiapan Fisik (Zero Double-Complaint):**  
   *Mobile Investigator* bermigrasi langsung ke database Housekeeping untuk memverifikasi kondisi fisik kamar. Kamar kotor otomatis disingkirkan, hanya kamar bersih dan siap huni (R103) yang diajukan ke tamu.
3. **Perlindungan Pendapatan Hotel (Policy Guardrail):**  
   Mencegah kerugian finansial akibat kompensasi kamar mewah gratis tanpa izin. Permohonan upgrade gratis (S02) otomatis dikunci oleh aturan sistem dan dialihkan ke Manajer Hotel.

---

## 🚀 2. Instalasi & Cara Menjalankan

Aplikasi dapat dijalankan secara penuh secara **offline** setelah dependensi terpasang:

```bash
# 1. Pasang dependensi
python -m pip install -r requirements.txt

# 2. Jalankan seluruh automated unit tests (68 tests)
python -m pytest -q

# 3. Jalankan aplikasi web Streamlit
python -m streamlit run app.py
```

Versi lingkungan pengembangan yang teruji (Python 3.11 / 3.12):
| Paket | Versi Teruji |
|---|---|
| `streamlit` | 1.39.0+ |
| `scikit-learn` | 1.5.2+ |
| `numpy` | 1.26.4+ |
| `pytest` | 8.3.3+ |

Ekspor laporan Machine Learning (CLI):
```bash
python -m hotel_demo.ml --out ml_report.json
python -m hotel_demo.ml --regenerate      # generate ulang dataset sintetis
```

---

## 📱 3. Antarmuka Baru (Business-First UX)

Antarmuka web telah disederhanakan agar ramah bagi manajemen hotel dan audiens non-teknis:

### A. Fitur Kemudahan Penggunaan (Usability & Comprehension Features):
1. **🎬 4 Kartu Kasus Nyata (1-Click Story):**
   - ❄️ **Kasus 1: AC Bocor Tengah Malam (Pak Budi - R101)** → Happy path otomatis penuh (kamar dipindahkan ke R103).
   - 🛡️ **Kasus 2: Tamu Minta Kamar Mewah Gratis (Ibu Sarah - R201)** → Proteksi biaya via Policy Guardrail & eskalasi manajer.
   - 🧹 **Kasus 3: Kamar Kotor Dieliminasi (Mas Kevin - R101)** → Verifikasi DB Housekeeping fisik (R102 kotor ditolak, R103 dipilih).
   - 🍳 **Kasus 4: Layanan Informasi Rutin (Mbak Rina - R105)** → Informasi instan concierge Front Office.
2. **🗺️ Peta Pergerakan Agen (2D Node Map Visualizer):**
   - Diagram topologi interaktif 2 node (`FRONT_OFFICE` ↔ `OPERATIONS`) yang memvisualisasikan posisi agen secara real-time (`📍 Posisi Agen`), koper state (`State Bag`), pipa migrasi data, dan gerbang kebijakan (*Policy Guardrail*).
3. **⏯️ Auto-Play Simulation Player:**
   - Tombol `[▶️ Putar Otomatis]`, `[⏸️ Jeda]`, dan `[⏭️ Langkah Berikutnya]` dengan animasi bertahap ~1 detik per langkah untuk demonstrasi langsung.
4. **🚨 Universal Action Bar:**
   - Tombol persetujuan tamu (`[✅ Setujui Pindah Kamar]`) dan tombol eskalasi manajer (`[👤 Ambil Alih Kasus]`) langsung muncul di bagian atas layar tab mana pun saat dibutuhkan, tanpa perlu mencari tab lain.
5. **📊 Live Visual Flow Stepper & Real-time Narration:**
   - Indikator 6 fase visual perhotelan (*Keluhan Masuk → Analisis SOP → Koordinasi Dept → Verifikasi Fisik → Persetujuan → Selesai*) beserta kotak penjelasan *"Apa yang terjadi di balik layar"*.
6. **🧮 Kalkulator Simulasi Penghematan Hotel (Interactive ROI):**
   - Widget interaktif untuk menghitung estimasi jam kerja staf yang dihemat dan uang yang diselamatkan dari kebocoran kamar mewah.
7. **📖 Modul Edukasi: Cara Kerja & Analogi Nyata:**
   - **Komik Storyboard 6 Panel:** Menjelaskan perjalanan koper agen secara visual ramah awam.
   - **Kamus Analogi Dunia Nyata:** Konsep teknis (Mobile Agent, State Bag SHA-256, Policy Guardrail, Idempotency) dianalogikan dengan Auditor Koper Bersegel, Segel Lilin Kerajaan, Satpam Brankas Hotel, dan Sakelar Lampu Otomatis.
   - **Tabel Kamus Istilah:** Padanan kata antara istilah teknis IT vs istilah operasional hotel.
   - **Kuis Interaktif 30 Detik:** 3 pertanyaan interaktif berbobot dengan evaluasi skor instan untuk menguji pemahaman audiens.

### B. Struktur Tab Navigasi:
1. **`🏨 Dasbor Eksekutif & Cerita Kasus`** — Pemilihan skenario 1-klik, Peta Pergerakan Agen 2D, Live Stepper alur kasus, metrik efisiensi, dan kalkulator ROI.
2. **`📖 Cara Kerja & Analogi Nyata`** — Pusat edukasi pemahaman konsep: Komik 6 Panel, Analogi Dunia Nyata, Kamus Istilah, dan Kuis Interaktif 30 Detik.
3. **`🛎️ HP Tamu (Layanan Tamu)`** — Simulasi tampilan smartphone tamu, percakapan agen interaktif, dan kartu persetujuan pindah kamar.
4. **`👔 Meja Kerja Staf Hotel`** — Antrean kasus eskalasi manajer (approval gate) dan papan tiket kerja fisik (Housekeeping/Maintenance).
5. **`🎬 Uji Seluruh Skenario`** — Eksekusi batch seluruh skenario (Autorun) dengan ringkasan status kelulusan.
6. **`🛠️ Mode Pengembang (Khusus IT)`** — Konsol teknis khusus pengembang: Lab Step Simulator, observabilitas event log DB, komparasi Mobile vs Static, dan confusion matrix ML.

---

## ⚖️ 4. Skenario Penanganan Komplain

| Kode | Kasus Komplain | Alur & Tindakan Agen | Hasil Akhir |
|---|---|---|---|
| **S01** | AC kamar bocor, minta kamar setara | Agen triase → migrasi ke Operations → verifikasi fisik R102 (kotor) & R103 (bersih) → tawarkan R103 | `DIGITAL_COMPLETED` (setelah persetujuan tamu) |
| **S02** | AC rusak, minta upgrade Suite gratis | Terdeteksi risiko over-kompensasi → bukti R201 terkumpul → dikunci aturan bisnis | `WAITING_HUMAN` (eskalasi wajib manajer) |
| **S03** | Kamar pengganti kotor di database fisik | Menginspeksi status fisik kamar → mengeliminasi R102 DIRTY | Menawarkan R103 READY |
| **S04** | Tanya jam sarapan & fasilitas | Ditangani instan oleh Concierge Front Office | Selesai instan tanpa tiket fisik |
| **S05** | Permintaan handuk & perlengkapan mandi | Membuat tiket tugas fisik ke Housekeeping | Tiket: `PENDING → IN_PROGRESS → DONE` |
| **S06** | Rincian tagihan minibar | Verifikasi folio billing F01+F02 (Rp650.000) | Selesai transparan tanpa perubahan tagihan |

---

## 🔬 5. Perbandingan: Mobile Agent vs Static Agent

| Indikator Evaluasi | Mobile Agent (ACE System) | Static Agent (Baseline Tradisional) |
|---|---|---|
| **Lokasi Eksekusi Inspeksi** | Instance agen bermigrasi ke node `OPERATIONS` | Agen tetap di `FRONT_OFFICE` |
| **Pola Komunikasi** | Mengirimkan 1 paket koper state (JSON Checkpoint terenkapsulasi) | Mengirimkan pesan RPC berulang bolak-balik antar node |
| **Keamanan & Privasi Data** | Data inspeksi internal operasional tetap berada di node lokal | Rentan membocorkan catatan operasional ke jaringan publik |
| **Integritas Migrasi** | Diproteksi validasi hash SHA-256 dan serialisasi state | Memerlukan sinkronisasi sesi jaringan terus-menerus |
| **Konsistensi Bisnis** | Keputusan kamar tetap 100% identik dan konsisten | Keputusan kamar identik |

---

## 🏗️ 6. Arsitektur Teknis

- **Topologi:** Satu proses Python, 2 node logis (`FRONT_OFFICE` dan `OPERATIONS`).
- **Database:** Dua SQLite `:memory:` terpisah per node + tabel `applied_operations` untuk menjamin *idempotency*.
- **Pesan & Event:** Antrean lokal `collections.deque` terurut deterministik, bebas race-condition.
- **Daftar Agen:**
  - `Scenario Scout Agent`: Deteksi dan pembacaan pesan tamu.
  - `Orchestrator Agent`: Triase kasus, prediksi risiko ML, dan orkestrasi alur.
  - `Reservation Agent`: Mutasi dan alokasi kamar di Meja Depan.
  - `Billing Agent`: Pengelolaan tagihan folio tamu.
  - `Concierge Agent`: Penjawab FAQ dan informasi umum hotel.
  - `Operations Agent`: Koordinator tugas fisik di node Operasional.
  - `Mobile Investigator Agent`: Agen otonom yang membungkus koper state, bermigrasi antar node, dan melakukan inspeksi lokal.

---

## 📁 7. Struktur Repositori

```text
├── app.py                         # Entry point web Streamlit (Business-First Layout)
├── requirements.txt               # Daftar pustaka dependensi
├── README.md                      # Dokumentasi komprehensif proyek
├── presentasi_ace_mobile_agent_v4.pptx # Slide presentasi eksekutif & teknis (16:9 Modern)
├── data/
│   ├── hotel_seed.json            # Data awal kamar & reservasi Hotel Nusantara
│   ├── scenarios.json             # Definisi skenario S01 - S09
│   └── escalation_synthetic.csv   # Dataset pelatihan model triase ML
├── hotel_demo/
│   ├── models.py                  # Dataclass, Enums (Action, CaseStatus, NodeId)
│   ├── repository.py              # Dua database SQLite, transaksi atomik
│   ├── policy.py                  # Aturan bisnis wajib (Policy Guardrail)
│   ├── ml.py                      # Model Logistic Regression triase komplain
│   ├── agents/                    # Satu file per agen + kernel inspeksi kandidat kamar
│   │   ├── base.py                #   BaseAgent + tabel capability
│   │   ├── inspection.py          #   evaluate_candidates (kernel murni)
│   │   ├── scenario_scout.py      #   ScenarioScoutAgent
│   │   ├── orchestrator.py        #   OrchestratorAgent
│   │   ├── reservation.py         #   ReservationAgent
│   │   ├── billing.py             #   BillingAgent
│   │   ├── concierge.py           #   ConciergeAgent
│   │   ├── operations.py          #   OperationsAgent
│   │   └── mobile_investigator.py #   MobileInvestigator
│   ├── migration.py               # Siklus hidup migrasi (PREPARE, DEPART, ARRIVE)
│   ├── simulation.py              # Engine simulasi deterministik, lifecycle kasus
│   ├── evaluation.py              # Komparasi kuantitatif Mobile vs Static
│   └── ui.py                      # Seluruh komponen visual & interaksi Streamlit
└── tests/                         # 68 Automated Unit Tests (pytest)
```

---

## ✅ 8. Hasil Pengujian Sistem (Automated Tests)

```text
$ python -m pytest -q
....................................................................     [100%]
68 passed in 3.3s
```

**Cakupan Pengujian:**
- Integritas migrasi state (verifikasi SHA-256, invariant kepemilikan single-instance, restore on failure).
- Keandalan *Policy Guardrail* vs prediksi model ML.
- Transaksi database atomik dan rollback kamar kotor.
- Eksekusi seluruh skenario komplain (S01–S09).
- Smoke test Streamlit UI via `AppTest` (tanpa browser).

---
*Dikembangkan oleh Kelompok 5 untuk Mata Kuliah Agent Enterprise (Semester 3).*
