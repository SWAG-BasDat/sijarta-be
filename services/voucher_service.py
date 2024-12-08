from psycopg2.extras import RealDictCursor
from decimal import Decimal
from uuid import uuid4
from datetime import date, timedelta
from models.voucher import Voucher

class VoucherService:
    def __init__(self, conn):
        self.conn = conn

    def get_all_vouchers(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT v.*, d.Potongan, d.MinTrPemesanan
                FROM VOUCHER v
                JOIN DISKON d ON v.Kode = d.Kode
                WHERE v.KuotaPenggunaan > 0
            """)
            return cur.fetchall()

    def get_voucher_by_kode(self, kode):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT v.*, d.Potongan, d.MinTrPemesanan
                FROM VOUCHER v
                JOIN DISKON d ON v.Kode = d.Kode
                WHERE v.Kode = %s
            """, (kode,))
            return cur.fetchone()

    def purchase_voucher(self, user_id, kode_voucher, metode_bayar_id):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT p.Id, u.SaldoMyPay, u.Nama 
                    FROM PELANGGAN p
                    JOIN "USER" u ON p.Id = u.Id
                    WHERE p.Id = %s
                """, (user_id,))
                pelanggan = cur.fetchone()
                
                if not pelanggan:
                    raise ValueError("User bukan merupakan pelanggan")

                voucher = self.get_voucher_by_kode(kode_voucher)
                if not voucher:
                    raise ValueError("Voucher tidak ditemukan")

                if voucher['kuotapenggunaan'] <= 0:
                    raise ValueError("Voucher sudah habis")

                cur.execute("""
                    SELECT Id, Nama FROM METODE_BAYAR WHERE Id = %s
                """, (metode_bayar_id,))
                metode_bayar = cur.fetchone()
                if not metode_bayar:
                    raise ValueError("Metode pembayaran tidak valid")

                if metode_bayar['nama'].upper() == 'MYPAY':
                    if Decimal(pelanggan['saldomypay']) < Decimal(voucher['harga']):
                        raise ValueError("Saldo MyPay tidak mencukupi")

                    cur.execute("""
                        SELECT Id FROM KATEGORI_TR_MYPAY 
                        WHERE NamaKategori = 'Pembelian Voucher'
                    """)
                    kategori = cur.fetchone()
                    if not kategori:
                        kategori_id = uuid4()
                        cur.execute("""
                            INSERT INTO KATEGORI_TR_MYPAY (Id, NamaKategori)
                            VALUES (%s, 'Pembelian Voucher')
                            RETURNING Id
                        """, (kategori_id,))
                        kategori = cur.fetchone()

                    mypay_id = uuid4()
                    cur.execute("""
                        INSERT INTO TR_MYPAY (Id, UserId, Tgl, Nominal, KategoriId, Keterangan)
                        VALUES (%s, %s, CURRENT_DATE, %s, %s, %s)
                    """, (mypay_id, user_id, -voucher['harga'], kategori['id'], kode_voucher))

                    new_balance = Decimal(pelanggan['saldomypay']) - Decimal(voucher['harga'])
                    cur.execute("""
                        UPDATE "USER"
                        SET SaldoMyPay = %s
                        WHERE Id = %s
                    """, (new_balance, user_id))

                tgl_awal = date.today()
                tgl_akhir = tgl_awal + timedelta(days=voucher['jmlhariberlaku'])

                purchase_id = uuid4()
                cur.execute("""
                    INSERT INTO TR_PEMBELIAN_VOUCHER 
                    (Id, TglAwal, TglAkhir, TelahDigunakan, IdPelanggan, IdVoucher, IdMetodeBayar)
                    VALUES (%s, %s, %s, 0, %s, %s, %s)
                """, (purchase_id, tgl_awal, tgl_akhir, user_id, kode_voucher, metode_bayar_id))

                cur.execute("""
                    UPDATE VOUCHER
                    SET KuotaPenggunaan = KuotaPenggunaan - 1
                    WHERE Kode = %s
                """, (kode_voucher,))

                self.conn.commit()

                response_data = {
                    "status": "success",
                    "message": "Voucher berhasil dibeli",
                    "data": {
                        "purchase_id": purchase_id,
                        "kode_voucher": kode_voucher,
                        "tgl_awal": tgl_awal,
                        "tgl_akhir": tgl_akhir
                    }
                }

                if metode_bayar['nama'].upper() == 'MYPAY':
                    response_data["data"].update({
                        "nama_user": pelanggan['nama'],
                        "harga": float(voucher['harga']),
                        "saldo_tersisa": float(new_balance)
                    })

                return response_data

        except ValueError as e:
            self.conn.rollback()
            raise ValueError(str(e))
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error sistem: {str(e)}")

    def get_user_vouchers(self, user_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    v.*, 
                    d.Potongan, 
                    d.MinTrPemesanan,
                    pv.TglAwal,
                    pv.TglAkhir,
                    pv.TelahDigunakan,
                    mb.Nama as MetodeBayar
                FROM TR_PEMBELIAN_VOUCHER pv
                JOIN VOUCHER v ON pv.IdVoucher = v.Kode
                JOIN DISKON d ON v.Kode = d.Kode
                JOIN METODE_BAYAR mb ON pv.IdMetodeBayar = mb.Id
                WHERE pv.IdPelanggan = %s 
                AND pv.TglAkhir >= CURRENT_DATE
            """, (user_id,))
            return cur.fetchall()
        
    def create_voucher(self, kode, jml_hari_berlaku, kuota_penggunaan, harga):
        with self.conn.cursor() as cur:
            cur.execute("SELECT 1 FROM DISKON WHERE Kode = %s", (kode,))
            if not cur.fetchone():
                raise ValueError(f"Discount code {kode} does not exist")
            
            cur.execute("SELECT 1 FROM VOUCHER WHERE Kode = %s", (kode,))
            if cur.fetchone():
                raise ValueError(f"Voucher with code {kode} already exists")

            if jml_hari_berlaku < 0:
                raise ValueError("Jumlah hari berlaku tidak boleh negatif")
            if kuota_penggunaan < 0:
                raise ValueError("Kuota penggunaan tidak boleh negatif")
            if harga < 0:
                raise ValueError("Harga tidak boleh negatif")
                
            cur.execute("""
                INSERT INTO VOUCHER (Kode, JmlHariBerlaku, KuotaPenggunaan, Harga) 
                VALUES (%s, %s, %s, %s)
            """, (kode, jml_hari_berlaku, kuota_penggunaan, harga))
            
            self.conn.commit()
            return Voucher(kode, jml_hari_berlaku, kuota_penggunaan, harga)