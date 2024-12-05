class TrPemesananStatus:
    def __init__(self,  id_tr_pemesanan, id_status, tgl_waktu):
        self.id_tr_pemesanan
        self.id_status
        self.tgl_waktu

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE TR_PEMESANAN_STATUS (
                    IdTrPemesanan UUID,
                    IdStatus UUID,
                    TglWaktu TIMESTAMP NOT NULL,
                    PRIMARY KEY (IdTrPemesanan, IdStatus),
                    FOREIGN KEY (IdTrPemesanan) REFERENCES TR_PEMESANAN_JASA (Id),
                    FOREIGN KEY (IdStatus) REFERENCES STATUS_PESANAN (Id)
                );
            """)
            conn.commit()