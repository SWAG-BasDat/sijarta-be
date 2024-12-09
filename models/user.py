import hashlib
import os

class User:
    def __init__(self, id, nama, jenis_kelamin, no_hp, pwd, tgl_lahir, alamat, saldo_mypay, is_pekerja):
        self.id = id
        self.nama = nama
        self.jenis_kelamin = jenis_kelamin
        self.no_hp = no_hp
        self.pwd = pwd
        self.tgl_lahir = tgl_lahir
        self.alamat = alamat
        self.saldo_mypay = saldo_mypay
        self.is_pekerja = is_pekerja

    @staticmethod
    def create_table(conn):
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS "USER" (
                    Id UUID PRIMARY KEY,
                    Nama VARCHAR,
                    JenisKelamin CHAR(1),
                    NoHP VARCHAR,
                    Pwd VARCHAR,
                    TglLahir DATE,
                    Alamat VARCHAR,
                    SaldoMyPay DECIMAL,
                    IsPekerja BOOLEAN,
                );
            """)
            conn.commit()
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'nama': self.nama,
            'jenis_kelamin': self.jenis_kelamin,
            'no_hp': self.no_hp,
            'tgl_lahir': self.tgl_lahir.isoformat() if self.tgl_lahir else None,
            'alamat': self.alamat,
            'saldo_mypay': self.saldo_mypay,
            'is_pekerja': self.is_pekerja,
        }