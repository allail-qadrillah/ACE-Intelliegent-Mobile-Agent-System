# Panduan Demo ACE — Intelligent Mobile Agent System

Dokumen ini menjadi panduan presentasi untuk aplikasi simulasi **Multi-Agent Customer Service Hotel**.

## 1. Tujuan demo

Demo menunjukkan cara beberapa agen menangani permintaan tamu hotel secara terkoordinasi:

- `FRONT_OFFICE` menerima dan mengklasifikasikan permintaan.
- `OPERATIONS` memeriksa kondisi kamar atau menangani tugas operasional.
- Mobile Agent membawa **state** kasus melalui checkpoint JSON antar-node logis.
- Policy Guardrail menghentikan keputusan berisiko dan meminta staf mengambil alih.

> Batas demo: migrasi berlangsung antar-node logis dalam satu proses Python. Ini bukan perpindahan server fisik, kode, atau call stack. Data hotel bersifat sintetis dan aplikasi berjalan lokal tanpa API eksternal.

## 2. Persiapan dan menjalankan aplikasi

Buka terminal pada folder proyek:

```bash
cd /mnt/e/MKA/Agentic/app
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Browser biasanya terbuka otomatis. Jika tidak, buka URL yang ditampilkan terminal, biasanya:

```text
http://localhost:8501
```

Untuk memastikan kode lolos pengujian sebelum demo:

```bash
python -m pytest -q
```

## 3. Urutan presentasi yang direkomendasikan

Durasi: sekitar 5–7 menit.

### A. Pembukaan — Dasbor Eksekutif

1. Tunjukkan judul aplikasi dan badge `Lokal`, `Data Sintetis`, serta `Tanpa API`.
2. Jelaskan masalah bisnis:
   - tamu menunggu saat kamar bermasalah;
   - kamar yang tercatat kosong belum tentu bersih;
   - upgrade gratis dapat menyebabkan kebocoran pendapatan.
3. Tunjukkan kartu cerita pada tab **🏨 Dasbor Eksekutif & Cerita Kasus**.
4. Singgung kalkulator ROI sebagai ilustrasi simulasi, bukan data hotel nyata.

### B. Demo utama — S01 AC rusak dan pindah kamar

Gunakan skenario ini untuk menunjukkan alur sukses end-to-end.

1. Pada kartu **Cerita 1: AC Bocor Tengah Malam**, klik **▶️ Jalankan Cerita 1 (AC Bocor)**.
2. Spanduk **Presenter** di bagian atas menjalankan agen secara bertahap. Klik **▶️ Putar** atau gunakan **Langkah Berikutnya**:
   - Scenario Scout membaca permintaan tamu;
   - Orchestrator menentukan alur pindah kamar;
   - state agen berpindah dari `FRONT_OFFICE` ke `OPERATIONS`;
   - Mobile Investigator memeriksa kamar pengganti;
   - R102 ditolak karena kotor;
   - R103 dipilih karena bersih dan siap.
3. Presenter berhenti otomatis saat muncul kartu **Persetujuan Tamu**. Klik **✅ Setujui Pindah ke R103**.
4. Tunjukkan hasil akhir `DIGITAL_COMPLETED` dan kamar resmi tamu menjadi `R103`.
5. Jelaskan inti nilai sistem:
   > Sistem tidak hanya melihat kamar kosong. Sistem memeriksa kesiapan fisik sebelum menawarkan kamar kepada tamu.

### C. Demo guardrail — S02 permintaan upgrade gratis

Gunakan skenario ini untuk menunjukkan bahwa agen tidak boleh mengambil keputusan finansial tanpa batas.

1. Klik **Cerita 2: Tamu Minta Suite Mewah** pada Dasbor Eksekutif.
2. Biarkan simulasi berjalan sampai status `WAITING_HUMAN`.
3. Tunjukkan alasan eskalasi dari **Policy Guardrail**.
4. Klik **👤 Ambil Alih Kasus (Take Over)**.
5. Isi atau gunakan catatan penyelesaian staf.
6. Klik **✅ Tutup Kasus Resmi**.
7. Jelaskan:
   > ML membantu triase, tetapi aturan wajib tetap mengendalikan keputusan berisiko. Agen tidak memberi upgrade gratis secara otomatis.

### D. Demo operasional singkat — S05 permintaan handuk

Gunakan jika ingin menunjukkan pekerjaan fisik dan portal staf.

1. Buka expander **⚙️ Mode Pengembang & Uji Teknis (Opsional)** pada sidebar.
2. Pilih mode **Mobile Agent**, lalu klik **S05 — Minta handuk**.
3. Jalankan langkah sampai tiket Housekeeping muncul.
4. Buka tab **👔 Meja Kerja Staf Hotel**.
5. Klik **▶️ Mulai Kerjakan**.
6. Klik **✔️ Tandai Selesai**.
7. Tunjukkan perubahan tiket:
   ```text
   PENDING → IN_PROGRESS → DONE
   ```

## 4. Arti tab aplikasi

### 🏨 Dasbor Eksekutif & Cerita Kasus

Untuk pembukaan demo. Berisi kartu cerita, metrik bisnis, kalkulator ROI, dan status kasus aktif.

### 🛎️ HP Tamu (Layanan Tamu)

Untuk menunjukkan perspektif tamu, percakapan agen, proposal kamar, dan tombol persetujuan.

### 👔 Meja Kerja Staf Hotel

Untuk menunjukkan kasus yang perlu diambil alih manusia serta tiket Housekeeping atau Maintenance.

### 🎬 Uji Seluruh Skenario

Untuk menjalankan banyak skenario secara otomatis dan melihat ringkasan hasil. Pakai setelah demo utama, bukan sebagai pembukaan, supaya alur cerita tetap mudah diikuti.

### 📖 Cara Kerja & Analogi Nyata

Gunakan setelah demo bisnis untuk menjelaskan Mobile Agent dengan komik storyboard, analogi, dan kamus istilah.

### 🛠️ Mode Pengembang (Khusus IT)

Gunakan untuk menjelaskan implementasi teknis:

- **Lab Step Simulator:** langkah kasus satu per satu;
- **Observabilitas & Audit DB:** event, pesan, state, dan jejak migrasi;
- **Evaluasi Ilmiah & ML:** laporan klasifikasi serta perbandingan Mobile vs Static;
- **Arsitektur & Spesifikasi:** dua node logis dan batas simulasi.

## 5. Flow aplikasi aktual

```text
Pilih cerita / skenario
        ↓
Simulation.start_scenario()
        ↓
Universal Action Bar + Presenter HUD menampilkan status dan aksi berikutnya
        ↓
Putar Otomatis atau Langkah Berikutnya
        ↓
Scenario Scout → Orchestrator → agent tujuan
        ↓
Keputusan:
  S01  → inspeksi kamar → menunggu persetujuan tamu → commit R103
  S02  → policy guardrail → WAITING_HUMAN → takeover staf
  S03  → baca folio sengketa → WAITING_HUMAN → takeover staf
  S04  → jawab FAQ → DIGITAL_COMPLETED
  S05  → buat tiket housekeeping → staf ubah status tiket
  S06  → tampilkan folio → DIGITAL_COMPLETED
        ↓
Dasbor bisnis / cara kerja / portal tamu / meja staf / console teknis
```

Catatan penting: tombol cerita pada dasbor langsung memulai skenario dan autoplay. Presenter HUD menyediakan pilihan tempo `1x`, `2x`, dan `3x`, tombol **Putar**, **Jeda**, serta langkah manual. Tombol skenario di sidebar dipakai untuk kontrol teknis, memilih mode `mobile` atau `static`, serta reset.

## 6. Narasi teknis singkat

Pakai narasi ini saat audiens bertanya tentang arsitektur:

> Aplikasi berjalan dalam satu proses Python dengan dua node logis, yaitu `FRONT_OFFICE` dan `OPERATIONS`. Mobile Investigator membawa state kasus dalam checkpoint JSON. Checkpoint divalidasi dengan hash SHA-256, lalu agen menjalankan inspeksi menggunakan data lokal node tujuan. Semua proses deterministik dan tidak membutuhkan jaringan.

Jangan menyebut aplikasi sebagai sistem produksi, autentikasi hotel, atau mobile agent yang memindahkan kode antarserver. Implementasi ini adalah simulasi pembelajaran dengan database SQLite in-memory dan data sintetis.

## 7. Tombol penting saat demo

| Tombol | Fungsi |
|---|---|
| `▶️ Putar Otomatis` | Menjalankan langkah simulasi otomatis |
| `⏸️ Jeda (Pause)` | Menghentikan autoplay sebelum langkah berikutnya |
| `⏭️ Langkah Berikutnya` | Menjalankan satu langkah simulasi |
| `✅ Setujui Pindah ke R103` | Persetujuan tamu pada alur S01 |
| `❌ Tolak Tawaran` | Menolak kamar pengganti |
| `👤 Ambil Alih Kasus` | Mengubah kasus eskalasi menjadi penanganan staf |
| `✅ Tutup Kasus Resmi` | Menutup kasus setelah catatan staf diisi |
| `Reset Skenario` | Mengulang skenario aktif dari kondisi awal |

## 8. Alur cadangan jika waktu sangat singkat

1. Jalankan aplikasi.
2. Klik **Cerita 1: AC Bocor Tengah Malam**.
3. Tunggu sampai sistem menawarkan `R103`.
4. Klik persetujuan tamu.
5. Tunjukkan status `DIGITAL_COMPLETED`.
6. Jalankan S02 hanya jika audiens ingin melihat keputusan yang memerlukan manusia.

## 9. Penutup demo

Tekankan tiga hasil:

1. **Otomasi:** permintaan rutin selesai tanpa intervensi staf.
2. **Verifikasi:** kamar kotor dieliminasi sebelum ditawarkan.
3. **Kontrol:** keputusan finansial berisiko dieskalasi ke manusia.

Kalimat penutup:

> ACE bukan sekadar chatbot. Demo ini menunjukkan orkestrasi beberapa agen, perpindahan state antar-node logis, verifikasi data operasional, dan guardrail bisnis dalam satu alur layanan hotel.
