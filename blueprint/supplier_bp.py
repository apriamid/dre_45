from flask import Blueprint, request, jsonify
from datetime import datetime
from common.id_generator import generate_supplier_id 
from common.mongo_connection import MongoConnection
from config import *

supplier_bp = Blueprint("supplier_bp", __name__)
mongo = MongoConnection(MONGODB_CONNECTION_STRING, db_name=MONGODB_DATABASE_NAME)


def _serialize_doc(doc):
    """
    Mengubah dokumen MongoDB menjadi format JSON-friendly.
    Args:
        doc (dict): Dokumen supplier dari MongoDB.
    Returns:
        dict: Dokumen yang telah diserialisasi, dengan _id diubah menjadi string,
        field datetime diubah ke ISO format, serta membersihkan field yang tidak diperlukan.
    """
    if not doc:
        return doc
    out = dict(doc)
    if "_id" in out:
        doc_id_str = str(out["_id"])
        out["id"] = doc_id_str 
        del out["_id"]
    for k, v in list(out.items()):
        if isinstance(v, datetime):
            out[k] = v.isoformat()
    if "id_supplier" in out:
        del out["id_supplier"]
        
    return out


# =======================================================================================
#                                       READ ALL 
# =======================================================================================
@supplier_bp.route("/", methods=["GET"])
def get_all_suppliers():
    """
    Mengambil seluruh data supplier dari database.
    Returns:
        tuple: JSON berisi data supplier dan status code HTTP.
    """
    try:
        cursor = mongo.db[MONGODB_COLLECTION_SUPPLIER].find().sort("nama", 1)
        data = [_serialize_doc(doc) for doc in cursor]
        return jsonify({"data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Gagal mengambil data: {str(e)}"}), 500


# =======================================================================================
#                                       CREATE 
# =======================================================================================
@supplier_bp.route("/", methods=["POST"])
def create_supplier():
    """
    Membuat data supplier baru.
    Body JSON:
        nama (str): Nama supplier.
        kontak (str/int): Nomor kontak (hanya angka).
        alamat (str): Alamat supplier.
    Returns:
        tuple: JSON respons success/fail dan status HTTP.
    """
    try:
        data = request.get_json(force=True)
        nama = data.get("nama")
        kontak = data.get("kontak")
        alamat = data.get("alamat")

        if not nama or not kontak:
            return jsonify({"success": False, "message": "Nama dan Kontak wajib diisi"}), 400
        if kontak and not str(kontak).isdigit():
             return jsonify({"success": False, "message": "Nomor Kontak hanya boleh berisi angka."}), 400
        if mongo.db[MONGODB_COLLECTION_SUPPLIER].find_one({"nama": nama}):
            return jsonify({"success": False, "message": "Supplier dengan nama tersebut sudah ada"}), 409
        
        new_id = generate_supplier_id(mongo, MONGODB_COLLECTION_SUPPLIER) 
        
        new_supplier = {
            "_id": new_id, 
            "nama": nama,
            "kontak": kontak,
            "alamat": alamat,
            "tanggal_dibuat": datetime.now()
        }
        mongo.db[MONGODB_COLLECTION_SUPPLIER].insert_one(new_supplier)

        return jsonify({
            "success": True, 
            "message": "Supplier berhasil ditambahkan",
            "data": _serialize_doc(new_supplier) 
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Gagal simpan Supplier: {str(e)}"}), 500


# =======================================================================================
#                                   UPDATE 
# =======================================================================================
@supplier_bp.route("/<id>", methods=["PUT"])
def update_supplier(id):
    """
    Memperbarui data supplier berdasarkan ID.
    Args:
        id (str): ID supplier yang akan diperbarui.
    Body JSON:
        Field yang dapat diperbarui: nama, kontak, alamat.
    Returns:
        tuple: JSON respons hasil update dan status HTTP.
    """
    try: 
        data = request.get_json(force=True)
        update_data = {k: v for k, v in data.items() if k not in ["_id", "id", "id_supplier", "tanggal_dibuat"]}

        if not update_data:
             return jsonify({"success": False, "message": "Tidak ada data yang dikirim untuk diupdate"}), 400
        if "kontak" in update_data and not str(update_data["kontak"]).isdigit():
             return jsonify({"success": False, "message": "Nomor Kontak hanya boleh berisi angka."}), 400
        
        nama_baru = update_data.get("nama")
        if nama_baru and mongo.db[MONGODB_COLLECTION_SUPPLIER].find_one({"nama": nama_baru, "_id": {"$ne": id}}): 
            return jsonify({"success": False, "message": "Nama supplier sudah digunakan"}), 409
        
        updated = mongo.db[MONGODB_COLLECTION_SUPPLIER].find_one_and_update(
            {"_id": id}, 
            {"$set": update_data},
            return_document=True 
        )

        if not updated:
            return jsonify({"success": False, "message": "Supplier tidak ditemukan"}), 404

        return jsonify({
            "success": True, 
            "message": "Supplier berhasil diperbarui",
            "data": _serialize_doc(updated) 
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Gagal update: {str(e)}"}), 500


# =======================================================================================
#                                      DELETE 
# =======================================================================================
@supplier_bp.route("/<id>", methods=["DELETE"])
def delete_supplier(id):
    """
    Menghapus supplier berdasarkan ID.
    Args:
        id (str): ID supplier yang akan dihapus.
    Returns:
        tuple: JSON respons dan status HTTP.
    """
    try:
        supplier_doc = mongo.db[MONGODB_COLLECTION_SUPPLIER].find_one({"_id": id})
        if not supplier_doc:
             return jsonify({"success": False, "message": "Supplier tidak ditemukan"}), 404
        
        nama_supplier = supplier_doc.get("nama")
        is_used = mongo.db[MONGODB_COLLECTION_T_PEMBELIAN].find_one({"nama_supplier": nama_supplier})

        if is_used:
            return jsonify({
                "success": False, 
                "message": "Tidak dapat menghapus. Supplier ini sudah terkait dengan Transaksi Pembelian."
            }), 409

        result = mongo.db[MONGODB_COLLECTION_SUPPLIER].delete_one({"_id": id})

        if result.deleted_count == 0:
            return jsonify({"success": False, "message": "Supplier tidak ditemukan"}), 404

        return jsonify({"success": True, "message": "Supplier berhasil dihapus"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Gagal hapus: {str(e)}"}), 500
