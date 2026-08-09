"""
Pipeline auto-generate produk digital Gumroad (100% otomatis, DUAL VERSION: EN + ID).
  - Tiap topik menghasilkan 2 produk: versi English (global) + versi Indonesia.
  - Prompt memaksa gaya storytelling + kaidah digital marketing + bahasa natural (tidak robotik).
  - PDF dibuat ber-CCD estetik (fpdf2: warna, bullet, header berwarna, footer).
  - Cover dibuat premium (gradient + dekoratif) via ffmpeg.

Cara pakai: python gemini_gumroad.py
"""
import json, os, re, subprocess, sys, time, glob

BASE = r"C:\Users\ASUS\projects\tanamanrumah\youtube"
TOOLS = os.path.join(BASE, "tools")
SCRIPTS = os.path.join(BASE, "scripts")
PRODUCTS_DIR = os.path.join(BASE, "gumroad_products")
STATE_FILE = os.path.join(SCRIPTS, "state_gumroad.json")
LOG_FILE = os.path.join(BASE, "gumroad_status.txt")

# Topik produk: tiap entry punya versi EN & ID (bahasa natural + storytelling + marketing)
QUEUE = [
    {
        "topik_en": "Plant Care Cheat Sheet for 30 Common Houseplants (actionable, practical)",
        "nama_en": "Houseplant Care Cheat Sheet: 30 Plants, Zero Guesswork",
        "topik_id": "Lembar Kerja Mudah Merawat 30 Tanaman Rumah (praktis, siap pakai)",
        "nama_id": "Tabel Usus Tanaman Rumah: 30 Tanaman Tanpa Hanya Tebak",
        "harga_cents": 300,
        "github": ["EN", "ID"],
    },
    {
        "topik_en": "The 7-Day Plant Revival Plan: Save A Dying Plant (story-driven, actionable)",
        "nama_en": "Revive Your Dying Plant in 7 Days (Step-by-Step Plan)",
        "topik_id": "Rancangan 7 Hari Selamatkan Tanaman Sekarat (bercerita, langkah demi langkah)",
        "nama_id": "Selamatkan Tanaman Sekarat dalam 7 Hari (Panduan Langkah)",
        "harga_cents": 400,
        "github": ["EN", "ID"],
    },
]

# Palette untuk cover & PDF (agar tidak monoton, beda warna per produk)
COLORS = [
    {"bg": "225539", "accent": "8fd694", "title": "FFFFFF"},   # hijau daun
    {"bg": "274060", "accent": "6fb1fc", "title": "FFFFFF"},   # biru
    {"bg": "5b2a4a", "accent": "e89ab8", "title": "FFFFFF"},   # berry
    {"bg": "4a3b12", "accent": "e7cf6f", "title": "FFFFFF"},   # emas
]

def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M')}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"queue": QUEUE, "done": [], "color_idx": 0}

def save_state(st):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50]

def ask_omni(prompt, out_txt, force=False):
    if not force and os.path.exists(out_txt) and os.path.getsize(out_txt) > 300:
        log(f"Omni: reuse file ({os.path.getsize(out_txt)} chars)")
        return True
    r = subprocess.run(["python", os.path.join(TOOLS, "gemini_chat.py"), prompt, out_txt],
                       capture_output=True, text=True, timeout=420)
    ok = os.path.exists(out_txt) and os.path.getsize(out_txt) > 300
    log(f"Omni: {'OK' if ok else 'GAGAL'} ({os.path.getsize(out_txt) if os.path.exists(out_txt) else 0} chars)")
    return ok

# ── Template prompt storytelling + digital marketing (per JENIS produk) ──
PRODUCT_TYPES = {
    "tutorial": ("Step-by-Step Tutorial", "give a clear step-by-step tutorial with ordered steps, real examples, and results"),
    "hack": ("Speed Hacks & Tips", "share powerful hacks, quick wins, and actionable tips that save time or money"),
    "prompt_pack": ("AI Prompt Pack", "curate a valuable collection of ready-to-use AI prompts with use-cases and expected output"),
    "kit": ("Templates & Kit", "provide ready-made templates/checklists/scripts the reader can copy and use immediately"),
    "cheat_sheet": ("Quick Cheat Sheet", "give a concise visual reference sheet covering the essentials at a glance"),
}

def make_prompt(lang, topik, nama, jenis="tutorial"):
    j = PRODUCT_TYPES.get(jenis, PRODUCT_TYPES['tutorial'])
    if lang == "EN":
        return (
            f"Write a complete, premium digital product ({j[0]}) in English titled: {nama}. "
            f"Topic: {topik}.\n\n"
            f"FORMAT & CONTENT: {j[1]}. 10-14 sections, each 2-3 short natural paragraphs.\n\n"
            f"STYLE RULES:\n"
            f"- Naturally conversational English like a helpful friend, NOT robotic or marketing-sleazy.\n"
            f"- Storytelling: open with a relatable hook/pain, guide the process, close with confident outcome.\n"
            f"- Digital-marketing structure: clear pain point, value/benefits, practical proof, and one clear action.\n"
            f"- Be genuinely specific and practical. No fluff.\n"
            f"- Structure EXACTLY: '## ' before every section title. No placeholders, no meta commentary, no code fences."
        )
    return (
        f"Tulis sebuah produk digital ({j[0]}) yang lengkap dan bernilai dalam bahasa Indonesia dengan judul: {nama}. "
        f"Topik: {topik}.\n\n"
        f"FORMAT & ISI: {j[1]} . Gunakan 10-14 section, tiap section 2-3 paragraf pendek berbahasa natural.\n\n"
        f"ATURAN GAYA:\n"
        f"- Bahasa sehari-hari yang enak dibaca, seperti teman yang membantu — jangan kaku/robotik, jangan jualan mau.\n"
        f"- Pakai storytelling: buka dengan hook/masalah yang relatable, alur prosesnya, tutup dengan hasil yang yakin.\n"
        f"- Struktur digital-marketing: pain point jelas, manfaat solusi, bukti/langkah, dan ajakan beraksi tunggal.\n"
        f"- Tulis spesifik praktis. Tidak boleh bertele-tele.\n"
        f"- Format TEPAT: pakai '## ' sebelum setiap judul section. Jangan ada placeholder, komentar meta, atau code fence."
    )

def parse_section(text):
    lines = text.splitlines()
    start = 0
    for i, l in enumerate(lines):
        s = l.strip()
        if re.match(r"^\d+\.\s+\S", s) or s.startswith("## "):
            start = i
            break
    sections = []
    cur_title, cur_body = None, []
    for line in lines[start:]:
        line = line.strip()
        m = re.match(r"^(\d+)\.\s+(.+)$", line)
        if m or line.startswith("## "):
            if cur_title:
                sections.append({"judul": cur_title, "isi": " ".join(cur_body).strip()})
            cur_title = (m.group(2) if m else line[3:]).strip()
            cur_body = []
        elif line and cur_title:
            cur_body.append(line)
    if cur_title:
        sections.append({"judul": cur_title, "isi": " ".join(cur_body).strip()})
    return sections

# ── Build PDF (estetik) ──
def build_pdf(sections, judul, out_path, color):
    from fpdf import FPDF
    bg, accent, tcol = color["bg"], color["accent"], color.get("title", "FFFFFF")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_font("Arial", "", r"C:\Windows\Fonts\arial.ttf", uni=True)
    pdf.add_font("Arial", "B", r"C:\Windows\Fonts\arialbd.ttf", uni=True)
    # judul page
    pdf.add_page()
    pdf.set_fill_color(int(bg[0:2],16), int(bg[2:4],16), int(bg[4:6],16))
    pdf.rect(0, 0, pdf.w, 160, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 24)
    pdf.set_xy(20, 60)
    pdf.multi_cell(0, 12, judul, align="C")
    pdf.set_font("Arial", "", 13)
    pdf.set_xy(20, 105)
    pdf.multi_cell(0, 8, "Practice guide · easy steps · real results", align="C")
    pdf.set_text_color(0, 0, 0)
    for i, s in enumerate(sections, 1):
        pdf.add_page()
        # header bar
        pdf.set_fill_color(int(accent[0:2],16), int(accent[2:4],16), int(accent[4:6],16))
        pdf.rect(0, 0, pdf.get_width(), 14, "F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 11)
        pdf.set_xy(12, 3)
        pdf.cell(0, 10, f"  {judul}", align="L")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(20)
        pdf.set_font("Arial", "B", 17)
        pdf.set_text_color(int(bg[0:2],16), int(bg[2:4],16), int(bg[4:6],16))
        pdf.multi_cell(0, 10, s["judul"])
        pdf.set_text_color(50, 50, 50)
        pdf.set_font("Arial", "", 11)
        pdf.ln(2)
        # bullets sederhana: pisah baris
        pdf.multi_cell(0, 6, s["isi"])
    pdf.output(out_path)
    return os.path.getsize(out_path)

# ── Cover estetik ──
FFDIR = r"C:\Users\ASUS\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin"
FFMPEG = os.path.join(FFDIR, "ffmpeg.exe")

def build_cover(judul, out_png, color):
    import subprocess as sp, tempfile, shutil
    tmp = tempfile.mkdtemp(prefix="cover_")
    try:
        shutil.copy(r"C:\Windows\Fonts\arialbd.ttf", os.path.join(tmp, "arialbd.ttf"))
        # judul pecah jadi baris
        words, lines, cur = judul.split(), [], ""
        for wd in words:
            if len(cur) + len(wd) + 1 <= 20:
                cur = (cur + " " + wd).strip()
            else:
                lines.append(cur); cur = wd
        if cur:
            lines.append(cur)
        with open(os.path.join(tmp, "judul.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        bg, accent = color["bg"], color["accent"]
        # gradient vertikal dingin + teks tengah (ffmpeg gradient + drawtext)
        vf = (f"format=yuv420p,gradients=b:bg0={bg}:bg1={shade(bg,-25)}:x0=0:y0=0:x1=100:y1=180:s=1200x1800,"
              f"drawbox=x=0:y=0:w=1200:h=1800:color=black@0.15:t=fill,"
              f"drawtext=textfile=judul.txt:fontfile=arialbd.ttf:fontsize=62:fontcolor=white@0.95:"
              f"x=(w-text_w)/2:y=(h-text_h)/2-160:line_spacing=18,"
              f"drawtext=text='Premium\nDigital\0Guide':fontfile=arialbd.ttf:fontsize=34:fontcolor={accent}:"
              f"x=(w-text_w)/2:y=(h-text_h)/2+220:line_spacing=14")
        r = sp.run([FFMPEG, "-y", "-f", "lavfi", "-i",
                    f"color=c=0x{bg}:s=1200x1800:r=1",
                    "-vf", vf, "-frames:v", "1", out_png],
                   capture_output=True, text=True, cwd=tmp)
        if r.returncode != 0 or not os.path.exists(out_png):
            raise RuntimeError(f"cover gagal: {r.stderr[-250:]}")
        return os.path.getsize(out_png)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def shade(hexc, delta):
    import colorsys
    r = max(0, min(255, int(hexc[0:2],16) + delta))
    g = max(0, min(255, int(hexc[2:4],16) + delta))
    b = max(0, min(255, int(hexc[4:6],16) + delta))
    return f"{r:02x}{g:02x}{b:02x}"

def upload(judul, desc, price, pdf_path):
    sys.path.insert(0, TOOLS)
    import gumroad_ebook as ge
    log("Upload PDF ke S3...")
    url = ge.upload_file(pdf_path)
    log("File URL OK")
    return ge.create_product(url, judul, desc, price)

def main():
    st = load_state()
    if not st.get("queue"):
        log("ANTRIAN KOSONG (kedua versi selesai?)")
        return
    item = st["queue"][0]
    cidx = st.get("color_idx", 0)
    color = COLORS[cidx % len(COLORS)]
    st["color_idx"] = cidx + 1
    lang = item["lang"]
    nama, topik = item["nama_"+lang], item["topik_"+lang]
    slug = slugify(nama)
    log(f"PRODUK [{lang}] : {nama}")
    os.makedirs(PRODUCTS_DIR, exist_ok=True)

    txt = os.path.join(PRODUCTS_DIR, f"{slug}.txt")
    prompt = make_prompt(lang, topik, nama)
    if not ask_omni(prompt, txt):
        log("Omni gagal — item dikembalikan ke antrian.")
        return
    sections = parse_section(open(txt, encoding="utf-8").read())
    log(f"Seksi: {len(sections)}")
    if len(sections) < 8:
        log("Konten terlalu pendek — retry dengan prompt ulang.")
        ask_omni(prompt, txt, force=True)
        sections = parse_section(open(txt, encoding="utf-8").read())
        if len(sections) < 8:
            log("Masih pendek — kembalikan ke antrian.")
            return
    pdf_path = os.path.join(PRODUCTS_DIR, f"{slug}.pdf")
    size = build_pdf(sections, nama, pdf_path, color)
    log(f"PDF: {size//1024} KB")
    cover_path = os.path.join(PRODUCTS_DIR, f"{slug}_cover.png")
    try:
        build_cover(nama, cover_path, color)
        log(f"COVER OK ({os.path.getsize(cover_path)//1024} KB)")
    except Exception as e:
        log(f"COVER LEBIH: {e}")
    desc = f"Organic, happening product in {lang.upper()}. Just download and put into practice today."
    try:
        p = upload(nama, desc, item["harga_cents"], pdf_path)
        url = p.get("short_url")
        log(f"✅ PRODUK JADI: {url}")
        st.setdefault("done", []).append({"nama": nama, "url": url, "pdf": pdf_path, "lang": lang,
                                          "when": time.strftime("%Y-%m-%d %H:%M")})
        st["queue"].pop(0)
    except Exception as e:
        log(f"UPLOAD GAGAL: {e}")
    save_state(st)

if __name__ == "__main__":
    main()