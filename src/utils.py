import re
from database import get_setting

def format_rupiah(amount):
    return f"Rp{amount:,.0f}".replace(",", ".")

def escape_md(text):
    """Escape karakter khusus Markdown v1 agar tidak merusak parsing."""
    if not text:
        return ""
    # Escape underscore dan karakter lain yang bisa merusak Markdown v1
    return str(text).replace("_", "\\_").replace("*", "\\*").replace("`", "\\`").replace("[", "\\[")

def format_order_detail(order, items):
    metode = order["metode_pengambilan"]
    bayar = order["metode_pembayaran"]
    lines = [
        f"🧾 *Invoice: {escape_md(order['order_id'])}*",
        f"📅 Tanggal: {escape_md(order['tanggal'])}",
        f"👤 Nama: {escape_md(order['nama'])}",
        f"📱 No HP: {escape_md(order['no_hp'])}",
        f"📍 Alamat: {escape_md(order['alamat'])}",
        f"🚚 Pengambilan: {escape_md(metode)}",
        f"💳 Pembayaran: {escape_md(bayar)}",
        f"📊 Status: *{escape_md(order['status'])}*",
        "",
        "🛒 *Item Pesanan:*",
    ]
    for item in items:
        lines.append(f"  • {escape_md(item['nama_produk'])} x{item['jumlah']} = {format_rupiah(item['subtotal'])}")
    lines += [
        "",
        f"💰 Subtotal: {format_rupiah(order['subtotal'])}",
        f"🚚 Ongkir: {format_rupiah(order['ongkir'])}",
        f"💵 *Total: {format_rupiah(order['total'])}*",
    ]
    if order.get("catatan"):
        lines.append(f"📝 Catatan: {escape_md(order['catatan'])}")
    return "\n".join(lines)

def get_ongkir():
    val = get_setting("ongkir")
    return float(val) if val else 10000

def get_gratis_ongkir_min():
    val = get_setting("gratis_ongkir_min")
    return float(val) if val else 0

def get_min_order():
    val = get_setting("min_order")
    return float(val) if val else 0

STATUS_EMOJI = {
    "Menunggu Persetujuan Admin": "⏳",
    "Menunggu Pembayaran": "💳",
    "Pesanan Disiapkan": "📦",
    "Pesanan Diantar": "🚚",
    "Pesanan Diterima": "✅",
    "Pesanan Siap Diambil": "🏪",
    "Pesanan Diambil": "✅",
    "Selesai": "🎉",
    "Dibatalkan": "❌",
}

def status_with_emoji(status):
    return f"{STATUS_EMOJI.get(status, '📌')} {status}"
