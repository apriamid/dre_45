import jwt
from common.mongo_connection import MongoConnection
from config import MONGODB_CONNECTION_STRING, MONGODB_AUTH_DATABASE, MONGODB_SESSION_COLLECTION
from datetime import datetime, timedelta


class SessionManager:
    """Kelas untuk mengelola sesi pengguna menggunakan JWT dan MongoDB."""

    def __init__(self):
        self.auth_mongo = MongoConnection(connection_string=MONGODB_CONNECTION_STRING, db_name=MONGODB_AUTH_DATABASE)
        self.secret_key = 'kapita_secret_key'
        self.coll = self.auth_mongo.db[MONGODB_SESSION_COLLECTION]

    def generate_token(self, username, role):
        """
        Membuat token JWT dan menyimpannya ke dalam koleksi sesi MongoDB.
        Jika sudah ada session aktif untuk username dan belum expired, kembalikan token yang ada.
        """
        now = datetime.utcnow()
        existing = self.coll.find_one({"username": username})
        if existing:
            existing_token = existing.get("token")
            try:
                payload = jwt.decode(existing_token, self.secret_key, algorithms=['HS256'])
                return existing_token
            except jwt.ExpiredSignatureError:
                self.coll.delete_one({"_id": existing["_id"]})
            except jwt.InvalidTokenError:
                self.coll.delete_one({"_id": existing["_id"]})
            except Exception:
                self.coll.delete_one({"_id": existing["_id"]})

        exp = now + timedelta(hours=24)
        payload = {
            "username": username,
            "role": role,
            "iat": now,
            "exp": exp
        }
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        if isinstance(token, bytes):
            token = token.decode("utf-8")

        session_doc = {
            "username": username,
            "role": role,
            "token": token,
            "created_at": now,
            "expires_at": exp,
            "user_agent": None,
            "ip": None
        }
        self.coll.insert_one(session_doc)
        return token

    def verify_token(self, token):
        """
        Dual-layer verification:
        1) Session Guard: token harus ada di collection user_sessions
        2) JWT Integrity & Expiration: jwt.decode() harus sukses
        """
        try:
            session_doc = self.coll.find_one({"token": token})
            if not session_doc:
                return None
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload

        except jwt.ExpiredSignatureError:
            try:
                self.coll.delete_one({"token": token})
            except Exception:
                pass
            return None

        except jwt.InvalidTokenError:
            try:
                self.coll.delete_one({"token": token})
            except Exception:
                pass
            return None

        except Exception as e:
            try:
                self.coll.delete_one({"token": token})
            except Exception:
                pass
            return None

    def remove_token(self, token):
        """Menghapus token dari database untuk mengakhiri sesi pengguna."""
        try:
            self.coll.delete_one({"token": token})
        except Exception:
            pass
