class StatusPekerjaanJasaService:
    def __init__(self, conn):
        self.conn = conn

    def get_status_pekerjaan(self, pekerja_id, nama_jasa=None, status=None):
        """
        Mendapatkan daftar pekerjaan jasa berdasarkan filter nama jasa dan status.
        :param pekerja_id: UUID pekerja.
        :param nama_jasa: Optional nama jasa untuk filter.
        :param status: Optional status pemesanan untuk filter.
        :return: List pekerjaan jasa.
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                    SELECT
                        tpj.Id AS PesananId,
                        skj.NamaSubkategori AS NamaJasa,
                        pel.Nama AS NamaPelanggan,
                        tpj.TglPemesanan,
                        tpj.TotalBiaya,
                        tpj.Sesi,
                        sp.Status
                    FROM TR_PEMESANAN_JASA tpj
                    JOIN SUBKATEGORI_JASA skj ON tpj.IdKategoriJasa = skj.Id
                    JOIN PELANGGAN pel ON tpj.IdPelanggan = pel.Id
                    JOIN STATUS_PESANAN sp ON tpj.IdStatus = sp.Id
                    WHERE tpj.IdPekerja = %s
                """
                params = [str(pekerja_id)]

                # Filter nama jasa
                if nama_jasa:
                    query += " AND LOWER(skj.NamaSubkategori) LIKE LOWER(%s)"
                    params.append(f"%{nama_jasa}%")

                # Filter status
                if status:
                    query += " AND LOWER(sp.Status) = LOWER(%s)"
                    params.append(status)

                query += " ORDER BY tpj.TglPemesanan DESC;"

                cur.execute(query, params)
                pesanan = cur.fetchall()

                return [{
                    "pesanan_id": row["PesananId"],
                    "nama_jasa": row["NamaJasa"],
                    "nama_pelanggan": row["NamaPelanggan"],
                    "tanggal_pemesanan": row["TglPemesanan"],
                    "total_biaya": row["TotalBiaya"],
                    "sesi": row["Sesi"],
                    "status": row["Status"]
                } for row in pesanan]
        except Exception as e:
            raise Exception(f"Error saat mendapatkan status pekerjaan: {str(e)}")

    def update_status_pemesanan(self, pekerja_id, pesanan_id, button_action):
        """
        Mengubah status pekerjaan jasa berdasarkan tombol yang ditekan.
        :param pekerja_id: UUID pekerja.
        :param pesanan_id: UUID pesanan jasa.
        :param button_action: Action dari tombol (1, 2, atau 3).
        :return: Pesan sukses.
        """
        try:
            with self.conn.cursor() as cur:
                # Pastikan pesanan milik pekerja
                cur.execute("""
                    SELECT tpj.IdStatus, sp.Status
                    FROM TR_PEMESANAN_JASA tpj
                    JOIN STATUS_PESANAN sp ON tpj.IdStatus = sp.Id
                    WHERE tpj.Id = %s AND tpj.IdPekerja = %s;
                """, (str(pesanan_id), str(pekerja_id)))
                pesanan = cur.fetchone()

                if not pesanan:
                    raise Exception("Pesanan tidak ditemukan atau tidak dimiliki pekerja ini.")

                # Tentukan status berikutnya berdasarkan tombol
                current_status = pesanan["Status"]
                next_status = None

                if button_action == 1 and current_status == "Menunggu pekerja berangkat":
                    next_status = "Pekerja tiba di lokasi"
                elif button_action == 2 and current_status == "Pekerja tiba di lokasi":
                    next_status = "Pelayanan jasa sedang dilakukan"
                elif button_action == 3 and current_status == "Pelayanan jasa sedang dilakukan":
                    next_status = "Pesanan selesai"

                if not next_status:
                    raise Exception("Aksi tidak valid untuk status saat ini.")

                # Update status pemesanan
                cur.execute("""
                    UPDATE TR_PEMESANAN_JASA
                    SET IdStatus = (SELECT Id FROM STATUS_PESANAN WHERE Status = %s)
                    WHERE Id = %s AND IdPekerja = %s;
                """, (next_status, str(pesanan_id), str(pekerja_id)))

                self.conn.commit()
                return {"message": f"Status berhasil diubah menjadi '{next_status}'."}
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error saat mengubah status pekerjaan: {str(e)}")
