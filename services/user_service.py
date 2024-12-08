from datetime import date
from models.user import User, hash_password, verify_password

class UserService:
    def __init__(self, conn):
        self.conn = conn

    def register_user(self, nama, jenis_kelamin, no_hp, pwd, tgl_lahir, alamat, is_pekerja, 
                      nama_bank=None, nomor_rekening=None, npwp=None, link_foto=None, level='Bronze'):
        if not all([nama, jenis_kelamin, no_hp, pwd, tgl_lahir, alamat, is_pekerja]):
            raise ValueError("All required parameters must be provided")

        hashed_pwd = hash_password(pwd)

        try:
            with self.conn.cursor() as cur:
                # Insert user
                cur.execute("""
                    INSERT INTO "USER" (Id, Nama, JenisKelamin, NoHP, Pwd, TglLahir, Alamat, SaldoMyPay, IsPekerja)
                    VALUES (uuid_generate_v4(), %s, %s, %s, %s, %s, %s, 0, %s)
                    RETURNING id
                """, (nama, jenis_kelamin, no_hp, hashed_pwd, tgl_lahir, alamat, is_pekerja))
                user_id = cur.fetchone()[0]

                if is_pekerja:
                    if not all([nama_bank, nomor_rekening, npwp, link_foto]):
                        raise ValueError("All pekerja-specific fields must be provided")

                    cur.execute("""
                        INSERT INTO PEKERJA (Id, NamaBank, NomorRekening, NPWP, LinkFoto, Rating, JmlPesananSelesai)
                        VALUES (%s, %s, %s, %s, %s, 0, 0)
                    """, (user_id, nama_bank, nomor_rekening, npwp, link_foto))
                else:
                    cur.execute("""
                        INSERT INTO PELANGGAN (Id, Level)
                        VALUES (%s, %s)
                    """, (user_id, level))

                self.conn.commit()

                return user_id

        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error registering user: {str(e)}")
        
    def get_user(self, user_id):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM "USER" WHERE Id = %s
            """, (user_id,))
            user = cur.fetchone()

            if not user:
                return None

            return User(*user)
        
    def get_user_by_no_hp(self, no_hp):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM "USER" WHERE NoHP = %s
            """, (no_hp,))
            user = cur.fetchone()

            if not user:
                return None

            return User(*user)
        
    def get_all_users(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM "USER"
            """)
            return [User(*user) for user in cur.fetchall()]

    def update_user(self, user_id, nama=None, jenis_kelamin=None, no_hp=None, pwd=None, tgl_lahir=None, alamat=None, is_pekerja=None, 
                    nama_bank=None, nomor_rekening=None, npwp=None, link_foto=None, level=None):
        if not any([nama, jenis_kelamin, no_hp, pwd, tgl_lahir, alamat, is_pekerja, nama_bank, nomor_rekening, npwp, link_foto, level]):
            raise ValueError("At least one field must be provided to update")

        try:
            with self.conn.cursor() as cur:
                # Update user
                if nama:
                    cur.execute("""
                        UPDATE "USER" SET Nama = %s WHERE Id = %s
                    """, (nama, user_id))
                if jenis_kelamin:
                    cur.execute("""
                        UPDATE "USER" SET JenisKelamin = %s WHERE Id = %s
                    """, (jenis_kelamin, user_id))
                if no_hp:
                    cur.execute("""
                        UPDATE "USER" SET NoHP = %s WHERE Id = %s
                    """, (no_hp, user_id))
                if pwd:
                    hashed_pwd = hash_password(pwd)
                    cur.execute("""
                        UPDATE "USER" SET Pwd = %s WHERE Id = %s
                    """, (hashed_pwd, user_id))
                if tgl_lahir:
                    cur.execute("""
                        UPDATE "USER" SET TglLahir = %s WHERE Id = %s
                    """, (tgl_lahir, user_id))
                if alamat:
                    cur.execute("""
                        UPDATE "USER" SET Alamat = %s WHERE Id = %s
                    """, (alamat, user_id))

                # Update pekerja
                if is_pekerja:
                    if nama_bank:
                        cur.execute("""
                            UPDATE PEKERJA SET NamaBank = %s WHERE Id = %s
                        """, (nama_bank, user_id))
                    if nomor_rekening:
                        cur.execute("""
                            UPDATE PEKERJA SET NomorRekening = %s WHERE Id = %s 
                        """, (nomor_rekening, user_id))
                    if npwp:
                        cur.execute("""
                            UPDATE PEKERJA SET NPWP = %s WHERE Id = %s
                        """, (npwp, user_id))
                    if link_foto:
                        cur.execute("""
                            UPDATE PEKERJA SET LinkFoto = %s WHERE Id = %s
                        """, (link_foto, user_id))
                else:
                    if level:
                        cur.execute("""
                            UPDATE PELANGGAN SET Level = %s WHERE Id = %s
                        """, (level, user_id))
                
                self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error registering user: {str(e)}")

    def login(self, no_hp, pwd):
        user = self.get_user_by_no_hp(no_hp)

        if not user:
            return None

        if verify_password(user.pwd, pwd):
            return user.id

        return None