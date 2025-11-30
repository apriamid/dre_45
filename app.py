from flask import Flask, render_template, redirect, url_for, make_response, flash, jsonify, request, g
# --- Perbaikan #1: Import ProxyFix ---
from werkzeug.middleware.proxy_fix import ProxyFix 

from common.mongo_connection import MongoConnection
from common.session_manage import SessionManager
from common.managelogin import Loginaja
from config import *

from blueprint.karyawan_bp import karyawan_bp
from blueprint.produk_bp import produk_bp
from blueprint.pembelian_bp import pembelian_bp
from blueprint.laporan_bp import laporan_bp
from blueprint.penjualan_bp import penjualan_bp
from blueprint.supplier_bp import supplier_bp

app = Flask(__name__, template_folder="templates")
app.secret_key = "kapita_secret_key"

app.wsgi_app = ProxyFix(
    app.wsgi_app, 
    x_for=1,    
    x_host=1,   
    x_proto=1   
)

# =========================================================================
# SOLUSI SERVER TERAKHIR: PAKSA SCHEME HTTPS PADA SEMUA URL GENERASI FLASK
# =========================================================================
# Ini memastikan bahwa jika Flask pernah menghasilkan URL absolut (misalnya untuk API) 
# karena Webix memicu *redirect* atau *request* aneh, protokolnya selalu HTTPS.
@app.url_defaults
def set_secure_url_defaults(endpoint, values):
    if 'static' in endpoint:
        # Abaikan aset statis
        return

    # Jika _scheme belum ditentukan dan request.url_root adalah HTTPS,
    # atau jika request_root masih HTTP, paksa HTTPS.
    # Namun, karena ProxyFix gagal, kita akan memaksanya:
    if '_scheme' not in values:
        values['_scheme'] = 'https'
    if '_external' not in values:
        values['_external'] = True # Penting untuk memaksa skema


@app.url_value_preprocessor
def pull_url_defaults(endpoint, values):
    # Mengembalikan url_for ke fungsionalitas normal untuk internal link
    if values is not None:
        values.pop('_scheme', None)
        values.pop('_external', None)
# =========================================================================

session_manager = SessionManager()
managelogin = Loginaja()
mongo = MongoConnection(connection_string=MONGODB_CONNECTION_STRING, db_name=MONGODB_DATABASE_NAME)

app.register_blueprint(karyawan_bp, url_prefix="/api/karyawan")
app.register_blueprint(produk_bp, url_prefix="/api/produk")
app.register_blueprint(pembelian_bp, url_prefix="/api/transaksi_pembelian")
app.register_blueprint(laporan_bp, url_prefix="/api/laporan")
app.register_blueprint(penjualan_bp, url_prefix="/api/penjualan")
app.register_blueprint(supplier_bp, url_prefix="/api/supplier")


@app.before_request
def before_request():
    g.user = None
    g.token_data = None
    g.role = "guest"
    
    token = request.cookies.get("token")

    if token:
        data = session_manager.verify_token(token)
        if data:
            g.token_data = data
            g.user = mongo.db[MONGODB_COLLECTION_USER].find_one({"username": data["username"]})
            if g.user:
                g.role = g.user.get("role", "guest")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user_doc = managelogin.authenticate_user(username, password)

        if user_doc:
            role = user_doc.get("role")
            token = session_manager.generate_token(user_doc)

            # --- Perbaikan #2: Tambahkan _scheme='https' ---
            resp = make_response(redirect(url_for("root_dashboard", _scheme='https')))
            resp.set_cookie("token", token, httponly=True, max_age=3600*24*7) # 1 week
            return resp
        else:
            flash("Username atau password salah", "error")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    # --- Perbaikan #2: Tambahkan _scheme='https' ---
    resp = make_response(redirect(url_for("login", _scheme='https')))
    resp.delete_cookie("token")
    return resp

@app.route("/")
def root_dashboard():
    if not hasattr(g, 'user') or not g.user:
        # --- Perbaikan #2: Tambahkan _scheme='https' ---
        return redirect(url_for("login", _scheme='https'))
    
    user_role = g.user.get('role')
    
    if user_role == 'kasir':
        # --- Perbaikan #2: Tambahkan _scheme='https' ---
        return redirect(url_for("kasir_dashboard", _scheme='https'))
        
    if user_role in ('admin', 'superadmin'):
        # --- Perbaikan #2: Tambahkan _scheme='https' ---
        return redirect(url_for("admin_dashboard", _scheme='https'))
        
    # --- Perbaikan #2: Tambahkan _scheme='https' ---
    return redirect(url_for("login", _scheme='https'))


@app.route("/admin-dashboard")
def admin_dashboard():
    if not hasattr(g, 'user') or not g.user:
        # --- Perbaikan #2: Tambahkan _scheme='https' ---
        return redirect(url_for("login", _scheme='https'))
    user_role = g.user.get('role')
    
    if user_role == 'kasir':
        # --- Perbaikan #2: Tambahkan _scheme='https' ---
        return redirect(url_for("kasir_dashboard", _scheme='https'))
        
    if user_role in ('admin', 'superadmin'):
        return render_template("admindashboard.html")
    # --- Perbaikan #2: Tambahkan _scheme='https' ---
    return redirect(url_for("login", _scheme='https'))


@app.route("/kasir-dashboard")
def kasir_dashboard():
    if not hasattr(g, 'user') or not g.user:
        # --- Perbaikan #2: Tambahkan _scheme='https' ---
        return redirect(url_for("login", _scheme='https'))
    user_role = g.user.get('role')
    
    if user_role in ('admin', 'superadmin'):
        # --- Perbaikan #2: Tambahkan _scheme='https' ---
        return redirect(url_for("admin_dashboard", _scheme='https'))
        
    if user_role == 'kasir':
        return render_template("sistemkasir.html")
    # --- Perbaikan #2: Tambahkan _scheme='https' ---
    return redirect(url_for("login", _scheme='https'))


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

    user_info = mongo.db[MONGODB_COLLECTION_USER].find_one({"username": data["username"]}, {"_id": 0, "password": 0, "id_karyawan": 0})
    if user_info:
        return jsonify({"success": True, "data": user_info}), 200
    return jsonify({"success": False, "message": "User not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)
    