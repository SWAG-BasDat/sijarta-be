from datetime import datetime, timedelta
from uuid import UUID


class PekerjaKategoriJasaService:
    def __init__(self, conn):
        self.conn = conn

    def get_pesanan_tersedia(self, pekerja_id, kategori_id=None, subkategori_id=None):
        """
        Mendapatkan daftar pesanan jasa yang tersedia untuk pekerja.
        :param pekerja_id: UUID pekerja.
        :param kategori_id: Optional UUID kategori jasa untuk filter.
        :param subkategori_id: Optional UUID subkategori jasa untuk filter.
        :return: List pesanan jasa.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT KategoriJasaId
                    FROM PEKERJA_KATEGORI_JASA
                    WHERE PekerjaId = %s;
                """, (str(pekerja_id),))
                kategori_jasa_pekerja = [row['KategoriJasaId'] for row in cur.fetchall()]

                if not kategori_jasa_pekerja:
                    raise Exception("Pekerja tidak memiliki kategori jasa.")

                query = """
                    SELECT
                        tpj.Id AS PesananId,
                        tpj.TglPemesanan,
                        tpj.TotalBiaya,
                        tpj.Sesi,
                        skj.NamaSubkategori,
                        pel.Nama AS NamaPelanggan
                    FROM TR_PEMESANAN_JASA tpj
                    JOIN SUBKATEGORI_JASA skj ON tpj.IdKategoriJasa = skj.Id
                    JOIN PELANGGAN pel ON tpj.IdPelanggan = pel.Id
                    WHERE tpj.IdKategoriJasa IN %s
                    AND tpj.IdStatus = (SELECT Id FROM STATUS_PESANAN WHERE Status = 'Mencari pekerja terdekat')
                """
                params = [tuple(kategori_jasa_pekerja)]

                if kategori_id:
                    query += " AND skj.KategoriJasaId = %s"
                    params.append(str(kategori_id))

                if subkategori_id:
                    query += " AND skj.Id = %s"
                    params.append(str(subkategori_id))

                query += " ORDER BY tpj.TglPemesanan ASC;"

                cur.execute(query, params)
                pesanan = cur.fetchall()

                return [{
                    "pesanan_id": row["PesananId"],
                    "tanggal_pemesanan": row["TglPemesanan"],
                    "total_biaya": row["TotalBiaya"],
                    "sesi": row["Sesi"],
                    "nama_subkategori": row["NamaSubkategori"],
                    "nama_pelanggan": row["NamaPelanggan"]
                } for row in pesanan]

        except Exception as e:
            raise Exception(f"Error saat mendapatkan pesanan tersedia: {str(e)}")
        
    #update
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


    def get_kategori_jasa(self, pekerja_id):
        """
        Mendapatkan kategori jasa yang dapat dilakukan oleh pekerja.
        :param pekerja_id: UUID pekerja.
        :return: List kategori jasa.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT kj.Id, kj.NamaKategori
                    FROM PEKERJA_KATEGORI_JASA pkj
                    JOIN KATEGORI_JASA kj ON pkj.KategoriJasaId = kj.Id
                    WHERE pkj.PekerjaId = %s;
                """, (str(pekerja_id),))
                return [{"id": row["Id"], "nama": row["NamaKategori"]} for row in cur.fetchall()]
        except Exception as e:
            raise Exception(f"Error saat mendapatkan kategori jasa: {str(e)}")

    def get_subkategori_jasa(self, kategori_id):
        """
        Mendapatkan subkategori jasa berdasarkan kategori.
        :param kategori_id: UUID kategori jasa.
        :return: List subkategori jasa.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT Id, NamaSubkategori
                    FROM SUBKATEGORI_JASA
                    WHERE KategoriJasaId = %s;
                """, (str(kategori_id),))
                return [{"id": row["Id"], "nama": row["NamaSubkategori"]} for row in cur.fetchall()]
        except Exception as e:
            raise Exception(f"Error saat mendapatkan subkategori jasa: {str(e)}")
