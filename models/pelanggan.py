class Pelanggan:
    def __init__(self, id, level):
        self.id = id
        self.level = level

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE PELANGGAN (
                    Id UUID,
                    Level VARCHAR,
                    FOREIGN KEY (Id) REFERENCES "USER"(Id),
                    CONSTRAINT unique_pelanggan_id UNIQUE (Id)
                );
            """)
            conn.commit()