import hashlib
import os

def hash_password(password):
    """
    Hash a password for storing in the database.
    
    Args:
        password (str): Plain text password to hash
    
    Returns:
        str: Hashed password with salt
    """
    # Generate a random salt
    salt = os.urandom(32)
    
    # Hash the password with the salt using SHA-256
    key = hashlib.pbkdf2_hmac(
        'sha256',  # The hash digest algorithm for hashing
        password.encode('utf-8'),  # Convert the password to bytes
        salt,  # Provide the salt
        100000,  # It is recommended to use at least 100,000 iterations of SHA-256 
        dklen=128  # Get a 128 byte key (changed from dkey_len to dklen)
    )
    
    # Combine salt and key for storage
    storage = salt + key
    
    # Convert to hex for database storage
    return storage.hex()

def verify_password(stored_password, provided_password):
    """
    Verify a stored password against one provided by user
    
    Args:
        stored_password (str): Hex-encoded password from database
        provided_password (str): Plain text password to verify
    
    Returns:
        bool: True if password is correct, False otherwise
    """
    # Convert hex storage back to bytes
    storage = bytes.fromhex(stored_password)
    
    # Extract salt (first 32 bytes)
    salt = storage[:32]
    
    # Hash the provided password with the extracted salt
    new_key = hashlib.pbkdf2_hmac(
        'sha256',
        provided_password.encode('utf-8'),
        salt,
        100000,
        dklen=128  # Changed from dkey_len to dklen
    )
    
    # Combine salt and new key
    new_storage = salt + new_key
    
    # Compare the new storage with the original
    return new_storage.hex() == stored_password

class User:
    def __init__(self, id, nama, jenis_kelamin, no_hp, pwd, tgl_lahir, alamat, saldo_mypay, is_pekerja):
        self.id = id
        self.nama = nama
        self.jenis_kelamin = jenis_kelamin
        self.no_hp = no_hp
        self.pwd = hash_password(pwd)
        self.tgl_lahir = tgl_lahir
        self.alamat = alamat
        self.saldo_mypay = 0
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