import html
import json
import traceback
from handlers.ai import tanya_ai
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

from database import init_db
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
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

# --- 1. SETUP LOGGING KE FILE DAN CONSOLE ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("error_log.txt"), # Menyimpan log ke file
        logging.StreamHandler()               # Menampilkan log di terminal
    ]
)
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
        "⚙️ Pengaturan Toko": pengaturan_toko,
        "🚨 Laporan Komplain": laporan_komplain,
        "🚪 Keluar Admin": admin_logout,
    }

    if text in menu_map:
        await menu_map[text](update, ctx)
    elif text in admin_map:
        await admin_map[text](update, ctx)
    else:
        await tanya_ai(update, ctx)

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

# ─── CALLBACK ROUTER ──────────────────────────────────────────────────────────

async def callback_router(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Router semua callback query."""
    data = update.callback_query.data

    if data.startswith(("cat_", "page_", "prod_", "addcart_", "back_")):
        await katalog_callback(update, ctx)
    elif data in ("checkout", "clear_cart") or data.startswith("delcart_"):
        await keranjang_callback(update, ctx)
    elif data in ("pickup", "delivery", "cancel_checkout"):
        await checkout_callback(update, ctx)
    elif data in ("pay_qris", "pay_cod"):
        await checkout_callback(update, ctx)
    elif data.startswith("sudah_bayar_"):
        await pembayaran_callback(update, ctx)
    elif data.startswith("confirm_order_") or data.startswith("complaint_") or data.startswith("komp_"):
        await order_action_callback(update, ctx)
    elif data.startswith("approve_") or data.startswith("reject_"):
        await approve_callback(update, ctx)
    elif data.startswith("setstatus_"):
        await setstatus_callback(update, ctx)
    elif data.startswith("konfpay_"):
        await konfirmasi_pembayaran_callback(update, ctx)
    elif data.startswith("editprod_") or data.startswith("delprod_"):
        await editprod_callback(update, ctx)
    elif data.startswith("resolusi_"):
        await resolusi_callback(update, ctx)

# ─── CARI BARANG COMMAND ──────────────────────────────────────────────────────

async def cari_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["search_active"] = True
    await update.message.reply_text("🔍 Ketik nama barang yang ingin dicari:")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
# --- 2. FUNGSI CRASH REPORTING ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # A. Catat error secara detail ke file error_log.txt
    logger.error("Exception while handling an update:", exc_info=context.error)

    # B. Ambil ID Admin Utama dari .env
    admin_id = os.getenv("ADMIN_CHAT_ID")
    if not admin_id:
        return

    # C. Kumpulkan detail traceback error
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # D. Format pesan laporan (dibatasi agar tidak melebihi batas karakter Telegram)
    # Kita menggunakan HTML parse_mode agar rapi
    message = (
        f"🚨 *BOT CRASH REPORT* 🚨\n\n"
        f"<b>Error:</b>\n<pre>{html.escape(tb_string[-3000:])}</pre>\n\n"
    )

    # E. Kirim notifikasi ke Admin
    try:
        await context.bot.send_message(
            chat_id=admin_id,
            text=message,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Gagal mengirim laporan error ke Telegram Admin: {e}")

def main():
    init_db()

    # Jika perlu proxy, uncomment dan isi:
    # from telegram.request import HTTPXRequest
    # request = HTTPXRequest(proxy="socks5://user:pass@host:port")
    # app = Application.builder().token(BOT_TOKEN).request(request).build()

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_login))
    app.add_handler(CommandHandler("order", order_detail_command))
    app.add_handler(CommandHandler("bayar", bayar_command))
    app.add_handler(CommandHandler("cari", cari_command))
    app.add_handler(CommandHandler("setstatus", setstatus_command))
    app.add_handler(CommandHandler("setstok", setstok_command))
    app.add_handler(CommandHandler("addprod", addprod_command))
    app.add_handler(CommandHandler("editprod", editprod_command))
    app.add_handler(CommandHandler("set", set_command))
    app.add_handler(CommandHandler("setqris", setqris_command))

    # Callback queries
    app.add_handler(CallbackQueryHandler(callback_router))

    # Pesan foto
    app.add_handler(MessageHandler(filters.PHOTO, photo_router))

    # Pesan teks (menu & state)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))

    # Error handler
    app.add_error_handler(error_handler)

    logger.info("Bot started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
