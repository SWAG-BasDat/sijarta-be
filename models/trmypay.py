class TrMyPay:
    def __init__(self, id, user_id, tgl, nominal, kategori_id):
        self.id = id
        self.user_id = user_id
        self.tgl = tgl
        self.nominal = nominal
        self.kategori_id = kategori_id

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS TR_MYPAY (
                    Id UUID PRIMARY KEY,
                    UserId UUID,
                    Tgl DATE,
                    Nominal DECIMAL,
                    KategoriId UUID,
                    FOREIGN KEY (UserId) REFERENCES "USER" (Id),
                    FOREIGN KEY (KategoriId) REFERENCES KATEGORI_TR_MYPAY (Id)
                );
            """)
            conn.commit()