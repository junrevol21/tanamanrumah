# 🌱 Rencana Konten & Produk — Hasil Riset Sub-Agent (Antigravity) — Agustus 2026

> Dibuat 2026-08-04 via kolaborasi Hermes + Antigravity (sub-agent).
> Niche BEDA-BEDA tiap platform — jangan dicampur.

---

## 📺 YouTube (@TanamanRumahh) — Timelapse GLOBAL EN, tanpa narasi

**Format:** video 3-5 menit (24+ klip 8s) + 2 Shorts reuse, label Day N, judul EN.

Ide baru (prioritas, dari riset):
1. **What Happens When You Put Salt Near a Sensitive Plant?** — Mimosa pudica macro, curiosity-driven
2. **Sprouting a Seed Inside the Fruit Itself (Vivipary Timelapse)** — oddly satisfying, thumbnail kuat
3. **Do Plants Fight? 30 Days of Vines Battling for Sunlight** — storyline clash, adiktif
4. **Root vs Rock: The Unstoppable Power of a Growing Seed** — dramatis & inspiratif ("Nature Always Wins")
5. **Inside a Venus Flytrap: 7 Days of Digestion in 4K Ultra Macro** — sains + visual mikro

**Antrian saat ini (state_pipeline.json):** butterfly (aktif) → bean → mushroom → flower → frog → crystals → leaf → mold → bread → sun-turning.
**Refill otomatis:** cron Senin 07:00 (queue_refill.py) — isi 10 topik kalau antrian ≤3.

---

## 🛒 Gumroad (junrevol.gumroad.com) — Digital GLOBAL EN, $3-15

Sudah ada: **Indoor Plant Care Guide**.

Ide produk baru (prioritas):
1. **The Ultimate Houseplant Pest & Disease Diagnostic Cards** — panic-buying, solusi instan
2. **Aesthetic Notion Indoor Plant Care & Propagation Dashboard** — kolektor milenial/Gen Z
3. **Printable Botanical Plant Pot Tags & Care Label Kit** — impulsive buy, estetik
4. **Low-Light & Apartment Plant Selection Matrix** — pet-friendly, urban
5. **Houseplant Propagation Logbook & Rooting Tracker** — hobi favorit kolektor

---

## 🎵 TikTok Affiliate (@packjeon) — LOKAL INDONESIA, produk 60-100rb, komisi ≥10rb

Ide konten (prioritas):
1. **Dulu Rumah Bau Apek, Sekarang Bersih Instan** — vacuum portable/anti-bau pet, Before-After
2. **Trik Rahasia Tanaman Auto Rimbun Bebas Hama** — neem oil + nutrisi daun, Edukasi
3. **Unboxing Dispenser Minum Otomatis Anti Tumpah** — pet water fountain, unboxing
4. **Solusi Dapur Rapi Tanpa Bor: Rak Tempel** — rak tempel, DIY/makeover
5. **Mengepel Tanpa Peras Tangan** — spin mop otomatis, relatable

**Status planner TikTok:** 17 produk (4 caption_ready: Cantik Hutan Hair Mask, POWER METABOLISME, NPURE Sunscreen, Phone Holder; 13 perlu link aff).

---

## 🔁 Mekanisme berulang (otomatis terus-menerus)
- **Pipeline YouTube:** cron 15:30 WIB harian (901b549e2cd5) — sudah difix (model drift) & jalan
- **Refill antrian:** cron Senin 07:00 WIB (fdbc27d05ce5) — anti-habis, ide baru via sub-agent
- **Gumroad auto-gen:** cron Minggu 10:00 WIB (019b1df0bfc2)
- **Artikel SEO:** cron Minggu 10:00 WIB (3bb01d7c96d9)
- **Report mingguan semua aliran:** cron Senin 08:00 WIB (66e48aa14489)
