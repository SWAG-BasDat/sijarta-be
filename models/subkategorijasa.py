class SubkategoriJasa:
    def __init__(self, id, nama_subkategori, deskripsi, kategori_jasa_id):
        self.id = id
        self.nama_subkategori = nama_subkategori
        self.deskripsi = deskripsi
        self.kategori_jasa_id = kategori_jasa_id

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS SUBKATEGORI_JASA (
                    Id UUID PRIMARY KEY,
                    NamaSubkategori VARCHAR,
                    Deskripsi TEXT,
                    KategoriJasaId UUID,
                    FOREIGN KEY (KategoriJasaId) REFERENCES KATEGORI_JASA (Id)
                );
            """)
            conn.commit()