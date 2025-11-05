import jwt
from common.mongo_connection import MongoConnection
from config import MONGODB_CONNECTION_STRING, MONGODB_AUTH_DATABASE, MONGODB_SESSION_COLLECTION
from datetime import datetime, timedelta


class SessionManager:
    """Kelas untuk mengelola sesi pengguna menggunakan JWT dan MongoDB."""

    def __init__(self):
        """Inisialisasi koneksi MongoDB dan secret key untuk JWT."""
        self.auth_mongo = MongoConnection(
            connection_string=MONGODB_CONNECTION_STRING,
            db_name=MONGODB_AUTH_DATABASE
        )
        self.secret_key = 'kapita_secret_key'

    def generate_token(self, username, role):
        """Membuat token JWT dan menyimpannya ke dalam koleksi sesi MongoDB.

        Args:
            username (str): Nama pengguna yang login.
            role (str): Peran pengguna, misalnya 'admin' atau 'kasir'.

        Returns:
            str: Token JWT yang telah dibuat dan disimpan ke database.
        """
        now = datetime.utcnow()
        payload = {
            'username': username,
            'role': role,
            'exp': now + timedelta(hours=24),
            'iat': now
        }
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')

        session_data = {
            'username': username,
            'role': role,
            'token': token,
            'created_at': now,
            'expires_at': payload['exp']
        }
        self.auth_mongo.insert(MONGODB_SESSION_COLLECTION, session_data)

        return token

    def verify_token(self, token):
        """Memverifikasi token JWT apakah valid atau telah kadaluarsa.
        Args:
            token (str): Token JWT yang akan diverifikasi.
        Returns:
            dict | None: Payload token jika valid, None jika token tidak valid atau kadaluarsa.
        """
        try:
            session = self.auth_mongo.find(MONGODB_SESSION_COLLECTION, {'token': token})

            # Pastikan session masih ada di database
            if not session:
                return None

            # Decode token dan kembalikan payload
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload

        except jwt.ExpiredSignatureError:
            # Token kadaluarsa, hapus session dari database
            self.auth_mongo.delete(MONGODB_SESSION_COLLECTION, {'token': token})
            print(f"Token expired: {token}")
            return None
        except jwt.InvalidTokenError:
            # Token tidak valid
            print(f"Invalid token: {token}")
            return None
        except Exception as e:
            print(f"Error verifying token: {e}")
            return None

    def remove_token(self, token):
        """Menghapus token dari database untuk mengakhiri sesi pengguna.

        Args:
            token (str): Token JWT yang akan dihapus.
        """
        self.auth_mongo.delete(MONGODB_SESSION_COLLECTION, {"token": token})


if __name__ == "__main__":
    pass
