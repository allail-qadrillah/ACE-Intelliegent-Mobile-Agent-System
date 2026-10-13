import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, 810, "Panduan Presentasi: ACE — Intelligent Mobile Agent System")
            self.drawRightString(555, 810, "Kelompok 5 — Agent Enterprise")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(40, 802, 555, 802)

        # Footer
        footer_text = f"Halaman {self._pageNumber} dari {page_count}"
        self.drawRightString(555, 25, footer_text)
        self.drawString(40, 25, "Confidential - Untuk Kebutuhan Presentasi Akademik")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(40, 35, 555, 35)
        
        self.restoreState()

def build_pdf(filename="Panduan_Presentasi_ACE_Mobile_Agent.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15
    )
    
    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.HexColor("#0284c7")
    )
    
    slide_header_style = ParagraphStyle(
        'SlideHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=0,
        spaceAfter=4
    )
    
    key_takeaway_style = ParagraphStyle(
        'KeyTakeaway',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )
    
    script_label_style = ParagraphStyle(
        'ScriptLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0369a1")
    )
    
    script_text_style = ParagraphStyle(
        'ScriptText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#1e293b")
    )
    
    tip_text_style = ParagraphStyle(
        'TipText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#92400e")
    )

    story = []
    
    # Title Section
    story.append(Paragraph("PANDUAN & SKRIP PRESENTASI SLIDE-BY-SLIDE", title_style))
    story.append(Paragraph("<b>Sistem:</b> ACE — Intelligent Mobile Agent System (Multi-Agent Customer Service Hotel)<br/><b>Mata Kuliah:</b> Agent Enterprise &bull; <b>Tim:</b> Kelompok 5", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=15))

    slides_data = [
        {
            "slide_num": "SLIDE 1",
            "title": "Cover & Tim Pengembang",
            "takeaway": "Membuka presentasi dengan percaya diri, memperkenalkan identitas proyek dan pembagian peran tim secara profesional.",
            "script": "<i>\"Selamat pagi/siang Bapak/Ibu Dosen dan rekan-rekan sekalian. Kami dari Kelompok 5 pada mata kuliah Agent Enterprise ingin mempresentasikan proyek rancang bangun kami yang berjudul <b>ACE — Intelligent Mobile Agent System: Multi-Agent Customer Service Hotel</b>.<br/><br/>"
                      "Proyek ini dikembangkan oleh tim kami: M. Al lail Qadrillah selaku Arsitek Sistem & Lead Developer, Dimas Prabowo yang mengkaji literatur dan produk pembanding, Monanta Alfiareza sebagai perancang spesialisasi agen, serta Frans Alwan pada integrasi dan pengujian sistem.<br/><br/>"
                      "Mari kita mulai dengan meninjau masalah operasional riil yang menjadi latar belakang perancangan sistem ini.\"</i>",
            "tips": "<b>Tips Pengantar:</b> Jaga tempo bicara tetap tenang dan tegas. Tegaskan bahwa proyek ini berfokus pada penerapan arsitektur Mobile Agent di domain enterprise hospitality."
        },
        {
            "slide_num": "SLIDE 2",
            "title": "Masalah Operasional yang Ingin Diselesaikan",
            "takeaway": "Menunjukkan tiga 'pain points' krusial hotel yang gagal diatasi oleh sistem chatbot konvensional (Silo data antar departemen, status fiktif/tidak sinkron, dan risiko kompensasi tanpa batasan).",
            "script": "<i>\"Dalam operasional hotel modern, terdapat tiga bottleneck utama yang kerap memicu inefisiensi dan ketidakpuasan tamu:<br/><br/>"
                      "<b>1. Koordinasi Antar-Departemen yang Lambat:</b> Front Office dan Operations memiliki sistem data terpisah. Verifikasi keluhan sering kali harus lewat telepon manual antar-staf. Dampaknya, telepon resepsionis overload dan tamu dibiarkan menunggu lama.<br/>"
                      "<b>2. Readiness Kamar Tidak Terverifikasi:</b> Status kamar di sistem FO sering tercatat 'Available', padahal kondisi fisik riilnya masih kotor atau AC-nya rusak. Hal ini memicu keluhan berulang (double complaint) dan ulasan buruk bintang 1 di platform OTA.<br/>"
                      "<b>3. Kebijakan Bisnis yang Kerap Dilanggar:</b> Staf sering memberikan kompensasi atau upgrade kamar tanpa batasan otorisasi yang ketat. Akibatnya, SOP dilanggar dan margin profit hotel tergerus.<br/><br/>"
                      "Sistem ACE hadir untuk menyelesaikan ketiga masalah ini secara otomatis, terintegrasi, dan terukur.\"</i>",
            "tips": "<b>Antisipasi Dosen:</b> Tekankan bahwa 'Double Complaint' adalah masalah bisnis paling fatal di hotel, dan sistem ini dirancang spesifik untuk mencegah kamar bermasalah dipindahtangankan ke tamu lain."
        },
        {
            "slide_num": "SLIDE 3",
            "title": "State of the Art: Produk & Solusi Relevan",
            "takeaway": "Memvalidasi riset terhadap solusi komersial terkemuka (HiJiffy, Asksuite, Canary, Quinta) dan mempertegas 'Novelty' atau kebaruan ACE dalam paradigma Mobile Agent & State Migration.",
            "script": "<i>\"Kami melakukan analisis benchmarking terhadap produk hospitality AI terkemuka industri:<br/><br/>"
                      "&bull; <b>HiJiffy & Canary:</b> Sangat kuat di sisi omnichannel messaging dan ticketing, namun komunikasinya bersifat client-server API biasa.<br/>"
                      "&bull; <b>Asksuite & Quinta:</b> Memiliki spesialisasi agen dan integrasi PMS yang rapi hingga ke eksekusi housekeeping.<br/><br/>"
                      "<b>Batas Perbandingan & Posisi ACE:</b> Seluruh solusi di pasar saat ini mengadopsi arsitektur <i>Static Agent</i> sentralistik. Belum ada yang mendokumentasikan kapabilitas <b>Mobile Agent dengan migrasi state di level aplikasi</b>.<br/>"
                      "Di sinilah kebaruan ilmiah ACE: Kami mengimplementasikan agen yang dapat berpindah secara fisik/logis ke sumber data lokal operasional, membawa state-nya sendiri, memverifikasi kesiapan secara lokal, dan mengeliminasi ketergantungan transfer data mentah lintas node.\"</i>",
            "tips": "<b>Pertanyaan Kunci Dosen:</b> <i>'Kenapa tidak pakai REST API query biasa saja?'</i><br/>"
                    "<b>Jawaban Mantap:</b> REST API memerlukan transfer kumpulan baris data mentah ke FO. Dengan Mobile Agent, logika evaluasi dieksekusi langsung di node lokal target, sehingga hanya hasil kesimpulan yang dikembalikan, menghemat bandwidth, menjaga isolasi database, dan mendukung operasi terputus (disconnected execution)."
        },
        {
            "slide_num": "SLIDE 4",
            "title": "Alur Penanganan Kasus: Observe -> Decide -> Migrate -> Verify -> Act -> Commit",
            "takeaway": "Menjabarkan alur kerja langkah-demi-langkah dari keluhan tamu masuk sampai masalah selesai secara deterministik.",
            "script": "<i>\"Berikut alur penanganan insiden yang dijalankan sistem ACE melalui 6 fase terstruktur:<br/><br/>"
                      "<b>1. Observe:</b> Tamu mengirim keluhan via pesan. Scenario Scout mengekstrak informasi dan membuat tiket resmi.<br/>"
                      "<b>2. Decide:</b> Orchestrator mengevaluasi tiket menggunakan model Machine Learning dan Policy Guardrail untuk menentukan jalur mitigasi.<br/>"
                      "<b>3. Migrate:</b> Mobile Investigator dikemas bersama state kasusnya, lalu bermigrasi dari Node Front Office menuju Node Operations.<br/>"
                      "<b>4. Verify:</b> Di node Operations, agen menginspeksi kesiapan fisik kamar secara lokal. Kamar R102 yang masih kotor otomatis dieliminasi; kamar R103 yang bersih dan siap huni dipilih.<br/>"
                      "<b>5. Act:</b> Rekomendasi kamar R103 dikirimkan ke HP tamu untuk konfirmasi, atau dieskalasi ke manajer jika melampaui limit wewenang.<br/>"
                      "<b>6. Commit:</b> Setelah disetujui, reservasi diperbarui secara atomik dan idempoten di Front Office tanpa komplain berulang.\"</i>",
            "tips": "<b>Tips:</b> Gunakan gestur tangan atau pointer mengalir dari poin 1 sampai 6 untuk menunjukkan kesinambungan proses state machine."
        },
        {
            "slide_num": "SLIDE 5 & 6",
            "title": "Arsitektur Sistem: Multi-Agent dengan Migrasi State Mobile Agent",
            "takeaway": "Menerangkan diagram arsitektur utuh: 2 logical node terisolasi, peran masing-masing specialist agent, model ML triase, checkpoint SHA-256, dan determinisme sistem.",
            "script": "<i>\"Mari kita cermati diagram arsitektur teknis sistem ACE pada slide ini.<br/><br/>"
                      "Sistem kami dirancang dengan <b>Dua Logical Node yang Terisolasi</b>: Node FRONT_OFFICE dan Node OPERATIONS. Masing-masing memiliki database SQLite mandiri—sama sekali tidak ada SQL JOIN lintas node guna menjamin desentralisasi.<br/><br/>"
                      "<b>Spesialisasi Agen:</b><br/>"
                      "&bull; Di Front Office ada <b>Scenario Scout</b> (inbox reader), <b>Orchestrator</b> (dirigen alur), <b>Reservation Agent</b> (katalog kamar), <b>Billing Agent</b> (read-only tagihan), dan <b>Concierge Agent</b> (FAQ).<br/>"
                      "&bull; Pengambilan keputusan dipandu oleh <b>Model ML (Logistic Regression)</b> untuk triase probabilitas eskalasi manusia, dipagari oleh <b>Policy Guardrail</b> ketat (keputusan finansial/refund selalu wajib human-in-the-loop).<br/><br/>"
                      "<b>Protokol Migrasi Mobile Agent:</b><br/>"
                      "Ketika dibutuhkan verifikasi fisik, <b>Mobile Investigator (MA-001)</b> mengemas state-nya ke JSON checkpoint yang divalidasi dengan checksum <b>SHA-256</b>. Agen melalui siklus <code>PREPARE &rarr; DEPART &rarr; ARRIVE</code> menuju Node Operations.<br/>"
                      "Di sana ia memeriksa tabel kesiapan fisik secara lokal dan hanya mengirimkan hasil validasi ke Front Office.<br/><br/>"
                      "<b>Penting:</b> Sistem ini berjalan 100% <i>deterministic rule-based state machine</i> tanpa risiko halusinasi LLM liar, menjamin keandalan transaksi enterprise.\"</i>",
            "tips": "<b>Poin Nilai Plus:</b> Sebutkan istilah 'Checksum SHA-256' dan 'Idempotent Commit'. Ini membuktikan implementasi teknis kelompok sangat mendalam dan memperhatikan aspek keamanan data terdistribusi."
        },
        {
            "slide_num": "SLIDE 7",
            "title": "Project Demonstration (Live Streamlit Demo)",
            "takeaway": "Transisi mulus dari pemaparan arsitektur ke pembuktian nyata pada antarmuka aplikasi Streamlit.",
            "script": "<i>\"Untuk membuktikan bahwa seluruh arsitektur dan siklus migrasi ini berjalan nyata, kami akan memperlihatkan Project Demonstration secara langsung pada aplikasi Streamlit yang telah kami kembangkan.<br/><br/>"
                      "Dalam demonstrasi ini kita akan melihat:<br/>"
                      "1. Simulasi tamu yang mengajukan keluhan AC rusak di kamar R103.<br/>"
                      "2. Bagaimana model ML melakukan triase risiko dan memicu penanganan otomatis.<br/>"
                      "3. Log inspeksi real-time saat Mobile Investigator bermigrasi dari FO ke Operations.<br/>"
                      "4. Eliminasi kamar kotor dan pemilihan kamar pengganti yang valid.<br/>"
                      "5. Halaman audit trail dan log checkpoint SHA-256 di tab 'Jejak & State'.<br/><br/>"
                      "[Beralih ke layar demo / jalankan simulasi Streamlit]\"</i>",
            "tips": "<b>Saat Live Demo:</b> Pastikan tab Streamlit sudah dibuka terlebih dahulu sebelum presentasi dimulai. Klik skenario secara perlahan sambil menerangkan log yang bergerak di layar."
        },
        {
            "slide_num": "SLIDE 8",
            "title": "Kesimpulan",
            "takeaway": "Merangkum 4 pencapaian kunci: pembuktian paradigma mobile agent, eliminasi double complaint, proteksi pendapatan dengan policy guardrail, dan antarmuka multi-stakeholder.",
            "script": "<i>\"Sebagai kesimpulan, proyek ACE berhasil membuktikan 4 pencapaian fundamental:<br/><br/>"
                      "<b>1. Kelayakan Paradigma Mobile Agent:</b> Kami berhasil membuktikan bahwa Mobile Agent sangat efektif untuk menyelesaikan kasus operasional terdistribusi di hotel.<br/>"
                      "<b>2. Mencegah 'Double Complaint':</b> Verifikasi lokal kamar memastikan tamu tidak akan pernah dipindahkan ke kamar yang masih kotor atau bermasalah.<br/>"
                      "<b>3. Perlindungan Pendapatan Hotel:</b> Penerapan Policy Guardrail dan Human-in-the-loop menjamin kompensasi finansial tidak bocor sembarangan.<br/>"
                      "<b>4. Transparansi Multi-Stakeholder:</b> Menyediakan dashboard terintegrasi yang mudah digunakan oleh Tamu, Staf Operasional, dan Manajemen IT untuk memantau jejak audit.\"</i>",
            "tips": "<b>Tips Penutup:</b> Jangan membaca poin kesimpulan kata-per-kata. Bacakan intinya dengan nada mantap sebagai solusi tuntas."
        },
        {
            "slide_num": "SLIDE 9",
            "title": "Referensi Utama & Sesi Tanya Jawab",
            "takeaway": "Menutup presentasi dengan kredibilitas literatur yang kuat dan membuka sesi Q&A secara percaya diri.",
            "script": "<i>\"Perancangan sistem ini didasarkan pada riset produk komersial terkemuka (HiJiffy, Asksuite, Canary, Quinta) serta diperkuat oleh literatur jurnal Q1 di bidang Agentic AI, Multi-Agent Systems, dan Mobile Agent Distributed Systems.<br/><br/>"
                      "Demikian presentasi dari Kelompok 5. Kami sangat berterima kasih atas perhatian Bapak/Ibu Dosen dan rekan-rekan. Kami siap menyambut pertanyaan, masukan, dan diskusi lebih lanjut. Terima kasih!\"</i>",
            "tips": "<b>Sikap Q&A:</b> Apabila ada pertanyaan yang dibagi antar anggota tim, silakan oper dengan sopan: <i>'Untuk aspek detail implementasi migrasi/ML, izin rekan saya Frans/Monanta/Dimas untuk menambahkan...'</i>."
        }
    ]

    for item in slides_data:
        # Construct Card Table for each slide
        card_content = []
        
        # Header Table: Badge and Title
        header_data = [
            [
                Paragraph(f"<b>{item['slide_num']}</b>", badge_style),
                Paragraph(item['title'], slide_header_style)
            ]
        ]
        t_header = Table(header_data, colWidths=[65, 435])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        card_content.append(t_header)
        
        # Key Takeaway Box
        takeaway_data = [[
            Paragraph(f"<b>Inti Pesan:</b> {item['takeaway']}", key_takeaway_style)
        ]]
        t_takeaway = Table(takeaway_data, colWidths=[500])
        t_takeaway.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        card_content.append(t_takeaway)
        card_content.append(Spacer(1, 6))
        
        # Script Box
        script_data = [
            [Paragraph("SKRIP BICARA (TALKING POINTS):", script_label_style)],
            [Paragraph(item['script'], script_text_style)]
        ]
        t_script = Table(script_data, colWidths=[500])
        t_script.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#86efac")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        card_content.append(t_script)
        card_content.append(Spacer(1, 6))
        
        # Tips / Q&A Box
        tips_data = [[
            Paragraph(item['tips'], tip_text_style)
        ]]
        t_tips = Table(tips_data, colWidths=[500])
        t_tips.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#fde68a")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        card_content.append(t_tips)
        card_content.append(Spacer(1, 14))
        
        story.append(KeepTogether(card_content))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully built: {filename}")

if __name__ == "__main__":
    build_pdf()
