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

# ─── CARI BARANG ──────────────────────────────────────────────────────────────

async def cari_barang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["search_active"] = True
    await update.message.reply_text("🔍 Ketik nama barang yang ingin dicari:")

async def proses_cari(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyword = update.message.text.strip()
    products = get_products(search=keyword)
    if not products:
        await update.message.reply_text(f"😔 Barang '{keyword}' tidak ditemukan.", reply_markup=main_menu())
    else:
        ctx.user_data["current_products"] = products
        await update.message.reply_text(
            f"🔍 Hasil pencarian '{keyword}':",
            reply_markup=produk_keyboard(products, page=0)
        )

# ─── KERANJANG ────────────────────────────────────────────────────────────────

async def show_keranjang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = get_cart(user_id)
    if not cart:
        await update.message.reply_text("🧺 Keranjang kamu kosong.", reply_markup=main_menu())
        return
    total = sum(i["harga"] * i["jumlah"] for i in cart)
    lines = ["🧺 *Keranjang Belanja:*\n"]
    for item in cart:
        lines.append(f"• {item['nama']} x{item['jumlah']} = {format_rupiah(item['harga']*item['jumlah'])}")
    lines.append(f"\n💰 *Total: {format_rupiah(total)}*")
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=cart_keyboard(cart)
    )

async def keranjang_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("delcart_"):
        product_id = int(data.split("_")[1])
        remove_from_cart(user_id, product_id)
        cart = get_cart(user_id)
        if not cart:
            await query.edit_message_text("🧺 Keranjang kamu sekarang kosong.")
            return
        total = sum(i["harga"] * i["jumlah"] for i in cart)
        lines = ["🧺 *Keranjang Belanja:*\n"]
        for item in cart:
            lines.append(f"• {item['nama']} x{item['jumlah']} = {format_rupiah(item['harga']*item['jumlah'])}")
        lines.append(f"\n💰 *Total: {format_rupiah(total)}*")
        await query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=cart_keyboard(cart))

    elif data == "clear_cart":
        clear_cart(user_id)
        await query.edit_message_text("🗑️ Keranjang telah dikosongkan.")

    elif data == "checkout":
        await query.edit_message_text("Lanjut ke checkout...")
        await _start_checkout(query.message, ctx, user_id)

# ─── CHECKOUT ─────────────────────────────────────────────────────────────────

async def checkout_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = get_cart(user_id)
    if not cart:
        await update.message.reply_text("🧺 Keranjang kamu kosong.", reply_markup=main_menu())
        return
    await _start_checkout(update.message, ctx, user_id)

async def _start_checkout(message, ctx, user_id):
    user = get_user(user_id)
    ctx.user_data["checkout"] = {}
    if user and user.get("nama"):
        ctx.user_data["checkout"]["nama"] = user["nama"]
        ctx.user_data["checkout"]["no_hp"] = user.get("no_hp", "")
        ctx.user_data["checkout"]["alamat"] = user.get("alamat", "")
    await message.reply_text(
        "📝 *Checkout*\n\nMasukkan nama penerima:",
        parse_mode="Markdown"
    )
    ctx.user_data["checkout_step"] = "nama"

async def checkout_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    step = ctx.user_data.get("checkout_step")
    if not step:
        return
    text = update.message.text.strip() if update.message.text else ""
    co = ctx.user_data.setdefault("checkout", {})

    if step == "nama":
        co["nama"] = text
        ctx.user_data["checkout_step"] = "hp"
        await update.message.reply_text("📱 Masukkan nomor HP:")
    elif step == "hp":
        co["no_hp"] = text
        ctx.user_data["checkout_step"] = "alamat"
        await update.message.reply_text("📍 Masukkan alamat lengkap:")
    elif step == "alamat":
        co["alamat"] = text
        ctx.user_data["checkout_step"] = "catatan"
        await update.message.reply_text("📝 Catatan tambahan (ketik '-' jika tidak ada):")
    elif step == "catatan":
        co["catatan"] = "" if text == "-" else text
        ctx.user_data["checkout_step"] = None
        await update.message.reply_text(
            "🚚 *Pilih metode pengambilan:*",
            parse_mode="Markdown",
            reply_markup=metode_pengambilan_keyboard()
        )

async def checkout_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    co = ctx.user_data.get("checkout", {})

    if data in ("pickup", "delivery"):
        co["metode_pengambilan"] = "Pickup" if data == "pickup" else "Delivery"
        ctx.user_data["checkout"] = co
        await query.edit_message_text(
            "💳 *Pilih metode pembayaran:*",
            parse_mode="Markdown",
            reply_markup=metode_pembayaran_keyboard()
        )

    elif data in ("pay_qris", "pay_cod"):
        co["metode_pembayaran"] = "QRIS" if data == "pay_qris" else "COD"
        cart = get_cart(user_id)
        if not cart:
            await query.edit_message_text("❌ Keranjang kosong.")
            return

        subtotal = sum(i["harga"] * i["jumlah"] for i in cart)
        min_order = get_min_order()
        if subtotal < min_order:
            await query.edit_message_text(f"❌ Minimum order {format_rupiah(min_order)}.")
            return

        ongkir = 0
        if co["metode_pengambilan"] == "Delivery":
            gratis_min = get_gratis_ongkir_min()
            ongkir = 0 if (gratis_min > 0 and subtotal >= gratis_min) else get_ongkir()

        total = subtotal + ongkir
        co["subtotal"] = subtotal
        co["ongkir"] = ongkir
        co["total"] = total

        # Buat order
        order_id = create_order(
            user_id=user_id,
            nama=co.get("nama", ""),
            alamat=co.get("alamat", ""),
            no_hp=co.get("no_hp", ""),
            metode_pengambilan=co["metode_pengambilan"],
            metode_pembayaran=co["metode_pembayaran"],
            subtotal=subtotal,
            ongkir=ongkir,
            total=total,
            catatan=co.get("catatan", "")
        )
        items = [{"product_id": i["product_id"], "nama": i["nama"], "harga": i["harga"], "jumlah": i["jumlah"]} for i in cart]
        add_order_items(order_id, items)
        create_payment(order_id, co["metode_pembayaran"])
        clear_cart(user_id)

        # Update profil user
        update_user(user_id, nama=co.get("nama"), no_hp=co.get("no_hp"), alamat=co.get("alamat"))

        order = get_order(order_id)
        order_items_list = get_order_items(order_id)
        detail = format_order_detail(order, order_items_list)

        await query.edit_message_text(
            f"✅ *Pesanan berhasil dibuat!*\n\n{detail}\n\n"
            f"⏳ Menunggu persetujuan admin...",
            parse_mode="Markdown"
        )

        # Notif ke semua admin
        await _notify_admins_new_order(ctx, order_id, detail)
        ctx.user_data["checkout"] = {}
        ctx.user_data["checkout_step"] = None

    elif data == "cancel_checkout":
        ctx.user_data["checkout"] = {}
        ctx.user_data["checkout_step"] = None
        await query.edit_message_text("❌ Checkout dibatalkan.")

async def _notify_admins_new_order(ctx, order_id, detail):
    admins = get_conn()
    rows = admins.execute("SELECT user_id FROM admins").fetchall()
    admins.close()
    order = get_order(order_id)
    for row in rows:
        try:
            await ctx.bot.send_message(
                chat_id=row["user_id"],
                text=f"🔔 *PESANAN BARU!*\n\n{detail}",
                parse_mode="Markdown",
                reply_markup=approve_order_keyboard(order_id)
            )
        except Exception:
            pass

# ─── PESANAN SAYA ─────────────────────────────────────────────────────────────

async def pesanan_saya(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    orders = get_user_orders(user_id)
    if not orders:
        await update.message.reply_text("📦 Kamu belum punya pesanan.", reply_markup=main_menu())
        return
    lines = ["📦 *Pesanan Saya:*\n"]
    for o in orders[:10]:
        lines.append(f"• `{o['order_id']}` - {status_with_emoji(o['status'])} - {format_rupiah(o['total'])}")
    lines.append("\nKetik /order <ID> untuk detail pesanan.")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=main_menu())

async def order_detail_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Gunakan: /order <ID_PESANAN>")
        return
    order_id = ctx.args[0]
    order = get_order(order_id)
    if not order or order["user_id"] != update.effective_user.id:
        await update.message.reply_text("❌ Pesanan tidak ditemukan.")
        return
    items = get_order_items(order_id)
    detail = format_order_detail(order, items)
    kb = None
    if order["status"] in ("Pesanan Diterima", "Pesanan Diambil"):
        kb = konfirmasi_order_keyboard(order_id)
    await update.message.reply_text(detail, parse_mode="Markdown", reply_markup=kb)

# ─── PEMBAYARAN ───────────────────────────────────────────────────────────────

async def pembayaran_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    orders = get_user_orders(user_id)
    pending = [o for o in orders if o["status"] == "Menunggu Pembayaran" and o["metode_pembayaran"] == "QRIS"]
    if not pending:
        await update.message.reply_text("💳 Tidak ada tagihan pembayaran QRIS yang menunggu.", reply_markup=main_menu())
        return
    lines = ["💳 *Tagihan Pembayaran QRIS:*\n"]
    for o in pending:
        lines.append(f"• `{o['order_id']}` - {format_rupiah(o['total'])}")
    lines.append("\nKetik /bayar <ID_PESANAN> untuk upload bukti bayar.")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def bayar_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Gunakan: /bayar <ID_PESANAN>")
        return
    order_id = ctx.args[0]
    order = get_order(order_id)
    if not order or order["user_id"] != update.effective_user.id:
        await update.message.reply_text("❌ Pesanan tidak ditemukan.")
        return
    if order["status"] != "Menunggu Pembayaran":
        await update.message.reply_text(f"Status pesanan: {order['status']}")
        return
    qris_foto = get_setting("qris_foto")
    if qris_foto:
        await update.message.reply_photo(
            photo=qris_foto,
            caption=f"📱 *Scan QRIS untuk membayar*\n\nTotal: *{format_rupiah(order['total'])}*\n\nSetelah bayar, klik tombol di bawah.",
            parse_mode="Markdown",
            reply_markup=sudah_bayar_keyboard(order_id)
        )
    else:
        await update.message.reply_text(
            f"💳 Total pembayaran: *{format_rupiah(order['total'])}*\n\nKlik tombol setelah bayar:",
            parse_mode="Markdown",
            reply_markup=sudah_bayar_keyboard(order_id)
        )

async def pembayaran_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("sudah_bayar_"):
        order_id = data.replace("sudah_bayar_", "")
        ctx.user_data["upload_bukti_order"] = order_id
        await query.edit_message_text(
            "📸 Silakan kirim foto bukti pembayaran QRIS kamu:"
        )

async def terima_bukti_bayar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    order_id = ctx.user_data.get("upload_bukti_order")
    if not order_id:
        return
    if not update.message.photo:
        await update.message.reply_text("❌ Harap kirim foto bukti pembayaran.")
        return
    foto = update.message.photo[-1].file_id
    update_payment(order_id, "Menunggu Konfirmasi", bukti_foto=foto)
    ctx.user_data["upload_bukti_order"] = None

    order = get_order(order_id)
    await update.message.reply_text(
        f"✅ Bukti pembayaran untuk `{order_id}` telah dikirim.\nMenunggu konfirmasi admin.",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    # Notif admin
    admins = get_conn()
    rows = admins.execute("SELECT user_id FROM admins").fetchall()
    admins.close()
    for row in rows:
        try:
            await ctx.bot.send_photo(
                chat_id=row["user_id"],
                photo=foto,
                caption=f"💳 *Bukti Pembayaran QRIS*\n\nOrder: `{order_id}`\nNama: {order['nama']}\nTotal: {format_rupiah(order['total'])}",
                parse_mode="Markdown",
                reply_markup=konfirmasi_pembayaran_keyboard(order_id)
            )
        except Exception:
            pass

# ─── KONFIRMASI & KOMPLAIN ────────────────────────────────────────────────────

async def order_action_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data.startswith("confirm_order_"):
        order_id = data.replace("confirm_order_", "")
        update_order_status(order_id, "Selesai")
        await query.edit_message_text(f"🎉 Pesanan `{order_id}` telah dikonfirmasi selesai. Terima kasih!", parse_mode="Markdown")
        # Notif admin
        admins = get_conn()
        rows = admins.execute("SELECT user_id FROM admins").fetchall()
        admins.close()
        for row in rows:
            try:
                await ctx.bot.send_message(row["user_id"], f"✅ Pesanan `{order_id}` dikonfirmasi selesai oleh customer.", parse_mode="Markdown")
            except Exception:
                pass

    elif data.startswith("complaint_"):
        order_id = data.replace("complaint_", "")
        ctx.user_data["complaint_order_id"] = order_id
        await query.edit_message_text(
            "🚨 *Laporkan Masalah*\n\nPilih jenis masalah:",
            parse_mode="Markdown",
            reply_markup=jenis_komplain_keyboard(order_id)
        )

    elif data.startswith("komp_"):
        parts = data.split("_")
        order_id = parts[1]
        jenis_map = {"kurang": "Barang Kurang", "salah": "Barang Salah", "rusak": "Barang Rusak", "lainnya": "Lainnya"}
        jenis = jenis_map.get(parts[2], "Lainnya")
        ctx.user_data["complaint_order_id"] = order_id
        ctx.user_data["complaint_jenis"] = jenis
        ctx.user_data["complaint_step"] = "desc"
        await query.edit_message_text(f"📝 Jelaskan masalah kamu ({jenis}):")

async def complaint_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    step = ctx.user_data.get("complaint_step")
    if not step:
        return
    if step == "desc":
        ctx.user_data["complaint_desc"] = update.message.text.strip()
        ctx.user_data["complaint_step"] = "foto"
        await update.message.reply_text("📸 Kirim foto bukti (atau ketik '-' jika tidak ada):")
    elif step == "foto":
        order_id = ctx.user_data.get("complaint_order_id")
        jenis = ctx.user_data.get("complaint_jenis")
        desc = ctx.user_data.get("complaint_desc")
        foto = None
        if update.message.photo:
            foto = update.message.photo[-1].file_id
        elif update.message.text != "-":
            await update.message.reply_text("❌ Harap kirim foto atau ketik '-'.")
            return
        create_complaint(order_id, update.effective_user.id, jenis, desc, foto)
        ctx.user_data["complaint_step"] = None
        await update.message.reply_text(
            f"✅ Komplain untuk pesanan `{order_id}` telah dikirim.\nAdmin akan segera menangani.",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        # Notif admin
        admins = get_conn()
        rows = admins.execute("SELECT user_id FROM admins").fetchall()
        admins.close()
        for row in rows:
            try:
                msg = f"🚨 *KOMPLAIN BARU*\nOrder: `{order_id}`\nJenis: {jenis}\nDeskripsi: {desc}"
                if foto:
                    await ctx.bot.send_photo(row["user_id"], foto, caption=msg, parse_mode="Markdown")
                else:
                    await ctx.bot.send_message(row["user_id"], msg, parse_mode="Markdown")
            except Exception:
                pass

