from pymongo import MongoClient

class MongoConnection:
    """Kelas utilitas untuk mengelola koneksi dan operasi database MongoDB."""

    def __init__(self, connection_string, db_name):
        """Inisialisasi koneksi ke MongoDB.

        Args:
            connection_string (str): URI koneksi MongoDB.
            db_name (str): Nama database yang akan digunakan.
        """
        self.connection_string = connection_string
        self.db_name = db_name
        self.client = None
        self.db = None
        self.__getConnection()

    def __getConnection(self):
        """Membuat koneksi ke MongoDB Atlas dan mengembalikan objek database.

        Returns:
            Database: Objek database MongoDB jika berhasil terhubung.
        """
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.db_name]
            self.client.admin.command('ping')
            print("Berhasil menghubungkan ke MongoDB Atlas!")
            return self.db
        except Exception as e:
            print(f"Error connection to MongoDB: {e}")

    def find(self, collection, query, project={}, limit=0, sort=[], multi=False):
        """Mengambil data dari koleksi MongoDB berdasarkan query.

        Args:
            collection (str): Nama koleksi.
            query (dict): Filter pencarian MongoDB.
            project (dict, optional): Field yang ingin diambil. Default {}.
            limit (int, optional): Jumlah data maksimal. Default 0.
            sort (list, optional): Urutan hasil. Default [].
            multi (bool, optional): Jika True, ambil banyak data. Default False.

        Returns:
            dict: Hasil pencarian dengan status, data, dan pesan.
        """
        result = {'status': False, 'data': None, 'message': "Terjadi kesalahan saat mengambil data"}
        try:
            if multi:
                resultFind = self.db[collection].find(query, projection=project, limit=limit, sort=sort)
                resultFind = list(resultFind)
            else:
                resultFind = self.db[collection].find_one(query, projection=project, sort=sort)

            if resultFind:
                result['status'] = True
                result['data'] = resultFind
                result['message'] = "Berhasil mengambil data"

        except Exception as e:
            print(f"Error find: {e}")

        return result

    def insert(self, collection, data, multi=False):
        """Menambahkan data ke koleksi MongoDB.

        Args:
            collection = string : Nama koleksi.
            data = dict & list : Data yang akan dimasukkan.
            multi (bool, optional): Jika True, gunakan `insert_many`. Default False.
            
        Returns:
            dict: Status dan informasi hasil penyimpanan data.
        """
        result = {'status': False, 'data': None, 'message': "Terjadi kesalahan saat menambahkan data"}
        try:
            if multi:
                result_insert = self.db[collection].insert_many(data)
            else:
                result_insert = self.db[collection].insert_one(data)

            if result_insert.acknowledged:
                result['status'] = True
                result['message'] = "Berhasil menambahkan data"
                if multi:
                    result['data'] = {'inserted_ids': result_insert.inserted_ids}
                else:
                    result['data'] = {'inserted_id': result_insert.inserted_id}
        except Exception as e:
            print(f"Error insert: {e}")

        return result

    def update(self, collection, query, data, multi=False):
        """Memperbarui data dalam koleksi MongoDB.

        Args:
            collection (str): Nama koleksi.
            query (dict): Filter untuk memilih data yang ingin diperbarui.
            data (dict): Data pembaruan menggunakan sintaks MongoDB (misalnya `{"$set": {...}}`).
            multi (bool, optional): Jika True, gunakan update_many

        Returns:
            dict: Status dan pesan hasil pembaruan data.
        """
        result = {'status': False, 'message': 'Terjadi kesalahan saat memperbarui data'}
        try:
            update_result = self.db[collection].update_one(query, data) if not multi else self.db[collection].update_many(query, data)
            if update_result.modified_count > 0 or update_result.matched_count > 0:
                result['status'] = True
                result['message'] = f'Berhasil memperbarui {update_result.modified_count} data.'
        except Exception as e:
            print(f"Error update data: {e}")
        return result

    def delete(self, collection, query):
        """Menghapus data dari koleksi MongoDB.

        Args:
            collection (str): Nama koleksi.
            query (dict): Filter data yang ingin dihapus.

        Returns:
            dict: Status dan pesan hasil penghapusan data.
        """
        result = {'status': False, 'message': 'Gagal menghapus data atau data tidak ditemukan.'}
        try:
            delete_result = self.db[collection].delete_one(query)
            if delete_result.deleted_count > 0:
                result['status'] = True
                result['message'] = 'Berhasil menghapus data.'
        except Exception as e:
            print(f"Error delete data: {e}")
        return result



    