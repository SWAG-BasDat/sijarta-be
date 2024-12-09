from datetime import datetime, timedelta
from uuid import UUID
from psycopg2.extras import DictCursor

class PekerjaKategoriJasaService:
    def __init__(self, conn):
        self.conn = conn

    def get_pesanan_tersedia(self, pekerja_id, kategori_id=None, subkategori_id=None):
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT kategorijasaid
                    FROM PEKERJA_KATEGORI_JASA
                    WHERE pekerjaid = %s;
                """, (str(pekerja_id),))
                kategori_jasa_pekerja = [row['kategorijasaid'] for row in cur.fetchall()]
                print(f"Kategori jasa pekerja: {kategori_jasa_pekerja}")  
                if not kategori_jasa_pekerja:
                    return []

                query = """
                    SELECT DISTINCT
                        tpj.id AS pesananid,
                        tpj.tglpemesanan,
                        tpj.totalbiaya,
                        tpj.sesi,
                        skj.namasubkategori,
                        usr.nama AS namapelanggan
                    FROM TR_PEMESANAN_JASA tpj
                    JOIN SESI_LAYANAN sl ON tpj.IdKategoriJasa = sl.SubkategoriId 
                        AND tpj.Sesi = sl.Sesi
                    JOIN SUBKATEGORI_JASA skj ON sl.SubkategoriId = skj.id
                    JOIN PELANGGAN pel ON tpj.idpelanggan = pel.id
                    JOIN "USER" usr ON pel.id = usr.id
                    JOIN TR_PEMESANAN_STATUS tps ON tpj.id = tps.idtrpemesanan
                    JOIN STATUS_PESANAN sp ON tps.idstatus = sp.id
                    WHERE skj.kategorijasaid IN %s
                    AND sp.status = 'Mencari pekerja terdekat'
                """
                params = [tuple(kategori_jasa_pekerja)]

                if kategori_id:
                    query += " AND skj.kategorijasaid = %s"
                    params.append(str(kategori_id))

                if subkategori_id:
                    query += " AND skj.id = %s"
                    params.append(str(subkategori_id))

                print(f"Executing query: {query}")  
                print(f"With params: {params}")     
                
                cur.execute(query, params)
                pesanan = cur.fetchall()
                print(f"Found {len(pesanan)} orders")  

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
            print(f"Error in get_pesanan_tersedia: {str(e)}")  
            raise Exception(f"Error saat mendapatkan pesanan tersedia: {str(e)}")

    def get_subkategori_jasa(self, kategori_id):
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                print(f"Getting subkategori for kategori_id: {kategori_id}")
                
                cur.execute("""
                    SELECT id, namasubkategori, deskripsi
                    FROM SUBKATEGORI_JASA
                    WHERE kategorijasaid = %s
                    ORDER BY namasubkategori;
                """, (str(kategori_id),))
                
                result = cur.fetchall()
                print(f"Found {len(result)} subkategories")
                
                return [{
                    "id": row["id"],
                    "nama": row["namasubkategori"],
                    "deskripsi": row["deskripsi"]
                } for row in result]
        except Exception as e:
            print(f"Error in get_subkategori_jasa: {str(e)}")
            raise Exception(f"Error saat mendapatkan subkategori jasa: {str(e)}")
        
    def get_kategori_jasa(self, pekerja_id):
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT kj.id, kj.namakategori
                    FROM PEKERJA_KATEGORI_JASA pkj
                    JOIN KATEGORI_JASA kj ON pkj.kategorijasaid = kj.id
                    WHERE pkj.pekerjaid = %s;
                """, (str(pekerja_id),))
                return [{"id": row["id"], "nama": row["namakategori"]} for row in cur.fetchall()]
        except Exception as e:
            raise Exception(f"Error saat mendapatkan kategori jasa: {str(e)}")
        
    def ambil_pesanan(self, pekerja_id, pesanan_id):
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT tps.IdStatus, tps.TglWaktu, pj.Sesi
                    FROM TR_PEMESANAN_STATUS tps
                    JOIN TR_PEMESANAN_JASA pj ON tps.IdTrPemesanan = pj.Id
                    WHERE tps.IdTrPemesanan = %s
                    ORDER BY tps.TglWaktu DESC
                    LIMIT 1;
                """, (str(pesanan_id),))
                current_status = cur.fetchone()

                if not current_status:
                    raise Exception("Pesanan tidak ditemukan.")

                cur.execute("""
                    SELECT Id, Status 
                    FROM STATUS_PESANAN 
                    WHERE Status IN ('Mencari pekerja terdekat', 'Menunggu pekerja berangkat');
                """)
                status_rows = cur.fetchall()
                status_dict = {row['status']: row['id'] for row in status_rows}

                if current_status['idstatus'] != status_dict['Mencari pekerja terdekat']:
                    raise Exception("Pesanan tidak tersedia untuk diambil.")

                tanggal_mulai = datetime.now().date()
                tanggal_selesai = tanggal_mulai + timedelta(days=current_status['sesi'])

                cur.execute("""
                    INSERT INTO TR_PEMESANAN_STATUS (IdTrPemesanan, IdStatus, TglWaktu)
                    VALUES (%s, %s, %s);
                """, (
                    str(pesanan_id),
                    status_dict['Menunggu pekerja berangkat'],
                    datetime.now()
                ))

                cur.execute("""
                    UPDATE TR_PEMESANAN_JASA
                    SET IdPekerja = %s,
                        TglPekerjaan = %s,
                        WaktuPekerjaan = %s
                    WHERE Id = %s;
                """, (
                    str(pekerja_id),
                    tanggal_mulai,
                    tanggal_selesai,
                    str(pesanan_id)
                ))

                self.conn.commit()
                return {
                    "message": "Pesanan berhasil diambil dan status diubah menjadi 'Menunggu pekerja berangkat'.",
                    "tanggal_mulai": tanggal_mulai.isoformat(),
                    "tanggal_selesai": tanggal_selesai.isoformat()
                }

        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error saat mengambil pesanan: {str(e)}")

