# Bot Telegram — S&A Online Shop Salaman

Bot Telegram berbasis Python untuk mendukung operasional **Usaha S&A Online Shop Salaman**. Bot ini dirancang sebagai solusi digital untuk manajemen pesanan, inventaris produk, dan layanan pelanggan secara otomatis melalui platform Telegram.

---

## Deskripsi Proyek

Proyek ini merupakan hasil Praktik Kerja Lapangan (PKL) yang dikembangkan secara tim. Bot ini membantu pemilik usaha dalam mengelola toko secara digital — mulai dari katalog produk, proses pemesanan, pembayaran QRIS maupun COD, hingga laporan penjualan harian — semua melalui antarmuka Telegram.

---

## Tujuan

### Hard Skills
- Mengimplementasikan bot Telegram menggunakan library `python-telegram-bot`
- Mengelola database relasional dengan SQLite
- Menerapkan arsitektur modular (main → handlers → database)
- Menggunakan Git & GitHub dalam alur kerja tim (branching, pull request, merge)
- Menerapkan keamanan konfigurasi dengan file `.env`

### Soft Skills
- Kolaborasi tim dalam pengembangan perangkat lunak
- Pembagian tugas dan tanggung jawab antar anggota
- Komunikasi teknis melalui dokumentasi dan kode
- Manajemen waktu dalam pengerjaan proyek bertahap

---

## Fitur Bot

### Untuk Customer

| Fitur | Keterangan |
|---|---|
| Lihat Katalog | Telusuri produk berdasarkan kategori |
| Cari Barang | Cari produk berdasarkan nama |
| Keranjang | Tambah, hapus, dan kosongkan keranjang |
| Checkout | Proses pemesanan dengan isi data penerima |
| Metode Pengambilan | Pilih Pickup atau Delivery |
| Metode Pembayaran | Pilih QRIS atau COD |
| Pesanan Saya | Lacak status semua pesanan |
| Pembayaran QRIS | Upload bukti bayar untuk konfirmasi admin |
| Konfirmasi Pesanan | Konfirmasi penerimaan barang |
| Komplain | Laporkan masalah pesanan (kurang / salah / rusak) |
| Promo | Lihat info promo dan gratis ongkir |
| Hubungi Admin | Tampilkan kontak toko |

### Untuk Admin

| Fitur | Keterangan |
|---|---|
| Login Admin | Masuk via PIN dengan perintah `/admin` |
| Pesanan Masuk | Lihat dan approve / tolak pesanan baru |
| Update Status | Ubah status pesanan secara manual |
| Validasi Pembayaran | Konfirmasi atau tolak bukti bayar QRIS |
| Kelola Produk | Tambah, edit, hapus produk |
| Kelola Stok | Pantau dan update stok produk |
| Data Customer | Lihat daftar customer terdaftar |
| Laporan Penjualan | Laporan harian, barang terlaris, customer terbanyak |
| Broadcast | Kirim pesan ke semua customer |
| Pengaturan Toko | Ubah nama, alamat, ongkir, jam buka, PIN, dll |
| Upload QRIS | Perbarui foto QRIS pembayaran |
| Laporan Komplain | Lihat dan selesaikan komplain customer |
| Keluar Admin | Logout dari mode admin |

---

## Alur Pesanan

```
Customer buat pesanan
    └─→ Menunggu Persetujuan Admin
            ├─→ [COD]  Pesanan Disiapkan → Diantar / Siap Diambil → Diterima / Diambil → Selesai
            └─→ [QRIS] Menunggu Pembayaran → Upload Bukti → Validasi Admin
                            └─→ Pesanan Disiapkan → Diantar / Siap Diambil → Diterima / Diambil → Selesai
```

---

## Contoh Alur Chat Bot

```
User: /start
Bot:  Selamat datang di S&A Online Shop Salaman!
      Jam Buka: 08:00 - 21:00
      Silakan pilih menu di bawah ini
      [Lihat Katalog] [Cari Barang]
      [Keranjang]     [Checkout]
      ...

User: Lihat Katalog
Bot:  Pilih Kategori: [Sembako] [Minuman] [Snack] ...

User: Sembako
Bot:  Daftar produk sembako beserta tombol detail dan harga

User: Checkout
Bot:  Masukkan nama penerima
      → Masukkan nomor HP
      → Masukkan alamat lengkap
      → Catatan tambahan
      → Pilih Pickup / Delivery
      → Pilih QRIS / COD
      → Invoice dikirim, admin dinotifikasi otomatis
```

---

## Arsitektur Proyek

```
main.py  ──→  handlers/client.py   ──→  database.py
         ──→  handlers/admin.py    ──→  database.py
         ──→  keyboards.py
              utils.py
```

`main.py` menerima semua update dari Telegram, melakukan routing ke handler yang sesuai. Handler memanggil fungsi di `database.py` untuk operasi baca/tulis data, lalu mengirim respons kembali ke user. `keyboards.py` menyediakan semua tampilan tombol, dan `utils.py` berisi fungsi pembantu seperti format rupiah dan escape teks Markdown.

---

## Pembagian Tim

| Anggota | Branch | Tanggung Jawab |
|---|---|---|
| Jiyad | `main-loop` | `src/main.py` — Core bot, routing semua handler, registrasi command dan callback |
| Ubed | `handlers` | `src/handlers/`, `src/keyboards.py`, `src/.env` — Logika respons user dan admin, tampilan keyboard |
| Amru | `controls` | `src/database.py` — Seluruh operasi database, query SQLite, inisialisasi tabel |

---

## Struktur Database

Database menggunakan SQLite (`toko.db`) dengan tabel berikut:

| Tabel | Keterangan |
|---|---|
| `users` | Data customer yang pernah berinteraksi dengan bot |
| `admins` | Daftar user yang sedang login sebagai admin |
| `categories` | Kategori produk (Sembako, Minuman, Snack, dll) |
| `products` | Data produk (nama, harga, stok, foto, kategori) |
| `stock` | Riwayat perubahan stok produk |
| `cart` | Keranjang belanja per user |
| `orders` | Data pesanan (invoice, status, metode, total) |
| `order_items` | Detail item per pesanan |
| `payments` | Status pembayaran dan bukti foto |
| `complaints` | Komplain customer beserta resolusi |
| `settings` | Konfigurasi toko (nama, ongkir, PIN, QRIS, dll) |

---

## Teknologi yang Digunakan

| Teknologi | Keterangan |
|---|---|
| Python 3.10+ | Bahasa pemrograman utama |
| python-telegram-bot | Library async untuk Telegram Bot API |
| SQLite | Database lokal ringan, tidak perlu server |
| python-dotenv | Manajemen konfigurasi sensitif via `.env` |
| Git & GitHub | Version control dan kolaborasi tim |

---

## Struktur Folder

```
Tugas-Proyek2-jihadin/
├── docs/
│   ├── ALUR KERJA PROGRAM.png
│   ├── DOKUMEN KEBUTUHAN SISTEM.pdf
│   ├── DOKUMEN OBSERVASI.docx
│   └── DOKUMEN WAWANCARA.docx
├── src/
│   ├── handlers/
│   │   ├── admin.py        # Handler fitur admin
│   │   └── client.py       # Handler fitur customer
│   ├── .env                # Konfigurasi token dan pengaturan (tidak di-commit)
│   ├── database.py         # Semua operasi SQLite
│   ├── keyboards.py        # Inline dan reply keyboard
│   ├── main.py             # Entry point dan router utama
│   ├── utils.py            # Helper (format rupiah, escape markdown, dll)
│   └── toko.db             # Database SQLite (dibuat otomatis saat pertama jalan)
├── .gitignore
└── README.md
```

---

## Cara Menjalankan Proyek

### 1. Clone Repositori

```bash
git clone https://github.com/<username>/<nama-repo>.git
cd <nama-repo>
```

### 2. Install Dependensi

```bash
pip install python-telegram-bot python-dotenv
```

Jika `pip` tidak dikenali, gunakan:

```bash
python -m pip install python-telegram-bot python-dotenv
```

### 3. Buat File `.env`

Buat file `src/.env` dengan isi berikut:

```env
BOT_TOKEN=isi_token_bot_dari_botfather

NAMA_TOKO=S&A Online Shop Salaman
ALAMAT_TOKO=Salaman, Magelang
NO_HP_TOKO=08xxxxxxxxxx
JAM_BUKA=08:00 - 21:00
ONGKIR_DEFAULT=10000
MIN_ORDER_DEFAULT=0
ADMIN_PIN=1234
```

> **Penting:** Jangan pernah commit file `.env` ke GitHub. Pastikan `.env` sudah tercantum di `.gitignore`.

### 4. Jalankan Bot

```bash
cd src
python main.py
```

---

## Workflow Git Tim

```
main
 ├── main-loop   →  Jiyad  (src/main.py)
 ├── handlers    →  Ubed   (src/handlers/, src/keyboards.py, src/.env)
 └── controls    →  Amru   (src/database.py)
```

Alur kerja:
1. Setiap anggota bekerja di branch masing-masing
2. Setelah fitur selesai, buat Pull Request ke branch `main`
3. Review bersama sebelum merge
4. Konflik diselesaikan secara kolaboratif

---

## Perintah Pengaturan Toko

Setelah login admin dengan `/admin`, gunakan perintah berikut untuk mengubah konfigurasi toko:

```
/set nama_toko <nilai>
/set alamat_toko <nilai>
/set no_hp_toko <nilai>
/set jam_buka <nilai>
/set ongkir <nilai>
/set min_order <nilai>
/set gratis_ongkir_min <nilai>
/set admin_pin <nilai>
/setqris                    → Upload foto QRIS baru
```

---

## Tahapan Pengerjaan

### Minggu 1 — Observasi dan Wawancara
- Observasi langsung ke lokasi usaha S&A Online Shop Salaman
- Wawancara dengan pemilik usaha untuk menggali kebutuhan sistem
- Hasil dokumentasi: `DOKUMEN OBSERVASI.docx`, `DOKUMEN WAWANCARA.docx`

### Minggu 2 — Perencanaan dan Desain Sistem
- Penyusunan alur kerja program (`ALUR KERJA PROGRAM.png`)
- Penyusunan dokumen kebutuhan sistem (`DOKUMEN KEBUTUHAN SISTEM.pdf`)
- Penentuan fitur, pembagian tugas, dan rancangan struktur database

### Minggu 3 — Pengembangan dan Upload GitHub
- Implementasi kode sesuai pembagian tugas:
  - Amru: `src/database.py` — seluruh operasi data dan inisialisasi database
  - Jiyad: `src/main.py` — core bot, routing, registrasi handler
  - Ubed: `src/handlers/`, `src/keyboards.py`, `src/.env` — handler dan tampilan
- Penggunaan branching Git sesuai pembagian tugas
- Pull request dan merge ke branch `main`

### Minggu 4 — Presentasi
- Demo bot secara langsung kepada penguji
- Penjelasan arsitektur, pembagian tugas, dan alur kerja sistem
- Evaluasi dan tanya jawab hasil proyek

---

## Dokumentasi

Seluruh dokumen pendukung tersedia di folder `docs/`:

| File | Keterangan |
|---|---|
| `DOKUMEN OBSERVASI.docx` | Hasil observasi lapangan di lokasi usaha |
| `DOKUMEN WAWANCARA.docx` | Hasil wawancara dengan pemilik usaha |
| `DOKUMEN KEBUTUHAN SISTEM.pdf` | Spesifikasi kebutuhan fungsional sistem |
| `ALUR KERJA PROGRAM.png` | Diagram alur kerja bot secara visual |

---

## Presentasi Akhir

Presentasi dilaksanakan pada Minggu 4 dengan materi:
- Latar belakang dan tujuan proyek
- Demo bot secara langsung (fitur customer dan admin)
- Penjelasan arsitektur dan pembagian tugas tim
- Kendala yang dihadapi dan solusinya
- Kesimpulan dan saran pengembangan

---

## Kesimpulan

Bot Telegram S&A Online Shop Salaman berhasil dikembangkan sebagai solusi digitalisasi operasional toko. Dengan fitur pemesanan otomatis, manajemen produk, validasi pembayaran QRIS, dan laporan penjualan, bot ini mampu membantu pemilik usaha dalam mengelola toko secara lebih efisien. Proyek ini juga menjadi sarana pembelajaran kolaborasi tim menggunakan Git dan GitHub dalam siklus pengembangan perangkat lunak nyata.
