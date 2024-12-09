from datetime import date
from models.user import User

class PelangganService:
    def __init__(self, conn):
        self.conn = conn
    
    def get_pelanggan(self, pelanggan_id):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM PELANGGAN WHERE Id = %s
            """, (pelanggan_id,))
            pelanggan = cur.fetchone()
        
            if not pelanggan:
                return None
        
            return User(*pelanggan)
        
    def get_all_pelanggan(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM PELANGGAN
            """)
            return [User(*pelanggan) for pelanggan in cur.fetchall()]
        
    def get_pelanggan_by_no_hp(self, no_hp):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT p.*
                FROM pelanggan p
                JOIN "USER" u ON p.id = u.id
                WHERE u.nohp = '%s';
            """, (no_hp,))
            pelanggan = cur.fetchone()
        
            if not pelanggan:
                return None
        
            return User(*pelanggan)