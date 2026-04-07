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
    from config import ONGKIR_DEFAULT, MIN_ORDER_DEFAULT, JAM_BUKA, NAMA_TOKO, ALAMAT_TOKO, NO_HP_TOKO, ADMIN_PIN
    defaults = {
        "ongkir": str(ONGKIR_DEFAULT),
        "min_order": str(MIN_ORDER_DEFAULT),
        "jam_buka": JAM_BUKA,
        "nama_toko": NAMA_TOKO,
        "alamat_toko": ALAMAT_TOKO,
        "no_hp_toko": NO_HP_TOKO,
        "admin_pin": ADMIN_PIN,
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