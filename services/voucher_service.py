from psycopg2.extras import RealDictCursor
from decimal import Decimal
from uuid import uuid4

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

    def get_user_vouchers(self, user_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT v.*, d.Potongan, d.MinTrPemesanan, t.Tgl as TanggalBeli
                FROM TR_MYPAY t
                JOIN VOUCHER v ON t.Keterangan = v.Kode
                JOIN DISKON d ON v.Kode = d.Kode
                WHERE t.UserId = %s 
                AND t.KategoriId = (
                    SELECT Id FROM KATEGORI_TR_MYPAY 
                    WHERE NamaKategori = 'Pembelian Voucher'
                )
            """, (user_id,))
            return cur.fetchall()

    def purchase_voucher_with_mypay(self, user_id, kode_voucher):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                voucher = self.get_voucher_by_kode(kode_voucher)
                if not voucher:
                    raise ValueError("Voucher tidak ditemukan")

                if voucher['kuotapenggunaan'] <= 0:
                    raise ValueError("Voucher sudah habis")

                cur.execute("""
                    SELECT SaldoMyPay, Nama 
                    FROM "USER"
                    WHERE Id = %s
                """, (user_id,))
                user = cur.fetchone()
                
                if not user:
                    raise ValueError("User tidak ditemukan")


                if Decimal(user['saldomypay']) < Decimal(voucher['harga']):
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

                transaction_id = uuid4()
                cur.execute("""
                    INSERT INTO TR_MYPAY (Id, UserId, Tgl, Nominal, KategoriId, Keterangan)
                    VALUES (%s, %s, CURRENT_DATE, %s, %s, %s)
                """, (transaction_id, user_id, -voucher['harga'], kategori['id'], kode_voucher))

                new_balance = Decimal(user['saldomypay']) - Decimal(voucher['harga'])
                cur.execute("""
                    UPDATE "USER"
                    SET SaldoMyPay = %s
                    WHERE Id = %s
                """, (new_balance, user_id))

                cur.execute("""
                    UPDATE VOUCHER
                    SET KuotaPenggunaan = KuotaPenggunaan - 1
                    WHERE Kode = %s
                """, (kode_voucher,))

                self.conn.commit()

                return {
                    "status": "success",
                    "message": "Voucher berhasil dibeli",
                    "data": {
                        "nama_user": user['nama'],
                        "kode_voucher": kode_voucher,
                        "harga": float(voucher['harga']),
                        "saldo_tersisa": float(new_balance)
                    }
                }

        except ValueError as e:
            self.conn.rollback()
            raise ValueError(str(e))
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error sistem: {str(e)}")