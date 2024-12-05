class TrPemesananJasa:
    def __init__(self, id, tgl_pemesanan, tgl_pekerjaan, waktu_pekerjaan, total_biaya, id_pelanggan, id_pekerja, id_kategori_jasa, sesi, id_diskon, id_metode_bayar):
        self.id = id
        self.tgl_pemesanan = tgl_pemesanan
        self.tgl_pekerjaan = tgl_pekerjaan
        self.waktu_pekerjaan = waktu_pekerjaan
        self.total_biaya = total_biaya
        self.id_pelanggan = id_pelanggan
        self.id_pekerja = id_pekerja
        self.id_kategori_jasa = id_kategori_jasa
        self.sesi = sesi
        self.id_diskon = id_diskon
        self.id_metode_bayar = id_metode_bayar

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS TR_PEMESANAN_JASA (
                    Id UUID PRIMARY KEY,
                    TglPemesanan DATE NOT NULL,
                    TglPekerjaan DATE NOT NULL,
                    WaktuPekerjaan TIMESTAMP NOT NULL,
                    TotalBiaya DECIMAL NOT NULL CHECK (TotalBiaya >= 0),
                    IdPelanggan UUID,
                    IdPekerja UUID,
                    IdKategoriJasa UUID,
                    Sesi INT,
                    IdDiskon VARCHAR(50),
                    IdMetodeBayar UUID,
                    FOREIGN KEY (IdPelanggan) REFERENCES PELANGGAN (Id),
                    FOREIGN KEY (IdPekerja) REFERENCES PEKERJA (Id),
                    FOREIGN KEY (IdKategoriJasa, Sesi) REFERENCES SESI_LAYANAN (SubkategoriId, Sesi),
                    FOREIGN KEY (IdDiskon) REFERENCES DISKON (Kode),
                    FOREIGN KEY (IdMetodeBayar) REFERENCES METODE_BAYAR (Id)
                );
            """)
            conn.commit()