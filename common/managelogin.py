# common/managelogin.py
import bcrypt
from flask import g, request, redirect, url_for, make_response, jsonify
from common.session_manage import SessionManager
from common.mongo_connection import MongoConnection
from config import (
    MONGODB_CONNECTION_STRING,
    MONGODB_DATABASE_NAME,      #  gunakan DB utama, bukan auth
    MONGODB_COLLECTION_USER,
)


class Loginaja:
    """Kelas untuk autentikasi pengguna menggunakan bcrypt dan JWT."""

    def __init__(self):
        #  Gunakan database utama tempat akun disimpan (bukan DB auth)
        self.auth_mongo = MongoConnection(
            MONGODB_CONNECTION_STRING,
            MONGODB_DATABASE_NAME
        )
        self.session_manager = SessionManager()
        self.user_collection = self.auth_mongo.db[MONGODB_COLLECTION_USER]

    def hash_password(self, password: str) -> str:
        """Hash password menggunakan bcrypt."""
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def authenticate_user(self, username, password):
        """Verifikasi user dari MongoDB menggunakan bcrypt."""
        try:
            #  Cari user berdasarkan username di DB utama
            find_result = self.auth_mongo.find(
                MONGODB_COLLECTION_USER, {"username": username}
            )
            user_data = find_result.get("data")
            user = user_data[0] if user_data and isinstance(user_data, list) else user_data

            # Debug opsional (bisa dihapus nanti)
            print("DEBUG LOGIN CARI USER:", username)
            print("HASIL USER:", user)

            if not user:
                print(f"User '{username}' tidak ditemukan di database {MONGODB_DATABASE_NAME}.")
                return None

            if "password" not in user:
                print("Field password tidak ditemukan di user.")
                return None

            hashed_pass = user["password"]

            #  Verifikasi bcrypt
            if bcrypt.checkpw(password.encode("utf-8"), hashed_pass.encode("utf-8")):
                print(f"Login berhasil untuk user '{username}'")
                return user
            else:
                print(f"Password salah untuk user '{username}'")
                return None

        except Exception as e:
            print(f"[ERROR authenticate_user]: {e}")
            return None

    def check_login(self):
        """Cek apakah pengguna sudah login berdasarkan token cookie."""
        token = request.cookies.get("token")
        if not token:
            return redirect(url_for("login"))

        session_data = self.session_manager.verify_token(token)
        if not session_data:
            resp = make_response(redirect(url_for("login")))
            resp.delete_cookie("token")
            return resp

        g.user = session_data
        return None
