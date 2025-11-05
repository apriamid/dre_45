# blueprint/shift_bp.py (FINAL FIXED VERSION)
from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId

from common.mongo_connection import MongoConnection
from config import (
    MONGODB_CONNECTION_STRING,
    MONGODB_DATABASE_NAME,
    MONGODB_COLLECTION_SHIFT
)


shift_bp = Blueprint("shift_bp", __name__)
mongo = MongoConnection(MONGODB_CONNECTION_STRING, db_name=MONGODB_DATABASE_NAME)


# ============================================================
#              Ambil semua data shift (READ)
# ============================================================
@shift_bp.route("/all", methods=["GET"])
def get_all_shift_combined():
    try:
        shift_list = list(mongo.db[MONGODB_COLLECTION_SHIFT].find({}))
        for s in shift_list:
            s["_id"] = str(s["_id"])
            if "waktu_mulai" in s and s["waktu_mulai"]:
                s["waktu_mulai"] = s["waktu_mulai"].isoformat()
            if "waktu_selesai" in s and s["waktu_selesai"]:
                s["waktu_selesai"] = s["waktu_selesai"].isoformat()
        return jsonify(shift_list), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ============================================================
#                Auto open shift saat login
# ============================================================
@shift_bp.route("/auto_open", methods=["POST"])
def auto_open_shift():
    """
    Membuka shift otomatis ketika Admin atau Kasir login.
    Jika shift hari ini untuk user sudah ada dan masih 'aktif', maka tidak dibuat baru.
    """
    try:
        data = request.get_json(force=True)
        id_karyawan = data.get("id_karyawan")
        nama_kasir = data.get("nama_kasir")

        if not id_karyawan or not nama_kasir:
            return jsonify({"success": False, "message": "Data karyawan tidak lengkap"}), 400

        today_str = datetime.now().strftime("%Y-%m-%d")

        existing = mongo.db[MONGODB_COLLECTION_SHIFT].find_one({
            "id_karyawan": id_karyawan,
            "tanggal": today_str,
            "status": "aktif"
        })

        if existing:
            existing["_id"] = str(existing["_id"])
            return jsonify({"success": True, "message": "Shift hari ini sudah aktif", "data": existing}), 200

        shift_data = {
            "id_karyawan": id_karyawan,
            "nama_kasir": nama_kasir,
            "tanggal": today_str,
            "waktu_mulai": datetime.now(),
            "status": "aktif",
            "waktu_selesai": None
        }

        result = mongo.db[MONGODB_COLLECTION_SHIFT].insert_one(shift_data)
        shift_data["_id"] = str(result.inserted_id)

        return jsonify({"success": True, "message": "Shift otomatis dibuka", "data": shift_data}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
