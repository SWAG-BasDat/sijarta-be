class Voucher:
    def __init__(self, kode, jml_hari_berlaku, kuota_penggunaan, harga):
        self.kode = kode
        self.jml_hari_berlaku = jml_hari_berlaku
        self.kuota_penggunaan = kuota_penggunaan
        self.harga = harga

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS VOUCHER (
                    Kode VARCHAR PRIMARY KEY,
                    JmlHariBerlaku INT NOT NULL CHECK (JmlHariBerlaku >= 0),
                    KuotaPenggunaan INT,
                    Harga DECIMAL NOT NULL CHECK (Harga >= 0),
                    FOREIGN KEY (Kode) REFERENCES DISKON (Kode)
                )
            """)
            conn.commit()