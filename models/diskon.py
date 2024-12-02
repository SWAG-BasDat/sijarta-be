class Diskon:
    def __init__(self, kode, potongan, min_tr_pemesanan):
        self.kode = kode
        self.potongan = potongan
        self.min_tr_pemesanan = min_tr_pemesanan

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS DISKON (
                    Kode VARCHAR(50) PRIMARY KEY,
                    Potongan DECIMAL NOT NULL CHECK (Potongan >= 0),
                    MinTrPemesanan INT NOT NULL CHECK (MinTrPemesanan >= 0)
                )
            """)
            conn.commit()