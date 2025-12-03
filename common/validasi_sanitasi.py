import re
from bson import ObjectId
# from datetime import datetime

# ========================================================================
#                           SANITASI INPUT
# ========================================================================

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

# ========================================================================
#                          VALIDASI DASAR
# ========================================================================

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
    """Memastikan value adalah angka >= 0 dan bukan string negatif seperti "-0"."""
    try:
        val = float(value)
        if val < 0:
            return False
        
        if val == 0 and isinstance(value, str) and value.strip().lstrip('+').lstrip('-').strip() == "0" and value.strip().startswith("-"):
             return False

        return True
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


# ========================================================================
#                          NORMALISASI OUTPUT
# ========================================================================

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

# ========================================================================
#                    VALIDASI KHUSUS (TERMASUK PASSWORD)
# ========================================================================

def is_valid_password(password):
    """
    Memvalidasi password sesuai ketentuan:
    - Minimal 6 karakter.
    - Mengandung setidaknya satu huruf besar (A–Z).
    
    Returns: (bool, str) -> (valid_status, message)
    """
    if not isinstance(password, str):
        return False, "Password harus berupa string."
    if len(password) < 6:
        return False, "Password minimal 6 karakter."
    if not re.search(r'[A-Z]', password):
        return False, "Password harus mengandung minimal satu huruf besar (A-Z)."

    return True, "Valid"
def validate_karyawan_input(data, required_fields=[]):
    try:
        nama = str(data.get("nama", "")).strip()
        jabatan = str(data.get("jabatan", "")).strip().capitalize()
        gaji_input = data.get("gaji", 0)
        is_valid, msg = validate_fields(data, required_fields) 
        if not is_valid:
            return False, msg

        if not nama or not jabatan:
            return False, "Nama dan jabatan wajib diisi"
        if jabatan not in ["Admin", "Kasir", "Superadmin"]:
            return False, "Jabatan hanya boleh 'Admin', 'Kasir', atau 'Superadmin'"

    
        if isinstance(gaji_input, str) and gaji_input.strip().lstrip('+').lstrip('-').strip() == "0" and gaji_input.strip().startswith("-"):
            return False, "Gaji harus berupa angka non-negatif"
        try:
            gaji = float(gaji_input)
            if gaji < 0:
                return False, "Gaji tidak boleh negatif"
        except ValueError:
            return False, "Gaji harus berupa angka"
            
        clean = {
            "nama": nama,
            "jabatan": jabatan,
            "gaji": gaji,
            "telepon": str(data.get("telepon", "")).strip(),
            "alamat": str(data.get("alamat", "")).strip()
        }
        return True, clean
    except Exception as e:
        return False, f"Kesalahan validasi: {str(e)}"
    
def validate_produk_input(data):
    data = sanitize_dict(data)
    nama = data.get("nama_produk", "")
    kategori = data.get("kategori", "")
    stok_input = data.get("stok", 0)
    harga_beli_input = data.get("harga_beli", 0)
    harga_jual_input = data.get("harga_jual", 0)

    if not nama or not kategori:
        return False, "Nama produk dan kategori wajib diisi."
    
    # Validasi Stok
    if not is_valid_number_positive(stok_input):
        return False, "Stok harus berupa angka non-negatif."
    
    # Validasi Harga Beli
    if not is_valid_number_positive(harga_beli_input):
        return False, "Harga beli harus berupa angka non-negatif."
    
    # Validasi Harga Jual
    if not is_valid_number_positive(harga_jual_input):
        return False, "Harga jual harus berupa angka non-negatif."

    try:
        clean = {
            "nama_produk": nama,
            "kategori": kategori,
            "stok": int(float(stok_input)),
            "harga_beli": float(harga_beli_input),
            "harga_jual": float(harga_jual_input),
            "deskripsi": data.get("deskripsi", ""),
            "status": str(data.get("status", "aktif")).lower()
        }
    except Exception:
        return False, "Terjadi kesalahan saat mengkonversi data numerik."

    return True, clean

# ========================================================================
#                          HELPER ID GENERATOR (ASUMSI ADA DI SINI)
# ========================================================================

def _zero_pad_num(num, length=3):
    return str(num).zfill(length)


def get_next_numeric_suffix_for_prefix(mongo, collection_name, id_field, prefix):
    """Cari suffix angka berikutnya dari ID tertentu (misal K001 -> K002)"""
    col = mongo.db[collection_name]
    q = {id_field: {"$regex": f"^{re.escape(prefix)}\\d+$"}}
    docs = list(col.find(q, {id_field: 1}))
    maxn = 0
    for d in docs:
        v = d.get(id_field) or ""
        # n = _extract_number_from_id(v)
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
