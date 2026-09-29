# 🏨 ACE — Intelligent Mobile Agent System
### Otomasi Penanganan Komplain & Operasional Hotel Nusantara (Multi-Agent Simulation)

Simulasi *multi-agent customer service* dan operasional hotel berbasis **migrasi state mobile agent** antar-node logis di dalam **satu proses Python**.

> **Label Ilmiah Jujur:** Simulasi ini berfokus pada migrasi **state** agen antar-node logis (`FRONT_OFFICE` dan `OPERATIONS`) dalam satu proses Python; kode agen tersedia di kedua node. Ini **bukan** perpindahan kode/call stack atau transfer server fisik. Seluruh data bersifat sintetis dan lokal. Tidak ada ketergantungan API eksternal, LLM berbayar, atau unduhan model saat runtime.

---

### 🎓 Informasi Akademik
- **Mata Kuliah:** Agent Enterprise (Semester 3)
- **Program Studi:** Magister Kecerdasan Artifisial — Universitas Gadjah Mada (UGM) 2026
- **Dosen Pengampu:** Prof. Dr. Azhari, MT.
- **Kelompok 5 — Tim Pengembang & Matriks Tanggung Jawab:**
  - **M. Al lail Qadrillah** (26/590736/PPA/07413) — *Leader & Core Engine Developer*
  - **Dimas Prabowo** (26/590092/PPA/07382) — *Researcher & Benchmark Evaluation*
  - **Monanta Alfiareza** (26/591492/PPA/07455) — *Designer, UI/UX & Flow Streamlit*
  - **Frans Alwan Purba** (25/563545/PPA/07116) — *Evaluator, Correctness Suite & Presenter*

---

### 📑 Dokumen & Berkas Proyek Resmi
- 📄 **Laporan Lengkap (PDF):** [`Laporan_Tugas_2_Multiagent_Hotel_Lengkap.pdf`](./Laporan_Tugas_2_Multiagent_Hotel_Lengkap.pdf)
- 📝 **Laporan Lengkap (Word DOCX):** [`Laporan_Tugas_2_Multiagent_Hotel_Lengkap.docx`](./Laporan_Tugas_2_Multiagent_Hotel_Lengkap.docx)
- 📊 **Slide Presentasi (PowerPoint 16:9):** [`Laporan_Tugas_2_Multiagent_Hotel.pptx`](./Laporan_Tugas_2_Multiagent_Hotel.pptx)
- 📖 **Panduan Skenario Demo:** [`PANDUAN_DEMO.md`](./PANDUAN_DEMO.md)
- 📋 **Product Requirements Document (PRD):** [`PRD_Demo_Mobile_Agent_Hotel.md`](./PRD_Demo_Mobile_Agent_Hotel.md)

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

# 2. Jalankan seluruh automated unit tests (70 tests)
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
| `python-docx` | 1.1.2+ |
| `python-pptx` | 1.0.2+ |

Ekspor laporan Machine Learning (CLI):
```bash
python -m hotel_demo.ml --out ml_report.json
python -m hotel_demo.ml --regenerate      # generate ulang dataset sintetis
```

---

## 📱 3. Antarmuka Bisnis & Presenter (Business-First UX)

Antarmuka web telah disederhanakan agar ramah bagi manajemen hotel dan audiens non-teknis:

### A. Fitur Kemudahan Penggunaan:
1. **🎬 4 Kartu Kasus Nyata (1-Click Story):**
   - ❄️ **Kasus 1: AC Bocor Tengah Malam (Pak Budi - R101)** → Happy path otomatis penuh (kamar dipindahkan ke R103).
   - 🛡️ **Kasus 2: Tamu Minta Kamar Mewah Gratis (Ibu Sarah - R201)** → Proteksi biaya via Policy Guardrail & eskalasi manajer.
   - 💰 **Kasus 3: Sengketa Tagihan Minibar** → Folio dibaca, tetapi perubahan tagihan dieskalasi ke staf.
   - 🕐 **Kasus 4: Informasi Check-In** → Informasi instan dari FAQ lokal Concierge Front Office.
2. **🗺️ Peta Pergerakan Agen (2D Node Map Visualizer):**
   - Diagram topologi interaktif 2 node (`FRONT_OFFICE` ↔ `OPERATIONS`) yang memvisualisasikan posisi agen secara real-time (`📍 Posisi Agen`), koper state (`State Bag`), pipa migrasi data, dan gerbang kebijakan (*Policy Guardrail*).
3. **⏯️ Auto-Play Simulation Player:**
   - Tombol `[▶️ Putar Otomatis]`, `[⏸️ Jeda]`, dan `[⏭️ Langkah Berikutnya]` dengan animasi bertahap ~1 detik per langkah untuk demonstrasi langsung.
4. **🚨 Universal Action Bar:**
   - Tombol persetujuan tamu (`[✅ Setujui Pindah Kamar]`) dan tombol eskalasi manajer (`[👤 Ambil Alih Kasus]`) langsung muncul di bagian atas layar tab mana pun saat dibutuhkan, mengeksekusi penyelesaian instan.
5. **📊 Live Visual Flow Stepper & Real-time Narration:**
   - Indikator 6 fase visual perhotelan (*Keluhan Masuk → Analisis SOP → Koordinasi Dept → Verifikasi Fisik → Persetujuan → Selesai*) beserta kotak penjelasan *"Apa yang terjadi di balik layar"*.
6. **🧮 Kalkulator Simulasi Penghematan Hotel (Interactive ROI):**
   - Widget interaktif untuk menghitung estimasi jam kerja staf yang dihemat dan uang yang diselamatkan dari kebocoran kamar mewah.
7. **📖 Modul Edukasi: Cara Kerja & Analogi Nyata:**
   - **Komik Storyboard 6 Panel:** Menjelaskan perjalanan koper agen secara visual ramah awam.
   - **Kamus Analogi Dunia Nyata:** Konsep teknis (Mobile Agent, State Bag SHA-256, Policy Guardrail, Idempotency) dianalogikan dengan Auditor Koper Bersegel, Segel Lilin Kerajaan, Satpam Brankas Hotel, dan Sakelar Lampu Otomatis.

### B. Struktur Tab Navigasi:
1. **`🏨 Dasbor Eksekutif & Cerita Kasus`** — Pemilihan skenario 1-klik, Peta Pergerakan Agen 2D, Live Stepper alur kasus, metrik efisiensi, dan kalkulator ROI.
2. **`📖 Cara Kerja & Analogi Nyata`** — Pusat edukasi pemahaman konsep: Komik 6 Panel, Analogi Dunia Nyata, dan Kamus Istilah.
3. **`🛎️ HP Tamu (Layanan Tamu)`** — Simulasi smartphone tamu, percakapan agen interaktif, dan kartu persetujuan pindah kamar instan.
4. **`👔 Meja Kerja Staf Hotel`** — Antrean kasus eskalasi manajer (takeover gate), form catatan SOP, dan papan tiket kerja fisik (Housekeeping/Maintenance).
5. **`🎬 Uji Seluruh Skenario`** — Eksekusi batch seluruh skenario (Autorun) dengan ringkasan status kelulusan.
6. **`🛠️ Mode Pengembang (Khusus IT)`** — Konsol teknis khusus pengembang: Lab Step Simulator, observabilitas event log DB, komparasi Mobile vs Static, dan confusion matrix ML.

---

## ⚖️ 4. Skenario Penanganan Komplain & Hasil Aktual

| Kode | Kasus Komplain | Alur & Tindakan Agen | Hasil Akhir Aktual |
|---|---|---|---|
| **S01** | AC kamar bocor, minta kamar setara | Agen triase → migrasi ke Operations → verifikasi fisik R102 (kotor) & R103 (bersih) → tawarkan R103 → tamu setuju → commit atomik | `DIGITAL_COMPLETED` (kamar resmi pindah ke R103, tarif tetap Rp500.000) |
| **S02** | AC rusak, kamar setara habis | MA-001 bermigrasi mengumpulkan bukti R201 (Deluxe, selisih Rp250.000) → terdeteksi risiko over-kompensasi → dikunci aturan bisnis | `WAITING_HUMAN` (eskalasi wajib ke manajer) |
| **S03** | Sengketa tagihan minibar | Billing membaca folio (Rp650.000) → perubahan tagihan sepihak dikunci policy | `WAITING_HUMAN` (eskalasi wajib ke staf keuangan) |
| **S04** | Tanya jam check-in | Ditangani instan oleh Concierge Front Office (14.00 WIB) | `CLOSED` (selesai tanpa tiket fisik) |
| **S05** | Permintaan handuk tambahan | Membuat tiket tugas fisik ke Housekeeping | Tiket: `PENDING → IN_PROGRESS → DONE` |
| **S06** | Rincian tagihan minibar | Verifikasi folio billing F01+F02 (Rp650.000) | `CLOSED` (selesai transparan tanpa mutasi saldo) |

---

## 🔬 5. Hasil Eksperimen Benchmark Aktual (30 Iterasi Berpasangan)

Hasil pengukuran empiris berpasangan (30 repetisi setelah 3 kali warm-up) membandingkan **Static MAS** vs **Mobile MAS** dengan kernel, seed, dan model yang identik:

| Metrik Evaluasi | S01 Static | S01 Mobile | S02 Static | S02 Mobile |
| :--- | :---: | :---: | :---: | :---: |
| **Hasil Bisnis Aktual** | Selesai digital, kamar pindah R103, 1 tiket | Selesai digital, kamar pindah R103, 1 tiket | Wajib review staf, kamar tetap R101 | Wajib review staf, kamar tetap R101 |
| **Ekivalensi Keputusan** | **Identik** | **Identik** | **Identik** | **Identik** |
| **Waktu Median (ms)** | 21,38 ms | 27,87 ms | 11,17 ms | 13,46 ms |
| **Waktu P95 (ms)** | 22,33 ms | 28,35 ms | 11,51 ms | 14,02 ms |
| **Pesan Antar-Node** | 6 pesan | **5 pesan** *(Hemat 16,7%)* | 4 pesan | **3 pesan** *(Hemat 25,0%)* |
| **Total Payload Simulasi** | 2.793 byte | 2.820 byte *(+27 byte / +0,96%)* | 1.861 byte | 1.888 byte *(+27 byte / +1,45%)* |
| **Ukuran Checkpoint Agen** | 0 byte (tidak ada) | 553 byte | 0 byte (tidak ada) | 470 byte |
| **Jumlah Langkah Engine** | 14 step | 16 step *(+2 step)* | 9 step | 11 step *(+2 step)* |
| **CPU Time Median (ms)** | 15,62 ms | 31,25 ms | 15,62 ms | 15,62 ms |
| **Peak Memory Allocation** | 104,87 KB | 109,52 KB | 72,50 KB | 76,97 KB |
| **Migrasi Sukses** | 0 kali | **1 kali** | 0 kali | **1 kali** |

**Kesimpulan Evaluasi:**  
Mobile Agent terbukti secara konsisten memangkas lalu lintas pesan koordinasi antar-node sebesar **16,7% hingga 25,0%** dengan penambahan payload serialisasi checkpoint yang sangat kecil (+27 byte). Pada jaringan riil terdistribusi (WAN/Internet) dengan latensi jaringan tinggi, pengurangan pesan bolak-balik ini akan memberikan keunggulan performa yang sangat signifikan.

---

## 🤖 6. Metrik Machine Learning & Keamanan Sistem

### A. Kinerja Model Regresi Logistik (Held-out Test):
- **Akurasi:** `91,67%` (11 dari 12 sampel uji benar pada threshold $\tau = 0{,}80$)
- **Precision:** `100,00%` (Zero False Positive eskalasi)
- **Recall:** `83,33%` (5 dari 6 kebutuhan eskalasi positif terdeteksi)
- **F1-Score:** `0,9091`
- **Confusion Matrix:** $\begin{bmatrix} 6 & 0 \\ 1 & 5 \end{bmatrix}$ (TN=6, FP=0, FN=1, TP=5)
- **Bobot Koefisien Terlatih:** Intercept $b = -0{,}0876$, $w_{\text{complexity}} = 1{,}4557$, $w_{\text{risk}} = 1{,}4098$, $w_{\text{attempts}} = 0{,}9490$, $w_{\text{missing}} = 1{,}3720$

### B. Keamanan Kontrol & Integritas:
- **Percobaan Terlarang Ditolak:** `14 / 14 (100%)` (Semua akses ilegal dan mutasi tanpa consent diblokir)
- **Invariant Migrasi Lulus:** `14 / 14 (100%)` ($N_{\text{active}}(a) \in \{0, 1\}$ terjaga; tidak ada duplikasi agen aktif)
- **Duplicate Side Effects:** `0 (Nol)` (*Idempotency key* mencegah pembuatan tiket ganda maupun mutasi kamar ganda)
- **Recovery Kasus Kegagalan:** `100% Berhasil` (Rollback otomatis ke node asal jika checkpoint atau node tujuan bermasalah)

---

## 🏗️ 7. Arsitektur Teknis

- **Topologi:** Satu proses Python, 2 node logis (`FRONT_OFFICE` dan `OPERATIONS`).
- **Database:** Dua SQLite `:memory:` terpisah per node + tabel `applied_operations` untuk menjamin *idempotency*.
- **Pesan & Event:** Antrean lokal `collections.deque` terurut deterministik, bebas race-condition.
- **Spesialisasi Agen:**
  - `Scenario Scout Agent`: Deteksi dan pembacaan pesan tamu.
  - `Orchestrator Agent`: Triase kasus, prediksi risiko ML, dan orkestrasi alur.
  - `Reservation Agent`: Mutasi dan alokasi kamar di Meja Depan.
  - `Billing Agent`: Pengelolaan tagihan folio tamu.
  - `Concierge Agent`: Penjawab FAQ dan informasi umum hotel.
  - `Operations Agent`: Koordinator tugas fisik di node Operasional.
  - `Mobile Investigator Agent`: Agen otonom yang membungkus koper state (SHA-256), bermigrasi antar node, dan melakukan inspeksi lokal.

---

## 📁 8. Struktur Repositori

```text
├── app.py                                        # Entry point web Streamlit (Business-First Layout)
├── requirements.txt                              # Daftar pustaka dependensi
├── README.md                                     # Dokumentasi komprehensif proyek
├── PANDUAN_DEMO.md                               # Panduan skenario dan presentasi demo
├── PRD_Demo_Mobile_Agent_Hotel.md                # Dokumen spesifikasi kebutuhan produk
├── Laporan_Tugas_2_Multiagent_Hotel_Lengkap.pdf  # Berkas laporan tugas lengkap (PDF)
├── Laporan_Tugas_2_Multiagent_Hotel_Lengkap.docx # Berkas laporan tugas lengkap (DOCX)
├── Laporan_Tugas_2_Multiagent_Hotel.pptx         # Slide presentasi resmi 12 slide (16:9)
├── build_full_report.py                          # Skrip generator/updater laporan DOCX & PDF
├── build_presentation_report.py                  # Skrip generator presentasi PowerPoint PPTX
├── data/
│   ├── hotel_seed.json                           # Data awal kamar & reservasi Hotel Nusantara
│   ├── scenarios.json                            # Definisi skenario S01 - S09
│   └── escalation_synthetic.csv                  # Dataset pelatihan model triase ML
├── hotel_demo/
│   ├── models.py                                 # Dataclass, Enums (Action, CaseStatus, NodeId)
│   ├── repository.py                             # Dua database SQLite, transaksi atomik
│   ├── policy.py                                 # Aturan bisnis wajib (Policy Guardrail)
│   ├── ml.py                                     # Model Logistic Regression triase komplain
│   ├── agents/                                   # Modul per agen + kernel inspeksi kandidat kamar
│   │   ├── base.py                               #   BaseAgent + tabel capability
│   │   ├── inspection.py                         #   evaluate_candidates (kernel murni)
│   │   ├── scenario_scout.py                     #   ScenarioScoutAgent
│   │   ├── orchestrator.py                       #   OrchestratorAgent
│   │   ├── reservation.py                        #   ReservationAgent
│   │   ├── billing.py                            #   BillingAgent
│   │   ├── concierge.py                          #   ConciergeAgent
│   │   ├── operations.py                         #   OperationsAgent
│   │   └── mobile_investigator.py                #   MobileInvestigator
│   ├── migration.py                              # Siklus hidup migrasi (PREPARE, DEPART, ARRIVE)
│   ├── simulation.py                             # Engine simulasi deterministik, lifecycle kasus
│   ├── evaluation.py                             # Komparasi kuantitatif Mobile vs Static
│   └── ui.py                                     # Seluruh komponen visual & interaksi Streamlit
└── tests/                                        # 70 Automated Unit Tests (pytest)
```

---

## ✅ 9. Hasil Pengujian Sistem (Automated Tests)

```text
$ python -m pytest -q
......................................................................   [100%]
70 passed in 3.53s
```

**Cakupan Pengujian (70 Tests):**
- Integritas migrasi state (verifikasi SHA-256, invariant kepemilikan single-instance, restore on failure).
- Keandalan *Policy Guardrail* vs prediksi model ML.
- Transaksi database atomik dan rollback kamar kotor.
- Eksekusi seluruh skenario komplain (S01–S09).
- Smoke test Streamlit UI via `AppTest` (tanpa browser).

---
*Dikembangkan oleh Kelompok 5 — Magister Kecerdasan Artifisial, Universitas Gadjah Mada (UGM) 2026.*
