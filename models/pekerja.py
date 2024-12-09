class Pekerja:
    def __init__(self, id, nama_bank, nomor_rekening, npwp, link_foto, jml_pesanan_selesai):
        self.id = id
        self.nama_bank = nama_bank
        self.nomor_rekening = nomor_rekening
        self.npwp = npwp
        self.link_foto = link_foto
        self.rating = 0
        self.jml_pesanan_selesai = 0

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS PEKERJA (
                    Id UUID,
                    NamaBank VARCHAR,
                    NomorRekening VARCHAR,
                    NPWP VARCHAR,
                    LinkFoto VARCHAR,
                    Rating FLOAT,
                    JmlPesananSelesai INT,
                    FOREIGN KEY (Id) REFERENCES "USER"(Id),
                    CONSTRAINT unique_pekerja_id UNIQUE (Id)
                );
            """)
            conn.commit()

    def to_dict(self):
        return {
            'id': str(self.id),
            'nama_bank': self.nama_bank,
            'nomor_rekening': self.nomor_rekening,
            'npwp': self.npwp,
            'link_foto': self.link_foto,
            'rating': self.rating,
            'jml_pesanan_selesai': self.jml_pesanan_selesai,
        }