# Demo Mobile Agent — Customer Service Hotel

Simulasi multi-agent customer service hotel dengan **migrasi state mobile agent**
antar-node logis di dalam **satu proses Python**.

> Simulasi migrasi state agen antar-node logis dalam satu proses Python; kode agen
> tersedia di kedua node. Ini **bukan** perpindahan kode/call stack atau server fisik.

Seluruh data bersifat sintetis dan lokal. Tidak ada panggilan API, LLM, unduhan model,
atau kredensial saat runtime.

Kelompok 5: M. Al lail Qadrillah, Dimas Prabowo, Monanta Alfiareza, Frans Alwan.
(NIM dan pembagian peran belum diisi.)

---

## 1. Instalasi dan menjalankan

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

Instalasi dependensi memerlukan internet. Setelah itu aplikasi dan tes berjalan
**offline**.

Versi yang diuji pada lingkungan pengembangan ini (Python 3.12.13):

| Paket | Versi |
|---|---|
| streamlit | 1.39.0 |
| scikit-learn | 1.5.2 |
| numpy | 1.26.4 |
| pytest | 8.3.3 |

Laporan ML dapat dicetak/ditulis dari CLI:

```bash
python -m hotel_demo.ml --out ml_report.json
python -m hotel_demo.ml --regenerate      # tulis ulang data/escalation_synthetic.csv
```

## 2. Enam skenario

| Tombol | Isi | Hasil utama |
|---|---|---|
| S01 | AC rusak, minta kamar setara | Kandidat R102/R103 → investigator menolak R102 (DIRTY), memilih R103 → tunggu consent → commit setelah validasi ulang |
| S02 | AC rusak, minta upgrade gratis | Wajib staf sejak triase; evidence R201 terkumpul (siap tapi upgrade) → `WAITING_HUMAN` |
| S03 | Sengketa tagihan minibar | Billing membaca F02; eskalasi wajib; folio tidak berubah |
| S04 | Jam check-in | Jawaban FAQ lokal (14.00), selesai tanpa tiket/migrasi |
| S05 | Minta handuk | Satu tiket housekeeping `PENDING`; staf dapat maju sampai `DONE` |
| S06 | Rincian tagihan | F01+F02, total Rp650.000, tanpa perubahan folio |

Pada S01 ada tiga pilihan: **Setuju** (commit pindah kamar), **Tolak**
(`CLOSED_GUEST_DECLINED`, tiket tetap terbuka), atau tidak memilih
(tetap `WAITING_GUEST`).

## 3. Demo step-by-step (skrip presentasi)

1. Jalankan aplikasi offline; pilih mode **Mobile Agent** dan **S01**.
2. Tunjukkan pesan tamu, `p(human_judgment)`, `threshold`, `decision_source`.
3. Tekan **Langkah Berikutnya** sampai kandidat R102/R103 diperoleh dan investigator `MA-001` dibuat.
4. **Step PREPARE**: lihat area Transit — checkpoint JSON berisi `MA-001`, `CASE-001`, goal, candidates, phase `INSPECT_LOCAL`, hash SHA-256 dan ukuran byte.
5. **Step DEPART**: tunjukkan `active_instance_count = 0`, `owner = None`, agen hanya ada di jalur transfer.
6. **Step ARRIVE**: tunjukkan ID tetap `MA-001`, instance tujuan adalah objek **baru**, node berubah ke `OPERATIONS`, `migration_count = 1`.
7. **Step inspeksi**: tab *Jejak & State* menunjukkan R102 ditolak `DIRTY`, R103 `READY_EQUAL_ROOM`.
8. Setujui perpindahan sebagai **Tamu**; lanjutkan step sampai reservasi berubah ke R103.
9. Pilih **S02**: tunjukkan migrasi tetap terjadi dan evidence R201 terkumpul, tetapi upgrade tetap `WAITING_HUMAN` (kamar tidak diubah).
10. Buka tab **Evaluasi** → **Jalankan Perbandingan**: hasil bisnis S01/S02 sama antara static dan mobile; biaya simulasi (byte, step, ms) tampil apa adanya.

## 4. Mobile vs Static

| | Mobile Agent | Static Agent |
|---|---|---|
| Investigator | Instance aktif berpindah node lewat checkpoint JSON | Tetap di Front Office |
| Inspeksi | Dijalankan di Operations setelah tiba | Mengirim satu batch `INSPECT_CANDIDATES` ke Operations Agent |
| Kernel | `evaluate_candidates()` | `evaluate_candidates()` yang **sama** |
| Migrasi | 1 migrasi sukses (S01/S02) | 0 migrasi |
| Data seed / model / policy | Identik | Identik |

Baseline statis tetap memiliki pemrosesan lokal setara (Operations Agent menjalankan
kernel di node tempat data berada). Tidak ada request per baris dan tidak ada penarikan
seluruh database ke Front Office.

## 5. Arsitektur singkat

- **Satu proses**, dua node logis: `FRONT_OFFICE` dan `OPERATIONS`.
- Dua database SQLite `:memory:` terpisah (satu per node) + `applied_operations` untuk idempotency.
- Queue lokal `collections.deque`, tanpa thread/background job.
- Agen: Scenario Scout, Orchestrator, Reservation, Billing, Concierge, Operations, **Mobile Investigator**.
- Policy wajib > prediksi ML (`P(human_judgment) >= 0.80`).
- Capability ditentukan konfigurasi runtime (bukan dari checkpoint/payload).

Status kasus: `CREATED → PROCESSING → WAITING_GUEST / WAITING_HUMAN → HUMAN_HANDLING →
DIGITAL_COMPLETED / CLOSED_GUEST_DECLINED / CLOSED_BY_STAFF / FAILED`.

Tiket (`PENDING → IN_PROGRESS → DONE`) disimpan terpisah dari status kasus. Menutup kasus
tidak menutup tiket.

## 6. Batas dan keterbatasan

- **Label jujur:** yang disimulasikan adalah migrasi **state** agen antar-node logis dalam
  satu proses Python. Kode agen sudah terpasang di kedua node; bukan migrasi kode,
  call stack, atau server fisik.
- **SHA-256** adalah pemeriksaan integritas demo, **bukan** autentikasi/tanda tangan digital.
- Allowlist node/capability dan validasi schema adalah **simulasi kontrol akses**, bukan sandbox OS.
- **ML** dilatih dari dataset sintetis 48 kombinasi dengan aturan anotasi buatan
  (`score >= 6`). Ini contoh pembelajaran, bukan SOP hotel tervalidasi, dan bukan klaim
  ML lebih baik daripada rules. Threshold `0.80` adalah parameter demo, bukan hasil optimisasi.
- Metrik byte payload adalah ukuran JSON kanonik, **bukan wire bytes**; waktu komputasi
  bukan benchmark jaringan/produksi.
- **DL/RL/GNN tidak diimplementasikan pada MVP ini.** MVP memakai ML (logistic regression) + rules.
- Chat bebas, LLM, NLP/DL, booking baru, refund otomatis, Docker, microservices, dan
  multiprocess migration berada di luar scope.
- SQLite in-memory tidak persisten antar restart; artefak laporan diperoleh dari ekspor JSON.

## 7. Struktur proyek

```text
app/
├── app.py                  # entry point Streamlit
├── requirements.txt
├── README.md
├── conftest.py
├── .streamlit/config.toml  # gatherUsageStats = false
├── data/
│   ├── hotel_seed.json
│   ├── scenarios.json
│   └── escalation_synthetic.csv
├── hotel_demo/
│   ├── models.py           # enum, dataclass, Case, kontrak pesan/event
│   ├── repository.py       # dua SQLite, guarded tools, commit atomik, idempotency
│   ├── policy.py           # policy wajib + validasi room change
│   ├── ml.py               # dataset, split, fit, predict, report
│   ├── agents.py           # agen statis + MobileInvestigator + kernel murni
│   ├── migration.py        # prepare / depart / arrive / restore + invariant
│   ├── simulation.py       # engine, queue, event log, lifecycle kasus
│   ├── evaluation.py       # perbandingan static vs mobile
│   └── ui.py               # rendering Streamlit
└── tests/                  # test_ml, test_policy, test_repository, test_migration,
                            # test_scenarios, test_evaluation, test_app
```

## 8. Hasil tes

```
$ python -m pytest -q
65 passed
```

Cakupan: invariant migrasi (zero/one owner, no shared reference, replay no-op, tolak
hash/schema/code-version/node palsu), policy wajib vs ML stub, transaksi dan rollback,
idempotency tiket/perubahan kamar, enam skenario, isolasi simulator, ekspor log,
tanpa koneksi jaringan, serta smoke test Streamlit `AppTest`.

Detail penyelesaian teknis: lihat `IMPLEMENTATION_NOTES.md`.
