import sqlite3
import os
from datetime import datetime

DB_PATH = "toko.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        nama TEXT,
        no_hp TEXT,
        alamat TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT NOT NULL,
        harga REAL NOT NULL,
        stok INTEGER DEFAULT 0,
        deskripsi TEXT,
        foto TEXT,
        category_id INTEGER,
        aktif INTEGER DEFAULT 1,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    );

    CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER UNIQUE,
        stok INTEGER DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        jumlah INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        user_id INTEGER,
        nama TEXT,
        alamat TEXT,
        no_hp TEXT,
        metode_pengambilan TEXT,
        metode_pembayaran TEXT,
        subtotal REAL,
        ongkir REAL DEFAULT 0,
        total REAL,
        status TEXT DEFAULT 'Menunggu Persetujuan Admin',
        catatan TEXT,
        tanggal TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        product_id INTEGER,
        nama_produk TEXT,
        harga REAL,
        jumlah INTEGER,
        subtotal REAL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );

    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE,
        metode TEXT,
        status TEXT DEFAULT 'Menunggu',
        bukti_foto TEXT,
        confirmed_at TEXT,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );

    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        user_id INTEGER,
        jenis TEXT,
        deskripsi TEXT,
        foto TEXT,
        status TEXT DEFAULT 'Menunggu',
        resolusi TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)

    # Seed kategori default
    categories = ["Sembako", "Minuman", "Snack", "Perabotan Rumah", "Gas & Air", "Listrik & Lampu", "Kebutuhan Harian"]
    for cat in categories:
        c.execute("INSERT OR IGNORE INTO categories (nama) VALUES (?)", (cat,))

    # Seed settings default
    import os
    from dotenv import load_dotenv
    load_dotenv()
    defaults = {
        "ongkir": os.getenv("ONGKIR_DEFAULT", "10000"),
        "min_order": os.getenv("MIN_ORDER_DEFAULT", "0"),
        "jam_buka": os.getenv("JAM_BUKA", "08:00 - 21:00"),
        "nama_toko": os.getenv("NAMA_TOKO", "Toko Berkah Jaya"),
        "alamat_toko": os.getenv("ALAMAT_TOKO", "Jl. Contoh No. 1, Kota Anda"),
        "no_hp_toko": os.getenv("NO_HP_TOKO", "08123456789"),
        "admin_pin": os.getenv("ADMIN_PIN", "1234"),
        "gratis_ongkir_min": "0",
        "qris_foto": "",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()

# ─── SETTINGS ────────────────────────────────────────────────────────────────

def get_setting(key):
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else None

def set_setting(key, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# ─── USERS ───────────────────────────────────────────────────────────────────

def upsert_user(user_id, username, nama=None):
    conn = get_conn()
    existing = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not existing:
        conn.execute("INSERT INTO users (user_id, username, nama) VALUES (?,?,?)", (user_id, username, nama or username))
        conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_user(user_id, nama=None, no_hp=None, alamat=None):
    conn = get_conn()
    if nama:
        conn.execute("UPDATE users SET nama=? WHERE user_id=?", (nama, user_id))
    if no_hp:
        conn.execute("UPDATE users SET no_hp=? WHERE user_id=?", (no_hp, user_id))
    if alamat:
        conn.execute("UPDATE users SET alamat=? WHERE user_id=?", (alamat, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── ADMIN ───────────────────────────────────────────────────────────────────

def is_admin(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM admins WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row is not None

def add_admin(user_id, username):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO admins (user_id, username) VALUES (?,?)", (user_id, username))
    conn.commit()
    conn.close()

# ─── CATEGORIES ──────────────────────────────────────────────────────────────

def get_categories():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_category(nama):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO categories (nama) VALUES (?)", (nama,))
    conn.commit()
    conn.close()

# ─── PRODUCTS ────────────────────────────────────────────────────────────────

def get_products(category_id=None, search=None):
    conn = get_conn()
    query = "SELECT p.*, c.nama as kategori FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.aktif=1"
    params = []
    if category_id:
        query += " AND p.category_id=?"
        params.append(category_id)
    if search:
        query += " AND p.nama LIKE ?"
        params.append(f"%{search}%")
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_product(product_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT p.*, c.nama as kategori FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.id=?",
        (product_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def add_product(nama, harga, stok, deskripsi, foto, category_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO products (nama, harga, stok, deskripsi, foto, category_id) VALUES (?,?,?,?,?,?)",
        (nama, harga, stok, deskripsi, foto, category_id)
    )
    pid = c.lastrowid
    conn.execute("INSERT OR REPLACE INTO stock (product_id, stok) VALUES (?,?)", (pid, stok))
    conn.commit()
    conn.close()
    return pid

def update_product(product_id, **kwargs):
    conn = get_conn()
    for k, v in kwargs.items():
        conn.execute(f"UPDATE products SET {k}=? WHERE id=?", (v, product_id))
    if "stok" in kwargs:
        conn.execute("INSERT OR REPLACE INTO stock (product_id, stok, updated_at) VALUES (?,?,datetime('now','localtime'))",
                     (product_id, kwargs["stok"]))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = get_conn()
    conn.execute("UPDATE products SET aktif=0 WHERE id=?", (product_id,))
    conn.commit()
    conn.close()

def get_all_products_admin():
    conn = get_conn()
    rows = conn.execute(
        "SELECT p.*, c.nama as kategori FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.aktif=1"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── CART ─────────────────────────────────────────────────────────────────────

def get_cart(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT c.*, p.nama, p.harga, p.stok, p.foto FROM cart c JOIN products p ON c.product_id=p.id WHERE c.user_id=?",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_to_cart(user_id, product_id, jumlah=1):
    conn = get_conn()
    existing = conn.execute("SELECT * FROM cart WHERE user_id=? AND product_id=?", (user_id, product_id)).fetchone()
    if existing:
        conn.execute("UPDATE cart SET jumlah=jumlah+? WHERE user_id=? AND product_id=?", (jumlah, user_id, product_id))
    else:
        conn.execute("INSERT INTO cart (user_id, product_id, jumlah) VALUES (?,?,?)", (user_id, product_id, jumlah))
    conn.commit()
    conn.close()

def remove_from_cart(user_id, product_id):
    conn = get_conn()
    conn.execute("DELETE FROM cart WHERE user_id=? AND product_id=?", (user_id, product_id))
    conn.commit()
    conn.close()

def clear_cart(user_id):
    conn = get_conn()
    conn.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

# ─── ORDERS ──────────────────────────────────────────────────────────────────

def generate_order_id():
    now = datetime.now()
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) as c FROM orders WHERE tanggal LIKE ?", (f"{now.strftime('%Y-%m-%d')}%",)).fetchone()["c"]
    conn.close()
    return f"INV{now.strftime('%Y%m%d')}{str(count+1).zfill(4)}"

def create_order(user_id, nama, alamat, no_hp, metode_pengambilan, metode_pembayaran, subtotal, ongkir, total, catatan=""):
    order_id = generate_order_id()
    conn = get_conn()
    conn.execute(
        "INSERT INTO orders (order_id,user_id,nama,alamat,no_hp,metode_pengambilan,metode_pembayaran,subtotal,ongkir,total,catatan) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (order_id, user_id, nama, alamat, no_hp, metode_pengambilan, metode_pembayaran, subtotal, ongkir, total, catatan)
    )
    conn.commit()
    conn.close()
    return order_id

def add_order_items(order_id, items):
    conn = get_conn()
    for item in items:
        conn.execute(
            "INSERT INTO order_items (order_id,product_id,nama_produk,harga,jumlah,subtotal) VALUES (?,?,?,?,?,?)",
            (order_id, item["product_id"], item["nama"], item["harga"], item["jumlah"], item["harga"]*item["jumlah"])
        )
        # Kurangi stok
        conn.execute("UPDATE products SET stok=stok-? WHERE id=?", (item["jumlah"], item["product_id"]))
        conn.execute("UPDATE stock SET stok=stok-?, updated_at=datetime('now','localtime') WHERE product_id=?",
                     (item["jumlah"], item["product_id"]))
    conn.commit()
    conn.close()

def get_order(order_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_order_items(order_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_user_orders(user_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM orders WHERE user_id=? ORDER BY tanggal DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_orders(status=None):
    conn = get_conn()
    if status:
        rows = conn.execute("SELECT * FROM orders WHERE status=? ORDER BY tanggal DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM orders ORDER BY tanggal DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_order_status(order_id, status):
    conn = get_conn()
    conn.execute("UPDATE orders SET status=? WHERE order_id=?", (status, order_id))
    conn.commit()
    conn.close()

# ─── PAYMENTS ────────────────────────────────────────────────────────────────

def create_payment(order_id, metode):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO payments (order_id, metode) VALUES (?,?)", (order_id, metode))
    conn.commit()
    conn.close()

def update_payment(order_id, status, bukti_foto=None):
    conn = get_conn()
    if bukti_foto:
        conn.execute("UPDATE payments SET status=?, bukti_foto=? WHERE order_id=?", (status, bukti_foto, order_id))
    else:
        conn.execute("UPDATE payments SET status=?, confirmed_at=datetime('now','localtime') WHERE order_id=?", (status, order_id))
    conn.commit()
    conn.close()

def get_payment(order_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM payments WHERE order_id=?", (order_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_pending_payments():
    conn = get_conn()
    rows = conn.execute(
        "SELECT p.*, o.user_id, o.nama, o.total FROM payments p JOIN orders o ON p.order_id=o.order_id WHERE p.status='Menunggu Konfirmasi'"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── COMPLAINTS ──────────────────────────────────────────────────────────────

def create_complaint(order_id, user_id, jenis, deskripsi, foto=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO complaints (order_id,user_id,jenis,deskripsi,foto) VALUES (?,?,?,?,?)",
        (order_id, user_id, jenis, deskripsi, foto)
    )
    conn.commit()
    conn.close()

def get_complaints(status=None):
    conn = get_conn()
    if status:
        rows = conn.execute("SELECT * FROM complaints WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM complaints ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_complaint(complaint_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM complaints WHERE id=?", (complaint_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_complaint(complaint_id, status, resolusi=None):
    conn = get_conn()
    if resolusi:
        conn.execute("UPDATE complaints SET status=?, resolusi=? WHERE id=?", (status, resolusi, complaint_id))
    else:
        conn.execute("UPDATE complaints SET status=? WHERE id=?", (status, complaint_id))
    conn.commit()
    conn.close()

# ─── LAPORAN ──────────────────────────────────────────────────────────────────

def laporan_harian(tanggal):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM orders WHERE status='Selesai' AND tanggal LIKE ?",
        (f"{tanggal}%",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def barang_terlaris(limit=5):
    conn = get_conn()
    rows = conn.execute(
        """SELECT nama_produk, SUM(jumlah) as total_terjual
           FROM order_items
           GROUP BY nama_produk
           ORDER BY total_terjual DESC
           LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def customer_terbanyak(limit=5):
    conn = get_conn()
    rows = conn.execute(
        """SELECT u.nama, COUNT(o.order_id) as total_order
           FROM orders o JOIN users u ON o.user_id=u.user_id
           WHERE o.status='Selesai'
           GROUP BY o.user_id
           ORDER BY total_order DESC
           LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
