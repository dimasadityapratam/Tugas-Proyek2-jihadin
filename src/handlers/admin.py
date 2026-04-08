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

# ─── PESANAN MASUK ────────────────────────────────────────────────────────────

async def pesanan_masuk(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    orders = get_all_orders(status="Menunggu Persetujuan Admin")
    if not orders:
        await update.message.reply_text("📥 Tidak ada pesanan masuk.", reply_markup=admin_menu())
        return
    for o in orders[:10]:
        items = get_order_items(o["order_id"])
        detail = format_order_detail(o, items)
        await update.message.reply_text(
            detail,
            parse_mode="Markdown",
            reply_markup=approve_order_keyboard(o["order_id"])
        )

async def approve_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("❌ Bukan admin!", show_alert=True)
        return
    data = query.data

    if data.startswith("approve_"):
        order_id = data.replace("approve_", "")
        order = get_order(order_id)
        update_order_status(order_id, "Menunggu Pembayaran")
        await query.edit_message_text(
            f"✅ Pesanan `{order_id}` *disetujui*.\nStatus: Menunggu Pembayaran",
            parse_mode="Markdown"
        )
        # Notif customer
        if order:
            try:
                msg = f"✅ Pesanan kamu `{order_id}` telah *disetujui admin*!\n\n"
                if order["metode_pembayaran"] == "QRIS":
                    msg += f"Silakan lakukan pembayaran QRIS sebesar *{format_rupiah(order['total'])}*\nGunakan /bayar {order_id}"
                else:
                    msg += "Pembayaran COD - bayar saat barang diterima."
                await ctx.bot.send_message(order["user_id"], msg, parse_mode="Markdown")
            except Exception:
                pass

    elif data.startswith("reject_"):
        order_id = data.replace("reject_", "")
        order = get_order(order_id)
        update_order_status(order_id, "Dibatalkan")
        await query.edit_message_text(f"❌ Pesanan `{order_id}` *ditolak*.", parse_mode="Markdown")
        if order:
            try:
                await ctx.bot.send_message(order["user_id"], f"❌ Maaf, pesanan kamu `{order_id}` ditolak oleh admin.", parse_mode="Markdown")
            except Exception:
                pass

# ─── UPDATE STATUS ────────────────────────────────────────────────────────────

async def update_status_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    orders = get_all_orders()
    active = [o for o in orders if o["status"] not in ("Selesai", "Dibatalkan")]
    if not active:
        await update.message.reply_text("📋 Tidak ada pesanan aktif.", reply_markup=admin_menu())
        return
    lines = ["🔄 *Pesanan Aktif:*\n"]
    for o in active[:15]:
        lines.append(f"• `{o['order_id']}` - {status_with_emoji(o['status'])}")
    lines.append("\nGunakan /setstatus <ID> untuk update status.")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def setstatus_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("Gunakan: /setstatus <ID_PESANAN>")
        return
    order_id = ctx.args[0]
    order = get_order(order_id)
    if not order:
        await update.message.reply_text("❌ Pesanan tidak ditemukan.")
        return
    await update.message.reply_text(
        f"📋 Pilih status baru untuk `{order_id}`:",
        parse_mode="Markdown",
        reply_markup=status_update_keyboard(order_id, order["metode_pengambilan"])
    )

async def setstatus_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    data = query.data
    if data.startswith("setstatus_"):
        parts = data.split("_", 2)
        order_id = parts[1]
        new_status = parts[2]
        order = get_order(order_id)
        update_order_status(order_id, new_status)
        await query.edit_message_text(f"✅ Status `{order_id}` diubah ke: *{new_status}*", parse_mode="Markdown")
        if order:
            try:
                msg = f"📦 Update pesanan `{order_id}`:\nStatus: *{status_with_emoji(new_status)}*"
                kb = None
                if new_status in ("Pesanan Diterima", "Pesanan Diambil"):
                    kb = konfirmasi_order_keyboard(order_id)
                await ctx.bot.send_message(order["user_id"], msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                pass
