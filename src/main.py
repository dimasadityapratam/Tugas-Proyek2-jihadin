import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

from database import init_db
from config import BOT_TOKEN
from handlers.client import (
    start, show_katalog, katalog_callback, cari_barang, proses_cari,
    show_keranjang, keranjang_callback, checkout_command, checkout_input,
    checkout_callback, pesanan_saya, order_detail_command, pembayaran_menu,
    bayar_command, pembayaran_callback, terima_bukti_bayar, order_action_callback,
    complaint_input, show_promo, hubungi_admin
)

from handlers.admin import (
    admin_login, check_pin, admin_logout,
    pesanan_masuk, approve_callback,
    update_status_menu, setstatus_command, setstatus_callback,
    validasi_pembayaran, konfirmasi_pembayaran_callback,
    kelola_produk, addprod_command, addprod_input, editprod_command,
    editprod_callback, editprod_input,
    kelola_stok, setstok_command,
    data_customer, laporan_penjualan,
    broadcast_menu, broadcast_input,
    pengaturan_toko, set_command, setqris_command, setqris_input,
    laporan_komplain, resolusi_callback
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    """Log error tapi jangan crash bot."""
    logger.error("Exception saat handle update:", exc_info=ctx.error)

# ─── ROUTER UTAMA ─────────────────────────────────────────────────────────────

async def message_router(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Router untuk semua pesan teks - menangani state & menu button."""
    text = update.message.text if update.message else ""

    # Cek PIN admin
    if ctx.user_data.get("waiting_pin"):
        await check_pin(update, ctx)
        return

    # Cek state addprod
    if ctx.user_data.get("addprod_step"):
        handled = await addprod_input(update, ctx)
        if handled:
            return

    # Cek state editprod
    if ctx.user_data.get("editprod_step") == "input":
        handled = await editprod_input(update, ctx)
        if handled:
            return

    # Cek state setqris
    if ctx.user_data.get("setqris_step") == "foto":
        handled = await setqris_input(update, ctx)
        if handled:
            return

    # Cek state broadcast
    if ctx.user_data.get("broadcast_step") == "input":
        handled = await broadcast_input(update, ctx)
        if handled:
            return

    # Cek state pencarian
    if ctx.user_data.get("search_active"):
        ctx.user_data["search_active"] = False
        await proses_cari(update, ctx)
        return

    # Cek state checkout
    if ctx.user_data.get("checkout_step"):
        await checkout_input(update, ctx)
        return

    # Cek state komplain
    if ctx.user_data.get("complaint_step"):
        await complaint_input(update, ctx)
        return

    # Cek upload bukti bayar (foto)
    if ctx.user_data.get("upload_bukti_order") and update.message.photo:
        await terima_bukti_bayar(update, ctx)
        return

    # Menu buttons client
    menu_map = {
        "🛒 Lihat Katalog": show_katalog,
        "🔍 Cari Barang": cari_barang,
        "🧺 Keranjang": show_keranjang,
        "✅ Checkout": checkout_command,
        "📦 Pesanan Saya": pesanan_saya,
        "💳 Pembayaran": pembayaran_menu,
        "🎁 Promo": show_promo,
        "📞 Hubungi Admin": hubungi_admin,
    }

    # Menu buttons admin
    admin_map = {
        "📥 Pesanan Masuk": pesanan_masuk,
        "🔄 Update Status": update_status_menu,
        "📦 Kelola Produk": kelola_produk,
        "📊 Kelola Stok": kelola_stok,
        "💰 Validasi Pembayaran": validasi_pembayaran,
        "👥 Data Customer": data_customer,
        "📈 Laporan Penjualan": laporan_penjualan,
        "📢 Broadcast": broadcast_menu,
        "⚙ Pengaturan Toko": pengaturan_toko,
        "🚨 Laporan Komplain": laporan_komplain,
        "🚪 Keluar Admin": admin_logout,
    }

    if text in menu_map:
        await menu_map[text](update, ctx)
    elif text in admin_map:
        await admin_map[text](update, ctx)

async def photo_router(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Router untuk pesan foto."""
    # Upload bukti bayar
    if ctx.user_data.get("upload_bukti_order"):
        await terima_bukti_bayar(update, ctx)
        return
    # Foto saat addprod
    if ctx.user_data.get("addprod_step") == "foto":
        await addprod_input(update, ctx)
        return
    # Foto saat editprod
    if ctx.user_data.get("editprod_step") == "input" and ctx.user_data.get("editprod_field") == "foto":
        await editprod_input(update, ctx)
        return
    # Foto saat setqris
    if ctx.user_data.get("setqris_step") == "foto":
        await setqris_input(update, ctx)
        return
    # Foto saat komplain
    if ctx.user_data.get("complaint_step") == "foto":
        await complaint_input(update, ctx)
        return

async def search_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handler khusus untuk state pencarian barang."""
    if ctx.user_data.get("search_active"):
        ctx.user_data["search_active"] = False
        await proses_cari(update, ctx)

