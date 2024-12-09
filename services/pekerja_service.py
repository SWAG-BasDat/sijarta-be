from datetime import date
from models.pekerja import Pekerja

class PekerjaService:
    def __init__(self, conn):
        self.conn = conn
    
    def get_pekerja(self, pekerja_id):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM PEKERJA WHERE Id = %s
            """, (pekerja_id,))
            pekerja = cur.fetchone()
        
            if not pekerja:
                return None
        
            return Pekerja(*pekerja)
        
    def get_all_pekerja(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM PEKERJA
            """)
            return [Pekerja(*pekerja) for pekerja in cur.fetchall()]
        
    def get_pekerja_by_no_hp(self, no_hp):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT p.*
                FROM pekerja p
                JOIN "USER" u ON p.id = u.id
                WHERE u.nohp = '%s';
            """, (no_hp,))
            pekerja = cur.fetchone()
        
            if not pekerja:
                return None
        
            return Pekerja(*pekerja)