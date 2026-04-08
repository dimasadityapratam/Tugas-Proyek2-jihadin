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