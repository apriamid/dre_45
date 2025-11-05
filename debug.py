# from common.mongo_connection import MongoConnection
# from common.managelogin import Loginaja
# from config import *

# #  Koneksi ke MongoDB auth_db
# db = MongoConnection(MONGODB_CONNECTION_STRING, MONGODB_AUTH_DATABASE)
# login = Loginaja()

# admin_user = {
#     "username": "kasir1",
#     "password": login.hash_password("kasir2002"),
#     "role":"kasir"
# }

# db.insert(MONGODB_COLLECTION_USER, admin_user)
# print("Admin berhasil ditambahkan:", admin_user)

# # # from common.mongo_connection import MongoConnection
# # # from common.managelogin import Loginaja
# # # from config import *
# # # from datetime import datetime
# # # import bcrypt

# # # # --- Asumsi: Import/Inisialisasi BCrypt di Loginaja ---
# # # # Jika Anda menggunakan Loginaja untuk hashing, pastikan metode hash_password tersedia.

# # # # Koneksi ke MongoDB (Gunakan DB yang menampung user login, sesuai setting di config.py)
# # # # Saya berasumsi MONGODB_DATABASE_NAME adalah DB tempat user login disimpan
# # # mongo = MongoConnection(connection_string=MONGODB_CONNECTION_STRING, db_name=MONGODB_DATABASE_NAME)
# # # login_manager = Loginaja()

# # # # ----------------------------------------------------
# # # # FUNGSI UNTUK MENGHASILKAN HASH YANG AMAN
# # # # Ini harusnya ada di common/managelogin.py
# # # # Saya mendefinisikannya di sini sebagai contoh
# # # # ----------------------------------------------------
# # # def hash_secure_password(password: str) -> str:
# # #     """Mengubah password plaintext menjadi hash Bcrypt."""
# # #     # Pastikan Loginaja/managelogin.py memiliki fungsi ini
# # #     # Jika Loginaja sudah ada, gunakan: return login_manager.hash_password(password)
    
# # #     # Jika Anda perlu mengimplementasikannya secara langsung:
# # #     encoded_password = password.encode('utf-8')
# # #     # Gunakan rounds yang cukup tinggi, misal 12
# # #     salt = bcrypt.gensalt(rounds=12) 
# # #     hashed_password = bcrypt.hashpw(encoded_password, salt)
# # #     return hashed_password.decode('utf-8') # Simpan sebagai string UTF-8

# # # # ----------------------------------------------------
# # # # DEFINISI USER BARU DENGAN PASSWORD PLAINTEXT AMAN
# # # # ----------------------------------------------------
# # # # PENTING: Password ini akan segera di-hash sebelum dimasukkan ke DB!
# # # USER_PASSWORDS = {
# # #     "kasir1": "kasir2001",
# # #     "kasir2": "kasir2002",
# # #     "kasir3": "kasir2003"
# # # }

# # # # ----------------------------------------------------
# # # # LIST DOKUMEN YANG AKAN DIMASUKKAN
# # # # ----------------------------------------------------
# # # users_to_insert = [
# # #     {
# # #         "_id": "K001",
# # #         "username": "kasir1",
# # #         "password": hash_secure_password(USER_PASSWORDS["kasir1"]),
# # #         "role": "kasir",
# # #         "store_id": "STR001",
# # #         "aktif": True,
# # #         "created_at": datetime.utcnow()
# # #     },
# # #     {
# # #         "_id": "K002",
# # #         "username": "kasir2",
# # #         "password": hash_secure_password(USER_PASSWORDS["kasir2"]),
# # #         "role": "kasir",
# # #         "store_id": "STR001",
# # #         "aktif": True,
# # #         "created_at": datetime.utcnow()
# # #     },
# # #     {
# # #         "_id": "K003",
# # #         "username": "kasir3",
# # #         "password": hash_secure_password(USER_PASSWORDS["kasir3"]),
# # #         "role": "kasir",
# # #         "store_id": "STR002",
# # #         "aktif": True,
# # #         "created_at": datetime.utcnow()
# # #     }
# # # ]

# # # # ----------------------------------------------------
# # # # EKSEKUSI: INSERT KE DATABASE
# # # # ----------------------------------------------------
# # # collection_name = MONGODB_COLLECTION_USER # Pastikan nama koleksi ini benar

# # # print(f"Memasukkan user ke koleksi '{collection_name}' di database '{MONGODB_DATABASE_NAME}'...")

# # # for user_data in users_to_insert:
# # #     # Cek apakah user sudah ada
# # #     existing_user = mongo.db[collection_name].find_one({"_id": user_data["_id"]})
    
# # #     if existing_user:
# # #         print(f"User ID {user_data['_id']} sudah ada. Melewati.")
# # #     else:
# # #         # Masukkan dokumen
# # #         try:
# # #             mongo.db[collection_name].insert_one(user_data)
# # #             print(f"User ID {user_data['_id']} ({user_data['username']} - {user_data['role']}) berhasil ditambahkan.")
# # #         except Exception as e:
# # #             print(f"Gagal menambahkan user {user_data['_id']}: {e}")
