class MetodeBayar:
    def __init__(self, id, nama):
        self.id = id
        self.nama = nama

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE METODE_BAYAR (
                    Id UUID PRIMARY KEY,
                    Nama VARCHAR NOT NULL
                );
            """)
            conn.commit()