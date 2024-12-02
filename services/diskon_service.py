from models.diskon import Diskon

class DiskonService:
    def __init__(self, conn):
        self.conn = conn

    def create_diskon(self, kode, potongan, min_tr_pemesanan):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO DISKON (Kode, Potongan, MinTrPemesanan) VALUES (%s, %s, %s)",
                (kode, potongan, min_tr_pemesanan)
            )
            self.conn.commit()
            return Diskon(kode, potongan, min_tr_pemesanan)

    def get_all_diskon(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM DISKON")
            return cur.fetchall()

    def get_diskon_by_kode(self, kode):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM DISKON WHERE Kode = %s", (kode,))
            return cur.fetchone()

    def update_diskon(self, kode, potongan, min_tr_pemesanan):
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE DISKON SET Potongan = %s, MinTrPemesanan = %s WHERE Kode = %s",
                (potongan, min_tr_pemesanan, kode)
            )
            self.conn.commit()

    def delete_diskon(self, kode):
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM DISKON WHERE Kode = %s", (kode,))
            self.conn.commit()