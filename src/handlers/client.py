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

# ─── KATALOG ──────────────────────────────────────────────────────────────────

async def show_katalog(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cats = get_categories()
    await update.message.reply_text(
        "🛒 *Pilih Kategori Produk:*",
        parse_mode="Markdown",
        reply_markup=kategori_keyboard(cats)
    )

async def katalog_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("cat_"):
        cat_id = int(data.split("_")[1])
        products = get_products(category_id=cat_id)
        ctx.user_data["current_products"] = products
        ctx.user_data["current_cat_id"] = cat_id
        if not products:
            await query.edit_message_text("😔 Belum ada produk di kategori ini.")
            return
        await query.edit_message_text(
            "📦 *Pilih Produk:*",
            parse_mode="Markdown",
            reply_markup=produk_keyboard(products, page=0)
        )

    elif data.startswith("page_"):
        page = int(data.split("_")[1])
        products = ctx.user_data.get("current_products", [])
        await query.edit_message_reply_markup(reply_markup=produk_keyboard(products, page=page))

    elif data.startswith("prod_"):
        product_id = int(data.split("_")[1])
        p = get_product(product_id)
        ctx.user_data["last_product_id"] = product_id
        if not p:
            await query.edit_message_text("Produk tidak ditemukan.")
            return
        text = (
            f"🏷️ *{p['nama']}*\n"
            f"📂 Kategori: {p['kategori']}\n"
            f"💰 Harga: {format_rupiah(p['harga'])}\n"
            f"📦 Stok: {p['stok']}\n\n"
            f"📝 {p['deskripsi'] or 'Tidak ada deskripsi.'}"
        )
        kb = produk_detail_keyboard(product_id, p["stok"])
        if p.get("foto"):
            try:
                await query.message.reply_photo(photo=p["foto"], caption=text, parse_mode="Markdown", reply_markup=kb)
                await query.delete_message()
            except Exception:
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
        else:
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)

    elif data.startswith("addcart_"):
        parts = data.split("_")
        product_id = int(parts[1])
        jumlah = int(parts[2])
        p = get_product(product_id)
        if not p or p["stok"] < jumlah:
            await query.answer("❌ Stok tidak cukup!", show_alert=True)
            return
        add_to_cart(query.from_user.id, product_id, jumlah)
        await query.answer(f"✅ {p['nama']} ditambahkan ke keranjang!", show_alert=True)

    elif data == "back_katalog":
        cats = get_categories()
        await query.edit_message_text(
            "🛒 *Pilih Kategori Produk:*",
            parse_mode="Markdown",
            reply_markup=kategori_keyboard(cats)
        )

    elif data == "back_produk":
        products = ctx.user_data.get("current_products", [])
        if products:
            await query.edit_message_text(
                "📦 *Pilih Produk:*",
                parse_mode="Markdown",
                reply_markup=produk_keyboard(products, page=0)
            )
        else:
            cats = get_categories()
            await query.edit_message_text(
                "🛒 *Pilih Kategori Produk:*",
                parse_mode="Markdown",
                reply_markup=kategori_keyboard(cats)
            )

    elif data == "back_main":
        await query.edit_message_text("Kembali ke menu utama.")
