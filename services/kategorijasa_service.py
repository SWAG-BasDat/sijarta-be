from models.kategorijasa import KategoriJasa
from psycopg2.extras import RealDictCursor

class KategoriJasaService:
    def __init__(self, conn):
        self.conn = conn

    def get_all_kategori(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM KATEGORI_JASA")
            return cur.fetchall()
        
    def get_kategori_by_id(self, id_kategorijasa):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM KATEGORI_JASA WHERE Id = %s", (id_kategorijasa,))
            return cur.fetchone()

    def get_subkategori_by_kategori(self, id_kategorijasa):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * 
                FROM SUBKATEGORI_JASA 
                WHERE KategoriJasaId = %s
            """, (id_kategorijasa,))
            return cur.fetchall()

    def search_subkategori(self, keyword):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * 
                FROM SUBKATEGORI_JASA
                WHERE LOWER(NamaSubkategori) LIKE %s
            """, (f"%{keyword.lower()}%",))
            return cur.fetchall()
