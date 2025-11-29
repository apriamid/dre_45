import re


def _zero_pad_num(n, width=3):
    return str(n).zfill(width)

def _extract_number_from_id(id_str):
    m = re.search(r'(\d+)$', str(id_str))
    return int(m.group(1)) if m else 0

def get_next_numeric_suffix_for_prefix(mongo, collection_name, id_field, prefix):
    col = mongo.db[collection_name]
    q = {id_field: {"$regex": f"^{re.escape(prefix)}\\d+$"}}
    docs = list(col.find(q, {id_field: 1}))
    maxn = 0
    for d in docs:
        v = d.get(id_field) or ""
        n = _extract_number_from_id(v)
        if n > maxn: maxn = n
    return maxn + 1

def generate_karyawan_id(mongo, coll_name, jabatan=None):
    """
    Generate ID unik berdasarkan huruf pertama jabatan.
    Misal: Manager -> M001, Kasir -> K001.
    Akan selalu cari nomor berikutnya agar tidak bentrok.
    """
    import re
    if jabatan and isinstance(jabatan, str) and jabatan.strip():
        prefix = jabatan.strip()[0].upper()
        if not re.match(r'[A-Z]', prefix):
            prefix = "K"
    else:
        prefix = "K"
    col = mongo.db[coll_name]
    q = {"_id": {"$regex": f"^{prefix}\\d+$"}}
    existing = list(col.find(q, {"_id": 1}))
    maxn = 0
    for d in existing:
        try:
            num = int(re.search(r'(\d+)$', d["_id"]).group(1))
            if num > maxn:
                maxn = num
        except:
            pass

    next_num = maxn + 1
    return f"{prefix}{str(next_num).zfill(3)}"

def generate_supplier_id(mongo, MONGODB_COLLECTION_SUPPLIER):
    next_num = get_next_numeric_suffix_for_prefix(mongo, MONGODB_COLLECTION_SUPPLIER, "_id", "SUP") 
    return "SUP" + _zero_pad_num(next_num)

def generate_pembelian_id(mongo, MONGODB_COLLLECTION_T_PEMBELIAN):
    next_num = get_next_numeric_suffix_for_prefix(mongo, MONGODB_COLLLECTION_T_PEMBELIAN, "id", "BLI")
    return "BLI" + _zero_pad_num(next_num)

def generate_produk_id_from_category(mongo, MONGODB_COLLECTION_PRODUCT, category):
    if not isinstance(category, str) or not category.strip():
        prefix = "PRD"
    else:
        letters = re.findall(r'[A-Za-z]', category)
        if len(letters) >= 3:
            prefix = ''.join(letters[:3]).upper()
        else:
            prefix = (''.join(letters).upper() + "XXX")[:3]
    next_num = get_next_numeric_suffix_for_prefix(mongo, MONGODB_COLLECTION_PRODUCT, "id", prefix)
    return prefix + _zero_pad_num(next_num)


