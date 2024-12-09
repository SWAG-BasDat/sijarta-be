import datetime
from psycopg2.extras import DictCursor


class StatusPekerjaanJasaService:
    def __init__(self, conn):
        self.conn = conn

    def get_status_pekerjaan(self, pekerja_id, nama_jasa=None, status=None):
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                query = """
                    SELECT DISTINCTgi
                        tpj.id AS pesananid,
                        skj.namasubkategori AS namajasa,
                        usr.nama AS namapelanggan,
                        tpj.tglpemesanan,
                        tpj.totalbiaya,
                        tpj.sesi,
                        sp.status
                    FROM TR_PEMESANAN_JASA tpj
                    JOIN SESI_LAYANAN sl ON tpj.idkategorijasa = sl.subkategoriid
                    AND tpj.Sesi = sl.Sesi
                    JOIN SUBKATEGORI_JASA skj ON sl.subkategoriid = skj.id
                    JOIN PELANGGAN pel ON tpj.idpelanggan = pel.id
                    JOIN "USER" usr ON pel.id = usr.id
                    JOIN TR_PEMESANAN_STATUS tps ON tpj.id = tps.idtrpemesanan
                    JOIN STATUS_PESANAN sp ON tps.idstatus = sp.id
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
                    "pesanan_id": row["pesananid"],
                    "nama_jasa": row["namajasa"],
                    "nama_pelanggan": row["namapelanggan"],
                    "tanggal_pemesanan": row["tglpemesanan"],
                    "total_biaya": row["totalbiaya"],
                    "sesi": row["sesi"],
                    "status": row["status"]
                } for row in pesanan]
        except Exception as e:
            raise Exception(f"Error saat mendapatkan status pekerjaan: {str(e)}")

    def update_status_pemesanan(self, pekerja_id, pesanan_id, button_action):
        try:
            with self.conn.cursor() as cur:
                # Pastikan pesanan milik pekerja dan ambil status terakhir
                cur.execute("""
                    SELECT ps.IdStatus, sp.Status
                    FROM TR_PEMESANAN_STATUS ps
                    JOIN STATUS_PESANAN sp ON ps.IdStatus = sp.Id
                    WHERE ps.IdTrPemesanan = %s
                    AND ps.TglWaktu = (
                        SELECT MAX(TglWaktu)
                        FROM TR_PEMESANAN_STATUS
                        WHERE IdTrPemesanan = %s
                    );
                """, (str(pesanan_id), str(pesanan_id)))
                pesanan = cur.fetchone()

                if not pesanan:
                    raise Exception("Pesanan tidak ditemukan atau status tidak valid.")

                # Pastikan pekerja terkait dengan pesanan
                cur.execute("""
                    SELECT Id
                    FROM TR_PEMESANAN_JASA
                    WHERE Id = %s AND IdPekerja = %s;
                """, (str(pesanan_id), str(pekerja_id)))
                pekerja_pesanan = cur.fetchone()

                if not pekerja_pesanan:
                    raise Exception("Pesanan tidak dimiliki pekerja ini.")

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

                # Update status di TR_PEMESANAN_STATUS
                cur.execute("""
                    UPDATE TR_PEMESANAN_STATUS
                    SET IdStatus = (SELECT Id FROM STATUS_PESANAN WHERE Status = %s),
                        TglWaktu = %s
                    WHERE IdTrPemesanan = %s
                    AND TglWaktu = (
                        SELECT MAX(TglWaktu)
                        FROM TR_PEMESANAN_STATUS
                        WHERE IdTrPemesanan = %s
                    );
                """, (next_status, datetime.now(), str(pesanan_id), str(pesanan_id)))

                self.conn.commit()
                return {"message": f"Status berhasil diubah menjadi '{next_status}'."}

        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error saat mengubah status pekerjaan: {str(e)}")
