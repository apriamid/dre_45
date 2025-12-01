from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
import re

from common.mongo_connection import MongoConnection
from config import * # Diasumsikan MONGODB_COLLECTION_PRODUCT, MONGODB_COLLECTION_STOK, dll. ada di sini

pembelian_bp = Blueprint("pembelian_bp", __name__)
mongo = MongoConnection(MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME)


def normalize(doc):
    """
    Mengubah struktur dokumen MongoDB menjadi JSON-friendly.
    ...
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
    ...
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
    ...
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
    ...
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
    Membuat transaksi pembelian baru dengan validasi wajib isi yang ketat,
    menggunakan pesan kesalahan yang lebih umum.
    """
    try:
        payload = request.get_json(force=True)
        nama_supplier = payload.get("nama_supplier", "").strip()
        daftar_item = payload.get("daftar_item") or []
        dibuat_oleh = payload.get("dibuat_oleh", "").strip() 

        if not nama_supplier or not dibuat_oleh:
            return jsonify({"success": False, "message": "Field (Nama Supplier/Dibuat Oleh) wajib diisi"}), 400
        if not daftar_item:
            return jsonify({"success": False, "message": "Daftar item pembelian kosong"}), 400

        total = 0
        items = []
        used_local_counters = {}

        for idx, it in enumerate(daftar_item):
            nama = (it.get("nama_produk") or "").strip()
            kategori = (it.get("kategori") or "").strip()
            kode = (it.get("kode_produk") or "").strip() 
            
            try:
                jumlah = int(float(it.get("jumlah") or 0)) 
                harga_beli = int(float(it.get("harga_beli") or 0))
            except:
                return jsonify({"success": False, "message": "Field wajib diisi dan harus berupa angka "}), 400
            if not nama or not kategori or jumlah <= 0 or harga_beli <= 0:
                return jsonify({"success": False, "message": "Semua field Item wajib diisi dan harus bernilai positif."}), 400
            
            # Generate kode jika kosong
            if not kode:
                kode = generate_kode_server_side(kategori, used_local_counters)

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
            "dibuat_oleh": dibuat_oleh, 
            "created_at": now
        })

        prod_coll = mongo.db[MONGODB_COLLECTION_PRODUCT]
        stok_log = mongo.db[MONGODB_COLLECTION_STOK]

        for it in items:
            kode = it["kode_produk"]
            jumlah = it["jumlah"]
            harga_beli = it["harga_beli"]
            
            # Perhitungan Harga Jual Otomatis (Harga Beli + 40%)
            harga_jual_otomatis = harga_beli * 1.4

            update_doc = {
                "$set": {
                    "nama_produk": it["nama_produk"],
                    "kategori": it["kategori"],
                    "kode_produk": kode,
                    "last_harga_beli": harga_beli,
                    "harga": harga_jual_otomatis, 
                    "updated_at": now
                },
                "$inc": {"stok": jumlah}
            }

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
                "referensi": new_id
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
    ...
    """
    try:
        res = mongo.db[MONGODB_COLLECTION_T_PEMBELIAN].delete_one({"_id": bid})
        if not res.deleted_count:
            return jsonify({"success": False, "message": "Pembelian tidak ditemukan"}), 404
        return jsonify({"success": True, "message": "Pembelian dihapus"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500