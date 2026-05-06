import os
import logging
from groq import Groq
from database import (
    get_setting, get_products, get_user_orders, get_order_items
)
from utils import format_rupiah, status_with_emoji

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah asisten virtual AI untuk toko {nama_toko}.
Lokasi: {alamat_toko}
Jam buka: {jam_buka}
Kontak: {no_hp_toko}
Ongkir: {ongkir}
Minimum order: {min_order}
Gratis ongkir jika belanja minimal: {gratis_ongkir}

=== PRODUK YANG TERSEDIA ===
{daftar_produk}

=== FITUR BOT ===
- Lihat Katalog: telusuri produk per kategori
- Cari Barang: cari produk berdasarkan nama
- Keranjang: kelola keranjang belanja
- Checkout: proses pemesanan
- Pesanan Saya: cek status pesanan
- Pembayaran: tagihan QRIS yang belum dibayar
- Promo: info promo dan gratis ongkir
- Hubungi Admin: kontak toko

Metode pengambilan: Pickup atau Delivery
Metode pembayaran: QRIS atau COD

=== DATA PESANAN CUSTOMER ===
{data_pesanan}

=== ATURAN WAJIB ===
- Jawab dalam bahasa Indonesia yang ramah dan jelas
- Hanya rekomendasikan produk dari daftar di atas
- Jika stok HABIS, sarankan produk lain
- Jangan mengarang harga, stok, atau info yang tidak ada
- KAMU HANYA BISA MEMBERIKAN INFORMASI, kamu TIDAK BISA dan TIDAK BOLEH mengklaim sudah menambahkan produk ke keranjang, membuat pesanan, atau melakukan aksi apapun di bot
- Jika customer ingin beli/pesan/tambah keranjang, SELALU arahkan mereka untuk menggunakan menu bot secara langsung
- Jangan pernah bilang "sudah ditambahkan", "sudah dipesan", atau kalimat seolah kamu melakukan aksi
- FOKUS HANYA PADA TOKO: kamu hanya boleh menjawab pertanyaan yang berkaitan dengan toko ini, produk, pesanan, pengiriman, pembayaran, jam buka, lokasi, dan hal-hal seputar toko
- Jika ada pertanyaan di luar topik toko (misalnya politik, hiburan, sains, resep masakan, dll), jawab dengan: "Maaf, saya hanya bisa membantu seputar informasi toko ini. Silakan gunakan menu bot atau hubungi admin jika butuh bantuan lain."
- JANGAN pernah menjawab pertanyaan umum, memberikan opini, atau membahas topik apapun yang tidak berhubungan langsung dengan toko ini

=== FORMAT JAWABAN WAJIB ===
Jika menampilkan produk:
📦 Nama Produk
💰 Harga: Rp...
📊 Stok: ... pcs

Jika menjelaskan langkah:
1️⃣ Langkah pertama
2️⃣ Langkah kedua
3️⃣ dst...

Aturan format:
- Gunakan emoji relevan di setiap poin
- Pisahkan bagian dengan baris kosong
- Maksimal tampilkan 5 produk per jawaban
- Akhiri dengan arahan ke menu bot yang sesuai, contoh: "Silakan tekan tombol 🛒 Lihat Katalog untuk memesan"
- Gunakan tanda bintang tunggal untuk *teks penting*, JANGAN gunakan tanda bintang ganda (**)
- JANGAN gunakan tanda bintang ganda (**teks**) sama sekali, karena tidak akan ter-render dengan benar
- Gunakan emoji untuk membuat teks lebih menarik dan mudah dibaca"""


def _build_daftar_produk():
    products = get_products()
    if not products:
        return "Belum ada produk tersedia."
    lines = []
    for p in products:
        stok_info = f"stok: {p['stok']}" if p['stok'] > 0 else "stok: HABIS"
        lines.append(
            f"- {p['nama']} | Kategori: {p['kategori']} | Harga: {format_rupiah(p['harga'])} | {stok_info}"
        )
    return "\n".join(lines)


def _build_data_pesanan(user_id):
    orders = get_user_orders(user_id)
    if not orders:
        return "Customer belum memiliki pesanan."
    lines = []
    for o in orders[:5]:  # 5 pesanan terakhir
        lines.append(
            f"- ID: {o['order_id']} | Status: {status_with_emoji(o['status'])} | "
            f"Total: {format_rupiah(o['total'])} | Bayar: {o['metode_pembayaran']}"
        )
    return "\n".join(lines)


async def tanya_ai(update, ctx):
    pertanyaan = update.message.text.strip()
    user_id = update.effective_user.id

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "isi_api_key_groq_disini":
        await update.message.reply_text(
            "Maaf, fitur AI belum dikonfigurasi. Silakan hubungi admin."
        )
        return

    # Ambil semua data konteks
    nama_toko    = get_setting("nama_toko") or "Toko Kami"
    alamat_toko  = get_setting("alamat_toko") or "-"
    jam_buka     = get_setting("jam_buka") or "08:00 - 21:00"
    no_hp_toko   = get_setting("no_hp_toko") or "-"
    ongkir_val   = get_setting("ongkir") or "0"
    min_order_val= get_setting("min_order") or "0"
    gratis_val   = get_setting("gratis_ongkir_min") or "0"

    ongkir       = format_rupiah(float(ongkir_val))
    min_order    = format_rupiah(float(min_order_val)) if float(min_order_val) > 0 else "Tidak ada minimum"
    gratis_ongkir= format_rupiah(float(gratis_val)) if float(gratis_val) > 0 else "Tidak ada promo gratis ongkir"

    daftar_produk = _build_daftar_produk()
    data_pesanan  = _build_data_pesanan(user_id)

    system = SYSTEM_PROMPT.format(
        nama_toko=nama_toko,
        alamat_toko=alamat_toko,
        jam_buka=jam_buka,
        no_hp_toko=no_hp_toko,
        ongkir=ongkir,
        min_order=min_order,
        gratis_ongkir=gratis_ongkir,
        daftar_produk=daftar_produk,
        data_pesanan=data_pesanan,
    )

    # Simpan riwayat percakapan per user (max 10 pesan)
    history = ctx.user_data.setdefault("ai_history", [])
    history.append({"role": "user", "content": pertanyaan})
    if len(history) > 10:
        history = history[-10:]
        ctx.user_data["ai_history"] = history

    messages = [{"role": "system", "content": system}] + history

    try:
        await ctx.bot.send_chat_action(update.effective_chat.id, "typing")
        groq_client = Groq(api_key=api_key)
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=600,
            temperature=0.6,
        )
        jawaban = response.choices[0].message.content.strip()
        # Simpan jawaban AI ke history
        history.append({"role": "assistant", "content": jawaban})
        ctx.user_data["ai_history"] = history
    except Exception as e:
        logger.error(f"Groq error: {type(e).__name__}: {e}")
        jawaban = "Maaf, asisten AI sedang tidak tersedia. Silakan hubungi admin langsung."

    await update.message.reply_text(jawaban, parse_mode="Markdown")
