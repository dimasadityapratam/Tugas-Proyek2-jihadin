from database import get_setting

def format_rupiah(amount):
    return f"Rp{amount:,.0f}".replace(",", ".")

def format_order_detail(order, items):
    metode = order["metode_pengambilan"]
    bayar = order["metode_pembayaran"]
    lines = [
        f"🧾 *Invoice: {order['order_id']}*",
        f"📅 Tanggal: {order['tanggal']}",
        f"👤 Nama: {order['nama']}",
        f"📱 No HP: {order['no_hp']}",
        f"📍 Alamat: {order['alamat']}",
        f"🚚 Pengambilan: {metode}",
        f"💳 Pembayaran: {bayar}",
        f"📊 Status: *{order['status']}*",
        "",
        "🛒 *Item Pesanan:*",
    ]
    for item in items:
        lines.append(f"  • {item['nama_produk']} x{item['jumlah']} = {format_rupiah(item['subtotal'])}")
    lines += [
        "",
        f"💰 Subtotal: {format_rupiah(order['subtotal'])}",
        f"🚚 Ongkir: {format_rupiah(order['ongkir'])}",
        f"💵 *Total: {format_rupiah(order['total'])}*",
    ]
    if order.get("catatan"):
        lines.append(f"📝 Catatan: {order['catatan']}")
    return "\n".join(lines)
