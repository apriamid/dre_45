from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
from common.mongo_connection import MongoConnection
from common.validasi_sanitasi import validate_produk_input, normalize_for_client
from common.id_generator import generate_produk_id_from_category
from config import (
    MONGODB_CONNECTION_STRING,
    MONGODB_DATABASE_NAME,
    MONGODB_COLLECTION_PRODUCT,
)

produk_bp = Blueprint("produk_bp", __name__)
mongo = MongoConnection(connection_string=MONGODB_CONNECTION_STRING, db_name=MONGODB_DATABASE_NAME)


def build_flexible_query(identifier):
    """
    Membangun query fleksibel untuk mencari produk berdasarkan berbagai kemungkinan format ID.
    Args:
        identifier (str): Nilai ID atau ObjectId dalam bentuk string.
    Returns:
        dict or None: Query MongoDB menggunakan operator $or.
    """
    if not identifier:
        return None
    try:
        oid = ObjectId(identifier)
        return {"$or": [{"_id": oid}, {"_id": identifier}, {"id": identifier}]}
    except Exception:
        return {"$or": [{"_id": identifier}, {"id": identifier}]}


# ==========================================================
#                       READ ALL
# ==========================================================
@produk_bp.route("", methods=["GET"])
@produk_bp.route("/", methods=["GET"]) 
def get_all_produk():
    try:
        query = {}
        nama_produk_query = request.args.get("nama", None) 
        if nama_produk_query:
            query["nama_produk"] = nama_produk_query 

        docs = list(mongo.db[MONGODB_COLLECTION_PRODUCT].find(query))
        return jsonify([normalize_for_client(d) for d in docs]), 200
    except Exception as e:
        return jsonify({"success": False, "message": "Gagal mengambil data", "detail": str(e)}), 500


# ==========================================================
#                       READ BY ID
# ==========================================================
@produk_bp.route("/<string:pid>", methods=["GET"])
def get_produk(pid):
    """
    Mengambil detail satu produk berdasarkan ID.
    Args:
        pid (string): ID produk yang dicari.
    Returns:
        tuple: JSON produk (jika ditemukan) dan status HTTP.
    """
    try:
        q = build_flexible_query(pid)
        d = mongo.db[MONGODB_COLLECTION_PRODUCT].find_one(q)
        if not d:
            return jsonify({"success": False, "message": "Produk tidak ditemukan"}), 404
        return jsonify(normalize_for_client(d)), 200
    except Exception as e:
        return jsonify({"success": False, "message": "Server error", "detail": str(e)}), 500

# ==========================================================
#                          CREATE
# ==========================================================
@produk_bp.route("", methods=["POST"])
def add_produk():
    """
    Menambahkan produk baru ke database atau menambah stok jika produk sudah ada.
    """
    try:
        data = request.get_json(force=True)
        valid, clean = validate_produk_input(data) 
        if not valid:
            return jsonify({"success": False, "message": clean}), 400

        nama_produk = clean.get("nama_produk", "")
        stok_baru = int(clean.get("stok", 0)) 

        # 1. Cek produk 
        existing_product = mongo.db[MONGODB_COLLECTION_PRODUCT].find_one(
            {"nama_produk": nama_produk}
        )

        if existing_product:
            # Jika sudah ada, tambahkan stok 
            res = mongo.db[MONGODB_COLLECTION_PRODUCT].update_one(
                {"_id": existing_product["_id"]},
                {"$inc": {"stok": stok_baru}, "$set": {"tanggal_update": datetime.utcnow()}} 
            )
            return jsonify({
                "success": True, 
                "message": f"Stok produk '{nama_produk}' berhasil ditambahkan ({stok_baru} unit)",
                "updated_id": normalize_for_client(existing_product)["id"]
            }), 200

        else:
            category = clean.get("kategori", "")

            new_id = None
            for _ in range(1, 20):
                new_id = generate_produk_id_from_category(mongo, MONGODB_COLLECTION_PRODUCT, category)
                if not mongo.db[MONGODB_COLLECTION_PRODUCT].find_one({"_id": new_id}):
                    break
            else:
                return jsonify({"success": False, "message": "Gagal membuat ID unik"}), 500

            clean["_id"] = new_id
            clean["tanggal_dibuat"] = datetime.utcnow()
            clean["tanggal_update"] = datetime.utcnow()
            
            if 'harga_jual' not in clean: clean['harga_jual'] = 0
            if 'harga_beli' not in clean: clean['harga_beli'] = 0

            mongo.db[MONGODB_COLLECTION_PRODUCT].insert_one(clean)

            return jsonify({"success": True, "data": clean, "message": "Produk baru berhasil ditambahkan"}), 201
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": "Gagal memproses produk", "detail": str(e)}), 500


# ==========================================================
#                       UPDATE
# ==========================================================
@produk_bp.route("/<string:pid>", methods=["PUT"])
def update_produk(pid):
    """
    Memperbarui data produk berdasarkan ID.
    Args:
        pid (string): ID produk yang akan diperbarui.
    Body JSON:
        Field-field yang dapat diperbarui sesuai validasi input.
    Returns:
        tuple: JSON hasil update dan status HTTP.
    """
    try:
        q = build_flexible_query(pid)
        data = request.get_json(force=True)
        valid, clean = validate_produk_input(data)
        if not valid:
            return jsonify({"success": False, "message": clean}), 400

        clean.pop("_id", None)
        clean.pop("id", None)

        res = mongo.db[MONGODB_COLLECTION_PRODUCT].update_one(q, {"$set": clean})
        if res.matched_count == 0:
            return jsonify({"success": False, "message": "Produk tidak ditemukan"}), 404
        return jsonify({"success": True, "message": "Produk berhasil diperbarui"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": "Gagal memperbarui produk", "detail": str(e)}), 500


# ==========================================================
#                        DELETE
# ==========================================================
@produk_bp.route("/<string:pid>", methods=["DELETE"])
@produk_bp.route("", methods=["DELETE"])
def delete_produk(pid=None):
    """
    Menghapus produk berdasarkan ID yang dikirim
    melalui URL, parameter query, atau body JSON.
    Args:
        pid (string, optional): ID produk. Bisa None jika ID dikirim melalui body atau query.
    Returns:
        tuple: JSON hasil hapus dan status HTTP.
    """
    try:
        identifier = pid or request.args.get("id")
        if not identifier:
            body = request.get_json(silent=True) or {}
            identifier = body.get("id") or body.get("_id")

        if not identifier:
            return jsonify({"success": False, "message": "ID produk wajib diberikan"}), 400

        q = build_flexible_query(identifier) 
        res = mongo.db[MONGODB_COLLECTION_PRODUCT].delete_one(q)
        if res.deleted_count == 0:
            return jsonify({"success": False, "message": "Produk tidak ditemukan"}), 404
        return jsonify({"success": True, "message": "Produk berhasil dihapus"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Gagal menghapus produk: {str(e)}"}), 500