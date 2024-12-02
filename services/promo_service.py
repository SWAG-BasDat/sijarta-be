from models.promo import Promo

class PromoService:
    def __init__(self, conn):
        self.conn = conn

    def get_all_promos(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT p.*, d.Potongan, d.MinTrPemesanan 
                FROM PROMO p
                JOIN DISKON d ON p.Kode = d.Kode
                WHERE p.TglAkhirBerlaku >= CURRENT_DATE
                ORDER BY p.TglAkhirBerlaku
            """)
            return cur.fetchall()

    def get_promo_by_kode(self, kode):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT p.*, d.Potongan, d.MinTrPemesanan 
                FROM PROMO p
                JOIN DISKON d ON p.Kode = d.Kode
                WHERE p.Kode = %s AND p.TglAkhirBerlaku >= CURRENT_DATE
            """, (kode,))
            return cur.fetchone()