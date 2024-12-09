from datetime import datetime, timedelta
from uuid import UUID


class PekerjaKategoriJasaService:
    def __init__(self, conn):
        self.conn = conn

    def get_pesanan_tersedia(self, pekerja_id, kategori_id=None, subkategori_id=None):
        try:
            with self.conn.cursor() as cur:
                # Ambil kategori jasa yang dapat dilakukan oleh pekerja
                cur.execute("""
                    SELECT kategorijasaid
                    FROM PEKERJA_KATEGORI_JASA
                    WHERE pekerjaid = %s;
                """, (str(pekerja_id),))
                kategori_jasa_pekerja = [row['kategorijasaid'] for row in cur.fetchall()]

                if not kategori_jasa_pekerja:
                    raise Exception("Pekerja tidak memiliki kategori jasa.")

                # Query pesanan jasa dengan join tabel status
                query = """
                    SELECT
                        tpj.id AS pesananid,
                        tpj.tglpemesanan,
                        tpj.totalbiaya,
                        tpj.sesi,
                        skj.namasubkategori,
                        usr.nama AS namapelanggan
                    FROM TR_PEMESANAN_JASA tpj
                    JOIN SESI_LAYANAN sl ON tpj.idkategorijasa = sl.subkategoriid
                    JOIN SUBKATEGORI_JASA skj ON sl.subkategoriid = skj.id
                    JOIN PELANGGAN pel ON tpj.idpelanggan = pel.id
                    JOIN "USER" usr ON pel.id = usr.id
                    JOIN TR_PEMESANAN_STATUS tps ON tpj.id = tps.idtrpemesanan
                    JOIN STATUS_PESANAN sp ON tps.idstatus = sp.id
                    WHERE sl.subkategoriid IN %s
                    AND sp.status = 'Mencari pekerja terdekat'
                """
                params = [tuple(kategori_jasa_pekerja)]

                # Filter berdasarkan kategori jasa jika diberikan
                if kategori_id:
                    query += " AND skj.kategorijasaid = %s"
                    params.append(str(kategori_id))

                # Filter berdasarkan subkategori jasa jika diberikan
                if subkategori_id:
                    query += " AND skj.id = %s"
                    params.append(str(subkategori_id))

                query += " ORDER BY tpj.tglpemesanan ASC;"

                cur.execute(query, params)
                pesanan = cur.fetchall()

                # Format hasil query menjadi list of dictionaries
                return [
                    {
                        "pesanan_id": row["pesananid"],
                        "tanggal_pemesanan": row["tglpemesanan"],
                        "total_biaya": row["totalbiaya"],
                        "sesi": row["sesi"],
                        "nama_subkategori": row["namasubkategori"],
                        "nama_pelanggan": row["namapelanggan"]
                    }
                    for row in pesanan
                ]

        except Exception as e:
            raise Exception(f"Error saat mendapatkan pesanan tersedia: {str(e)}")
        
    def get_kategori_jasa(self, pekerja_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT kj.id, kj.namakategori
                    FROM PEKERJA_KATEGORI_JASA pkj
                    JOIN KATEGORI_JASA kj ON pkj.kategorijasaid = kj.id
                    WHERE pkj.pekerjaid = %s;
                """, (str(pekerja_id),))
                return [{"id": row["Id"], "nama": row["namakategori"]} for row in cur.fetchall()]
        except Exception as e:
            raise Exception(f"Error saat mendapatkan kategori jasa: {str(e)}")

    def get_subkategori_jasa(self, kategori_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, namasubkategori
                    FROM SUBKATEGORI_JASA
                    WHERE kategorijasaid = %s;
                """, (str(kategori_id),))
                return [{"id": row["Id"], "nama": row["namasubkategori"]} for row in cur.fetchall()]
        except Exception as e:
            raise Exception(f"Error saat mendapatkan subkategori jasa: {str(e)}")
        
        
    #update belum fix
    def ambil_pesanan(self, pekerja_id, pesanan_id):
        """
        Mengambil pesanan oleh pekerja.
        :param pekerja_id: UUID pekerja.
        :param pesanan_id: UUID pesanan jasa.
        :return: Pesan sukses.
        """
        try:
            with self.conn.cursor() as cur:
                # Validasi status pesanan saat ini adalah 'Mencari pekerja terdekat'
                cur.execute("""
                    SELECT MAX(ps.IdStatus) AS IdStatus, pj.Sesi, pj.TglPemesanan
                    FROM TR_PEMESANAN_JASA pj
                    JOIN TR_PEMESANAN_STATUS ps ON pj.Id = ps.IdTrPemesanan
                    WHERE pj.Id = %s
                    GROUP BY pj.Id, pj.Sesi, pj.TglPemesanan;
                """, (str(pesanan_id),))
                pesanan = cur.fetchone()

                if not pesanan:
                    raise Exception("Pesanan tidak ditemukan.")

                # Ambil ID status 'Mencari pekerja terdekat'
                cur.execute("""
                    SELECT Id 
                    FROM STATUS_PESANAN 
                    WHERE Status = 'Mencari pekerja terdekat';
                """)
                id_status_mencari = cur.fetchone()['id']

                # Pastikan statusnya adalah 'Mencari pekerja terdekat'
                if pesanan["idstatus"] != id_status_mencari:
                    raise Exception("Pesanan tidak tersedia untuk diambil.")

                # Hitung tanggal pekerjaan dan waktu selesai
                sesi = pesanan["sesi"]
                tanggal_mulai = datetime.now().date()
                tanggal_selesai = tanggal_mulai + timedelta(days=sesi)

                # Ambil ID status 'Menunggu pekerja berangkat'
                cur.execute("""
                    SELECT Id 
                    FROM STATUS_PESANAN 
                    WHERE Status = 'Menunggu pekerja berangkat';
                """)
                id_status_menunggu = cur.fetchone()['id']

                # Update status di TR_PEMESANAN_STATUS
                cur.execute("""
                    UPDATE TR_PEMESANAN_STATUS
                    SET IdStatus = %s, TglWaktu = %s
                    WHERE IdTrPemesanan = %s
                    AND IdStatus = %s;
                """, (id_status_menunggu, datetime.now(), str(pesanan_id), id_status_mencari))

                # Update TR_PEMESANAN_JASA untuk menambahkan pekerja dan jadwal pekerjaan
                cur.execute("""
                    UPDATE TR_PEMESANAN_JASA
                    SET IdPekerja = %s,
                        TglPekerjaan = %s,
                        WaktuPekerjaan = %s
                    WHERE Id = %s;
                """, (str(pekerja_id), tanggal_mulai, tanggal_selesai, str(pesanan_id)))

                self.conn.commit()
                return {"message": "Pesanan berhasil diambil dan status diubah menjadi 'Menunggu pekerja berangkat'."}

        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error saat mengambil pesanan: {str(e)}")
