class PekerjaKategoriJasa:
    def __init__(self, pekerja_id, kategori_jasa_id):
        self.pekerja_id = pekerja_id
        self.kategori_jasa_id = kategori_jasa_id

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS PEKERJA_KATEGORI_JASA (
                    PekerjaId UUID,
                    KategoriJasaID UUID,
                    FOREIGN KEY (PekerjaId) REFERENCES PEKERJA (Id),
                    FOREIGN KEY (KategoriJasaId) REFERENCES KATEGORI_JASA (Id)
                );
            """)
            conn.commit()