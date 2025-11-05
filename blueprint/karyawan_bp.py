# blueprint/karyawan_bp.py
from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
import bcrypt

from common.mongo_connection import MongoConnection
from common.validasi_sanitasi import validate_karyawan_input
from common.id_generator import generate_karyawan_id
from config import (
    MONGODB_CONNECTION_STRING,
    MONGODB_DATABASE_NAME,
    MONGODB_COLLECTION_KARYAWAN,
    MONGODB_COLLECTION_USER,
)

karyawan_bp = Blueprint("karyawan_bp", __name__)
mongo = MongoConnection(MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME)

# ==========================================================
# GET ALL KARYAWAN
# ==========================================================
@karyawan_bp.route("", methods=["GET"])
def get_all_karyawan():
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


# ==========================================================
# GET BY ID
# ==========================================================
@karyawan_bp.route("/<string:kid>", methods=["GET"])
def get_karyawan(kid):
    try:
        doc = mongo.db[MONGODB_COLLECTION_KARYAWAN].find_one({"_id": kid})
        if not doc:
            return jsonify({"success": False, "message": "Karyawan tidak ditemukan"}), 404

        if isinstance(doc.get("_id"), ObjectId):
            doc["_id"] = str(doc["_id"])

        user = mongo.db[MONGODB_COLLECTION_USER].find_one(
            {"id_karyawan": kid},
            {"_id": 0, "username": 1, "role": 1}
        )
        if user:
            doc["username"] = user.get("username")
            doc["role"] = user.get("role")

        return jsonify(doc), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==========================================================
# CREATE (Tambah Karyawan + Akun Login)
# ==========================================================
@karyawan_bp.route("", methods=["POST"])
def add_karyawan():
    try:
        data = request.get_json(force=True)
        valid, clean = validate_karyawan_input(data)
        if not valid:
            return jsonify({"success": False, "message": clean}), 400

        jabatan = clean.get("jabatan", "").capitalize()
        if jabatan not in ["Admin", "Kasir"]:
            return jsonify({"success": False, "message": "Role tidak valid. Hanya Admin atau Kasir"}), 400

        # buat id baru
        new_id = generate_karyawan_id(mongo, MONGODB_COLLECTION_KARYAWAN, jabatan)
        clean["_id"] = new_id
        clean["status_aktif"] = True
        clean["tanggal_dibuat"] = datetime.utcnow()
        clean["tanggal_diperbarui"] = datetime.utcnow()

        mongo.db[MONGODB_COLLECTION_KARYAWAN].insert_one(clean)

        # buat akun login jika dikirim username & password
        username = data.get("username")
        password = data.get("password")

        if username and password:
            if mongo.db[MONGODB_COLLECTION_USER].find_one({"username": username}):
                return jsonify({"success": False, "message": "Username sudah digunakan"}), 400

            hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            user_doc = {
                "id_karyawan": new_id,
                "username": username,
                "password": hashed_pw,
                "role": jabatan.lower(),  # admin / kasir
                "aktif": True,
                "created_at": datetime.utcnow()
            }
            mongo.db[MONGODB_COLLECTION_USER].insert_one(user_doc)

        return jsonify({
            "success": True,
            "message": "Karyawan dan akun login berhasil ditambahkan",
            "data": clean
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==========================================================
# UPDATE (Update data karyawan + akun login)
# ==========================================================
@karyawan_bp.route("/<string:kid>", methods=["PUT"])
def update_karyawan(kid):
    try:
        data = request.get_json(force=True)
        valid, clean = validate_karyawan_input(data)
        if not valid:
            return jsonify({"success": False, "message": clean}), 400

        jabatan = clean.get("jabatan", "").capitalize()
        if jabatan not in ["Admin", "Kasir"]:
            return jsonify({"success": False, "message": "Role tidak valid. Hanya Admin atau Kasir"}), 400

        clean["tanggal_diperbarui"] = datetime.utcnow()
        mongo.db[MONGODB_COLLECTION_KARYAWAN].update_one({"_id": kid}, {"$set": clean})

        username = data.get("username")
        password = data.get("password")

        user = mongo.db[MONGODB_COLLECTION_USER].find_one({"id_karyawan": kid})
        if user:
            update_fields = {"role": jabatan.lower()}
            if username:
                update_fields["username"] = username
            if password:
                hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                update_fields["password"] = hashed_pw

            mongo.db[MONGODB_COLLECTION_USER].update_one({"id_karyawan": kid}, {"$set": update_fields})

        return jsonify({"success": True, "message": "Karyawan berhasil diperbarui"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==========================================================
#   DELETE         
# ==========================================================
@karyawan_bp.route("/<string:kid>", methods=["DELETE"])
def delete_karyawan(kid):
    try:
        doc = mongo.db[MONGODB_COLLECTION_KARYAWAN].find_one({"_id": kid})
        if not doc:
            return jsonify({"success": False, "message": "Karyawan tidak ditemukan"}), 404

        mongo.db[MONGODB_COLLECTION_KARYAWAN].delete_one({"_id": kid})
        mongo.db[MONGODB_COLLECTION_USER].delete_one({"id_karyawan": kid})

        return jsonify({"success": True, "message": "Karyawan dan akun login berhasil dihapus"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
