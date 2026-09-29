"""Script untuk men-generate presentasi PowerPoint profesional (PPTX)
berdasarkan dokumen resmi Laporan Tugas 2 (Intelligent Multi-Agent System Hotel).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

# Output paths
TARGET_DIR = Path(__file__).resolve().parent
TARGET_PPTX = TARGET_DIR / "Laporan_Tugas_2_Multiagent_Hotel.pptx"
DOWNLOADS_DIR = Path(r"C:\Users\Admin\Downloads")
DOWNLOADS_PPTX = DOWNLOADS_DIR / "Laporan_Tugas_2_Multiagent_Hotel.pptx"

# Color Palette (Corporate Academic / Tech Navy & Teal)
C_NAVY_DARK = RGBColor(15, 23, 42)      # #0F172A - Deep slate navy
C_NAVY_LIGHT = RGBColor(30, 41, 59)     # #1E293B - Card background dark
C_TEAL = RGBColor(13, 148, 136)         # #0D9488 - Teal accent
C_BLUE = RGBColor(37, 99, 235)          # #2563EB - Royal blue
C_LIGHT_BG = RGBColor(248, 250, 252)    # #F8FAFC - Slide background light
C_WHITE = RGBColor(255, 255, 255)       # Pure white
C_CARD_BORDER = RGBColor(226, 232, 240) # #E2E8F0 - Subtle border
C_TEXT_DARK = RGBColor(30, 41, 59)      # #1E293B - Primary dark text
C_TEXT_MUTED = RGBColor(100, 116, 139)  # #64748B - Secondary muted text
C_SUCCESS = RGBColor(22, 101, 52)       # #166534 - Forest green
C_WARNING = RGBColor(180, 83, 9)        # #B45309 - Amber warning
C_CARD_BG = RGBColor(255, 255, 255)     # Card fill


def create_slide_header(slide, title_text: str, category_text: str = "LAPORAN TUGAS 2 • MULTI-AGENT CUSTOMER SERVICE HOTEL") -> None:
    """Tambahkan header standar yang rapi pada slide."""
    # Category badge / breadcrumb
    badge_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
    tf_b = badge_box.text_frame
    tf_b.word_wrap = True
    tf_b.margin_left = tf_b.margin_top = tf_b.margin_right = tf_b.margin_bottom = 0
    p_b = tf_b.paragraphs[0]
    p_b.text = category_text.upper()
    p_b.font.size = Pt(10)
    p_b.font.bold = True
    p_b.font.color.rgb = C_TEAL

    # Main Slide Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.6))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.size = Pt(22)
    p_t.font.bold = True
    p_t.font.color.rgb = C_NAVY_DARK

    # Subtle horizontal line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.4), Inches(11.73), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = C_CARD_BORDER
    line.line.color.rgb = C_CARD_BORDER


def add_card(slide, left, top, width, height, bg_color=C_WHITE, border_color=C_CARD_BORDER):
    """Tambahkan kartu berbentuk persegi panjang dengan border halus."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1)
    return card


def build_presentation() -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: TITLE & IDENTITAS KELOMPOK
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = C_NAVY_DARK
    bg1.line.fill.background()

    # Pill badge
    pill1 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(0.9), Inches(3.8), Inches(0.45))
    pill1.fill.solid()
    pill1.fill.fore_color.rgb = C_TEAL
    pill1.line.fill.background()
    p1_tf = pill1.text_frame
    p1_tf.paragraphs[0].text = "LAPORAN TUGAS 2 • PROTOTIPE MAS"
    p1_tf.paragraphs[0].font.size = Pt(11)
    p1_tf.paragraphs[0].font.bold = True
    p1_tf.paragraphs[0].font.color.rgb = C_WHITE
    p1_tf.paragraphs[0].alignment = PP_ALIGN.CENTER

    # Title Box
    t1_box = s1.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(11.3), Inches(2.2))
    tf1 = t1_box.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "CUSTOMER SERVICE AGENT"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = C_WHITE

    p2 = tf1.add_paragraph()
    p2.text = "Multiagent Customer Service Hotel: Simulasi Migrasi State Mobile Agent"
    p2.font.size = Pt(20)
    p2.font.color.rgb = RGBColor(148, 163, 184)
    p2.space_before = Pt(8)

    p3 = tf1.add_paragraph()
    p3.text = "Magister Kecerdasan Artifisial — Universitas Gadjah Mada (UGM) 2026\nDosen Pengampu: Prof. Dr. Azhari, MT."
    p3.font.size = Pt(13)
    p3.font.color.rgb = RGBColor(203, 213, 225)
    p3.space_before = Pt(12)

    # Team Members Card
    team_card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(4.3), Inches(11.33), Inches(2.3))
    team_card.fill.solid()
    team_card.fill.fore_color.rgb = C_NAVY_LIGHT
    team_card.line.color.rgb = RGBColor(51, 65, 85)

    team_tf = team_card.text_frame
    team_tf.word_wrap = True
    t_head = team_tf.paragraphs[0]
    t_head.text = "KELOMPOK 5 — TIM PENYUSUN & MATRIKS TANGGUNG JAWAB:"
    t_head.font.size = Pt(13)
    t_head.font.bold = True
    t_head.font.color.rgb = RGBColor(56, 189, 248)

    members = [
        ("M. Al lail Qadrillah", "26/590736/PPA/07413", "Leader & Core Engine Developer"),
        ("Dimas Prabowo", "26/590092/PPA/07382", "Researcher & Benchmark Evaluation"),
        ("Monanta Alfiareza", "26/591492/PPA/07455", "Designer, UI/UX & Flow Streamlit"),
        ("Frans Alwan Purba", "25/563545/PPA/07116", "Evaluator, Correctness Suite & Presenter"),
    ]

    for name, nim, role in members:
        p = team_tf.add_paragraph()
        p.text = f"• {name} ({nim}) — {role}"
        p.font.size = Pt(11)
        p.font.color.rgb = RGBColor(241, 245, 249)
        p.space_before = Pt(4)

    # =========================================================================
    # SLIDE 2: PROBLEM STATEMENT & PAIN POINTS
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    create_slide_header(s2, "Problem Statement: Tantangan Operasional Customer Service Hotel")

    # 3 Column Cards for Pain Points
    cards_data = [
        (
            "1. Koordinasi Lambat & Silo Data",
            "Front Office, Housekeeping, dan Maintenance beroperasi pada database terpisah. Penanganan keluhan kamar via telepon memakan waktu lama, menimbulkan friksi antar staf, dan membuat tamu menunggu di kamar bermasalah.",
            "Dampak: Waktu tunggu tinggi & inefisiensi staf.",
            C_NAVY_DARK,
        ),
        (
            "2. Risiko Kamar Kotor (Double Complaint)",
            "Resepsionis sering kali memindahkan tamu hanya melihat status 'Vacant' di PMS tanpa tahu kondisi fisik riil dari Housekeeping. Tamu dipindahkan ke kamar yang masih kotor atau sedang diservis.",
            "Dampak: Komplain dua kali & reputasi hotel anjlok.",
            RGBColor(190, 24, 93),
        ),
        (
            "3. Batas Wewenang & Kebocoran Biaya",
            "Keluhan larut malam sering kali memicu staf melakukan upgrade gratis ke kamar tipe mewah (misal Suite) tanpa otorisasi manajerial, menyebabkan kerugian pendapatan hotel secara kumulatif.",
            "Dampak: Kebocoran margin finansial hotel.",
            C_WARNING,
        ),
    ]

    for i, (title, desc, impact, color) in enumerate(cards_data):
        c = add_card(s2, Inches(0.8 + i * 4.0), Inches(1.7), Inches(3.73), Inches(4.3))
        tf = c.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(15)
        p_t.font.bold = True
        p_t.font.color.rgb = color

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = C_TEXT_DARK
        p_d.space_before = Pt(10)

        p_i = tf.add_paragraph()
        p_i.text = f"\n{impact}"
        p_i.font.size = Pt(10.5)
        p_i.font.bold = True
        p_i.font.color.rgb = color
        p_i.space_before = Pt(12)

    # Bottom Scope Summary Card
    b_card = add_card(s2, Inches(0.8), Inches(6.2), Inches(11.73), Inches(0.9), bg_color=RGBColor(241, 245, 249))
    b_tf = b_card.text_frame
    b_tf.word_wrap = True
    b_p = b_tf.paragraphs[0]
    b_p.text = "🎯 Rumusan Masalah & Ruang Lingkup MVP:"
    b_p.font.size = Pt(11)
    b_p.font.bold = True
    b_p.font.color.rgb = C_NAVY_DARK

    b_p2 = b_tf.add_paragraph()
    b_p2.text = "Merancang Multi-Agent System yang mengoordinasikan layanan kamar lintas unit, membedakan keputusan otomatis vs intervensi manusia melalui Policy Guardrails, serta mensimulasikan migrasi state Mobile Agent yang dapat diaudit secara transparan."
    b_p2.font.size = Pt(10)
    b_p2.font.color.rgb = C_TEXT_DARK

    # =========================================================================
    # SLIDE 3: STATE OF THE ART (SOTA) & KONTRIBUSI
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    create_slide_header(s3, "State of the Art (SOTA) & Posisi Kontribusi Akademik")

    # Table of SOTA comparison
    sota_table_shape = s3.shapes.add_table(5, 4, Inches(0.8), Inches(1.7), Inches(11.73), Inches(3.2))
    table = sota_table_shape.table
    table.columns[0].width = Inches(2.2)
    table.columns[1].width = Inches(3.1)
    table.columns[2].width = Inches(3.1)
    table.columns[3].width = Inches(3.33)

    headers = ["Solusi / Produk", "Kemampuan Terdokumentasi", "Kelebihan Relevan", "Batas Pembandingan"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_NAVY_DARK
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_WHITE

    sota_rows = [
        ("HiJiffy / Asksuite", "Guest journey assistant, booking, FAQ, omnichannel", "Fokus komersial konteks perhotelan", "Protokol koordinasi dan migrasi internal tidak terverifikasi terbuka"),
        ("Oracle OHIP", "Spesifikasi REST & integrasi data operasional hotel", "Kontrak integrasi enterprise yang matang", "Platform integrasi API; bukan runtime penerima kode/state agen"),
        ("Mews Connector", "API operasi reservasi dan tiket departemen", "Padanan konkret data tamu & tugas staf", "Endpoint berbatas scope; bukan runtime eksekusi mobile agent"),
        ("Prototipe Kelompok 5", "Simulasi MIMA, dual SQLite in-memory, checkpoint & audit", "Alur terbuka, deterministik, dan dapat diinspeksi", "Data sintetis hotel demo; evaluasi berbasis komparasi setara"),
    ]

    for i, row in enumerate(sota_rows):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(248, 250, 252) if i % 2 == 0 else C_WHITE
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(10)
            p.font.color.rgb = C_TEXT_DARK

    # Bottom contribution cards (2 cards)
    c1 = add_card(s3, Inches(0.8), Inches(5.1), Inches(5.7), Inches(1.9))
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "💡 Transparansi Koordinasi & Auditabilitas"
    p1.font.size = Pt(12)
    p1.font.bold = True
    p1.font.color.rgb = C_BLUE
    p1_desc = tf1.add_paragraph()
    p1_desc.text = "Menyediakan keterjelasan hubungan: Observasi → Keputusan (ML & Policy) → Tindakan → Mutasi State. Seluruh siklus hidup migrasi dan eksekusi tercatat dalam log audit kanonikal yang tidak dapat dimanipulasi."
    p1_desc.font.size = Pt(9.5)
    p1_desc.font.color.rgb = C_TEXT_DARK
    p1_desc.space_before = Pt(4)

    c2 = add_card(s3, Inches(6.8), Inches(5.1), Inches(5.73), Inches(1.9))
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = "⚖️ Evaluasi Empiris Baseline yang Setara"
    p2.font.size = Pt(12)
    p2.font.bold = True
    p2.font.color.rgb = C_TEAL
    p2_desc = tf2.add_paragraph()
    p2_desc.text = "Menguji Mobile MAS head-to-head melawan Static MAS menggunakan database seed, model ML, dan logika bisnis yang identik. Pengurangan beban komunikasi diuji secara statistik, bukan diasumsikan."
    p2_desc.font.size = Pt(9.5)
    p2_desc.font.color.rgb = C_TEXT_DARK
    p2_desc.space_before = Pt(4)

    # =========================================================================
    # SLIDE 4: ARSITEKTUR SISTEM & 2 NODE LOGIS
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    create_slide_header(s4, "Desain Arsitektur Sistem: Dua Node Logis & Spesialisasi Agen")

    # Left Node Card: FRONT_OFFICE
    fo_card = add_card(s4, Inches(0.8), Inches(1.7), Inches(5.7), Inches(5.3))
    fo_tf = fo_card.text_frame
    fo_tf.word_wrap = True
    fo_p = fo_tf.paragraphs[0]
    fo_p.text = "🏢 Node FRONT_OFFICE (Layanan Tamu & Tagihan)"
    fo_p.font.size = Pt(14)
    fo_p.font.bold = True
    fo_p.font.color.rgb = C_BLUE

    fo_db = fo_tf.add_paragraph()
    fo_db.text = "Basis Data Lokal SQLite: guests, reservations, rooms, folio, FAQ, cases"
    fo_db.font.size = Pt(10)
    fo_db.font.italic = True
    fo_db.font.color.rgb = C_TEXT_MUTED
    fo_db.space_before = Pt(4)

    fo_agents = [
        ("Scenario Scout", "Membaca input skenario/pesan tamu dan membentuk request terstruktur."),
        ("Orchestrator Agent", "Pusat koordinasi, triase kasus, inferensi ML, dan orkestrasi subtask."),
        ("Reservation Agent", "Membaca ketersediaan kamar, mengajukan proposal, dan eksekusi commit."),
        ("Billing Agent", "Akses folio transaksi tamu; dilarang keras mengubah saldo sepihak."),
        ("Concierge Agent", "Menjawab FAQ umum hotel (check-in, Wi-Fi) dari knowledge base lokal."),
        ("Policy Agent", "Penjaga aturan wajib bisnis (guardrails) sebelum tindakan dieksekusi."),
    ]
    for a_name, a_desc in fo_agents:
        p = fo_tf.add_paragraph()
        p.text = f"• {a_name}: {a_desc}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = C_TEXT_DARK
        p.space_before = Pt(4)

    # Right Node Card: OPERATIONS
    ops_card = add_card(s4, Inches(6.8), Inches(1.7), Inches(5.73), Inches(5.3))
    ops_tf = ops_card.text_frame
    ops_tf.word_wrap = True
    ops_p = ops_tf.paragraphs[0]
    ops_p.text = "⚙️ Node OPERATIONS (Fasilitas & Fisik Kamar)"
    ops_p.font.size = Pt(14)
    ops_p.font.bold = True
    ops_p.font.color.rgb = C_TEAL

    ops_db = ops_tf.add_paragraph()
    ops_db.text = "Basis Data Lokal SQLite: room_readiness, maintenance_tickets"
    ops_db.font.size = Pt(10)
    ops_db.font.italic = True
    ops_db.font.color.rgb = C_TEXT_MUTED
    ops_db.space_before = Pt(4)

    ops_agents = [
        ("Operations Agent", "Mengelola tiket staf pemeliharaan & membaca status kesiapan kamar."),
        ("Mobile Investigator (MA-001)", "Agen mobile yang bermigrasi membawa working state dari FO ke OPS untuk melakukan inspeksi lokal mandiri."),
    ]
    for a_name, a_desc in ops_agents:
        p = ops_tf.add_paragraph()
        p.text = f"• {a_name}: {a_desc}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = C_TEXT_DARK
        p.space_before = Pt(6)

    # Mobility Banner inside Operations
    m_box = ops_tf.add_paragraph()
    m_box.text = "\n📦 Simulasi Mobilitas State (MIMA):"
    m_box.font.size = Pt(11)
    m_box.font.bold = True
    m_box.font.color.rgb = C_NAVY_DARK

    m_desc = ops_tf.add_paragraph()
    m_desc.text = "Kode agen prainstal pada kedua runtime. Yang bermigrasi adalah data aplikasi terstruktur (checkpoint JSON kanonikal) yang diverifikasi melalui hash SHA-256. Node terisolasi logis tanpa akses memori silang."
    m_desc.font.size = Pt(9.5)
    m_desc.font.color.rgb = C_TEXT_DARK
    m_desc.space_before = Pt(4)

    # =========================================================================
    # SLIDE 5: PROTOKOL MIGRASI STATE MOBILE AGENT
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    create_slide_header(s5, "Mekanisme Simulasi Migrasi State: Protokol 3-Fase")

    # 3 Stage Migration Flow Cards
    stages = [
        ("FASE 1: PREPARE", "Front Office", "• Validasi kapabilitas node tujuan.\n• Serialisasi working state agen ke JSON kanonikal (ID, goal, kandidat kamar, progress).\n• Hitung hash SHA-256 dan ukuran checkpoint.\n• Instance sumber di-suspend.", C_BLUE),
        ("FASE 2: DEPART", "In-Transit", "• Instance aktif dilepas dari registry Front Office.\n• Status agen resmi IN_TRANSIT.\n• Kepemilikan agen (owner) menjadi KOSONG.\n• Invariant terpenuhi: N_active = 0 saat transit.", C_WARNING),
        ("FASE 3: ARRIVE", "Operations", "• Validasi integritas hash SHA-256 & versi skema.\n• Deserialisasi menjadi objek instance baru di node tujuan.\n• Daftarkan owner: OPERATIONS.\n• Lanjutkan inspeksi data lokal.", C_SUCCESS),
    ]

    for i, (title, sub, text, color) in enumerate(stages):
        c = add_card(s5, Inches(0.8 + i * 4.0), Inches(1.7), Inches(3.73), Inches(3.4))
        tf = c.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(14)
        p_t.font.bold = True
        p_t.font.color.rgb = color

        p_s = tf.add_paragraph()
        p_s.text = f"Lokasi: {sub}"
        p_s.font.size = Pt(10)
        p_s.font.bold = True
        p_s.font.color.rgb = C_TEXT_MUTED

        p_d = tf.add_paragraph()
        p_d.text = f"\n{text}"
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = C_TEXT_DARK

    # Invariant & Security Guardrail Card
    inv_card = add_card(s5, Inches(0.8), Inches(5.3), Inches(11.73), Inches(1.7), bg_color=C_NAVY_DARK)
    inv_tf = inv_card.text_frame
    inv_tf.word_wrap = True

    inv_p = inv_tf.paragraphs[0]
    inv_p.text = "🔒 Invariant Kunci & Jaminan Keamanan Migrasi State"
    inv_p.font.size = Pt(13)
    inv_p.font.bold = True
    inv_p.font.color.rgb = RGBColor(56, 189, 248)

    inv_math = inv_tf.add_paragraph()
    inv_math.text = "Invariant Keberadaan Agen:  N_active(a) ∈ {0, 1}   dan   in_transit(a) ⟹ N_active(a) = 0"
    inv_math.font.size = Pt(12)
    inv_math.font.bold = True
    inv_math.font.color.rgb = C_WHITE
    inv_math.space_before = Pt(4)

    inv_desc = inv_tf.add_paragraph()
    inv_desc.text = "• Mencegah duplikasi agen: Tidak pernah ada dua instance aktif bersamaan untuk ID yang sama.\n• Pemulihan kegagalan: Jika hash rusak atau node tujuan tidak aktif, sistem me-restore sumber dan eskalasi teknis."
    inv_desc.font.size = Pt(10)
    inv_desc.font.color.rgb = RGBColor(203, 213, 225)
    inv_desc.space_before = Pt(4)

    # =========================================================================
    # SLIDE 6: ALGORITMA ML & POLICY GUARDRAILS
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    create_slide_header(s6, "Algoritma AI: Model Regresi Logistik & Policy Guardrails")

    # Left: ML Model Details
    ml_card = add_card(s6, Inches(0.8), Inches(1.7), Inches(5.7), Inches(5.3))
    ml_tf = ml_card.text_frame
    ml_tf.word_wrap = True

    ml_p = ml_tf.paragraphs[0]
    ml_p.text = "🤖 Model Regresi Logistik Terlatih Aktual"
    ml_p.font.size = Pt(13)
    ml_p.font.bold = True
    ml_p.font.color.rgb = C_BLUE

    ml_desc = ml_tf.add_paragraph()
    ml_desc.text = "Pipeline: StandardScaler → LogisticRegression(C=1.0, max_iter=1000)\nDilatih lokal secara deterministik (36 sampel train, 12 test, seed 42)."
    ml_desc.font.size = Pt(9.5)
    ml_desc.font.color.rgb = C_TEXT_DARK
    ml_desc.space_before = Pt(4)

    params = [
        ("Intercept (b):", "-0,0876"),
        ("w1 (intent_complexity):", "+1,4557"),
        ("w2 (risk_level):", "+1,4098"),
        ("w3 (prior_failed_attempts):", "+0,9490"),
        ("w4 (context_missing):", "+1,3720"),
        ("Decision Threshold (τ):", "0,80 (Demonstrasi)"),
        ("Dataset SHA-256:", "baa22175... (48 baris kartesian)"),
    ]
    for k, v in params:
        p = ml_tf.add_paragraph()
        p.text = f"• {k} {v}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = C_TEXT_DARK
        p.space_before = Pt(3)

    # Right: Policy Guardrails & Formula
    pol_card = add_card(s6, Inches(6.8), Inches(1.7), Inches(5.73), Inches(5.3))
    pol_tf = pol_card.text_frame
    pol_tf.word_wrap = True

    pol_p = pol_tf.paragraphs[0]
    pol_p.text = "🛡️ Integrasi Kebijakan Wajib (Policy Guardrails)"
    pol_p.font.size = Pt(13)
    pol_p.font.bold = True
    pol_p.font.color.rgb = RGBColor(190, 24, 93)

    pol_rule = pol_tf.add_paragraph()
    pol_rule.text = "Keputusan Akhir D(x, c):\n1. HUMAN jika policy wajib aktif pada konteks c.\n2. HUMAN jika P(H = 1 | x) ≥ τ = 0,80.\n3. AGENT dalam batas izin otonom."
    pol_rule.font.size = Pt(10)
    pol_rule.font.color.rgb = C_NAVY_DARK
    pol_rule.space_before = Pt(4)

    guards = [
        ("Emergency:", "Kasus darurat langsung eskalasi dengan prioritas URGENT."),
        ("Financial Dispute:", "Perubahan saldo sepihak diblokir; diteruskan ke staf."),
        ("Upgrade Exception:", "Kamar lebih tinggi tidak boleh diberikan otomatis."),
        ("Consent Wajib:", "Mutasi kamar ditolak tanpa persetujuan eksplisit tamu."),
        ("Eligibility Formula:", "ready(r) = clean(r) ∧ ¬blocked(r)\neligible(r) = vacant(r) ∧ ready(r) ∧ sameType(r) ∧ noExtraFee(r)"),
    ]
    for g_t, g_d in guards:
        p = pol_tf.add_paragraph()
        p.text = f"• {g_t} {g_d}"
        p.font.size = Pt(9)
        p.font.color.rgb = C_TEXT_DARK
        p.space_before = Pt(4)

    # =========================================================================
    # SLIDE 7: VALIDASI 6 SKENARIO PENGUJIAN AKTUAL
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    create_slide_header(s7, "Validasi Eksekusi Aktual 6 Skenario Pengujian (S01 – S06)")

    s7_table_shape = s7.shapes.add_table(7, 3, Inches(0.8), Inches(1.7), Inches(11.73), Inches(5.3))
    t7 = s7_table_shape.table
    t7.columns[0].width = Inches(1.0)
    t7.columns[1].width = Inches(3.2)
    t7.columns[2].width = Inches(7.53)

    t7_headers = ["ID", "Skenario Kasus", "Hasil Eksekusi Aktual Sistem"]
    for j, h in enumerate(t7_headers):
        cell = t7.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_NAVY_DARK
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_WHITE

    scenarios = [
        ("S01", "AC Rusak, Kamar Tersedia\n(Standard)", "Tiket dibuat di OPS; MA-001 bermigrasi; R102 ditolak (kotor); R103 divalidasi layak. Tamu memberi consent; mutasi atomik R101 → R103 tarif tetap Rp500.000. Status: DIGITAL_COMPLETED."),
        ("S02", "Kamar Setara Habis\n(Perlu Upgrade)", "MA-001 bermigrasi mengumpulkan bukti kamar R201 (Deluxe, selisih Rp250.000). Policy upgrade aktif: otomatisasi diblokir, kasus dialihkan ke staf manusia. Status: WAITING_HUMAN."),
        ("S03", "Sengketa Minibar\n(Financial Dispute)", "Folio RES001 diambil dari FO (Rp650.000). Policy financial dispute memblokir perubahan saldo sepihak. Kasus dieskalasi ke staf keuangan; saldo tidak berubah; tanpa migrasi. Status: WAITING_HUMAN."),
        ("S04", "FAQ Jam Check-in\n(Layanan Concierge)", "Concierge Agent menjawab langsung waktu check-in (14.00 WIB) dari knowledge base lokal Front Office. Selesai instan tanpa tiket dan tanpa migrasi. Status: CLOSED."),
        ("S05", "Permintaan Handuk\n(Housekeeping)", "Tiket housekeeping dibuat di OPS (PENDING). Staf dapat mengupdate status menjadi IN_PROGRESS dan DONE secara independen tanpa memicu eskalasi keliru. Status: DIGITAL_COMPLETED."),
        ("S06", "Rincian Tagihan\n(Billing Inquiry)", "Billing Agent menampilkan rincian folio (kamar Rp500.000 + minibar Rp150.000) secara transparan tanpa mutasi saldo dan tanpa migrasi agen. Status: CLOSED."),
    ]

    for i, row in enumerate(scenarios):
        for j, val in enumerate(row):
            cell = t7.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(248, 250, 252) if i % 2 == 0 else C_WHITE
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(9.5)
            p.font.color.rgb = C_TEXT_DARK

    # =========================================================================
    # SLIDE 8: ANTARMUKA 3-STAKEHOLDER & UX
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    create_slide_header(s8, "Antarmuka Terpadu: Desain UX Ramah 3 Pemangku Kepentingan")

    panels = [
        (
            "👤 1. Portal Tamu Mandiri",
            "• Tampilan mobile-friendly untuk tamu hotel.\n• Melihat status penanganan keluhan secara real-time.\n• Menerima proposal kamar pengganti layak (R103).\n• Tombol persetujuan 1-klik (Setujui Pindah) yang mengeksekusi penyelesaian otomatis secara instan.",
            C_BLUE,
        ),
        (
            "👔 2. Portal Staf Operasional",
            "• Ruang kerja khusus staf & manajer hotel.\n• Tombol Ambil Alih Kasus (Take Over) saat eskalasi.\n• Form wajib catatan penyelesaian SOP sebelum kasus ditutup.\n• Manajemen tiket pemeliharaan fisik (PENDING → IN_PROGRESS → DONE).",
            C_SUCCESS,
        ),
        (
            "📊 3. Dasbor Eksekutif & Teknis",
            "• Ringkasan metrik ROI & proteksi pendapatan.\n• Stepper visual 6-fase alur penanganan komplain.\n• Universal Action Bar dan kontrol Auto-Play simulation.\n• Tab Jejak & State: Timeline migrasi state dan audit log terurut yang dapat diekspor ke JSON.",
            C_TEAL,
        ),
    ]

    for i, (title, text, color) in enumerate(panels):
        c = add_card(s8, Inches(0.8 + i * 4.0), Inches(1.7), Inches(3.73), Inches(5.3))
        tf = c.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(14)
        p_t.font.bold = True
        p_t.font.color.rgb = color

        p_d = tf.add_paragraph()
        p_d.text = f"\n{text}"
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = C_TEXT_DARK
        p_d.space_before = Pt(8)

    # =========================================================================
    # SLIDE 9: HASIL EKSPERIMEN BENCHMARK AKTUAL (30 REPETISI)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    create_slide_header(s9, "Hasil Eksperimen Benchmark Aktual (30 Iterasi Berpasangan)")

    # Table 15 from report
    bench_table_shape = s9.shapes.add_table(11, 5, Inches(0.8), Inches(1.6), Inches(11.73), Inches(4.3))
    tb = bench_table_shape.table
    tb.columns[0].width = Inches(2.73)
    tb.columns[1].width = Inches(2.25)
    tb.columns[2].width = Inches(2.25)
    tb.columns[3].width = Inches(2.25)
    tb.columns[4].width = Inches(2.25)

    tb_headers = ["Metrik Pengukuran", "S01 Static", "S01 Mobile", "S02 Static", "S02 Mobile"]
    for j, h in enumerate(tb_headers):
        cell = tb.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_NAVY_DARK
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = C_WHITE

    bench_data = [
        ("Hasil Bisnis Aktual", "Selesai, R103, 1 tiket", "Selesai, R103, 1 tiket", "Eskalasi staf, R101", "Eskalasi staf, R101"),
        ("Ekivalensi Keputusan", "Identik 100%", "Identik 100%", "Identik 100%", "Identik 100%"),
        ("Waktu Median (ms)", "21,38 ms", "27,87 ms", "11,17 ms", "13,46 ms"),
        ("Waktu P95 (ms)", "22,33 ms", "28,35 ms", "11,51 ms", "14,02 ms"),
        ("Pesan Antar-Node", "6 pesan", "5 pesan (-16,7%)", "4 pesan", "3 pesan (-25,0%)"),
        ("Total Payload (byte)", "2.793 byte", "2.820 byte (+0,96%)", "1.861 byte", "1.888 byte (+1,45%)"),
        ("Ukuran Checkpoint", "0 byte", "553 byte", "0 byte", "470 byte"),
        ("Jumlah Langkah Engine", "14 step", "16 step (+2 step)", "9 step", "11 step (+2 step)"),
        ("CPU Time (ms)", "15,62 ms", "31,25 ms", "15,62 ms", "15,62 ms"),
        ("Peak Memory Allocation", "104,87 KB", "109,52 KB", "72,50 KB", "76,97 KB"),
    ]

    for i, row in enumerate(bench_data):
        for j, val in enumerate(row):
            cell = tb.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(248, 250, 252) if i % 2 == 0 else C_WHITE
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(9)
            if "(-" in val:
                p.font.bold = True
                p.font.color.rgb = C_SUCCESS
            else:
                p.font.color.rgb = C_TEXT_DARK

    # Bottom analysis note
    nt_card = add_card(s9, Inches(0.8), Inches(6.05), Inches(11.73), Inches(1.1), bg_color=RGBColor(240, 253, 244), border_color=RGBColor(187, 247, 208))
    nt_tf = nt_card.text_frame
    nt_tf.word_wrap = True
    nt_p = nt_tf.paragraphs[0]
    nt_p.text = "💡 Temuan Utama Evaluasi Empiris:"
    nt_p.font.size = Pt(11)
    nt_p.font.bold = True
    nt_p.font.color.rgb = C_SUCCESS

    nt_p2 = nt_tf.add_paragraph()
    nt_p2.text = "1. Mobile Agent terbukti memangkas jumlah transaksi pesan antar-node sebesar 16,7% (S01) dan 25,0% (S02).\n2. Overhead payload checkpoint sangat kecil (+27 byte kanonikal), sehingga keuntungan latensi pada jaringan riil akan sangat signifikan."
    nt_p2.font.size = Pt(9.5)
    nt_p2.font.color.rgb = C_NAVY_DARK

    # =========================================================================
    # SLIDE 10: EVALUASI ML & KONTROL SISTEM
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    create_slide_header(s10, "Evaluasi Kinerja Model ML & Keamanan Kontrol Sistem")

    # Left: ML Metrics Table
    m_left = add_card(s10, Inches(0.8), Inches(1.7), Inches(5.7), Inches(5.3))
    m_tf = m_left.text_frame
    m_tf.word_wrap = True

    p_mhead = m_tf.paragraphs[0]
    p_mhead.text = "📊 Metrik Performa Regresi Logistik (Held-out Test)"
    p_mhead.font.size = Pt(13)
    p_mhead.font.bold = True
    p_mhead.font.color.rgb = C_BLUE

    ml_metrics = [
        ("Accuracy", "91,67%", "11 dari 12 sampel uji dievaluasi benar pada τ = 0,80."),
        ("Precision", "100,00%", "Zero False Positive: Tidak ada eskalasi keliru."),
        ("Recall", "83,33%", "5 dari 6 kebutuhan eskalasi positif terdeteksi."),
        ("F1-Score", "0,9091", "Keseimbangan harmonik optimal."),
        ("Confusion Matrix", "[[6, 0], [1, 5]]", "TN=6, FP=0, FN=1 (Row E041), TP=5."),
    ]

    for m_name, m_val, m_desc in ml_metrics:
        p = m_tf.add_paragraph()
        p.text = f"• {m_name}: {m_val} — {m_desc}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = C_TEXT_DARK
        p.space_before = Pt(6)

    # Right: Security & Reliability Table
    s_right = add_card(s10, Inches(6.8), Inches(1.7), Inches(5.73), Inches(5.3))
    s_tf = s_right.text_frame
    s_tf.word_wrap = True

    p_shead = s_tf.paragraphs[0]
    p_shead.text = "🛡️ Keamanan Sistem & Keandalan Transaksi"
    p_shead.font.size = Pt(13)
    p_shead.font.bold = True
    p_shead.font.color.rgb = C_SUCCESS

    ctrl_metrics = [
        ("Percobaan Terlarang Ditolak", "14 / 14 (100%)", "Mutasi tanpa consent, kamar kotor, atau akses ilegal ditolak mutlak."),
        ("Invariant Migrasi Lulus", "14 / 14 (100%)", "N_active(a) ∈ {0,1} dan nol owner saat transit ditaati setiap step."),
        ("Duplicate Side Effects", "0 (Nol)", "Idempotency key mencegah tiket ganda dan mutasi kamar ganda."),
        ("Recovery Kasus Kegagalan", "100% Berhasil", "Checkpoint korup atau server crash di-rollback ke node asal."),
        ("Automated Test Suite", "70 / 70 Passed", "100% lulus dalam 3,53 detik pada framework pytest."),
    ]

    for c_name, c_val, c_desc in ctrl_metrics:
        p = s_tf.add_paragraph()
        p.text = f"• {c_name}: {c_val}\n  {c_desc}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = C_TEXT_DARK
        p.space_before = Pt(6)

    # =========================================================================
    # SLIDE 11: KESIMPULAN & NILAI TAMBAH
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    create_slide_header(s11, "Kesimpulan & Nilai Tambah bagi Operasional Hotel")

    conclusions = [
        (
            "1. Pembuktian Kelayakan Mobile Agent",
            "Simulasi migrasi state membuktikan bahwa agen dapat berpindah antar node logis secara aman, mempertahankan kontinuitas identitas dan progress tanpa duplikasi instance aktif (N_active ≤ 1).",
            C_BLUE,
        ),
        (
            "2. Efisiensi Komunikasi Terukur",
            "Mobile Agent terbukti mereduksi pesan koordinasi antar-node sebesar 16,7% hingga 25,0% dibandingkan agen statis, dengan trade-off penambahan payload checkpoint kanonikal yang sangat kecil (+27 byte).",
            C_TEAL,
        ),
        (
            "3. Eliminasi Risiko 'Double Complaint'",
            "Verifikasi fisik lokal di node Operations berhasil memastikan kamar kotor (R102) langsung dieliminasi sebelum diajukan ke tamu, mencegah komplain berulang dan ulasan buruk.",
            C_SUCCESS,
        ),
        (
            "4. Proteksi Finansial & Kepatuhan SOP",
            "Pemisahan probabilitas ML dan aturan kebijakan wajib (Policy Guardrails) menjamin tidak ada kebocoran biaya atau upgrade liar tanpa otorisasi manajerial manusia.",
            C_WARNING,
        ),
    ]

    for i, (title, text, color) in enumerate(conclusions):
        col = i % 2
        row = i // 2
        c = add_card(s11, Inches(0.8 + col * 6.0), Inches(1.7 + row * 2.7), Inches(5.73), Inches(2.4))
        tf = c.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = color

        p_d = tf.add_paragraph()
        p_d.text = f"\n{text}"
        p_d.font.size = Pt(10.5)
        p_d.font.color.rgb = C_TEXT_DARK

    # =========================================================================
    # SLIDE 12: REKOMENDASI MASA DEPAN & PENUTUP
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    bg12 = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg12.fill.solid()
    bg12.fill.fore_color.rgb = C_NAVY_DARK
    bg12.line.fill.background()

    # Header on dark
    title_box = s12.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(11.33), Inches(1.0))
    tf12 = title_box.text_frame
    tf12.word_wrap = True
    p12 = tf12.paragraphs[0]
    p12.text = "Rekomendasi Pengembangan & Penutup"
    p12.font.size = Pt(28)
    p12.font.bold = True
    p12.font.color.rgb = C_WHITE

    # 3 Recommendation cards on dark
    recs = [
        ("1. Multi-Host Deployment", "Memisahkan node logis ke container Docker/host terdistribusi nyata (gRPC / HTTP REST) untuk mengukur latensi jaringan dan wire-traffic sebenarnya."),
        ("2. Natural Language Processing", "Mengintegrasikan model transformer lokal ringan (misal MiniLM Multilingual) untuk memahami pesan chat teks bebas dari tamu hotel berbahasa Indonesia."),
        ("3. Adaptive Continual Learning", "Merekam aksi koreksi atau persetujuan staf ke basis data audit untuk pelatihan ulang model ML offline secara berkala."),
    ]

    for i, (r_t, r_d) in enumerate(recs):
        c = add_card(s12, Inches(1.0 + i * 3.85), Inches(2.0), Inches(3.6), Inches(2.6), bg_color=C_NAVY_LIGHT, border_color=RGBColor(51, 65, 85))
        tf = c.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = r_t
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = RGBColor(56, 189, 248)

        p_desc = tf.add_paragraph()
        p_desc.text = f"\n{r_d}"
        p_desc.font.size = Pt(10)
        p_desc.font.color.rgb = RGBColor(226, 232, 240)

    # Repository & Q&A Box
    end_card = add_card(s12, Inches(1.0), Inches(4.9), Inches(11.33), Inches(1.8), bg_color=C_NAVY_LIGHT, border_color=RGBColor(51, 65, 85))
    end_tf = end_card.text_frame
    end_tf.word_wrap = True

    ep1 = end_tf.paragraphs[0]
    ep1.text = "🌐 Repositori Kode Sumber Publik:"
    ep1.font.size = Pt(13)
    ep1.font.bold = True
    ep1.font.color.rgb = C_TEAL

    ep2 = end_tf.add_paragraph()
    ep2.text = "https://github.com/allail-qadrillah/ACE-Intelliegent-Mobile-Agent-System"
    ep2.font.size = Pt(12)
    ep2.font.bold = True
    ep2.font.color.rgb = C_WHITE
    ep2.space_before = Pt(4)

    ep3 = end_tf.add_paragraph()
    ep3.text = "Terima Kasih • Sesi Tanya Jawab (Q&A)\nKelompok 5 — Magister Kecerdasan Artifisial UGM 2026"
    ep3.font.size = Pt(12)
    ep3.font.color.rgb = RGBColor(203, 213, 225)
    ep3.space_before = Pt(8)

    # Save to targets
    prs.save(str(TARGET_PPTX))
    prs.save(str(DOWNLOADS_PPTX))
    print(f"Presentation saved successfully to:\n- {TARGET_PPTX}\n- {DOWNLOADS_PPTX}")


if __name__ == "__main__":
    build_presentation()
