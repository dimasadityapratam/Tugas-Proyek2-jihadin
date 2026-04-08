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

# ─── VALIDASI PEMBAYARAN ──────────────────────────────────────────────────────

async def validasi_pembayaran(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    pending = get_pending_payments()
    if not pending:
        await update.message.reply_text("💰 Tidak ada pembayaran yang menunggu konfirmasi.", reply_markup=admin_menu())
        return
    for p in pending:
        order = get_order(p["order_id"])
        items = get_order_items(p["order_id"])
        detail = format_order_detail(order, items)
        if p.get("bukti_foto"):
            await update.message.reply_photo(
                photo=p["bukti_foto"],
                caption=f"💳 *Bukti Pembayaran QRIS*\n\n{detail}",
                parse_mode="Markdown",
                reply_markup=konfirmasi_pembayaran_keyboard(p["order_id"])
            )
        else:
            await update.message.reply_text(
                f"💳 *Pembayaran Menunggu*\n\n{detail}",
                parse_mode="Markdown",
                reply_markup=konfirmasi_pembayaran_keyboard(p["order_id"])
            )

async def konfirmasi_pembayaran_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    data = query.data
    if data.startswith("konfpay_"):
        parts = data.split("_")
        order_id = parts[1]
        action = parts[2]
        order = get_order(order_id)
        if action == "lunas":
            update_payment(order_id, "Lunas")
            update_order_status(order_id, "Pesanan Disiapkan")
            try:
                await query.edit_message_caption(f"✅ Pembayaran `{order_id}` *dikonfirmasi lunas*.", parse_mode="Markdown")
            except Exception:
                await query.edit_message_text(f"✅ Pembayaran `{order_id}` *dikonfirmasi lunas*.", parse_mode="Markdown")
            if order:
                try:
                    await ctx.bot.send_message(order["user_id"], f"✅ Pembayaran kamu untuk `{order_id}` telah *dikonfirmasi*!\nPesanan sedang disiapkan.", parse_mode="Markdown")
                except Exception:
                    pass
        elif action == "tolak":
            update_payment(order_id, "Ditolak")
            try:
                await query.edit_message_caption(f"❌ Pembayaran `{order_id}` *ditolak*.", parse_mode="Markdown")
            except Exception:
                await query.edit_message_text(f"❌ Pembayaran `{order_id}` *ditolak*.", parse_mode="Markdown")
            if order:
                try:
                    await ctx.bot.send_message(order["user_id"], f"❌ Bukti pembayaran `{order_id}` ditolak. Silakan upload ulang dengan /bayar {order_id}", parse_mode="Markdown")
                except Exception:
                    pass

# ─── KELOLA PRODUK ────────────────────────────────────────────────────────────

async def kelola_produk(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    products = get_all_products_admin()
    lines = ["📦 *Daftar Produk:*\n"]
    for p in products:
        lines.append(f"• [{p['id']}] {p['nama']} - {format_rupiah(p['harga'])} (Stok: {p['stok']})")
    lines.append("\n/addprod - Tambah produk baru")
    lines.append("/editprod <ID> - Edit produk")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def addprod_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    cats = get_categories()
    cat_list = "\n".join([f"{c['id']}. {c['nama']}" for c in cats])
    ctx.user_data["addprod_step"] = "nama"
    ctx.user_data["addprod"] = {}
    await update.message.reply_text(f"📦 *Tambah Produk Baru*\n\nMasukkan nama produk:", parse_mode="Markdown")

async def addprod_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    step = ctx.user_data.get("addprod_step")
    if not step:
        return False
    text = update.message.text.strip()
    p = ctx.user_data.setdefault("addprod", {})

    if step == "nama":
        p["nama"] = text
        ctx.user_data["addprod_step"] = "harga"
        await update.message.reply_text("💰 Masukkan harga (angka saja):")
    elif step == "harga":
        try:
            p["harga"] = float(text.replace(".", "").replace(",", ""))
        except ValueError:
            await update.message.reply_text("❌ Harga tidak valid.")
            return True
        ctx.user_data["addprod_step"] = "stok"
        await update.message.reply_text("📦 Masukkan stok awal:")
    elif step == "stok":
        try:
            p["stok"] = int(text)
        except ValueError:
            await update.message.reply_text("❌ Stok tidak valid.")
            return True
        ctx.user_data["addprod_step"] = "deskripsi"
        await update.message.reply_text("📝 Masukkan deskripsi produk:")
    elif step == "deskripsi":
        p["deskripsi"] = text
        cats = get_categories()
        cat_list = "\n".join([f"{c['id']}. {c['nama']}" for c in cats])
        ctx.user_data["addprod_step"] = "kategori"
        await update.message.reply_text(f"📂 Pilih kategori (ketik nomor):\n{cat_list}")
    elif step == "kategori":
        try:
            p["category_id"] = int(text)
        except ValueError:
            await update.message.reply_text("❌ Nomor kategori tidak valid.")
            return True
        ctx.user_data["addprod_step"] = "foto"
        await update.message.reply_text("🖼️ Kirim foto produk (atau ketik '-' untuk skip):")
    elif step == "foto":
        foto = None
        if update.message.photo:
            foto = update.message.photo[-1].file_id
        p["foto"] = foto
        pid = add_product(p["nama"], p["harga"], p["stok"], p["deskripsi"], foto, p["category_id"])
        ctx.user_data["addprod_step"] = None
        await update.message.reply_text(f"✅ Produk *{p['nama']}* berhasil ditambahkan! (ID: {pid})", parse_mode="Markdown", reply_markup=admin_menu())
    return True

async def editprod_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not ctx.args:
        await update.message.reply_text("Gunakan: /editprod <ID_PRODUK>")
        return
    product_id = int(ctx.args[0])
    p = get_product(product_id)
    if not p:
        await update.message.reply_text("❌ Produk tidak ditemukan.")
        return
    await update.message.reply_text(
        f"✏️ *Edit Produk: {p['nama']}*\nHarga: {format_rupiah(p['harga'])}\nStok: {p['stok']}",
        parse_mode="Markdown",
        reply_markup=produk_admin_keyboard(product_id)
    )

async def editprod_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    data = query.data
    if data.startswith("editprod_"):
        parts = data.split("_")
        field = parts[1]
        product_id = int(parts[2])
        ctx.user_data["editprod_field"] = field
        ctx.user_data["editprod_id"] = product_id
        ctx.user_data["editprod_step"] = "input"
        prompts = {"harga": "💰 Masukkan harga baru:", "stok": "📦 Masukkan stok baru:", "deskripsi": "📝 Masukkan deskripsi baru:", "foto": "🖼️ Kirim foto baru:"}
        await query.edit_message_text(prompts.get(field, "Masukkan nilai baru:"))
    elif data.startswith("delprod_"):
        product_id = int(data.split("_")[1])
        delete_product(product_id)
        await query.edit_message_text("🗑️ Produk berhasil dihapus.")

async def editprod_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get("editprod_step") != "input":
        return False
    field = ctx.user_data.get("editprod_field")
    product_id = ctx.user_data.get("editprod_id")
    if field == "foto":
        if update.message.photo:
            val = update.message.photo[-1].file_id
            update_product(product_id, foto=val)
            await update.message.reply_text("✅ Foto produk diperbarui.", reply_markup=admin_menu())
        else:
            await update.message.reply_text("❌ Harap kirim foto.")
            return True
    else:
        text = update.message.text.strip()
        if field == "harga":
            update_product(product_id, harga=float(text.replace(".", "").replace(",", "")))
        elif field == "stok":
            update_product(product_id, stok=int(text))
        elif field == "deskripsi":
            update_product(product_id, deskripsi=text)
        await update.message.reply_text(f"✅ {field.capitalize()} produk diperbarui.", reply_markup=admin_menu())
    ctx.user_data["editprod_step"] = None
    return True

# ─── KELOLA STOK ──────────────────────────────────────────────────────────────

async def kelola_stok(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    products = get_all_products_admin()
    lines = ["📊 *Stok Produk:*\n"]
    for p in products:
        status = "⚠️" if p["stok"] <= 5 else "✅"
        lines.append(f"{status} [{p['id']}] {p['nama']}: {p['stok']} pcs")
    lines.append("\n/setstok <ID> <JUMLAH> - Update stok")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def setstok_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not ctx.args or len(ctx.args) < 2:
        await update.message.reply_text("Gunakan: /setstok <ID_PRODUK> <JUMLAH>")
        return
    try:
        product_id = int(ctx.args[0])
        jumlah = int(ctx.args[1])
    except ValueError:
        await update.message.reply_text("❌ Format salah.")
        return
    p = get_product(product_id)
    if not p:
        await update.message.reply_text("❌ Produk tidak ditemukan.")
        return
    update_product(product_id, stok=jumlah)
    await update.message.reply_text(f"✅ Stok *{p['nama']}* diperbarui menjadi {jumlah} pcs.", parse_mode="Markdown")

# ─── DATA CUSTOMER ────────────────────────────────────────────────────────────

async def data_customer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    users = get_all_users()
    if not users:
        await update.message.reply_text("👥 Belum ada customer.", reply_markup=admin_menu())
        return
    lines = [f"👥 *Data Customer ({len(users)} orang):*\n"]
    for u in users[:20]:
        lines.append(f"• {u['nama'] or '-'} | {u['no_hp'] or '-'} | @{u['username'] or '-'}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ─── LAPORAN PENJUALAN ────────────────────────────────────────────────────────

async def laporan_penjualan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    orders = laporan_harian(today)
    total_omzet = sum(o["total"] for o in orders)
    terlaris = barang_terlaris(5)
    top_customer = customer_terbanyak(5)

    lines = [
        f"📈 *Laporan Penjualan Hari Ini ({today})*\n",
        f"📦 Total Pesanan Selesai: {len(orders)}",
        f"💰 Total Omzet: {format_rupiah(total_omzet)}",
        "",
        "🏆 *Barang Terlaris:*",
    ]
    for i, b in enumerate(terlaris, 1):
        lines.append(f"{i}. {b['nama_produk']} - {b['total_terjual']} pcs")

    lines.append("\n👑 *Customer Terbanyak Belanja:*")
    for i, c in enumerate(top_customer, 1):
        lines.append(f"{i}. {c['nama']} - {c['total_order']} pesanan")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ─── BROADCAST ────────────────────────────────────────────────────────────────

async def broadcast_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    ctx.user_data["broadcast_step"] = "input"
    await update.message.reply_text(
        "📢 *Broadcast ke Semua Customer*\n\nKetik pesan yang ingin dikirim:",
        parse_mode="Markdown"
    )

async def broadcast_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get("broadcast_step") != "input":
        return False
    text = update.message.text.strip()
    ctx.user_data["broadcast_step"] = None
    users = get_all_users()
    success = 0
    fail = 0
    nama_toko = get_setting("nama_toko") or "Toko"
    for u in users:
        try:
            await ctx.bot.send_message(
                u["user_id"],
                f"📢 *Pesan dari {nama_toko}:*\n\n{text}",
                parse_mode="Markdown"
            )
            success += 1
        except Exception:
            fail += 1
    await update.message.reply_text(
        f"✅ Broadcast selesai.\nTerkirim: {success} | Gagal: {fail}",
        reply_markup=admin_menu()
    )
    return True

# ─── PENGATURAN TOKO ──────────────────────────────────────────────────────────

async def pengaturan_toko(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    settings_info = [
        ("nama_toko", "Nama Toko"),
        ("alamat_toko", "Alamat"),
        ("no_hp_toko", "No HP"),
        ("jam_buka", "Jam Buka"),
        ("ongkir", "Ongkir"),
        ("min_order", "Min Order"),
        ("gratis_ongkir_min", "Gratis Ongkir Min"),
        ("admin_pin", "PIN Admin"),
    ]
    lines = ["⚙️ *Pengaturan Toko:*\n"]
    for key, label in settings_info:
        val = get_setting(key) or "-"
        if key == "admin_pin":
            val = "****"
        lines.append(f"• {label}: {val}")
    lines += [
        "",
        "Perintah pengaturan:",
        "/set nama_toko <nilai>",
        "/set alamat_toko <nilai>",
        "/set no_hp_toko <nilai>",
        "/set jam_buka <nilai>",
        "/set ongkir <nilai>",
        "/set min_order <nilai>",
        "/set gratis_ongkir_min <nilai>",
        "/set admin_pin <nilai>",
        "/setqris - Upload foto QRIS baru",
    ]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def set_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not ctx.args or len(ctx.args) < 2:
        await update.message.reply_text("Gunakan: /set <key> <nilai>")
        return
    key = ctx.args[0]
    value = " ".join(ctx.args[1:])
    allowed_keys = ["nama_toko", "alamat_toko", "no_hp_toko", "jam_buka", "ongkir", "min_order", "gratis_ongkir_min", "admin_pin"]
    if key not in allowed_keys:
        await update.message.reply_text(f"❌ Key tidak valid. Pilihan: {', '.join(allowed_keys)}")
        return
    set_setting(key, value)
    await update.message.reply_text(f"✅ *{key}* diperbarui menjadi: {value if key != 'admin_pin' else '****'}", parse_mode="Markdown")

async def setqris_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    ctx.user_data["setqris_step"] = "foto"
    await update.message.reply_text("🖼️ Kirim foto QRIS baru:")

async def setqris_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get("setqris_step") != "foto":
        return False
    if not update.message.photo:
        await update.message.reply_text("❌ Harap kirim foto QRIS.")
        return True
    foto = update.message.photo[-1].file_id
    set_setting("qris_foto", foto)
    ctx.user_data["setqris_step"] = None
    await update.message.reply_text("✅ Foto QRIS berhasil diperbarui.", reply_markup=admin_menu())
    return True


