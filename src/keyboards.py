from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# ─── MAIN MENU CLIENT (Inline - langsung tampil di chat) ──────────────────────

def main_menu_inline():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Lihat Katalog", callback_data="menu_katalog"),
         InlineKeyboardButton("🔍 Cari Barang", callback_data="menu_cari")],
        [InlineKeyboardButton("🧺 Keranjang", callback_data="menu_keranjang"),
         InlineKeyboardButton("✅ Checkout", callback_data="menu_checkout")],
        [InlineKeyboardButton("📦 Pesanan Saya", callback_data="menu_pesanan"),
         InlineKeyboardButton("💳 Pembayaran", callback_data="menu_pembayaran")],
        [InlineKeyboardButton("🎁 Promo", callback_data="menu_promo"),
         InlineKeyboardButton("📞 Hubungi Admin", callback_data="menu_hubungi")],
    ])

# Tetap ada ReplyKeyboard sebagai fallback
def main_menu():
    keyboard = [
        [KeyboardButton("🛒 Lihat Katalog"), KeyboardButton("🔍 Cari Barang")],
        [KeyboardButton("🧺 Keranjang"), KeyboardButton("✅ Checkout")],
        [KeyboardButton("📦 Pesanan Saya"), KeyboardButton("💳 Pembayaran")],
        [KeyboardButton("🎁 Promo"), KeyboardButton("📞 Hubungi Admin")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False, is_persistent=True)

# ─── ADMIN MENU ───────────────────────────────────────────────────────────────

def admin_menu():
    keyboard = [
        [KeyboardButton("📥 Pesanan Masuk"), KeyboardButton("🔄 Update Status")],
        [KeyboardButton("📦 Kelola Produk"), KeyboardButton("📊 Kelola Stok")],
        [KeyboardButton("💰 Validasi Pembayaran"), KeyboardButton("👥 Data Customer")],
        [KeyboardButton("📈 Laporan Penjualan"), KeyboardButton("📢 Broadcast")],
        [KeyboardButton("⚙️ Pengaturan Toko"), KeyboardButton("🚨 Laporan Komplain")],
        [KeyboardButton("🚪 Keluar Admin")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False, is_persistent=True)

# ─── INLINE KEYBOARDS ─────────────────────────────────────────────────────────

def kategori_keyboard(categories):
    buttons = []
    row = []
    for i, cat in enumerate(categories):
        row.append(InlineKeyboardButton(cat["nama"], callback_data=f"cat_{cat['id']}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)

def produk_keyboard(products, page=0, per_page=5):
    start = page * per_page
    end = start + per_page
    chunk = products[start:end]
    buttons = []
    for p in chunk:
        stok_info = f"(Stok: {p['stok']})" if p['stok'] > 0 else "(Habis)"
        buttons.append([InlineKeyboardButton(f"{p['nama']} - Rp{p['harga']:,.0f} {stok_info}", callback_data=f"prod_{p['id']}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"page_{page-1}"))
    if end < len(products):
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"page_{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("🔙 Kembali ke Kategori", callback_data="back_katalog")])
    return InlineKeyboardMarkup(buttons)

def produk_detail_keyboard(product_id, stok):
    buttons = []
    if stok > 0:
        buttons.append([
            InlineKeyboardButton("➕ Tambah ke Keranjang", callback_data=f"addcart_{product_id}_1")
        ])
    buttons.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_produk")])
    return InlineKeyboardMarkup(buttons)

def cart_keyboard(cart_items):
    buttons = []
    for item in cart_items:
        buttons.append([InlineKeyboardButton(f"❌ Hapus {item['nama']}", callback_data=f"delcart_{item['product_id']}")])
    buttons.append([InlineKeyboardButton("🛒 Checkout", callback_data="checkout")])
    buttons.append([InlineKeyboardButton("🗑️ Kosongkan Keranjang", callback_data="clear_cart")])
    return InlineKeyboardMarkup(buttons)

def metode_pengambilan_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏪 Ambil di Toko", callback_data="pickup")],
        [InlineKeyboardButton("🚚 Delivery", callback_data="delivery")],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel_checkout")],
    ])

def metode_pembayaran_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 QRIS", callback_data="pay_qris")],
        [InlineKeyboardButton("💵 COD (Bayar di Tempat)", callback_data="pay_cod")],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel_checkout")],
    ])


