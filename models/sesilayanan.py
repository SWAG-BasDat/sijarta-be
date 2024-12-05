class SesiLayanan:
    def __init__(self, sub_kategori_id, sesi, harga):
        self.sub_kategori_id = sub_kategori_id
        self.sesi = sesi
        self.harga = harga

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS SESI_LAYANAN (
                    SubkategoriId UUID,
                    Sesi INT,
                    Harga DECIMAL,
                    PRIMARY KEY (SubkategoriId, Sesi),
                    FOREIGN KEY (SubkategoriId) REFERENCES SUBKATEGORI_JASA (Id)
                );
            """)
            conn.commit()