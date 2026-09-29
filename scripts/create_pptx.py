"""Script to generate professional PowerPoint presentation for ACE Mobile Agent System."""

import os
import sys
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

    # Theme Colors
    NAVY = RGBColor(24, 34, 53)
    DARK_BLUE = RGBColor(33, 46, 70)
    ORANGE = RGBColor(255, 107, 53)
    DARK_TEXT = RGBColor(30, 41, 59)
    MUTED_TEXT = RGBColor(100, 116, 139)
    LIGHT_BG = RGBColor(245, 247, 250)
    WHITE = RGBColor(255, 255, 255)
    CARD_BORDER = RGBColor(226, 232, 240)
    ACCENT_BLUE = RGBColor(37, 99, 235)
    GREEN = RGBColor(16, 185, 129)
    LIGHT_GREEN = RGBColor(236, 253, 245)
    AMBER = RGBColor(245, 158, 11)

    def set_bg(slide, color):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="ACE - INTELLIGENT MOBILE AGENT SYSTEM"):
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.35))
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

    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(1.3), Inches(1.5), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ORANGE
    bar.line.fill.background()

    tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(11.3), Inches(3.4))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "ACE — Intelligent Mobile Agent System"
    p0.font.size = Pt(36)
    p0.font.bold = True
    p0.font.color.rgb = WHITE

    p1 = tf1.add_paragraph()
    p1.text = "Otomasi Penanganan Komplain & Operasional Hotel Nusantara Berbasis Mobile Agent"
    p1.font.size = Pt(18)
    p1.font.color.rgb = RGBColor(203, 213, 225)
    p1.space_before = Pt(12)

    p2 = tf1.add_paragraph()
    p2.text = "Mata Kuliah: Agent Enterprise  |  Program Studi Informatika / Sistem Informasi  |  Semester 3"
    p2.font.size = Pt(13)
    p2.font.bold = True
    p2.font.color.rgb = ORANGE
    p2.space_before = Pt(16)

    # Team Card
    add_card(s1, Inches(1.0), Inches(5.0), Inches(11.3), Inches(1.7), bg_color=DARK_BLUE, border_color=ORANGE)
    tb_team = s1.shapes.add_textbox(Inches(1.2), Inches(5.1), Inches(10.9), Inches(1.5))
    tf_team = tb_team.text_frame
    tf_team.word_wrap = True

    pt0 = tf_team.paragraphs[0]
    pt0.text = "👥 KELOMPOK 5 — TIM PENGEMBANG:"
    pt0.font.size = Pt(13)
    pt0.font.bold = True
    pt0.font.color.rgb = WHITE

    members = [
        ("M. Al lail Qadrillah", "Arsitektur Sistem & Lead Developer"),
        ("Dimas Prabowo", "Evaluasi Model ML & Data Pipeline"),
        ("Monanta Alfiareza", "Protokol Migrasi State & Keamanan"),
        ("Frans Alwan", "Antarmuka Pengguna & Integrasi Bisnis")
    ]
    pt1 = tf_team.add_paragraph()
    pt1.space_before = Pt(6)
    for i, (name, role) in enumerate(members):
        sep = "   |   " if i < len(members) - 1 else ""
        r1 = pt1.add_run()
        r1.text = f"{name} "
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = ORANGE
        r2 = pt1.add_run()
        r2.text = f"({role}){sep}"
        r2.font.size = Pt(10)
        r2.font.color.rgb = RGBColor(203, 213, 225)

    # ==========================================
    # SLIDE 2: Masalah Bisnis Operasional Hotel
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    set_bg(s2, LIGHT_BG)
    add_header(s2, "Tantangan Nyata Operasional Hotel Tradisional")

    problems = [
        ("📞 Koordinasi Lambat & Silo Data", "Front Office dan Housekeeping bekerja terpisah. Koordinasi keluhan tamu via telepon manual memakan waktu rata-rata 35-45 menit.", "Beban telepon meja depan tinggi & tamu menunggu di kamar yang rusak."),
        ("🧹 Risiko Kamar Kotor (Double Complaint)", "Resepsionis memindahkan tamu ke kamar kosong di sistem tanpa verifikasi fisik kesiapan kamar. Tamu mendapati kamar baru belum dibersihkan!", "Keluhan berulang dan ulasan bintang 1 di platform online."),
        ("💸 Kebocoran Finansial (Upgrade Liar)", "Staf panik saat komplain tengah malam sering memberikan upgrade gratis ke kamar mewah tanpa wewenang manajer hotel.", "Margin profit hotel tergerus dan pelanggaran SOP berulang.")
    ]

    for idx, (title, desc, impact) in enumerate(problems):
        x = Inches(0.8 + idx * 4.0)
        add_card(s2, x, Inches(1.8), Inches(3.7), Inches(4.9))
        tb = s2.shapes.add_textbox(x + Inches(0.2), Inches(2.0), Inches(3.3), Inches(4.5))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = DARK_TEXT
        p_d.space_before = Pt(12)

        p_imp_title = tf.add_paragraph()
        p_imp_title.text = "Dampak Kerugian:"
        p_imp_title.font.size = Pt(11)
        p_imp_title.font.bold = True
        p_imp_title.font.color.rgb = ORANGE
        p_imp_title.space_before = Pt(16)

        p_imp = tf.add_paragraph()
        p_imp.text = impact
        p_imp.font.size = Pt(11)
        p_imp.font.color.rgb = MUTED_TEXT
        p_imp.space_before = Pt(2)

    # ==========================================
    # SLIDE 3: Solusi Sistem ACE & 3 Nilai Bisnis Utama
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    set_bg(s3, LIGHT_BG)
    add_header(s3, "Solusi ACE: Otomasi Cerdas Berbasis Mobile Agent")

    solutions = [
        ("⚡ Resolusi Super Cepat (< 1 Menit)", "Menyelesaikan 80% keluhan kamar rutin secara mandiri dan otomatis tanpa membebani resepsionis telepon.", "Penghematan Waktu Staf Hingga 360 Jam / Bulan"),
        ("🔍 Zero Double-Complaint (Verifikasi Fisik)", "Mobile Investigator bermigrasi langsung ke database Housekeeping untuk mengeliminasi kamar kotor (R102) dan hanya menawarkan kamar siap huni (R103).", "Tingkat Kepuasan Tamu (CSAT) Meningkat ke 4.9/5.0"),
        ("🛡️ Proteksi Pendapatan (Policy Guardrail)", "AI dibatasi aturan bisnis ketat. Permohonan upgrade kamar mewah gratis (S02) otomatis dikunci dan dialihkan ke persetujuan Manajer.", "Mencegah Kebocoran Finansial Rp 11.2 Juta / Bulan")
    ]

    for idx, (title, desc, value) in enumerate(solutions):
        x = Inches(0.8 + idx * 4.0)
        add_card(s3, x, Inches(1.8), Inches(3.7), Inches(4.9), bg_color=WHITE, border_color=ORANGE)
        tb = s3.shapes.add_textbox(x + Inches(0.2), Inches(2.0), Inches(3.3), Inches(4.5))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = ORANGE

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = DARK_TEXT
        p_d.space_before = Pt(14)

        p_v_title = tf.add_paragraph()
        p_v_title.text = "Nilai Tambah Nyata:"
        p_v_title.font.size = Pt(11)
        p_v_title.font.bold = True
        p_v_title.font.color.rgb = GREEN
        p_v_title.space_before = Pt(18)

        p_v = tf.add_paragraph()
        p_v.text = value
        p_v.font.size = Pt(11)
        p_v.font.color.rgb = DARK_TEXT
        p_v.space_before = Pt(2)

    # ==========================================
    # SLIDE 4: Fitur Kemudahan Penggunaan (Usability Redesign)
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    set_bg(s4, LIGHT_BG)
    add_header(s4, "Antarmuka Ramah Manajemen: Bebas Jargon Koding")

    features = [
        ("🎬 4 Kartu Kasus Nyata (1-Click)", "Menggantikan kode skenario rumit (S01-S06) dengan kartu cerita kasus nyata: Pak Budi (AC Bocor), Ibu Sarah (Minta Suite), Mas Kevin (Kamar Kotor), dan Mbak Rina (Sarapan)."),
        ("⏯️ Auto-Play Simulation Player", "Kendali penuh simulasi layaknya video: tombol Play Otomatis (jeda ~1 detik per langkah), Pause, dan Langkah Manual untuk presentasi yang santai tanpa repot mengklik berulang."),
        ("🚨 Universal Action Bar", "Tombol persetujuan tamu (Setujui Pindah Kamar) dan eskalasi manajer (Ambil Alih Kasus) otomatis muncul di bagian atas layar di tab mana pun Anda berada. Pengguna tidak akan pernah tersesat!"),
        ("📖 Panduan Kilat 1-Menit", "Menu panduan 3 langkah di bagian paling atas untuk memandu audiens/dosen menjalankan demo dalam 60 detik.")
    ]

    for idx, (title, desc) in enumerate(features):
        x = Inches(0.8 + (idx % 2) * 5.9)
        y = Inches(1.8 + (idx // 2) * 2.5)
        add_card(s4, x, y, Inches(5.6), Inches(2.3))
        tb = s4.shapes.add_textbox(x + Inches(0.2), y + Inches(0.15), Inches(5.2), Inches(2.0))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = DARK_TEXT
        p_d.space_before = Pt(8)

    # ==========================================
    # SLIDE 5: Alur 6-Fase Live Stepper & Narasi
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    set_bg(s5, LIGHT_BG)
    add_header(s5, "Indikator Visual 6-Fase Alur Penanganan Komplain")

    stepper_steps = [
        ("1. Keluhan Masuk", "Pesan dari Tamu di HP", "Scenario Scout membaca keluhan dan membuat tiket kasus resmi."),
        ("2. Analisis Kasus", "Evaluasi SOP Hotel", "Orchestrator menganalisis keluhan dengan model ML dan memeriksa batasan SOP."),
        ("3. Koordinasi Dept", "Pemeriksaan Sistem", "Mobile Investigator mengemas koper state (SHA-256) menuju database Housekeeping."),
        ("4. Verifikasi Fisik", "Kesiapan Kamar", "Kamar R102 kotor otomatis dieliminasi; kamar R103 bersih & siap huni dipilih."),
        ("5. Persetujuan / Staf", "Konfirmasi / Manajer", "Proposal kamar dikirimkan ke HP tamu untuk disetujui, atau eskalasi ke staf."),
        ("6. Masalah Selesai", "Kamar Resmi Pindah", "Status reservasi diperbarui atomik tanpa komplain berulang.")
    ]

    for idx, (title, sub, detail) in enumerate(stepper_steps):
        col = idx % 3
        row = idx // 3
        x = Inches(0.8 + col * 4.0)
        y = Inches(1.8 + row * 2.5)

        add_card(s5, x, y, Inches(3.7), Inches(2.3))
        tb = s5.shapes.add_textbox(x + Inches(0.15), y + Inches(0.15), Inches(3.4), Inches(2.0))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = ORANGE

        p_sub = tf.add_paragraph()
        p_sub.text = sub
        p_sub.font.size = Pt(10)
        p_sub.font.bold = True
        p_sub.font.color.rgb = MUTED_TEXT
        p_sub.space_before = Pt(2)

        p_det = tf.add_paragraph()
        p_det.text = detail
        p_det.font.size = Pt(11)
        p_det.font.color.rgb = DARK_TEXT
        p_det.space_before = Pt(8)

    # ==========================================
    # SLIDE 6: Dasbor Eksekutif & Kalkulator Simulasi ROI
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    set_bg(s6, LIGHT_BG)
    add_header(s6, "Dasbor Eksekutif: Metrik Nilai Bisnis & Kalkulator ROI")

    # 4 ROI Cards
    metrics = [
        ("Waktu Resolusi (MTTR)", "< 1 Menit", "97% Lebih Cepat vs 35 Menit Manual"),
        ("Proteksi Pendapatan", "100% Aman", "Zero Leakage via Policy Guardrail"),
        ("Beban Meja Depan", "-60%", "Otomasi Keluhan Kamar Rutin"),
        ("Kepuasan Tamu (CSAT)", "4.9 / 5.0", "Mencegah Ulasan Bintang 1 Online")
    ]
    for idx, (title, val, delta) in enumerate(metrics):
        x = Inches(0.8 + idx * 3.0)
        add_card(s6, x, Inches(1.8), Inches(2.7), Inches(1.5), bg_color=WHITE, border_color=CARD_BORDER)
        tb = s6.shapes.add_textbox(x + Inches(0.1), Inches(1.9), Inches(2.5), Inches(1.3))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(11)
        p.font.color.rgb = MUTED_TEXT

        p_v = tf.add_paragraph()
        p_v.text = val
        p_v.font.size = Pt(20)
        p_v.font.bold = True
        p_v.font.color.rgb = ORANGE
        p_v.space_before = Pt(3)

        p_d = tf.add_paragraph()
        p_d.text = delta
        p_d.font.size = Pt(9)
        p_d.font.color.rgb = GREEN
        p_d.space_before = Pt(2)

    # Interactive Calculator Box
    add_card(s6, Inches(0.8), Inches(3.6), Inches(11.7), Inches(3.1))
    tb_calc = s6.shapes.add_textbox(Inches(1.1), Inches(3.8), Inches(11.1), Inches(2.7))
    tf_calc = tb_calc.text_frame
    tf_calc.word_wrap = True

    p_c0 = tf_calc.paragraphs[0]
    p_c0.text = "🧮 Hasil Simulasi ROI Hotel (Contoh Skala: 150 Kamar & 15 Keluhan/Hari)"
    p_c0.font.size = Pt(16)
    p_c0.font.bold = True
    p_c0.font.color.rgb = NAVY

    calc_points = [
        ("Waktu Staf Dihemat:", "360 Jam per Bulan", "Setara dengan produktivitas 2 staf penuh waktu yang dapat dialihkan melayani tamu VIP."),
        ("Kebocoran Biaya Dicegah:", "Rp 11.250.000 per Bulan", "Dihitung dari pencegahan 45 kasus permohonan upgrade liar (selisih tarif Rp250.000/kamar)."),
        ("Pencegahan Komplain Berulang:", "360 Tamu per Bulan", "Tamu menerima solusi kamar bersih dalam < 1 menit langsung di smartphone mereka.")
    ]
    for label, val, desc in calc_points:
        p_item = tf_calc.add_paragraph()
        p_item.text = f"• {label} "
        p_item.font.size = Pt(12)
        p_item.font.bold = True
        p_item.font.color.rgb = DARK_TEXT
        p_item.space_before = Pt(8)

        r_val = p_item.add_run()
        r_val.text = f"{val} — "
        r_val.font.bold = True
        r_val.font.color.rgb = ORANGE

        r_desc = p_item.add_run()
        r_desc.text = desc
        r_desc.font.bold = False
        r_desc.font.color.rgb = MUTED_TEXT

    # ==========================================
    # SLIDE 7: Arsitektur Teknis Dua Node Logis
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    set_bg(s7, LIGHT_BG)
    add_header(s7, "Arsitektur Sistem: Dua Node Logis & Spesialisasi Agen")

    # Node 1: Front Office
    add_card(s7, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.9))
    tb_fo = s7.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.5))
    tf_fo = tb_fo.text_frame
    tf_fo.word_wrap = True
    p = tf_fo.paragraphs[0]
    p.text = "🏢 Node FRONT_OFFICE"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    p_sub = tf_fo.add_paragraph()
    p_sub.text = "Database In-Memory: Data Tamu, Reservasi, Folio Tagihan, FAQ"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = MUTED_TEXT
    p_sub.space_before = Pt(4)

    agents_fo = [
        ("Scenario Scout", "Membaca pesan tamu & membuat tiket terstruktur."),
        ("Orchestrator", "Triase keluhan, klasifikasi risiko ML, & koordinasi alur."),
        ("Reservation Agent", "Mencari kandidat kamar & eksekusi commit mutasi."),
        ("Billing Agent", "Membaca folio tagihan & kalkulasi biaya minibar."),
        ("Concierge Agent", "Menjawab FAQ umum hotel (check-in, check-out, Wi-Fi).")
    ]
    for name, desc in agents_fo:
        p_a = tf_fo.add_paragraph()
        p_a.text = f"• {name}: {desc}"
        p_a.font.size = Pt(12)
        p_a.font.color.rgb = DARK_TEXT
        p_a.space_before = Pt(8)

    # Node 2: Operations
    add_card(s7, Inches(6.9), Inches(1.8), Inches(5.6), Inches(4.9))
    tb_op = s7.shapes.add_textbox(Inches(7.2), Inches(2.0), Inches(5.0), Inches(4.5))
    tf_op = tb_op.text_frame
    tf_op.word_wrap = True
    p = tf_op.paragraphs[0]
    p.text = "🔧 Node OPERATIONS"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GREEN

    p_sub2 = tf_op.add_paragraph()
    p_sub2.text = "Database In-Memory: Kesiapan Fisik Kamar & Tiket Petugas"
    p_sub2.font.size = Pt(11)
    p_sub2.font.color.rgb = MUTED_TEXT
    p_sub2.space_before = Pt(4)

    agents_op = [
        ("Operations Agent", "Koordinator pembersihan kamar & tiket kerja staf fisik."),
        ("Mobile Investigator (MA-001)", "Agen yang bermigrasi dari Front Office ke Operations untuk menginspeksi kesiapan kamar langsung di sumber data.")
    ]
    for name, desc in agents_op:
        p_a = tf_op.add_paragraph()
        p_a.text = f"• {name}: {desc}"
        p_a.font.size = Pt(12)
        p_a.font.color.rgb = DARK_TEXT
        p_a.space_before = Pt(10)

    p_mig = tf_op.add_paragraph()
    p_mig.text = "✈️ Siklus Migrasi State: PREPARE → DEPART → ARRIVE (SHA-256 Validated)"
    p_mig.font.size = Pt(11)
    p_mig.font.bold = True
    p_mig.font.color.rgb = ORANGE
    p_mig.space_before = Pt(22)

    # ==========================================
    # SLIDE 8: Komparasi Mobile vs Static Agent
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    set_bg(s8, LIGHT_BG)
    add_header(s8, "Evaluasi Komparatif: Mobile Agent vs Static Agent")

    add_card(s8, Inches(0.8), Inches(1.8), Inches(11.7), Inches(4.9))
    tb_cmp = s8.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(4.5))
    tf_cmp = tb_cmp.text_frame
    tf_cmp.word_wrap = True

    p0 = tf_cmp.paragraphs[0]
    p0.text = "📊 Perbandingan Dua Jalur Arsitektur pada Skenario Identik (S01 & S02)"
    p0.font.size = Pt(17)
    p0.font.bold = True
    p0.font.color.rgb = NAVY

    comparisons = [
        ("Lokasi Eksekusi Evaluasi", "Instance agen bermigrasi ke node OPERATIONS dan menjalankan kernel inspeksi lokal.", "Agen tetap berada di FRONT_OFFICE dan mengirim request RPC berulang."),
        ("Efisiensi Komunikasi", "Hanya 1 kali pengiriman koper state JSON kanonik.", "Mengandalkan pertukaran pesan request/response multi-hop."),
        ("Privasi & Keamanan Data", "Data audit operasional internal tetap berada di node lokal (Zero Data Leakage).", "Data operasional harus dikirim melintasi batas jaringan Front Office."),
        ("Kesetaraan Hasil Bisnis", "Keputusan kamar (R103) dan tarif akhir 100% identik.", "Keputusan kamar (R103) dan tarif akhir 100% identik.")
    ]

    for aspect, mob, sta in comparisons:
        p_item = tf_cmp.add_paragraph()
        p_item.text = f"• {aspect}: "
        p_item.font.size = Pt(12)
        p_item.font.bold = True
        p_item.font.color.rgb = NAVY
        p_item.space_before = Pt(10)

        r_mob = p_item.add_run()
        r_mob.text = f"[Mobile] {mob}  vs  "
        r_mob.font.bold = False
        r_mob.font.color.rgb = ORANGE

        r_sta = p_item.add_run()
        r_sta.text = f"[Static] {sta}"
        r_sta.font.bold = False
        r_sta.font.color.rgb = MUTED_TEXT

    # ==========================================
    # SLIDE 9: Hasil Pengujian & Verifikasi Kualitas
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    set_bg(s9, LIGHT_BG)
    add_header(s9, "Pengujian Otomatis & Keandalan Sistem (68/68 Passed)")

    tests_info = [
        ("Integritas Migrasi State", "Verifikasi SHA-256 hash, jaminan single-instance active, serta mekanisme restore/rollback jika transit gagal.", "100% Lulus"),
        ("Policy Guardrail vs ML", "Model Logistic Regression mengklasifikasikan risiko komplain; Aturan Kebijakan Bisnis selalu mengesampingkan ML jika terjadi sengketa.", "100% Lulus"),
        ("Konsistensi Transaksi DB", "Dua database SQLite in-memory terisolasi; mutasi kamar bersifat atomik dan aman dari konflik konkurensi.", "100% Lulus"),
        ("Automated Test Suite (pytest)", "Seluruh 68 automated unit & integration tests selesai dalam waktu 3.3 detik secara deterministik dan offline.", "68 / 68 Passed")
    ]

    for idx, (title, desc, status) in enumerate(tests_info):
        x = Inches(0.8 + (idx % 2) * 5.9)
        y = Inches(1.8 + (idx // 2) * 2.5)
        add_card(s9, x, y, Inches(5.6), Inches(2.3))
        tb = s9.shapes.add_textbox(x + Inches(0.2), y + Inches(0.15), Inches(5.2), Inches(2.0))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_s = tf.add_paragraph()
        p_s.text = f"Status: {status}"
        p_s.font.size = Pt(11)
        p_s.font.bold = True
        p_s.font.color.rgb = GREEN
        p_s.space_before = Pt(3)

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = DARK_TEXT
        p_d.space_before = Pt(6)

    # ==========================================
    # SLIDE 10: Kesimpulan & Penutup (Dark Theme)
    # ==========================================
    s10 = prs.slides.add_slide(blank_layout)
    set_bg(s10, NAVY)

    tb10 = s10.shapes.add_textbox(Inches(1.5), Inches(1.6), Inches(10.3), Inches(4.5))
    tf10 = tb10.text_frame
    tf10.word_wrap = True

    p0 = tf10.paragraphs[0]
    p0.text = "Kesimpulan & Dampak bagi Industri Perhotelan"
    p0.font.size = Pt(30)
    p0.font.bold = True
    p0.font.color.rgb = WHITE

    points = [
        "Membuktikan kelayakan paradigma Mobile Agent dalam menyelesaikan komplain kamar hotel dalam hitungan detik.",
        "Mencegah 'Double Complaint' dengan memverifikasi kesiapan fisik kamar secara lokal langsung di database operasional.",
        "Menjamin perlindungan pendapatan hotel dari kompensasi liar melalui Policy Guardrail yang kokoh.",
        "Menyediakan antarmuka intuitif bagi 3 pemangku kepentingan: Tamu Hotel, Staf Operasional, dan Tim Manajemen/IT."
    ]

    for pt in points:
        p = tf10.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(15)
        p.font.color.rgb = RGBColor(226, 232, 240)
        p.space_before = Pt(14)

    p_close = tf10.add_paragraph()
    p_close.text = "Terima Kasih — Kelompok 5 (Agent Enterprise)"
    p_close.font.size = Pt(20)
    p_close.font.bold = True
    p_close.font.color.rgb = ORANGE
    p_close.space_before = Pt(26)

    # Safe save routine
    targets = [
        "presentasi_ace_mobile_agent_v4.pptx",
        "presentasi_ace_mobile_agent_v3.pptx",
        "presentasi_ace_mobile_agent.pptx"
    ]
    saved_paths = []
    for tgt in targets:
        try:
            prs.save(tgt)
            saved_paths.append(tgt)
            print(f"Presentation successfully saved to: {os.path.abspath(tgt)}")
        except PermissionError:
            print(f"Skipping {tgt} (currently locked/open in PowerPoint)")

    if not saved_paths:
        fallback = "presentasi_ace_mobile_agent_latest.pptx"
        prs.save(fallback)
        print(f"Presentation saved to fallback: {os.path.abspath(fallback)}")

if __name__ == "__main__":
    create_deck()
