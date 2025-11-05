from flask import Blueprint, jsonify, request
from datetime import datetime
from common.mongo_connection import MongoConnection
from config import (
    MONGODB_CONNECTION_STRING,
    MONGODB_DATABASE_NAME,
    MONGODB_COLLECTION_T_PEMBELIAN,
    MONGODB_COLLECTION_T_PENJUALAN
)

laporan_bp = Blueprint("laporan_bp", __name__)
mongo = MongoConnection(MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME)
@laporan_bp.route("/profit", methods=["GET"])
def get_laporan_profit():
    try:
        pembelian = list(mongo.db[MONGODB_COLLECTION_T_PEMBELIAN].find())
        penjualan = list(mongo.db[MONGODB_COLLECTION_T_PENJUALAN].find())

        daily = {}

        # proses pembelian per hari
        for p in pembelian:
            tgl = p.get("tanggal_pembelian") or p.get("tanggal") or p.get("waktu")
            try:
                date_str = datetime.fromisoformat(str(tgl)).strftime("%Y-%m-%d")
            except:
                continue
            daily.setdefault(date_str, {"pembelian":0,"penjualan":0})
            daily[date_str]["pembelian"] += float(p.get("total_pembelian", 0) or 0)

        # proses penjualan per hari
        for p in penjualan:
            tgl = p.get("tanggal_penjualan") or p.get("tanggal") or p.get("waktu")
            try:
                date_str = datetime.fromisoformat(str(tgl)).strftime("%Y-%m-%d")
            except:
                continue
            daily.setdefault(date_str, {"pembelian":0,"penjualan":0})
            daily[date_str]["penjualan"] += float(p.get("total_penjualan", 0) or p.get("total", 0) or 0)

        # konversi ke array untuk chart
        result = []
        for date_str, val in sorted(daily.items()):
            profit = val["penjualan"] - val["pembelian"]
            result.append({
                "date": date_str,
                "profit": profit
            })

        return jsonify({"success": True, "data": result}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
