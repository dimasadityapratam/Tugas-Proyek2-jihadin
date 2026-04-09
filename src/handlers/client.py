import os
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from database import *
from keyboards import *
from utils import format_rupiah, format_order_detail, get_ongkir, get_gratis_ongkir_min, get_min_order, status_with_emoji

# ─── CONVERSATION STATES ──────────────────────────────────────────────────────
(
    CHECKOUT_NAMA, CHECKOUT_HP, CHECKOUT_ALAMAT, CHECKOUT_CATATAN,
    COMPLAINT_DESC, COMPLAINT_FOTO,
    PROFILE_NAMA, PROFILE_HP, PROFILE_ALAMAT,
    SEARCH_QUERY,
) = range(10)

# Simpan state sementara per user
user_state = {}

# ─── START ────────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username, user.first_name)
    toko = get_setting("nama_toko") or "Toko Kami"
    jam = get_setting("jam_buka") or "08:00-21:00"
    await update.message.reply_text(
        f"👋 Selamat datang di *{toko}*!\n"
        f"🕐 Jam Buka: {jam}\n\n"
        f"Silakan pilih menu di bawah ini 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
