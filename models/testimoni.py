class Testimoni:
    def __init__(self, id_tr_pemesanan, tgl, teks, rating):
        self.id_tr_pemesanan = id_tr_pemesanan
        self.tgl = tgl
        self.rating = rating
        self.teks = teks

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS TESTIMONI (
                    IdTrPemesanan UUID,
                    Tgl DATE,
                    Teks TEXT,
                    Rating INT NOT NULL DEFAULT 0,
                    PRIMARY KEY (IdTrPemesanan, Tgl),
                    FOREIGN KEY (IdTrPemesanan) REFERENCES TR_PEMESANAN_JASA (Id)
                )
            """)
            conn.commit()