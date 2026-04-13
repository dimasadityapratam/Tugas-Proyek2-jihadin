import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_PIN = os.getenv("ADMIN_PIN", "1234")
ONGKIR_DEFAULT = int(os.getenv("ONGKIR_DEFAULT", "10000"))
MIN_ORDER_DEFAULT = int(os.getenv("MIN_ORDER_DEFAULT", "0"))
JAM_BUKA = os.getenv("JAM_BUKA", "08:00 - 21:00")
NAMA_TOKO = os.getenv("NAMA_TOKO", "Toko Berkah Jaya")
ALAMAT_TOKO = os.getenv("ALAMAT_TOKO", "Jl. Contoh No. 1, Kota Anda")
NO_HP_TOKO = os.getenv("NO_HP_TOKO", "08123456789")
