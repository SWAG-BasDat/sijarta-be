from models.voucher import Voucher

class VoucherService:
    def __init__(self, conn):
        self.conn = conn

    def get_all_vouchers(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT v.*, d.Potongan, d.MinTrPemesanan 
                FROM VOUCHER v
                JOIN DISKON d ON v.Kode = d.Kode
            """)
            return cur.fetchall()

    def get_voucher_by_kode(self, kode):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT v.*, d.Potongan, d.MinTrPemesanan 
                FROM VOUCHER v
                JOIN DISKON d ON v.Kode = d.Kode
                WHERE v.Kode = %s
            """, (kode,))
            return cur.fetchone()