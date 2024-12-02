from datetime import date
from models.testimoni import Testimoni

class TestimoniService:
    def __init__(self, conn):
        self.conn = conn

    def get_testimoni_by_subkategori(self, id_subkategori):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    t.*,
                    tj.NamaJasa,
                    p.Nama as NamaPelanggan
                FROM TESTIMONI t
                JOIN TR_PEMESANAN_JASA tj ON t.IdTrPemesanan = tj.Id
                JOIN PELANGGAN p ON tj.IdPelanggan = p.Id
                WHERE tj.IdSubKategori = %s
                ORDER BY t.Tgl DESC
            """, (id_subkategori,))
            return cur.fetchall()

    def check_order_status(self, id_tr_pemesanan):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT Status 
                FROM TR_PEMESANAN_JASA 
                WHERE Id = %s
            """, (id_tr_pemesanan,))
            result = cur.fetchone()
            if not result:
                return False
            return result['status'] == 'Pesanan Selesai'

    def can_add_testimoni(self, id_tr_pemesanan):
        try:
            if not self.check_order_status(id_tr_pemesanan):
                return False, "Order harus dalam status 'Pesanan Selesai'"

            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM TESTIMONI 
                    WHERE IdTrPemesanan = %s
                """, (id_tr_pemesanan,))
                count = cur.fetchone()['count']
                if count > 0:
                    return False, "Testimonial sudah pernah ditambahkan"

            return True, "Testimoni berhasil ditambahkan"
        except Exception as e:
            return False, str(e)

    def create_testimoni(self, id_tr_pemesanan, teks, rating):
        try:
            can_add, message = self.can_add_testimoni(id_tr_pemesanan)
            if not can_add:
                raise Exception(message)

            if not (1 <= rating <= 5):
                raise Exception("Rating harus berada di antara 1 hingga 5")

            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO TESTIMONI (IdTrPemesanan, Tgl, Teks, Rating)
                    VALUES (%s, CURRENT_DATE, %s, %s)
                    RETURNING *
                """, (id_tr_pemesanan, teks, rating))
                
                new_testimoni = cur.fetchone()

                cur.execute("""
                    SELECT 
                        t.*,
                        tj.NamaJasa,
                        p.Nama as NamaPelanggan
                    FROM TESTIMONI t
                    JOIN TR_PEMESANAN_JASA tj ON t.IdTrPemesanan = tj.Id
                    JOIN PELANGGAN p ON tj.IdPelanggan = p.Id
                    WHERE t.IdTrPemesanan = %s AND t.Tgl = CURRENT_DATE
                """, (id_tr_pemesanan,))
                
                self.conn.commit()
                return cur.fetchone()
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_testimoni(self, id_tr_pemesanan, tgl):
        try:
            with self.conn.cursor() as cur:
    
                if not self.check_order_status(id_tr_pemesanan):
                    raise Exception("Tidak bisa menghapus testimoni karena order belum selesai")

                cur.execute("""
                    DELETE FROM TESTIMONI 
                    WHERE IdTrPemesanan = %s AND Tgl = %s
                    RETURNING *
                """, (id_tr_pemesanan, tgl))
                
                deleted_testimoni = cur.fetchone()
                if not deleted_testimoni:
                    raise Exception("Testimoni not found")
                
                self.conn.commit()
                return deleted_testimoni
        except Exception as e:
            self.conn.rollback()
            raise e