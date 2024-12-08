from models.kategoritrmypay import KategoriTrMyPay

class KategoriTrMyPayService:
    def __init__(self, conn):
        self.conn = conn

    def get_kategori_id_by_name(self, nama_kategori):
        """
        Mendapatkan ID kategori berdasarkan nama kategori
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT Id FROM KATEGORI_TR_MYPAY WHERE NamaKategori = %s;
                """, (nama_kategori,))
                kategori = cur.fetchone()
                if not kategori:
                    raise Exception(f"Kategori dengan nama '{nama_kategori}' tidak ditemukan.")
                return kategori['id']
        except Exception as e:
            raise Exception(f"Error saat mengambil kategori: {str(e)}")
        
    def get_all_kategori(self):
        """
        Mendapatkan semua kategori transaksi MyPay
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM KATEGORI_TR_MYPAY;
                """)
                return cur.fetchall()
        except Exception as e:
            raise Exception(f"Error saat mengambil semua kategori: {str(e)}")
    
