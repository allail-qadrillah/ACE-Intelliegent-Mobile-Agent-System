# IMPLEMENTATION_NOTES

Catatan penyelesaian teknis selama implementasi PRD v1.0. Tidak mengubah scope.

## 1. Lokasi folder

PRD (bagian 15 dan 19) meminta folder `hotel_mobile_demo/` di sebelah file PRD.
Instruksi pengguna pada sesi ini meminta implementasi di folder `/app`.
Keduanya diselesaikan dengan membangun aplikasi di `app/` (sejajar dengan PRD) dan
seluruh struktur internal mengikuti kontrak modul PRD tanpa perubahan.

## 2. `requirements.txt` memuat `numpy` eksplisit

PRD menyebut dependensi langsung cukup `streamlit`, `scikit-learn`, `pytest`.
`numpy` ditambahkan karena `tests/test_ml.py` memakainya langsung untuk memverifikasi
bahwa `StandardScaler` benar-benar di-fit hanya pada train split. `pandas` tidak dipakai
(tabel dirender lewat `st.dataframe` dari list of dict).

## 3. ML: laporan aturan anotasi

Aturan anotasi `score >= 6` menghasilkan kelas positif yang lebih sedikit sehingga
split 36/12 terstratifikasi memberi 6 positif di train dan 6 di test. Akurasi test pada
recipe ini sekitar `0.917` dengan precision `1.0` dan recall `0.833` (1 false negative).
PRD tidak menetapkan target angka, jadi hasil dilaporkan apa adanya.

Probabilitas aktual untuk fitur skenario (dihitung, bukan hardcode):

| Skenario | Fitur | p(human_judgment) |
|---|---|---|
| S01 | (2,0,0,0) | 0.0107 |
| S02 | (3,1,0,0) | 0.4102 |
| S03 | (4,1,0,0) | 0.7271 |
| S04/S05/S06 | (1,0,0,0) | 0.0028 |

Sesuai AC-22, skenario low-risk S01/S04/S05/S06 berada di bawah threshold 0.80 dan
berjalan rutin. S02 dan S03 tetap eskalasi karena **mandatory flags** policy
(`upgrade_exception`, `compensation_requested`, `financial_dispute`), bukan karena ML —
ini memang perilaku yang diminta PRD bagian 10.1.

## 4. Kelengkapan versi pada commit kamar

PRD bagian 9.4 meminta validasi `version` cocok untuk record yang berubah. Implementasi
menyimpan `reservation_version`, `original_room_version`, `target_room_version`, dan
`proposal_evidence_version` saat proposal dibuat, lalu membandingkannya di commit.
Karena itu setiap perubahan yang tidak terlihat dari proposal akan ditolak dengan
`STALE_ROOM_STATE` (fixture uji AC-10 memverifikasi ini).

## 5. Migrasi gagal sebelum vs sesudah DEPART

- Gagal **sebelum** DEPART (mis. node tujuan tidak aktif): source tetap satu-satunya
  owner dan dikembalikan `ACTIVE` dengan phase `READY_TO_MOVE`.
- Gagal **sesudah** DEPART (mis. hash/schema/node palsu): source direstore dari salinan
  checkpoint asli (`original_bytes`), bukan dari bytes yang rusak. Investigator ditandai
  `FAILED`, kasus menjadi `WAITING_HUMAN`, dan tidak ada auto-retry.

## 6. Idempotency ganda

Dua lapis dipertahankan sesuai PRD bagian 7.3:

1. `processed_message_ids` di engine → event `DUPLICATE_IGNORED` untuk `message_id` yang sama.
2. `applied_operations` per node → operasi berbeda dengan `operation_key` sama
   mengembalikan hasil tersimpan tanpa side effect baru (tiket dan room change).

## 7. Perbandingan static vs mobile

Pesan antar-node sedikit lebih banyak pada jalur mobile karena migrasi menambah
`MIGRATION_ARRIVED` dan `INSPECT_CANDIDATES` lintas node, sementara jalur statis
mengirim satu batch ke Operations Agent. Hasil bisnis, kernel inspeksi, jumlah tiket,
tarif, dan folio identik pada kedua jalur. Angka ditampilkan apa adanya tanpa klaim
efisiensi.

## 8. Yang belum dikerjakan

- DL/RL/GNN tidak diimplementasikan (sesuai keputusan MVP PRD bagian 2.3).
- NIM/PIC Kelompok 5 belum diisi karena datanya tidak tersedia.
- SQLite in-memory tidak persisten antar restart (sesuai PRD bagian 9.1).
