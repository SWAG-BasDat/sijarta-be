from models.sesilayanan import SesiLayanan

class SesiLayananService:
    def __init__(self, conn):
        self.conn = conn

    def get_sesi_by_subkategori(self, id_subkategori):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT Sesi, Harga
                FROM SESI_LAYANAN
                WHERE SubkategoriId = %s
                """,
                (str(id_subkategori),)
            )
            return cur.fetchall()
        
    def get_sesi_details(self, id_subkategori, sesi):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT Sesi, Harga
                FROM SESI_LAYANAN
                WHERE SubkategoriId = %s AND Sesi = %s
                """,
                (str(id_subkategori), str(sesi))
            )
            return cur.fetchone()
        
    def add_sesi_layanan(self, id_subkategori, sesi, harga):
        with self.conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO SESI_LAYANAN (SubaktegoriId, Sesi, Harga)
                    VALUES (%s, %s, %s)
                    """,
                    (id_subkategori, sesi, harga)
                )
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                raise e
            