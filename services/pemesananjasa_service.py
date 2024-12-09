from models.trpemesananjasa import TrPemesananJasa
from datetime import date, datetime

class PemesananJasaService:
    def __init__(self, conn):
        self.conn = conn;

    def create_pesanan_jasa(self, tanggal_pemesanan, diskon_id, metode_bayar_id, pelanggan_id):
        with self.conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    SELECT Nominal FROM DISKON WHERE Id = %s
                    """,
                    (diskon_id,)
                )
                diskon = cur.fetchone()
                diskon_nominal = diskon[0] if diskon else 0

                cur.execute(
                    """
                    INSERT INTO TR_PEMESANAN_JASA (TanggalPemesanan, DiskonId, MetodeBayarId, PelangganId, TotalPembayaran, StatusPesanan)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING Id
                    """,
                    (
                        tanggal_pemesanan,
                        diskon_id,
                        metode_bayar_id,
                        pelanggan_id,
                        -diskon_nominal,
                        'Menunggu Pembayaran',
                    ),
                )
                pesanan_id = cur.fetchone()[0]
                self.conn.commit()
                return pesanan_id
            except Exception as e:
                self.conn.rollback()
                raise e
            
    def get_pesanan_by_pelanggan(self, pelanggan_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT tpj.Id, tpj.TanggalPemesanan, tpj.TotalPembayaran, tpj.StatusPesanan,
                        sl.Sesi, sl.Harga,
                        u.Nama AS NamaPekerja
                    FROM TR_PEMESANAN_JASA tpj
                    LEFT JOIN SESI_LAYANAN sl ON tpj.Id = sl.SubkategoriId
                    LEFT JOIN PEKERJA p ON sl.SubkategoriId = p.id
                    LEFT JOIN "USER" ON p.Id = u.Id
                    WHERE tpj.PelangganId = %s
                    ORDER BY tpj.TanggalPemesanan DESC
                    """,
                    (pelanggan_id,)
                )
                return cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Database error in get_pesanan_by_pelanggan: {str(e)}")
        
    def update_status_pesanan(self, pesanan_id, status):
        with self.conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    UPDATE TR_PEMESANAN_JASA
                    SET StatusPesanan = %s
                    WHERE Id = %s
                    """,
                    (status, pesanan_id),
                )
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                raise e

    def cancel_pesanan(self, pesanan_id):
        with self.conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    UPDATE TR_PEMESANAN_JASA
                    SET StatusPesanan = 'Dibatalkan'
                    WHERE Id = %s
                    """,
                    (pesanan_id,)
                )
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                raise e
