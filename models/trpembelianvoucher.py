class TrPembelianVoucher:
    def __init__(self, id, tgl_awal, tgl_akhir, telah_digunakan, id_pelanggan=None, id_voucher=None, id_metode_bayar=None):
        self.id = id
        self.tgl_awal = tgl_awal
        self.tgl_akhir = tgl_akhir
        self.telah_digunakan = telah_digunakan
        self.id_pelanggan = id_pelanggan
        self.id_voucher = id_voucher
        self.id_metode_bayar = id_metode_bayar

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS TR_PEMBELIAN_VOUCHER (
                    Id UUID PRIMARY KEY,
                    TglAwal DATE NOT NULL,
                    TglAkhir DATE NOT NULL,
                    TelahDigunakan INT NOT NULL CHECK (TelahDigunakan >= 0),
                    IdPelanggan UUID,
                    IdVoucher VARCHAR,
                    IdMetodeBayar UUID,
                    FOREIGN KEY (IdPelanggan) REFERENCES PELANGGAN (Id),
                    FOREIGN KEY (IdVoucher) REFERENCES VOUCHER (Kode),
                    FOREIGN KEY (IdMetodeBayar) REFERENCES METODE_BAYAR (Id)
                )
            """)
            conn.commit()