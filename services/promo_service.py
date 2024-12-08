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
        
    def create_promo(self, kode, tgl_akhir_berlaku):
        with self.conn.cursor() as cur:
            cur.execute("SELECT 1 FROM DISKON WHERE Kode = %s", (kode,))
            if not cur.fetchone():
                raise ValueError(f"Discount code {kode} does not exist")
            
            cur.execute("SELECT 1 FROM PROMO WHERE Kode = %s", (kode,))
            if cur.fetchone():
                raise ValueError(f"Promo with code {kode} already exists")
            
            cur.execute(
                "INSERT INTO PROMO (Kode, TglAkhirBerlaku) VALUES (%s, %s)",
                (kode, tgl_akhir_berlaku)
            )
            self.conn.commit()
            
            return Promo(kode, tgl_akhir_berlaku)