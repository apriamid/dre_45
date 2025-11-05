import re
from bson import ObjectId
from datetime import datetime

# ======================================================
#  SANITASI INPUT
# ======================================================

def sanitize_input(value):
    """Hilangkan tag HTML dan spasi berlebih"""
    if isinstance(value, str):
        v = re.sub(r'<[^>]*>', '', value)
        return v.strip()
    return value


def sanitize_dict(data):
    """Membersihkan seluruh dictionary input"""
    if not isinstance(data, dict):
        return {}
    return {k: sanitize_input(v) for k, v in data.items() if v is not None}


# ======================================================
# VALIDASI DASAR
# ======================================================
RE_NAME = re.compile(r'^[A-Za-zÀ-ÖØ-öø-ÿ\s]+$')
RE_PHONE = re.compile(r'^[0-9]+$')
RE_EMAIL_GMAIL = re.compile(r'^[\w\.-]+@gmail\.com$', re.IGNORECASE)

def validate_fields(data, required_fields):
    """Pastikan semua field wajib terisi"""
    for f in required_fields:
        if data.get(f) in [None, ""]:
            return False, f"Field '{f}' wajib diisi!"
    return True, None


def is_valid_string(value):
    """Hanya huruf dan spasi"""
    return isinstance(value, str) and bool(RE_NAME.match(value.strip()))


def is_valid_phone(value):
    """Nomor telepon hanya angka"""
    return isinstance(value, str) and bool(RE_PHONE.match(value.strip()))


def is_valid_email_gmail(email):
    """Email wajib @gmail.com"""
    return isinstance(email, str) and bool(RE_EMAIL_GMAIL.match(email.strip()))


def is_valid_number_positive(value):
    """Memastikan value adalah angka >= 0"""
    try:
        val = float(value)
        return val >= 0
    except (ValueError, TypeError):
        return False


def is_valid_number_strict_positive(value):
    """Memastikan value adalah angka > 0"""
    try:
        val = float(value)
        return val > 0
    except (ValueError, TypeError):
        return False


def parse_id_query(id_str):
    """Helper untuk query berdasarkan ObjectId atau ID string biasa"""
    if not id_str:
        return {}
    try:
        return {"_id": ObjectId(id_str)}
    except Exception:
        return {"id": id_str}


# ======================================================
# NORMALISASI OUTPUT
# ======================================================

def normalize_for_client(doc):
    """Ubah ObjectId ke string agar bisa dibaca di frontend"""
    if not isinstance(doc, dict):
        return doc
    new = dict(doc)
    _id = new.get("_id")
    if _id is not None:
        new["_id"] = str(_id)
        if "id" not in new:
            new["id"] = str(_id)
    return new


# ======================================================
# VALIDASI ENTITY SPESIFIK
# ======================================================

def validate_karyawan_input(data):
    try:
        nama = str(data.get("nama", "")).strip()
        jabatan = str(data.get("jabatan", "")).strip().capitalize()
        gaji = data.get("gaji", 0)

        if not nama or not jabatan:
            return False, "Nama dan jabatan wajib diisi"

        if jabatan not in ["Admin", "Kasir"]:
            return False, "Jabatan hanya boleh 'Admin' atau 'Kasir'"

        try:
            gaji = float(gaji)
            if gaji < 0:
                return False, "Gaji tidak boleh negatif"
        except ValueError:
            return False, "Gaji harus berupa angka"

        clean = {
            "nama": nama,
            "jabatan": jabatan,
            "gaji": gaji
        }

        return True, clean

    except Exception as e:
        return False, f"Kesalahan validasi: {str(e)}"


# ---------- PRODUK ----------
def validate_produk_input(data):
    data = sanitize_dict(data)
    nama = data.get("nama_produk", "")
    kategori = data.get("kategori", "")
    stok = data.get("stok", 0)
    harga = data.get("harga", 0)

    if not is_valid_string(nama):
        return False, "Nama produk hanya boleh huruf dan spasi."
    if not is_valid_string(kategori):
        return False, "Kategori hanya boleh huruf dan spasi."

    try:
        stok = int(stok)
        if stok < 0:
            raise ValueError()
    except Exception:
        return False, "Stok harus berupa integer positif."

    if not is_valid_number_positive(harga):
        return False, "Harga harus angka >= 0."

    data["stok"] = stok
    data["harga"] = float(harga)
    return True, data


# ---------- SUPPLIER ----------
def validate_supplier_input(data):
    data = sanitize_dict(data)
    nama = data.get("nama_supplier", "")
    telp = data.get("no_telp", "")
    alamat = data.get("alamat", "")
    email = data.get("email", "")

    if not is_valid_string(nama):
        return False, "Nama supplier hanya boleh huruf dan spasi."
    if not is_valid_phone(telp):
        return False, "Nomor telepon hanya boleh angka."
    if not is_valid_email_gmail(email):
        return False, "Email harus berakhiran @gmail.com."

    return True, data


# ---------- PEMBELIAN ----------
def validate_pembelian_input(data):
    data = sanitize_dict(data)
    status = str(data.get("status", "")).strip().lower()
    items = data.get("items", [])
    total_beli = data.get("total_beli", 0)

    if status not in ["selesai", "ditunda"]:
        return False, "Status hanya boleh 'selesai' atau 'ditunda'."

    if not isinstance(items, list) or len(items) == 0:
        return False, "List barang (items) wajib berupa array dan tidak boleh kosong."

    total_calc = 0.0
    for idx, it in enumerate(items):
        try:
            qty = int(float(it.get("qty", 0)))
            harga_beli = float(it.get("harga_beli", 0))
            if qty < 0 or harga_beli < 0:
                raise ValueError()
            total_calc += qty * harga_beli
        except Exception:
            return False, f"Item ke-{idx+1}: qty dan harga_beli harus angka >= 0."

    # Jika total dikirim, cek valid
    try:
        if float(total_beli) < 0:
            return False, "Total pembelian tidak boleh negatif."
    except Exception:
        return False, "Total pembelian harus berupa angka."

    data["total_beli"] = total_calc
    data["status"] = status
    data["tanggal"] = datetime.utcnow()
    return True, data


# ======================================================
#  HELPER UNTUK VALIDASI ID
# ======================================================
def _zero_pad_num(n, width=3):
    return str(n).zfill(width)


def _extract_number_from_id(id_str):
    m = re.search(r'(\d+)$', str(id_str))
    return int(m.group(1)) if m else 0


def get_next_numeric_suffix_for_prefix(mongo, collection_name, id_field, prefix):
    """Cari suffix angka berikutnya dari ID tertentu (misal K001 -> K002)"""
    col = mongo.db[collection_name]
    q = {id_field: {"$regex": f"^{re.escape(prefix)}\\d+$"}}
    docs = list(col.find(q, {id_field: 1}))
    maxn = 0
    for d in docs:
        v = d.get(id_field) or ""
        n = _extract_number_from_id(v)
        if n > maxn:
            maxn = n
    return maxn + 1


def generate_karyawan_id(mongo, coll_name, jabatan=None):
    """Buat ID otomatis karyawan: default 'K001' dst, prefix huruf pertama jabatan jika ada"""
    try:
        if jabatan and isinstance(jabatan, str) and jabatan.strip():
            prefix = jabatan.strip()[0].upper()
            if not re.match(r'[A-Z]', prefix):
                prefix = "K"
        else:
            prefix = "K"
    except Exception:
        prefix = "K"

    next_num = get_next_numeric_suffix_for_prefix(mongo, coll_name, "id", prefix)
    return prefix + _zero_pad_num(next_num)


def generate_supplier_id(mongo, coll_name):
    next_num = get_next_numeric_suffix_for_prefix(mongo, coll_name, "id", "SUP")
    return "SUP" + _zero_pad_num(next_num)


def generate_pembelian_id(mongo, coll_name):
    next_num = get_next_numeric_suffix_for_prefix(mongo, coll_name, "id", "BLI")
    return "BLI" + _zero_pad_num(next_num)


def generate_produk_id_from_category(mongo, coll_name, category):
    """Prefix 3 huruf pertama kategori (uppercase), contoh 'Elektronik' -> 'ELE001'"""
    if not isinstance(category, str) or not category.strip():
        prefix = "PRD"
    else:
        letters = re.findall(r'[A-Za-z]', category)
        if len(letters) >= 3:
            prefix = ''.join(letters[:3]).upper()
        else:
            prefix = (''.join(letters).upper() + "XXX")[:3]
    next_num = get_next_numeric_suffix_for_prefix(mongo, coll_name, "id", prefix)
    return prefix + _zero_pad_num(next_num)
