class Promo:
    def __init__(self, kode, tgl_akhir_berlaku):
        self.kode = kode
        self.tgl_akhir_berlaku = tgl_akhir_berlaku

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS PROMO (
                    Kode VARCHAR PRIMARY KEY,
                    TglAkhirBerlaku DATE NOT NULL,
                    FOREIGN KEY (Kode) REFERENCES DISKON (Kode)
                )
            """)
            conn.commit()