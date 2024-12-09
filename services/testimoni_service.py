from datetime import date, datetime
from psycopg2.extras import RealDictCursor

class TestimoniService:
    def __init__(self, conn):
        self.conn = conn

    def get_testimoni_by_subkategori(self, id_subkategori):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    t.IdTrPemesanan as idtrpemesanan,
                    t.Tgl as tgl,
                    t.Teks as teks,
                    t.Rating as rating,
                    u.Nama as nama_pelanggan,
                    kj.NamaKategori as nama_jasa
                FROM TESTIMONI t
                JOIN TR_PEMESANAN_JASA tj ON t.IdTrPemesanan = tj.Id
                JOIN SUBKATEGORI_JASA sj ON tj.IdKategoriJasa = sj.Id
                JOIN KATEGORI_JASA kj ON sj.KategoriJasaId = kj.Id
                JOIN PELANGGAN p ON tj.IdPelanggan = p.Id
                JOIN "USER" u ON p.Id = u.Id
                WHERE sj.Id = %s
                ORDER BY t.Tgl DESC
            """, (id_subkategori,))
            testimonis = cur.fetchall()
            return [dict(t) for t in testimonis]

    def get_testimoni_by_order(self, id_tr_pemesanan):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    t.id_tr_pemesanan,
                    t.tgl,
                    t.teks,
                    t.rating
                FROM testimoni t
                WHERE t.id_tr_pemesanan = %s
            """, (id_tr_pemesanan,))
            return dict(cur.fetchone()) if cur.fetchone() else None

    def check_order_status(self, id_tr_pemesanan):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    tps.id_status,
                    sp.nama as status_nama
                FROM tr_pemesanan_status tps
                JOIN status_pesanan sp ON tps.id_status = sp.id
                WHERE tps.id_tr_pemesanan = %s
                ORDER BY tps.created_at DESC
                LIMIT 1
            """, (id_tr_pemesanan,))
            result = cur.fetchone()
            
            if not result:
                return False, "Pesanan tidak ditemukan"
                
            return result['status_nama'] == 'Pesanan Selesai', "Pesanan harus dalam status 'Pesanan Selesai'"

    def can_add_testimoni(self, id_tr_pemesanan):
        try:
            is_completed, message = self.check_order_status(id_tr_pemesanan)
            if not is_completed:
                return False, message

            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*)
                    FROM testimoni
                    WHERE id_tr_pemesanan = %s
                """, (id_tr_pemesanan,))
                count = cur.fetchone()[0]
                
                if count > 0:
                    return False, "Testimonial sudah pernah ditambahkan untuk pesanan ini"
                
            return True, "Bisa menambahkan testimoni"
        except Exception as e:
            return False, f"Error checking testimoni eligibility: {str(e)}"

    def create_testimoni(self, id_tr_pemesanan, teks, rating):
        try:
            if not teks or len(teks.strip()) == 0:
                raise ValueError("Teks testimoni tidak boleh kosong")
                
            if not isinstance(rating, int) or not (1 <= rating <= 5):
                raise ValueError("Rating harus berupa angka antara 1 sampai 5")

            can_add, message = self.can_add_testimoni(id_tr_pemesanan)
            if not can_add:
                raise ValueError(message)

            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO testimoni (id_tr_pemesanan, tgl, teks, rating)
                    VALUES (%s, CURRENT_DATE, %s, %s)
                    RETURNING id_tr_pemesanan, tgl, teks, rating
                """, (id_tr_pemesanan, teks, rating))
                
                new_testimoni = dict(cur.fetchone())
                
                cur.execute("""
                    SELECT 
                        t.*,
                        p.nama as nama_pelanggan,
                        tj.nama_jasa
                    FROM testimoni t
                    JOIN tr_pemesanan_jasa tj ON t.id_tr_pemesanan = tj.id
                    JOIN pelanggan p ON tj.id_pelanggan = p.id
                    WHERE t.id_tr_pemesanan = %s
                """, (id_tr_pemesanan,))
                
                self.conn.commit()
                return dict(cur.fetchone())

        except Exception as e:
            self.conn.rollback()
            raise ValueError(f"Gagal membuat testimoni: {str(e)}")

    def delete_testimoni(self, id_tr_pemesanan):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM testimoni 
                    WHERE id_tr_pemesanan = %s
                """, (id_tr_pemesanan,))
                
                testimoni = cur.fetchone()
                if not testimoni:
                    raise ValueError("Testimoni tidak ditemukan")

                cur.execute("""
                    DELETE FROM testimoni
                    WHERE id_tr_pemesanan = %s
                    RETURNING *
                """, (id_tr_pemesanan,))
                
                deleted = dict(cur.fetchone())
                self.conn.commit()
                return deleted

        except Exception as e:
            self.conn.rollback()
            raise ValueError(f"Gagal menghapus testimoni: {str(e)}")