from models.subkategorijasa import SubkategoriJasa

class SubkategoriJasaService:
    def __init__(self, conn):
        self.conn = conn

    def get_subkategori_by_id(self, id_subkategori):
        """
        Get subcategory details by ID with proper error handling.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT sj.Id, sj.NamaSubkategori, sj.Deskripsi, kj.NamaKategori
                    FROM SUBKATEGORI_JASA sj
                    JOIN KATEGORI_JASA kj ON sj.KategoriJasaId = kj.Id
                    WHERE sj.Id = %s
                    """,
                    (str(id_subkategori),) 
                )
                result = cur.fetchone()
                if result is None:
                    return None
                    
                return {
                    'id': result[0],
                    'nama_subkategori': result[1],
                    'deskripsi': result[2],
                    'nama_kategori': result[3]
                }
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Database error in get_subkategori_by_id: {str(e)}")

    def get_pekerja_by_subkategori(self, id_kategori):
        """
        Get workers for a subcategory with proper error handling.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        p.Id, 
                        u.Nama, 
                        COALESCE(p.Rating, 0) as Rating, 
                        COALESCE(p.JmlPesananSelesai, 0) as JmlPesananSelesai
                    FROM PEKERJA p
                    JOIN "USER" u ON p.Id = u.Id
                    JOIN PEKERJA_KATEGORI_JASA pkj ON p.Id = pkj.PekerjaId
                    WHERE pkj.KategoriJasaId = %s
                    ORDER BY p.Rating DESC NULLS LAST
                    """,
                    (str(id_kategori),)  
                )
                results = cur.fetchall()
                
                return [
                    {
                        'id': row[0],
                        'nama': row[1],
                        'rating': float(row[2]) if row[2] is not None else 0.0,
                        'jumlah_pesanan_selesai': row[3]
                    }
                    for row in results
                ]
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Database error in get_pekerja_by_subkategori: {str(e)}")

    def add_pekerja_to_kategori(self, pekerja_id, kategori_id):
        """
        Add worker to category with proper error handling.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM PEKERJA_KATEGORI_JASA 
                    WHERE PekerjaId = %s AND KategoriJasaId = %s
                    """,
                    (str(pekerja_id), str(kategori_id))
                )
                if cur.fetchone():
                    raise ValueError("Pekerja sudah terdaftar dalam kategori ini")

                cur.execute(
                    """
                    INSERT INTO PEKERJA_KATEGORI_JASA (PekerjaId, KategoriJasaId)
                    VALUES (%s, %s)
                    RETURNING PekerjaId
                    """,
                    (str(pekerja_id), str(kategori_id))
                )
                self.conn.commit()
                return cur.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Database error in add_pekerja_to_kategori: {str(e)}")