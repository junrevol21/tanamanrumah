# 🌿 TanamanRumah — Situs Affiliate Otomatis

Situs review/rekomendasi perlengkapan tanaman indoor & urban gardening (Indonesia).
100% konten dibuat & dipublish oleh AI agent (Hermes). Anda hanya perlu setup akun SEKALI.

## 📁 Struktur
```
tanamanrumah/
├── index.html                    # Beranda
├── css/style.css                 # Tema
├── artikel/
│   ├── lampu-tanam-terbaik-2026.html    # Artikel #1 (produk utama: grow light)
│   ├── kit-hidroponik-pemula.html       # Artikel #2
│   └── alat-siram-otomatis.html         # Artikel #3
└── youtube/
    └── script-video-1-lampu-tanam.md    # Script YouTube (project cadangan)
```

## ⚙️ Setup Anda (SEKALI, ±30–45 menit)

### 1. Daftar affiliate (WAJIB — ini sumber komisi)
- **Shopee Affiliate (program Non-KOL / Blogger)**: buka https://shopee.co.id/m/affiliates → daftar dengan akun Shopee → verifikasi KTP/NPWP → aktifkan program.
  - Komisi: 3,5% direct / 1,5% indirect (cap Rp 11.500/order) + **Komisi Xtra** dari toko Mall/Star+ (bisa 5–59,5% TANPA cap — cek tab "Komisi XTRA" di dashboard).
  - Payout: mingguan ke rekening bank (di bawah Rp 500rb via ShopeePay). PPh 21 dipotong otomatis.
- **Tokopedia Affiliate**: buka https://affiliate.tokopedia.com → daftar (tanpa syarat follower) → komisi dasar (maks Rp 20.000/barang) + Komisi Ekstra 1–20%.
- (Opsional) **Blibli Affiliate** — KYC saat cair pertama, komisi s/d 12%.

### 2. Hosting situs — PILIHAN: GitHub Pages (dipilih karena bisa 100% otomatis)
- **GitHub Pages** ✅ (Rekomendasi): buat repo publik `tanamanrumah` di github.com → Settings → Pages → deploy dari branch `main`. Setelah itu Hermes bisa push artikel baru otomatis via git (cron).
- Alternatif manual: Netlify Drop (tarik folder ke https://app.netlify.com/drop) — cepat tapi tiap update harus upload ulang manual.
- (Opsional, nanti) Beli domain `.id`/`.com` ±Rp 150–300rb/tahun — bagus untuk SEO jangka panjang.

### 3. Tempel link affiliate (5 menit)
Ganti semua placeholder di file artikel (cari teks `AFFILIATE-...`):
1. Buka produk di Shopee → tap ikon bagikan → "Salin link afiliasi" (pastikan lewat program affiliate).
2. Ganti `https://s.shopee.co.id/AFFILIATE-SHOPEE-XXX` dengan link afiliasi asli produk grow light / kit hidroponik / alat siram.
3. Lakukan sama untuk Tokopedia (`https://tokopedia.link/AFFILIATE-...`).
4. Kabari saya — saya verifikasi & ganti sisanya.

## 🤖 Pipeline otomatis (dijalankan Hermes)
Setelah repo siap, saya pasang:
- **Cron mingguan**: riset keyword → tulis 1–2 artikel baru → publish ke repo → lapor ke Telegram.
- **Verifikasi link**: cek tautan afiliasi tidak rusak.
- **Laporan bulanan**: trafik (via Google Search Console bila disambungkan), klik affiliate (dashboard Shopee/Tokopedia), rekomendasi iterasi.

## 📈 Target & ekspektasi jujur
- Klik pertama: 2–6 minggu (SEO long-tail). Komisi pertama: ±2–6 bulan.
- Konversi situs review: 0,5–1% visitor→beli (artikel review bagus: s/d 2,3%).
- Butuh ±100–300 klik untuk komisi pertama. Konsistensi 2–3 artikel/minggu = kunci.

## 🎬 Project cadangan: YouTube (opsional)
- Script siap di `youtube/script-video-1-lampu-tanam.md`.
- Video faceless: TTS + gambar (bisa dibuat Hermes via Python), link afiliasi di deskripsi sejak video #1 (konversi YouTube 2–5%).
- Upload manual oleh Anda (YouTube API butuh OAuth — setup sekali) atau semi-otomatis.

## ⚠️ Aturan wajib (agar aman & tidak kena sanksi)
- Konten asli & bermanfaat — Shopee melarang spam link tanpa konten (komisi hangus).
- Jangan gunakan identitas/atribut jabatan di situs ini.
- Laporkan penghasilan di SPT Tahunan (penghasilan tambahan, tarif progresif).
- Jangan pakai fasilitas negara (laptop kantor/jam kerja) untuk mengelola situs ini.
