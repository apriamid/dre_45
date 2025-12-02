import bcrypt
from flask import g, request, redirect, url_for, make_response
from common.session_manage import SessionManager
from common.mongo_connection import MongoConnection
from config import (
    MONGODB_CONNECTION_STRING,
    MONGODB_DATABASE_NAME,      
    MONGODB_COLLECTION_USER,
)

class Loginaja:
    """Kelas untuk autentikasi pengguna menggunakan bcrypt dan JWT."""

    def __init__(self):
        self.auth_mongo = MongoConnection(MONGODB_CONNECTION_STRING, db_name=MONGODB_DATABASE_NAME)
        self.session_manager = SessionManager()
        self.user_collection = self.auth_mongo.db[MONGODB_COLLECTION_USER]

    def hash_password(self, password: str) -> str:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def authenticate_user(self, username, password):
        """Verifikasi user dari MongoDB menggunakan bcrypt."""
        try:
            user = self.user_collection.find_one({"username": username})
            if not user:
                return None

            if "password" not in user:
                return None

            hashed_pass = user["password"]
            if bcrypt.checkpw(password.encode("utf-8"), hashed_pass.encode("utf-8")):
                return user
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
            resp.delete_cookie("token", path="/")
            return resp
        g.user = session_data
        return None
