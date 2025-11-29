from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
import re

from common.mongo_connection import MongoConnection
from config import *

pembelian_bp = Blueprint("pembelian_bp", __name__)
mongo = MongoConnection(MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME)


def normalize(doc):
    """
    Mengubah struktur dokumen MongoDB menjadi JSON-friendly.

    Fungsi ini mengonversi ObjectId menjadi string serta
    mengonversi datetime menjadi format ISO agar dapat
    dikembalikan melalui API.
    Args:
        doc (dict): Dokumen pembelian dari database.
    Returns:
        dict: Dokumen yang sudah dinormalisasi untuk JSON.
    """
    if not doc:
        return doc
    d = dict(doc)
    if isinstance(d.get("_id"), ObjectId):
        d["_id"] = str(d["_id"])
    for k, v in list(d.items()):
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


def generate_pembelian_id():
    """
    Menghasilkan ID unik untuk transaksi pembelian.

    Format ID:
        PB001, PB002, PB003, ...
    Algoritma:
        - Mencari semua dokumen dengan pola ID "PBxxx".
        - Mengambil angka terbesar.
        - Menambahkan +1.
    Returns:
        str: ID pembelian berikutnya.
    """
    coll = mongo.db[MONGODB_COLLECTION_T_PEMBELIAN]
    docs = coll.find({"_id": {"$regex": "^PB[0-9]{3,}$"}}, {"_id": 1})
    max_num = 0
    for d in docs:
        _id = d.get("_id") or ""
        m = re.match(r"PB0*([0-9]+)$", _id)
        if m:
            try:
                n = int(m.group(1))
                if n > max_num:
                    max_num = n
            except:
                continue
    return f"PB{max_num+1:03d}"


def find_max_kode_for_prefix(prefix):
    """
    Menemukan kode produk tertinggi berdasarkan prefix kategori.
    Prefix contoh:
        - "DET" → DET001, DET002
        - "MIN" → MIN001, MIN002
    Args:
        prefix (str): Tiga huruf pertama kategori produk.
    Returns:
        int: Nomor terbesar yang ditemukan pada kode produk dengan prefix tersebut.
    """
    prefix_esc = re.escape(prefix)
    regex = re.compile(rf"^{prefix_esc}0*([0-9]+)$", re.IGNORECASE)
    max_num = 0

    for doc in mongo.db[MONGODB_COLLECTION_T_PEMBELIAN].find({}, {"daftar_item": 1}):
        for it in doc.get("daftar_item") or []:
            kd = it.get("kode_produk") or ""
            m = regex.match(kd)
            if m:
                n = int(m.group(1))
                if n > max_num:
                    max_num = n

    for p in mongo.db[MONGODB_COLLECTION_PRODUCT].find(
        {"kode_produk": {"$regex": f"^{prefix_esc}0*[0-9]+$", "$options": "i"}}, {"kode_produk": 1}
    ):
        kd = p.get("kode_produk") or ""
        m = regex.match(kd)
        if m:
            n = int(m.group(1))
            if n > max_num:
                max_num = n

    return max_num


def generate_kode_server_side(kategori, used_local_counters):
    """
    Membuat kode produk berdasarkan kategori (prefix tiga huruf).
    Format:
        {PREFIX}{003}
        Contoh: DET → DET001, DET002, dst.
    Args:
        kategori (str): Nama kategori produk.
        used_local_counters (dict): Counter sementara untuk prefix tertentu.
    Returns:
        str: Kode produk unik berdasarkan kategori.
    """
    pref = (kategori or "").strip()[0:3].upper() or "XXX"
    db_max = find_max_kode_for_prefix(pref)
    local_used = used_local_counters.get(pref, 0)
    next_num = db_max + local_used + 1
    used_local_counters[pref] = local_used + 1
    return f"{pref}{str(next_num).zfill(3)}"


# ==================================================================================
#                                      GET 
# ==================================================================================
@pembelian_bp.route("", methods=["GET"])
def list_pembelian():
    """
    Mengambil seluruh data transaksi pembelian dan mengurutkannya
    berdasarkan tanggal terbaru.
    Returns:
        tuple: JSON list pembelian dan status HTTP.
    """
    try:
        docs = list(mongo.db[MONGODB_COLLECTION_T_PEMBELIAN].find().sort("tanggal_pembelian", -1))
        return jsonify([normalize(d) for d in docs]), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ================================================================================
#                                  CREATE
# ================================================================================
@pembelian_bp.route("", methods=["POST"])
def add_pembelian():
    """
    Membuat transaksi pembelian baru.

    Fitur:
        - Menghasilkan ID pembelian otomatis.
        - Mengolah daftar item & menghitung subtotal.
        - Menambahkan produk baru otomatis ke master produk jika belum ada.
        - Update stok produk.
        - Membuat log stok (pembelian).
    Body JSON:
        nama_supplier (str)
        daftar_item (list):
            - nama_produk
            - kategori
            - kode_produk (opsional)
            - jumlah
            - harga_beli
    Returns:
        tuple: JSON hasil penyimpanan pembelian.
    """
    try:
        payload = request.get_json(force=True)
        nama_supplier = payload.get("nama_supplier", "").strip()
        daftar_item = payload.get("daftar_item") or []

        if not nama_supplier:
            return jsonify({"success": False, "message": "Nama supplier wajib diisi"}), 400
        if not daftar_item:
            return jsonify({"success": False, "message": "Daftar item kosong"}), 400

        total = 0
        items = []
        used_local_counters = {}

        # VALIDASI & PERSIAPAN ITEM
        for idx, it in enumerate(daftar_item):
            nama = (it.get("nama_produk") or "").strip()
            kategori = (it.get("kategori") or "").strip()
            kode = (it.get("kode_produk") or "").strip()
            jumlah = int(it.get("jumlah") or 0)
            harga_beli = int(it.get("harga_beli") or 0)

            if not nama:
                return jsonify({"success": False, "message": f"Nama produk item {idx+1} tidak boleh kosong"}), 400
            if jumlah <= 0 or harga_beli <= 0:
                return jsonify({"success": False, "message": f"Jumlah & harga item {idx+1} harus > 0"}), 400

            if not kode:
                kode = generate_kode_server_side(kategori or "XXX", used_local_counters)

            subtotal = jumlah * harga_beli
            total += subtotal

            items.append({
                "kode_produk": kode,
                "nama_produk": nama,
                "kategori": kategori,
                "jumlah": jumlah,
                "harga_beli": harga_beli,
                "subtotal": subtotal
            })

        new_id = generate_pembelian_id()
        now = datetime.utcnow()

        mongo.db[MONGODB_COLLECTION_T_PEMBELIAN].insert_one({
            "_id": new_id,
            "nama_supplier": nama_supplier,
            "daftar_item": items,
            "total_pembelian": total,
            "tanggal_pembelian": now,
            "dibuat_oleh": payload.get("dibuat_oleh"),
            "created_at": now
        })

        prod_coll = mongo.db[MONGODB_COLLECTION_PRODUCT]
        stok_log = mongo.db[MONGODB_COLLECTION_STOK]

        for it in items:
            kode = it["kode_produk"]
            nama = it["nama_produk"]
            kategori = it["kategori"]
            jumlah = it["jumlah"]
            harga_beli = it["harga_beli"]

            update_doc = {
                "$set": {
                    "nama_produk": nama,
                    "kategori": kategori,
                    "kode_produk": kode,
                    "last_harga_beli": harga_beli,
                    "harga": it.get("harga_jual") or harga_beli * 1.2,
                    "updated_at": now
                },
                "$inc": {"stok": jumlah}
            }

            existing = prod_coll.find_one({"kode_produk": kode})
            if existing:
                prod_coll.update_one({"kode_produk": kode}, update_doc)
            else:
                prod_coll.update_one(
                    {"kode_produk": kode},
                    {
                        "$setOnInsert": {"_id": kode, "tanggal": now},
                        **update_doc
                    },
                    upsert=True
                )

            stok_log.insert_one({
                "id_produk": kode,
                "jenis": "pembelian",
                "jumlah": jumlah,
                "tanggal": now,
                "referensi": new_id,
                "store_id": "STR001"
            })

        return jsonify({
            "success": True,
            "message": "Pembelian berhasil disimpan dan produk diperbarui otomatis",
            "id": new_id
        }), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


# ========================================================================================
#                                       DELETE
# ========================================================================================
@pembelian_bp.route("/<string:bid>", methods=["DELETE"])
def delete_form_pembelian(bid):
    """
    Menghapus satu transaksi pembelian berdasarkan ID.
    Args:
        bid (str): ID pembelian (misal: PB001).
    Returns:
        tuple: JSON status penghapusan.
    """
    try:
        res = mongo.db[MONGODB_COLLECTION_T_PEMBELIAN].delete_one({"_id": bid})
        if not res.deleted_count:
            return jsonify({"success": False, "message": "Pembelian tidak ditemukan"}), 404
        return jsonify({"success": True, "message": "Pembelian dihapus"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
