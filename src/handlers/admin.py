from telegram import Update
from telegram.ext import ContextTypes
from database import *
from keyboards import *
from utils import format_rupiah, format_order_detail, status_with_emoji

# LOGIN ADMIN
async def admin_login(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        await update.message.reply_text("✅ Kamu sudah login sebagai admin.", reply_markup=admin_menu())
        return
    ctx.user_data["waiting_pin"] = True
    await update.message.reply_text("🔐 Masukkan PIN Admin:")

async def check_pin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_pin"):
        return False
    pin = update.message.text.strip()
    correct_pin = get_setting("admin_pin") or "1234"
    ctx.user_data["waiting_pin"] = False
    if pin == correct_pin:
        add_admin(update.effective_user.id, update.effective_user.username)
        await update.message.reply_text("✅ Login admin berhasil!", reply_markup=admin_menu())
        return True
    else:
        await update.message.reply_text("❌ PIN salah. Akses ditolak.")
        return True

async def admin_logout(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_conn()
    conn.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    from keyboards import main_menu
    await update.message.reply_text("👋 Kamu telah keluar dari mode admin.", reply_markup=main_menu())