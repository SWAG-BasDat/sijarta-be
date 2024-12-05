class StatusPesanan:
    def __init__(self, id, status):
        self.id = id
        self.status = status

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""    
                CREATE TABLE IF NOT EXISTS STATUS_PESANAN (
                    Id UUID PRIMARY KEY,
                    Status VARCHAR(50) NOT NULL
                );
            """)
            conn.commit()