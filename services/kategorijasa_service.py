from models.kategorijasa import KategoriJasa

class KategoriJasaService:
    def __init__(self, conn):
        self.conn = conn

    def get_all_kategori(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT NamaKategori FROM KATEGORI_JASA")
            return cur.fetchall()
        
    def get_kategori_by_id(self, kategori_jasa):
        with self.conn.cursor() as cur:
            cur.execute("SELECT NamaKategori FROM KATEGORI_JASA WHERE NamaKategori = %s", (kategori_jasa))
            return cur.fetchone()
