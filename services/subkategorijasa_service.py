class SubkategoriJasaService:
    def __init__(self, conn):
        self.conn = conn
        
    def get_subkategori_by_id(self, id_subkategori):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT sj.Id, sj.NamaSubkategori, sj.Deskripsi, kj.NamaKategori
                FROM SUBKATEGORI_JASA sj
                JOIN KATEGORI_JASA kj ON sj.KategoriJasa = kj.Id
                WHERE sj.Id = %s
                """,
                (id_subkategori,)
            )
            return cur.fetchone()
        
    def get_pekerja_by_subkategori(self, id_subkategori):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.Id, u.Nama, p.Rating, p.JmlPsnananSelesai
                FROM PEKERJA p
                JOIN "USER" u ON p.Id = u.Id
                JOIN PEKERJA_KATEGORI_JASA pkj ON p.Id = pkj.PekerjaId
                WHERE pkj.KategoriJasaId = %s
                """,
                (id_subkategori,)
            )
            return cur.fetchall()
        
    def add_pekerja_to_kategori(self, pekerja_id, kategori_id):
        with self.conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO PEKERJA_KATEGORI_JASA (PekerjaId, KategoriJasaId)
                    VALUES (%s, %s)
                    """,
                    (pekerja_id, kategori_id)
                )
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                raise e
