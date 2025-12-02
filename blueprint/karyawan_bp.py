from flask import Blueprint, request, jsonify, g
from datetime import datetime
from bson import ObjectId
import bcrypt

from common.mongo_connection import MongoConnection
from common.validasi_sanitasi import validate_karyawan_input,is_valid_password
from common.id_generator import generate_karyawan_id
from config import (
    MONGODB_CONNECTION_STRING,
    MONGODB_DATABASE_NAME,
    MONGODB_COLLECTION_KARYAWAN,
    MONGODB_COLLECTION_USER,
)

karyawan_bp = Blueprint("karyawan_bp", __name__)
mongo = MongoConnection(MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME)

# =========================================================================
#                           GET ALL KARYAWAN
# =========================================================================
@karyawan_bp.route("", methods=["GET"])
def get_all_karyawan():
    """
    Mengambil seluruh data karyawan beserta username & role user terkait.

    Proses:
        - Mengambil semua data karyawan dari DB.
        - Konversi ObjectId menjadi string.
        - Mengambil data user (username & role) berdasarkan id_karyawan.
        - Menggabungkan hasil ke dalam satu respons.

    Returns:
        tuple: JSON list karyawan dan status HTTP.
    """
    try:
        data = []
        karyawans = list(mongo.db[MONGODB_COLLECTION_KARYAWAN].find())

        for k in karyawans:
            if isinstance(k.get("_id"), ObjectId):
                k["_id"] = str(k["_id"])

            user = mongo.db[MONGODB_COLLECTION_USER].find_one(
                {"id_karyawan": k["_id"]},
                {"_id": 0, "username": 1, "role": 1}
            )
            k["username"] = user.get("username") if user else None
            k["role"] = user.get("role") if user else None

            data.append(k)

        return jsonify(data), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@karyawan_bp.route("", methods=["POST"])
def add_karyawan():
    """
    Menambahkan karyawan baru beserta akun user opsional.
    ... [Dokumentasi dan logika validasi input/role lainnya tetap sama] ...
    """
    try:
        data = request.get_json(force=True)
        valid, clean = validate_karyawan_input(data)

        if not valid:
            return jsonify({"success": False, "message": clean}), 400

        user_role = getattr(g, "role", "superadmin").lower()
        jabatan = clean.get("jabatan", "").capitalize()

        if jabatan not in ["Admin", "Kasir"]:
            return jsonify({"success": False, "message": "Role tidak valid. Hanya Admin atau Kasir"}), 400

        if user_role == "admin" and jabatan.lower() == "admin":
            return jsonify({
                "success": False,
                "message": "Admin tidak diizinkan menambah pengguna dengan jabatan Admin."
            }), 403

        new_id = generate_karyawan_id(mongo, MONGODB_COLLECTION_KARYAWAN, jabatan)

        clean["_id"] = new_id
        clean["status_aktif"] = True
        clean["tanggal_dibuat"] = datetime.utcnow()
        clean["tanggal_diperbarui"] = datetime.utcnow()

        mongo.db[MONGODB_COLLECTION_KARYAWAN].insert_one(clean)

        username = data.get("username")
        password = data.get("password")

        if username and password:
            is_valid, msg = is_valid_password(password)
            if not is_valid:
                mongo.db[MONGODB_COLLECTION_KARYAWAN].delete_one({"_id": new_id}) 
                return jsonify({"success": False, "message": msg}), 400
            
            if mongo.db[MONGODB_COLLECTION_USER].find_one({"username": username}):
                mongo.db[MONGODB_COLLECTION_KARYAWAN].delete_one({"_id": new_id}) 
                return jsonify({"success": False, "message": "Username sudah digunakan"}), 400

            hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            mongo.db[MONGODB_COLLECTION_USER].insert_one({
                "id_karyawan": new_id,
                "username": username,
                "password": hashed_pw,
                "role": jabatan.lower(),
                "aktif": True,
                "created_at": datetime.utcnow()
            })

        return jsonify({"success": True, "message": "Karyawan berhasil ditambahkan"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
# ==========================================================
#                       UPDATE
# ==========================================================
@karyawan_bp.route("/<string:kid>", methods=["PUT"])
def update_karyawan(kid):
    """
    Memperbarui data karyawan dan role user terkait.
    ... [Dokumentasi dan logika validasi input/role lainnya tetap sama] ...
    """
    try:
        data = request.get_json(force=True)
        valid, clean = validate_karyawan_input(data)

        if not valid:
            return jsonify({"success": False, "message": clean}), 400

        user_role = getattr(g, "role", "superadmin").lower()
        jabatan_baru = clean.get("jabatan", "").capitalize()

        target = mongo.db[MONGODB_COLLECTION_KARYAWAN].find_one({"_id": kid})
        if not target:
            return jsonify({"success": False, "message": "Karyawan tidak ditemukan"}), 404

        jabatan_lama = target.get("jabatan", "").capitalize()

        if user_role == "admin":
            if jabatan_lama == "Admin":
                return jsonify({"success": False, "message": "Admin tidak dapat mengubah data sesama Admin"}), 403
            if jabatan_baru == "Admin":
                return jsonify({"success": False, "message": "Admin tidak dapat mengubah jabatan menjadi Admin"}), 403
       
        password = data.get("password")
        if password:
            is_valid, msg = is_valid_password(password)
            if not is_valid:
                return jsonify({"success": False, "message": msg}), 400
            
            hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            mongo.db[MONGODB_COLLECTION_USER].update_one(
                {"id_karyawan": kid},
                {"$set": {"password": hashed_pw}}
            )

        clean["tanggal_diperbarui"] = datetime.utcnow()

        mongo.db[MONGODB_COLLECTION_KARYAWAN].update_one({"_id": kid}, {"$set": clean})

        # Update role user (jika jabatan berubah)
        mongo.db[MONGODB_COLLECTION_USER].update_one(
            {"id_karyawan": kid},
            {"$set": {"role": jabatan_baru.lower()}}
        )

        return jsonify({"success": True, "message": "Karyawan berhasil diperbarui"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ========================================================================================
#                                   DELETE
# ========================================================================================
@karyawan_bp.route("/<string:kid>", methods=["DELETE"])
def delete_karyawan(kid):
    """
    Menghapus data karyawan dan user terkait.
    Ketentuan:
        - Admin tidak boleh menghapus Admin lainnya.
        - Jika data karyawan tidak ditemukan → error 404.
        - Menghapus data di tabel karyawan & user sekaligus.
    Args:
        kid (str): ID karyawan (contoh: K001).

    Returns:
        tuple: JSON pesan status.
    """
    try:
        user_role = getattr(g, "role", "superadmin").lower()

        doc = mongo.db[MONGODB_COLLECTION_KARYAWAN].find_one({"_id": kid})
        if not doc:
            return jsonify({"success": False, "message": "Karyawan tidak ditemukan"}), 404

        if user_role == "admin" and doc.get("jabatan", "").lower() == "admin":
            return jsonify({"success": False, "message": "Admin tidak dapat menghapus sesama Admin"}), 403

        mongo.db[MONGODB_COLLECTION_KARYAWAN].delete_one({"_id": kid})
        mongo.db[MONGODB_COLLECTION_USER].delete_one({"id_karyawan": kid})

        return jsonify({"success": True, "message": "Karyawan berhasil dihapus"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
