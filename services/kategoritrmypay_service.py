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
        
    def get_selected_kategori(self):
        """
        Mendapatkan kategori transaksi tertentu (topup, bayar jasa, transfer, withdraw).
        """
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:  # Gunakan DictCursor
                cur.execute("""
                    SELECT id, namakategori
                    FROM KATEGORI_TR_MYPAY
                    WHERE namakategori IN (
                        'topup MyPay',
                        'membayar transaksi jasa',
                        'transfer MyPay ke pengguna lain',
                        'withdrawal MyPay ke rekening bank'
                    );
                """)
                return cur.fetchall()
        except Exception as e:
            raise Exception(f"Error saat mengambil kategori transaksi tertentu: {str(e)}")


    
