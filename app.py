from flask import Flask, render_template, redirect, url_for, make_response, flash, jsonify, request, g
from common.mongo_connection import MongoConnection
from common.session_manage import SessionManager
from common.managelogin import Loginaja
from config import *

from blueprint.karyawan_bp import karyawan_bp
from blueprint.produk_bp import produk_bp
from blueprint.pembelian_bp import pembelian_bp
from blueprint.laporan_bp import laporan_bp
from blueprint.penjualan_bp import penjualan_bp


app = Flask(__name__, template_folder="templates")
app.secret_key = "kapita_secret_key"

session_manager = SessionManager()
managelogin = Loginaja()
mongo = MongoConnection(connection_string=MONGODB_CONNECTION_STRING, db_name=MONGODB_DATABASE_NAME)

app.register_blueprint(karyawan_bp, url_prefix="/api/karyawan")
app.register_blueprint(produk_bp, url_prefix="/api/produk")
app.register_blueprint(pembelian_bp, url_prefix="/api/transaksi_pembelian")
app.register_blueprint(laporan_bp, url_prefix="/api/laporan")
app.register_blueprint(penjualan_bp, url_prefix="/api/penjualan")



@app.before_request
def before_request_func():
    """
    Sebagai front-gate: memeriksa token pada setiap request non-public.
    - API routes -> kembalikan JSON 401 jika tidak valid (tidak redirect)
    - HTML protected pages -> redirect ke /login bila tidak valid
    """
    path = request.path

    PUBLIC_ROUTES = {"/login", "/", "/favicon.ico"}
  
    if path.startswith("/static/"):
        return None
    if path in PUBLIC_ROUTES:
        return None

    token = request.cookies.get("token")
    if path.startswith("/api/"):
        if not token:
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        session_data = session_manager.verify_token(token)
        if not session_data:
            return jsonify({"success": False, "message": "Invalid or expired token"}), 401

        g.user = session_data
        return None
    if not token:
        return redirect(url_for("login"))

    session_data = session_manager.verify_token(token)
    if not session_data:
        resp = make_response(redirect(url_for("login")))
        resp.delete_cookie("token", path="/")
        return resp

    g.user = session_data
    return None

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
            resp.set_cookie("token", token, httponly=True, samesite="Lax", path="/")
            return resp

        return jsonify({"success": False, "message": "Username atau Password salah!"}), 401

    return render_template("login.html")


@app.route("/logout")
def logout():
    token = request.cookies.get("token")
    if token:
        session_manager.remove_token(token)
    resp = make_response(redirect(url_for("login")))
    resp.delete_cookie("token", path="/")
    flash("Logout berhasil!", "success")
    return resp


@app.route("/admin-dashboard")
def admin_dashboard():
    if not hasattr(g, 'user') or not g.user:
        return redirect(url_for("login"))
    user_role = g.user.get('role')

    if user_role == 'kasir':
        return redirect(url_for("kasir_dashboard"))
        
    if user_role in ('admin', 'superadmin'):
        return render_template("admindashboard.html")
    return redirect(url_for("login"))


@app.route("/kasir-dashboard")
def kasir_dashboard():
    if not hasattr(g, 'user') or not g.user:
        return redirect(url_for("login"))
    user_role = g.user.get('role')
    
    if user_role in ('admin', 'superadmin'):
        return redirect(url_for("admin_dashboard"))
        
    if user_role == 'kasir':
        return render_template("sistemkasir.html")
    return redirect(url_for("login"))


@app.route("/api/me")
def api_me():
    token = request.cookies.get("token")
    if not token:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    data = session_manager.verify_token(token)
    if not data:
        return jsonify({"success": False, "message": "Invalid token"}), 401
    return jsonify({"success": True, "username": data["username"], "role": data["role"]}), 200


@app.route("/api/userinfo")
def api_userinfo():
    token = request.cookies.get("token")
    if not token:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    data = session_manager.verify_token(token)
    if not data:
        return jsonify({"success": False, "message": "Invalid token"}), 401
    return jsonify({"success": True, "username": data["username"], "role": data["role"]}), 200


if __name__ == '__main__':
    app.run(debug=True)
