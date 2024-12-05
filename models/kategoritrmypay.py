class KategoriTrMyPay:
    def __init__(self, id, nama_kategori):
        self.id = id
        self.nama_kategori = nama_kategori

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS KATEGORI_TR_MYPAY (
                    Id UUID PRIMARY KEY,
                    NamaKategori VARCHAR
                );
            """)
            conn.commit()