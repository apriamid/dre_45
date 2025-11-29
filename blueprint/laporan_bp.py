from flask import Blueprint, jsonify
from datetime import datetime
from common.mongo_connection import MongoConnection
from config import *

laporan_bp = Blueprint("laporan_bp", __name__)
mongo = MongoConnection(MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME)


# ======================================================================
#                            TOTAL PENJUALAN
# ======================================================================
@laporan_bp.route("/total_penjualan", methods=["GET"])
def total_penjualan():
    """
    Menghitung total nilai transaksi penjualan.
    Mengambil semua data penjualan dari koleksi transaksi penjualan dan
    menjumlahkan field:
        - total_penjualan
        - atau total
    (bergantung pada struktur data yang tersimpan).

    Returns:
        tuple: JSON berisi total penjualan dan status HTTP.
    """
    try:
        data = mongo.db[MONGODB_COLLECTION_T_PENJUALAN].find()
        total = 0

        for row in data:
            total += float(
                row.get("total_penjualan") or
                row.get("total") or 0
            )

        return jsonify({"success": True, "total": total}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# =========================================================================
#                             TOTAL PEMBELIAN
# =========================================================================
@laporan_bp.route("/total_pembelian", methods=["GET"])
def total_pembelian():
    """
    Menghitung total nilai transaksi pembelian.
    Mengambil seluruh data pembelian dari database dan menjumlahkan nilai:
        - total_pembelian

    Returns:
        tuple: JSON berisi total pembelian dan status HTTP.
    """
    try:
        data = mongo.db[MONGODB_COLLECTION_T_PEMBELIAN].find()
        total = 0

        for row in data:
            total += float(row.get("total_pembelian", 0) or 0)

        return jsonify({"success": True, "total": total}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==========================================================================
#                       TREN TRANSAKSI UNTUK LINE CHART
# ==========================================================================
@laporan_bp.route("/tren_transaksi", methods=["GET"])
def tren_transaksi():
    """
    Menghasilkan data tren transaksi harian untuk kebutuhan grafik (line chart).
    Menggabungkan dan mengelompokkan data penjualan serta pembelian berdasarkan tanggal.
    Tanggal diambil dari salah satu field berikut:
        - tanggal_pembelian / tanggal_penjualan
        - tanggal
        - waktu
    Digunakan pada dashboard untuk visualisasi tren.

    Returns:
        tuple: JSON list berisi tanggal, total penjualan, total pembelian.
    """
    try:
        pembelian = list(mongo.db[MONGODB_COLLECTION_T_PEMBELIAN].find())
        penjualan = list(mongo.db[MONGODB_COLLECTION_T_PENJUALAN].find())

        timeline = {}

        # Pembelian
        for p in pembelian:
            tgl = p.get("tanggal_pembelian") or p.get("tanggal") or p.get("waktu")
            try:
                tgl = datetime.fromisoformat(str(tgl)).strftime("%Y-%m-%d")
            except:
                continue

            timeline.setdefault(tgl, {"penjualan": 0, "pembelian": 0})
            timeline[tgl]["pembelian"] += float(p.get("total_pembelian", 0) or 0)

        # Penjualan
        for p in penjualan:
            tgl = p.get("tanggal_penjualan") or p.get("tanggal") or p.get("waktu")
            try:
                tgl = datetime.fromisoformat(str(tgl)).strftime("%Y-%m-%d")
            except:
                continue

            timeline.setdefault(tgl, {"penjualan": 0, "pembelian": 0})
            timeline[tgl]["penjualan"] += float(
                p.get("total_penjualan") or
                p.get("total") or 0
            )

        result = []
        for tgl, val in sorted(timeline.items()):
            result.append({
                "tanggal": tgl,
                "penjualan": val["penjualan"],
                "pembelian": val["pembelian"]
            })

        return jsonify({"success": True, "data": result}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ======================================================
#                          PROFIT (LAMA)
# ======================================================
@laporan_bp.route("/profit", methods=["GET"])
def get_laporan_profit():
    """
    Menghasilkan laporan profit harian.
    Rumus:
        profit = total_penjualan - total_pembelian
    Data dikelompokkan berdasarkan tanggal sehingga dapat digunakan
    untuk grafik profit atau tabel laporan harian

    Returns:
        tuple: JSON list berisi tanggal dan nilai profit.
    """
    try:
        pembelian = list(mongo.db[MONGODB_COLLECTION_T_PEMBELIAN].find())
        penjualan = list(mongo.db[MONGODB_COLLECTION_T_PENJUALAN].find())

        daily = {}

        # Pembelian
        for p in pembelian:
            tgl = p.get("tanggal_pembelian") or p.get("tanggal") or p.get("waktu")
            try:
                date_str = datetime.fromisoformat(str(tgl)).strftime("%Y-%m-%d")
            except:
                continue

            daily.setdefault(date_str, {"pembelian": 0, "penjualan": 0})
            daily[date_str]["pembelian"] += float(p.get("total_pembelian", 0) or 0)

        # Penjualan
        for p in penjualan:
            tgl = p.get("tanggal_penjualan") or p.get("tanggal") or p.get("waktu")
            try:
                date_str = datetime.fromisoformat(str(tgl)).strftime("%Y-%m-%d")
            except:
                continue

            daily.setdefault(date_str, {"pembelian": 0, "penjualan": 0})
            daily[date_str]["penjualan"] += float(p.get("total_penjualan", 0) or p.get("total", 0) or 0)

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
