"""Script to generate professional PowerPoint presentation for ACE Mobile Agent System."""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    # 16:9 Widescreen layout
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Colors
    NAVY = RGBColor(24, 34, 53)
    ORANGE = RGBColor(255, 107, 53)
    DARK_TEXT = RGBColor(30, 41, 59)
    MUTED_TEXT = RGBColor(100, 116, 139)
    LIGHT_BG = RGBColor(245, 247, 250)
    WHITE = RGBColor(255, 255, 255)
    CARD_BORDER = RGBColor(226, 232, 240)
    ACCENT_BLUE = RGBColor(37, 99, 235)
    GREEN = RGBColor(16, 185, 129)
    RED = RGBColor(239, 68, 68)

    def set_bg(slide, color):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="ACE - INTELLIGENT MOBILE AGENT SYSTEM"):
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.4))
        tf_c = cat_box.text_frame
        tf_c.word_wrap = True
        p_c = tf_c.paragraphs[0]
        p_c.text = category_text.upper()
        p_c.font.size = Pt(11)
        p_c.font.bold = True
        p_c.font.color.rgb = ORANGE

        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.5), Inches(0.8))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.size = Pt(24)
        p_t.font.bold = True
        p_t.font.color.rgb = NAVY

    def add_card(slide, left, top, width, height, bg_color=WHITE, border_color=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)
        return card

    # ==========================================
    # SLIDE 1: Title Slide (Dark Theme)
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    set_bg(s1, NAVY)

    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(1.5), Inches(1.2), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ORANGE
    bar.line.fill.background()

    tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(3.2))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "ACE — Intelligent Mobile Agent System"
    p0.font.size = Pt(36)
    p0.font.bold = True
    p0.font.color.rgb = WHITE

    p1 = tf1.add_paragraph()
    p1.text = "Solusi Multi-Agent Enterprise: Otomasi Layanan Tamu, Perlindungan Pendapatan, & Migrasi State Agen"
    p1.font.size = Pt(18)
    p1.font.color.rgb = RGBColor(203, 213, 225)
    p1.space_before = Pt(14)

    p2 = tf1.add_paragraph()
    p2.text = "Mata Kuliah: Agent Enterprise  |  Program Studi Informatika / Sistem Informasi"
    p2.font.size = Pt(14)
    p2.font.bold = True
    p2.font.color.rgb = ORANGE
    p2.space_before = Pt(20)

    team_card = add_card(s1, Inches(1.0), Inches(5.2), Inches(11.3), Inches(1.5), bg_color=RGBColor(33, 46, 70), border_color=ORANGE)
    tb_team = s1.shapes.add_textbox(Inches(1.2), Inches(5.3), Inches(10.9), Inches(1.3))
    tf_team = tb_team.text_frame
    p_t0 = tf_team.paragraphs[0]
    p_t0.text = "Disusun oleh: KELOMPOK 5"
    p_t0.font.size = Pt(12)
    p_t0.font.bold = True
    p_t0.font.color.rgb = ORANGE

    p_t1 = tf_team.add_paragraph()
    p_t1.text = "• M. Al lail Qadrillah     • Dimas Prabowo     • Monanta Alfiareza     • Frans Alwan"
    p_t1.font.size = Pt(14)
    p_t1.font.color.rgb = WHITE
    p_t1.space_before = Pt(8)

    p_t2 = tf_team.add_paragraph()
    p_t2.text = "Hotel Fiktif: Hotel Nusantara Demo  |  100% Offline, Deterministic, & Local Simulation"
    p_t2.font.size = Pt(11)
    p_t2.font.color.rgb = RGBColor(148, 163, 184)
    p_t2.space_before = Pt(6)

    # ==========================================
    # SLIDE 2: Sisi Bisnis - Masalah Riil Operasional
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    set_bg(s2, LIGHT_BG)
    add_header(s2, "Sisi Bisnis: Masalah Nyata di Operasional Hotel Tradisional", "PERSPEKTIF BISNIS & OPERASIONAL")

    pain_points = [
        ("⏳ Gesekan Koordinasi (Time Friction)", "Ketika AC rusak di malam hari, tamu harus menunggu 30-45 menit karena Front Desk harus koordinasi manual via telepon/intercom ke tim Housekeeping & Engineering yang sedang bertugas di lapangan."),
        ("💥 Risiko Kamar Kotor (Double Complaint)", "Resepsionis melihat kamar kosong di sistem komputer, lalu langsung memindahkan tamu. Ternyata sprei masih kotor (DIRTY) karena status fisik belum diperbarui. Tamu komplain 2 kali!"),
        ("💸 Kebocoran Pendapatan (Revenue Leakage)", "Karena panik menghadapi tamu yang marah di tengah malam, staf Front Office sering memberikan upgrade gratis ke kamar Deluxe/Suite tanpa otorisasi manajer, merugikan pendapatan hotel."),
        ("📉 Kerusakan Reputasi (Online Reviews)", "Keterlambatan penanganan komplain langsung berujung ulasan bintang 1 di TripAdvisor & Google Maps, menurunkan angka okupansi dan tingkat pemesanan ulang (guest retention).")
    ]

    for idx, (title, desc) in enumerate(pain_points):
        col = idx % 2
        row = idx // 2
        x = Inches(0.8 + col * 6.0)
        y = Inches(1.8 + row * 2.5)

        add_card(s2, x, y, Inches(5.6), Inches(2.2), border_color=RED if idx in (1, 2) else CARD_BORDER)
        tb = s2.shapes.add_textbox(x + Inches(0.2), y + Inches(0.15), Inches(5.2), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(12)
        p_desc.font.color.rgb = DARK_TEXT
        p_desc.space_before = Pt(8)

    # ==========================================
    # SLIDE 3: Business Value & ROI
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    set_bg(s3, LIGHT_BG)
    add_header(s3, "Business Value & ROI: Dampak Finansial & Kepuasan Tamu", "NILAI TAMBAH ENTERPRISE")

    # Left: 4 Pillars of Value
    add_card(s3, Inches(0.8), Inches(1.8), Inches(6.0), Inches(5.0))
    tb_val = s3.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.6), Inches(4.6))
    tf_val = tb_val.text_frame
    tf_val.word_wrap = True

    p = tf_val.paragraphs[0]
    p.text = "💎 4 Pilar Nilai Bisnis Sistem ACE"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = NAVY

    pillars = [
        ("Resolusi Cepat 80% Kasus Rutin", "Kasus AC rusak (S01) selesai otomatis dalam < 1 menit. Mobile agent memverifikasi kamar bersih di Operations tanpa perlu telepon manual."),
        ("Proteksi Pendapatan (Revenue Guardrail)", "Aturan bisnis (Policy) mengunci otomatis jika tamu minta upgrade gratis (S02) atau sengketa uang (S03). AI tidak bisa sembarangan menggratiskan kamar!"),
        ("Efisiensi Tenaga Kerja & Lembur", "Menangani ribuan pertanyaan rutin (FAQ check-in/out, Wi-Fi, handuk) secara mandiri. Menghemat beban lembur shift malam."),
        ("Kepuasan & Kepercayaan Tamu (CSAT)", "Tamu menerima penawaran resmi di HP, melihat kamar pengganti bersih & setara, lalu konfirmasi dengan 1 klik.")
    ]

    for title, desc in pillars:
        p_t = tf_val.add_paragraph()
        p_t.text = "• " + title + ": "
        p_t.font.size = Pt(12)
        p_t.font.bold = True
        p_t.font.color.rgb = ORANGE
        p_t.space_before = Pt(8)

        run = p_t.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = DARK_TEXT

    # Right: KPI Comparison Table Card
    add_card(s3, Inches(7.1), Inches(1.8), Inches(5.4), Inches(5.0), border_color=GREEN)
    tb_kpi = s3.shapes.add_textbox(Inches(7.3), Inches(2.0), Inches(5.0), Inches(4.6))
    tf_kpi = tb_kpi.text_frame
    tf_kpi.word_wrap = True

    p_kpi = tf_kpi.paragraphs[0]
    p_kpi.text = "📈 Dampak Terhadap Indikator Kinerja (KPI)"
    p_kpi.font.size = Pt(18)
    p_kpi.font.bold = True
    p_kpi.font.color.rgb = GREEN

    kpis = [
        ("Waktu Resolusi Komplain (MTTR)", "Sebelum: 30 - 45 Menit", "Setelah: < 1 Menit (Instan)"),
        ("Beban Telepon Front Desk", "Sebelum: Sangat Tinggi (Sibuk)", "Setelah: Berkurang hingga 60%"),
        ("Kepatuhan SOP & Pendapatan", "Sebelum: Rentan Human Error", "Setelah: 100% Patuh SOP Policy"),
        ("Kepuasan Tamu (CSAT / NPS)", "Sebelum: Rawan Review Buruk", "Setelah: Meningkat & Tamu Nyaman")
    ]

    for metric, before, after in kpis:
        p_m = tf_kpi.add_paragraph()
        p_m.text = f"📊 {metric}"
        p_m.font.size = Pt(13)
        p_m.font.bold = True
        p_m.font.color.rgb = NAVY
        p_m.space_before = Pt(10)

        p_b = tf_kpi.add_paragraph()
        p_b.text = f"   ❌ {before}  ➔  ✅ {after}"
        p_b.font.size = Pt(11)
        p_b.font.color.rgb = DARK_TEXT
        p_b.space_before = Pt(2)

    # ==========================================
    # SLIDE 4: Mengapa Mobile Agent?
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    set_bg(s4, LIGHT_BG)
    add_header(s4, "Mengapa Konsep 'Mobile Agent'? Perspektif Enterprise IT", "ARUS DATA & KEAMANAN SISTEM")

    add_card(s4, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    tb_st = s4.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.4))
    tf_st = tb_st.text_frame
    tf_st.word_wrap = True
    p = tf_st.paragraphs[0]
    p.text = "🏢 Pendekatan Tradisional (Static Agent)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = NAVY

    items_st = [
        "Data ditarik melintasi jaringan dari Operations ke Front Office.",
        "Membuka database operasional internal ke resepsionis (rawan privasi).",
        "Transfer data mentah yang berulang dan boros bandwidth.",
        "Ketergantungan tinggi pada stabilitas jaringan antar-gedung/resort.",
        "0 Migrasi agen (hanya request-response biasa)."
    ]
    for item in items_st:
        p_i = tf_st.add_paragraph()
        p_i.text = "• " + item
        p_i.font.size = Pt(12)
        p_i.font.color.rgb = DARK_TEXT
        p_i.space_before = Pt(10)

    add_card(s4, Inches(6.9), Inches(1.8), Inches(5.6), Inches(4.8), border_color=ORANGE)
    tb_mb = s4.shapes.add_textbox(Inches(7.2), Inches(2.0), Inches(5.0), Inches(4.4))
    tf_mb = tb_mb.text_frame
    tf_mb.word_wrap = True
    p = tf_mb.paragraphs[0]
    p.text = "🚀 Pendekatan Proyek (Mobile Agent)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ORANGE

    items_mb = [
        "Agen membawa state tugas dan bermigrasi ke tempat data berada.",
        "Inspeksi dilakukan secara lokal di node Operations tanpa eksposur data mentah.",
        "Hanya hasil akhir ('Kamar 103 Ready') yang dilaporkan kembali.",
        "Jauh lebih hemat bandwidth (Checkpoint JSON kanonik hanya ~1-2 KB).",
        "1 Migrasi sukses dengan kontinuitas ID 'MA-001' & integritas SHA-256."
    ]
    for item in items_mb:
        p_i = tf_mb.add_paragraph()
        p_i.text = "• " + item
        p_i.font.size = Pt(12)
        p_i.font.color.rgb = DARK_TEXT
        p_i.space_before = Pt(10)

    # ==========================================
    # SLIDE 5: Arsitektur 2 Node Logis & 7 Agen
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    set_bg(s5, LIGHT_BG)
    add_header(s5, "Arsitektur Sistem: Dua Node Logis & Spesialisasi Agen", "DESAIN ARSITEKTUR PERANGKAT LUNAK")

    add_card(s5, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    tb_fo = s5.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.4))
    tf_fo = tb_fo.text_frame
    tf_fo.word_wrap = True
    p = tf_fo.paragraphs[0]
    p.text = "🏢 Node FRONT_OFFICE"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    p_sub = tf_fo.add_paragraph()
    p_sub.text = "Database In-Memory: Data Tamu, Reservasi, Folio, FAQ"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = MUTED_TEXT
    p_sub.space_before = Pt(4)

    agents_fo = [
        ("Scenario Scout", "Menerima pesan tamu & membentuk request terstruktur."),
        ("Orchestrator", "Pusat koordinasi, triase policy/ML, & alur kasus."),
        ("Reservation Agent", "Mencari kamar setara & commit perpindahan kamar."),
        ("Billing Agent", "Membaca folio & kalkulasi tagihan kamar/minibar."),
        ("Concierge Agent", "Menjawab FAQ hotel (check-in, check-out, Wi-Fi).")
    ]
    for name, desc in agents_fo:
        p_a = tf_fo.add_paragraph()
        p_a.text = f"• {name}: {desc}"
        p_a.font.size = Pt(12)
        p_a.font.color.rgb = DARK_TEXT
        p_a.space_before = Pt(8)

    add_card(s5, Inches(6.9), Inches(1.8), Inches(5.6), Inches(4.8))
    tb_op = s5.shapes.add_textbox(Inches(7.2), Inches(2.0), Inches(5.0), Inches(4.4))
    tf_op = tb_op.text_frame
    tf_op.word_wrap = True
    p = tf_op.paragraphs[0]
    p.text = "🔧 Node OPERATIONS"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GREEN

    p_sub2 = tf_op.add_paragraph()
    p_sub2.text = "Database In-Memory: Status Kesiapan Fisik Kamar & Tiket Petugas"
    p_sub2.font.size = Pt(11)
    p_sub2.font.color.rgb = MUTED_TEXT
    p_sub2.space_before = Pt(4)

    agents_op = [
        ("Operations Agent", "Kelola kesiapan fisik kamar, blok maintenance, & tiket staf."),
        ("Mobile Investigator (MA-001)", "Agen yang bermigrasi dari Front Office ke Operations untuk menginspeksi kesiapan kamar langsung di sumber data.")
    ]
    for name, desc in agents_op:
        p_a = tf_op.add_paragraph()
        p_a.text = f"• {name}: {desc}"
        p_a.font.size = Pt(12)
        p_a.font.color.rgb = DARK_TEXT
        p_a.space_before = Pt(10)

    p_note = tf_op.add_paragraph()
    p_note.text = "🔒 Hak Akses Data: Agen hanya berhak membaca data sesuai hak akses node aktif."
    p_note.font.size = Pt(11)
    p_note.font.bold = True
    p_note.font.color.rgb = ORANGE
    p_note.space_before = Pt(24)

    # ==========================================
    # SLIDE 6: Protokol Migrasi & Integritas
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    set_bg(s6, LIGHT_BG)
    add_header(s6, "Protokol Migrasi State Agen & Jaminan Keamanan SHA-256", "MEKANISME TEKNIS MIGRASI")

    stages = [
        ("1. PREPARE", "Serialisasi state agen (tujuan, kandidat kamar, kriteria) menjadi Checkpoint JSON kanonik UTF-8. Hash SHA-256 digenerate."),
        ("2. DEPART", "Instance agen di node asal ditutup dan diarsipkan. Instance aktif = 0; agen hanya berada di jalur transit."),
        ("3. ARRIVE", "Instance baru dibuat di node tujuan dari checkpoint. Integritas hash SHA-256 & skema divalidasi sebelum aktivasi."),
        ("4. ROLLBACK", "Jika terjadi anomali (hash rusak, skema tidak cocok), mekanisme rollback memulihkan agen ke node asal secara aman.")
    ]

    for idx, (title, desc) in enumerate(stages):
        x = Inches(0.8 + idx * 3.0)
        add_card(s6, x, Inches(1.8), Inches(2.7), Inches(4.8))
        tb = s6.shapes.add_textbox(x + Inches(0.15), Inches(2.0), Inches(2.4), Inches(4.4))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = ORANGE

        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(12)
        p_desc.font.color.rgb = DARK_TEXT
        p_desc.space_before = Pt(12)

    # ==========================================
    # SLIDE 7: Pengalaman Multi-Stakeholder
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    set_bg(s7, LIGHT_BG)
    add_header(s7, "Antarmuka Berbasis Peran (Multi-Stakeholder Experience)", "DESAIN USER EXPERIENCE")

    stakeholders = [
        ("🛎️ Tamu Hotel (Customer)", "Portal interaktif ramah pengguna:\n• Chat asisten AI hotel yang ramah\n• Kartu penawaran kamar baru (bersih & setara)\n• Tombol persetujuan tamu (Consent) langsung\n• Pilihan layanan cepat & ketik keluhan bebas"),
        ("👔 Staf Hotel (Operations)", "Dashboard operasional terpadu:\n• Ringkasan KPI tiket tugas & eskalasi\n• Inbox eskalasi kasus yang butuh staf\n• Tombol 'Ambil Alih' & resolusi catatan staf\n• Papan kerja tiket housekeeping/maintenance"),
        ("💻 Tim IT / DevOps", "Konsol observabilitas mendalam:\n• Pemantauan topologi agen & node\n• Verifikasi integritas hash SHA-256\n• Pengukuran payload bytes & latency\n• Unduh laporan audit log JSON lengkap")
    ]

    for idx, (title, desc) in enumerate(stakeholders):
        x = Inches(0.8 + idx * 4.0)
        add_card(s7, x, Inches(1.8), Inches(3.7), Inches(4.8))
        tb = s7.shapes.add_textbox(x + Inches(0.2), Inches(2.0), Inches(3.3), Inches(4.4))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(12)
        p_desc.font.color.rgb = DARK_TEXT
        p_desc.space_before = Pt(14)

    # ==========================================
    # SLIDE 8: Skenario Pengujian (S01 - S09)
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    set_bg(s8, LIGHT_BG)
    add_header(s8, "9 Skenario Pengujian Realistis & Otomatisasi 1-Klik", "CAKUPAN KASUS BISNIS")

    scenarios_summary = [
        ("S01: AC Rusak — Kamar Setara", "Migrasi Mobile Investigator -> Temukan R103 ready -> Proposal -> Persetujuan Tamu -> Selesai Digital."),
        ("S02: AC Rusak — Minta Upgrade", "Kamar setara habis. Bukti terkumpul, namun dialihkan ke staf karena aturan wajib eskalasi upgrade."),
        ("S03: Sengketa Tagihan Minibar", "Tamu menolak tagihan F02. Kebijakan finansial wajib eskalasi staf (WAITING_HUMAN)."),
        ("S04: Tanya Jam Check-In", "Pertanyaan jam operasional. Dijawab instan oleh Concierge Agent dari FAQ lokal (14.00)."),
        ("S05: Permintaan Handuk", "Layanan kamar. Tiket Housekeeping dibuat otomatis (PENDING -> IN_PROGRESS -> DONE)."),
        ("S06: Rincian Tagihan", "Menampilkan folio tagihan terperinci (Total Rp650.000) tanpa perubahan saldo."),
        ("S07: Jam Check-Out & Late", "Informasi check-out maksimal 12.00 WIB dan alur permohonan late check-out."),
        ("S08: Permintaan Bantal Tambahan", "Housekeeping membuat work order antar bantal tambahan ke kamar tamu."),
        ("S09: Informasi Wi-Fi Hotel", "Concierge menjawab detail SSID HotelNusantara_Guest tanpa kata sandi.")
    ]

    for idx, (title, desc) in enumerate(scenarios_summary):
        col = idx % 3
        row = idx // 3
        x = Inches(0.8 + col * 4.0)
        y = Inches(1.8 + row * 1.6)

        add_card(s8, x, y, Inches(3.7), Inches(1.4))
        tb = s8.shapes.add_textbox(x + Inches(0.15), y + Inches(0.1), Inches(3.4), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = ORANGE

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = DARK_TEXT
        p_d.space_before = Pt(3)

    # ==========================================
    # SLIDE 9: Hasil Evaluasi & Kesetaraan
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    set_bg(s9, LIGHT_BG)
    add_header(s9, "Evaluasi & Benchmark: Kesetaraan Hasil Bisnis", "VERIFIKASI & PENGUJIAN ILMIAH")

    add_card(s9, Inches(0.8), Inches(1.8), Inches(11.7), Inches(4.8))
    tb_ev = s9.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(4.4))
    tf_ev = tb_ev.text_frame
    tf_ev.word_wrap = True

    p = tf_ev.paragraphs[0]
    p.text = "📊 Temuan Utama Evaluasi Komparatif (S01 & S02)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = NAVY

    eval_points = [
        ("Hasil Bisnis 100% Identik", "Kedua jalur (Mobile dan Static) menghasilkan keputusan kamar, tarif akhir, dan status tiket yang sama persis karena berbagi kernel evaluasi murni ('evaluate_candidates')."),
        ("Efisiensi Payload & Trafik Komunikasi", "Jalur Mobile Agent mengemas migrasi dalam satu checkpoint kanonik. Tidak ada polling berulang atau penarikan seluruh database reservasi/kamar."),
        ("Keandalan & Kebijakan (Policy vs ML)", "Prediksi Machine Learning (Logistic Regression) dikombinasikan dengan Mandatory Rules. Jika terdeteksi risiko tinggi/sengketa/permintaan staf, aturan bisnis selalu mengesampingkan ML."),
        ("Pengujian Otomatis Menyeluruh", "Seluruh 68 automated unit & integration tests lulus (100% pass) dalam waktu < 4 detik secara deterministik dan offline.")
    ]

    for title, desc in eval_points:
        p_t = tf_ev.add_paragraph()
        p_t.text = "✓ " + title + ": "
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = ORANGE
        p_t.space_before = Pt(12)

        run = p_t.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = DARK_TEXT

    # ==========================================
    # SLIDE 10: Kesimpulan & Penutup
    # ==========================================
    s10 = prs.slides.add_slide(blank_layout)
    set_bg(s10, NAVY)

    tb10 = s10.shapes.add_textbox(Inches(1.5), Inches(1.8), Inches(10.3), Inches(4.0))
    tf10 = tb10.text_frame
    tf10.word_wrap = True

    p0 = tf10.paragraphs[0]
    p0.text = "Kesimpulan & Nilai Tambah Enterprise"
    p0.font.size = Pt(32)
    p0.font.bold = True
    p0.font.color.rgb = WHITE

    points = [
        "Membuktikan kelayakan implementasi konsep Mobile Agent pada domain operasional perhotelan.",
        "Mengurangi waktu penanganan keluhan tamu dari 30-45 menit menjadi < 1 menit secara otonom.",
        "Mencegah kebocoran pendapatan dengan jaminan aturan bisnis mutlak (Policy Guardrails).",
        "Menyediakan antarmuka intuitif untuk 3 stakeholder utama: Tamu, Staf Hotel, dan Tim IT.",
        "Sistem siap didemonstrasikan secara langsung (live interactive demo) maupun otomatis (1-click)."
    ]

    for pt in points:
        p = tf10.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(15)
        p.font.color.rgb = RGBColor(226, 232, 240)
        p.space_before = Pt(12)

    p_close = tf10.add_paragraph()
    p_close.text = "Terima Kasih — Kelompok 5 (Agent Enterprise)"
    p_close.font.size = Pt(20)
    p_close.font.bold = True
    p_close.font.color.rgb = ORANGE
    p_close.space_before = Pt(24)

    # Save presentation
    output_path = "presentasi_ace_mobile_agent_v2.pptx"
    try:
        prs.save("presentasi_ace_mobile_agent.pptx")
        print(f"Presentation saved to {os.path.abspath('presentasi_ace_mobile_agent.pptx')}")
    except PermissionError:
        prs.save(output_path)
        print(f"File utama sedang dibuka oleh aplikasi lain. Berhasil disimpan ke: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    create_deck()
