from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
from common.mongo_connection import MongoConnection
from config import *

penjualan_bp = Blueprint("penjualan_bp", __name__)
mongo = MongoConnection(MONGODB_CONNECTION_STRING, db_name=MONGODB_DATABASE_NAME)


def normalize(doc):
    """
    Mengubah dokumen MongoDB menjadi bentuk JSON-friendly.
    Args:
        doc (dict): Dokumen transaksi dari database.
    Returns:
        dict: Dokumen yang telah dikonversi, dengan ObjectId menjadi string dan
        datetime menjadi ISO format.
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


# ==========================================================
#                       GET PRODUK
# ==========================================================
@penjualan_bp.route("/", methods=["GET"])
def get_products():
    """
    Mengambil semua produk aktif dari master product.
    Returns:
        tuple: JSON berisi daftar produk aktif dan status HTTP.
    """
    data = list(mongo.db[MONGODB_COLLECTION_PRODUCT].find({"status": "aktif"}))
    for p in data:
        p["_id"] = str(p["_id"])
    return jsonify({"success": True, "data": data})


# ==========================================================
#                      AUTO GENERATE ID
# ==========================================================
@penjualan_bp.route("/nextid", methods=["GET"])
def get_nextid():
    """
    Menghasilkan ID transaksi berikutnya berdasarkan ID terakhir.
    Returns:
        tuple: JSON berisi next_id dan status HTTP.
    """
    last = mongo.db[MONGODB_COLLECTION_T_PENJUALAN].find_one(sort=[("_id", -1)])
    next_id = "TRX001"
    if last and "_id" in last and str(last["_id"]).startswith("TRX"):
        try:
            next_num = int(str(last["_id"])[3:]) + 1
            next_id = f"TRX{next_num:03}"
        except:
            pass
    return jsonify({"success": True, "next_id": next_id})


# ==========================================================
#                   CREATE TRANSAKSI PENJUALAN
# ==========================================================
@penjualan_bp.route("/create", methods=["POST"])
def create_penjualan():
    """
    Membuat transaksi penjualan baru, menghitung total, dan memperbarui stok.
    Body JSON:
        daftar_item (list): Daftar produk yang dibeli.
        uang_diterima (float): Nominal uang pembayaran.
    Returns:
        tuple: JSON berisi ID transaksi dan total, atau pesan error.
    """
    try:
        data = request.get_json(force=True)
        daftar_item = data.get("daftar_item", [])
        if not daftar_item:
            return jsonify({"success": False, "message": "Tidak ada item"}), 400

        uang_diterima = float(data.get("uang_diterima", 0))
        total = sum(float(i.get("subtotal", 0)) for i in daftar_item)

        if uang_diterima < total:
            return jsonify({"success": False, "message": "Uang kurang"}), 400

        last = mongo.db[MONGODB_COLLECTION_T_PENJUALAN].find_one(sort=[("_id", -1)])
        next_id = "TRX001"
        if last and "_id" in last and str(last["_id"]).startswith("TRX"):
            try:
                next_num = int(str(last["_id"])[3:]) + 1
                next_id = f"TRX{next_num:03}"
            except:
                pass

        trx_doc = {
            "_id": next_id,
            "tanggal": datetime.utcnow(),
            "id_kasir": "K001",
            "items": daftar_item,
            "total": total,
            "pembayaran": {
                "metode": "tunai",
                "bayar": uang_diterima,
                "kembalian": uang_diterima - total
            },
            "status": "selesai",
            "store_id": "STR001"
        }

        mongo.db[MONGODB_COLLECTION_T_PENJUALAN].insert_one(trx_doc)

        # Update stok + log stok
        for item in daftar_item:
            pid = item.get("kode_produk")
            qty = int(item.get("qty", 0))
            if pid:
                mongo.db[MONGODB_COLLECTION_PRODUCT].update_one({"_id": pid}, {"$inc": {"stok": -qty}})
                log_count = mongo.db[MONGODB_COLLECTION_STOK].count_documents({})
                log_id = f"LOG{log_count + 1:03}"
                mongo.db[MONGODB_COLLECTION_STOK].insert_one({
                    "_id": log_id,
                    "id_produk": pid,
                    "jenis": "penjualan",
                    "jumlah": -qty,
                    "tanggal": datetime.utcnow(),
                    "referensi": next_id,
                    "store_id": "STR001"
                })

        return jsonify({"success": True, "id": next_id, "total": total}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==========================================================
#                     HISTORY TRANSAKSI
# ==========================================================
@penjualan_bp.route("/history", methods=["GET"])
def history_penjualan():
    """
    Mengambil seluruh riwayat transaksi penjualan.
    Returns:
        tuple: JSON berisi list transaksi yang telah dinormalisasi.
    """
    data = list(mongo.db[MONGODB_COLLECTION_T_PENJUALAN].find().sort("tanggal", -1))
    return jsonify({"success": True, "data": [normalize(d) for d in data]})


# ==========================================================
#                       DETAIL STRUK 
# ==========================================================
@penjualan_bp.route("/<trx_id>", methods=["GET"])
def get_detail_struk(trx_id):
    """
    Mengambil detail struk berdasarkan ID transaksi.
    Args:
        trx_id (str): ID transaksi penjualan.
    Returns:
        tuple: JSON detail struk atau pesan error.
    """
    data = mongo.db[MONGODB_COLLECTION_T_PENJUALAN].find_one({"_id": trx_id})
    if not data:
        return jsonify({"success": False, "message": "Transaksi tidak ditemukan"}), 404
    return jsonify({"success": True, "data": normalize(data)})
