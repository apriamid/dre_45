# app.py
from flask import Flask, render_template, redirect, url_for, make_response, flash, jsonify, request
from common.mongo_connection import MongoConnection
from common.session_manage import SessionManager
from common.managelogin import Loginaja
from config import *

# blueprints
from blueprint.karyawan_bp import karyawan_bp
from blueprint.produk_bp import produk_bp
from blueprint.pembelian_bp import pembelian_bp
from blueprint.laporan_bp import laporan_bp
from blueprint.shift_bp import shift_bp
from blueprint.penjualan_bp import penjualan_bp


app = Flask(__name__, template_folder="templates")
app.secret_key = "kapita_secret_key"

session_manager = SessionManager()
managelogin = Loginaja()
mongo = MongoConnection(connection_string=MONGODB_CONNECTION_STRING, db_name=MONGODB_DATABASE_NAME)

# register blueprints
app.register_blueprint(karyawan_bp, url_prefix="/api/karyawan")
app.register_blueprint(produk_bp, url_prefix="/api/produk")
app.register_blueprint(pembelian_bp, url_prefix="/api/transaksi_pembelian")
app.register_blueprint(laporan_bp, url_prefix="/api/laporan")
app.register_blueprint(shift_bp, url_prefix="/api/shift")
app.register_blueprint(penjualan_bp, url_prefix="/api/penjualan")


@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json(force=True)
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            return jsonify({"success": False, "message": "Lengkapi semua kolom!"}), 400

        user = managelogin.authenticate_user(username, password)
        if user:
            token = session_manager.generate_token(user["username"], user["role"])
            resp = jsonify({"success": True, "role": user["role"]})
            resp.set_cookie("token", token, httponly=True, samesite="Lax")
            return resp
        return jsonify({"success": False, "message": "Username atau Password salah!"}), 401

    return render_template("login.html")

@app.route("/logout")
def logout():
    token = request.cookies.get("token")
    if token:
        session_manager.remove_token(token)
    resp = make_response(redirect(url_for("login")))
    resp.delete_cookie("token")
    flash("Logout berhasil!", "success")
    return resp

@app.route("/admin-dashboard")
def admin_dashboard():
    return render_template("coba.html")

@app.route("/kasir-dashboard")
def kasir_dashboard():
    return render_template("sistemkasir.html")

# simple /api/me (keperluan lama)
@app.route("/api/me")
def api_me():
    token = request.cookies.get("token")
    if not token:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    data = session_manager.verify_token(token)
    if not data:
        return jsonify({"success": False, "message": "Invalid token"}), 401
    return jsonify({"success": True, "username": data.get("username"), "role": data.get("role")}), 200


@app.route("/api/userinfo")
def api_userinfo():
    token = request.cookies.get("token")
    if not token:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    data = session_manager.verify_token(token)
    if not data:
        return jsonify({"success": False, "message": "Invalid token"}), 401
    return jsonify({"success": True, "username": data.get("username"), "role": data.get("role")}), 200

if __name__ == "__main__":
    app.run(debug=True)
