import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from models.diskon import Diskon
from models.kategorijasa import KategoriJasa
from models.kategoritrmypay import KategoriTrMyPay
from models.metodebayar import MetodeBayar
from models.pekerja import Pekerja
from models.pekerjakategorijasa import PekerjaKategoriJasa
from models.pelanggan import Pelanggan
from models.promo import Promo
from models.sesilayanan import SesiLayanan
from models.statuspesanan import StatusPesanan
from models.subkategorijasa import SubkategoriJasa
from models.testimoni import Testimoni
from models.trmypay import TrMyPay
from models.trpemesananjasa import TrPemesananJasa
from models.trpemesananstatus import TrPemesananStatus
from models.user import User
from models.voucher import Voucher
from models.trpembelianvoucher import TrPembelianVoucher

def get_connection():
    return psycopg2.connect(os.getenv('DATABASE_PUBLIC_URL'))

def migrate():
    models = [
        User,
        Pelanggan,
        KategoriJasa,
        SubkategoriJasa,
        Pekerja,
        PekerjaKategoriJasa,
        StatusPesanan,
        MetodeBayar,
        Diskon, 
        Voucher,
        Promo,
        SesiLayanan,
        TrPemesananJasa,
        TrPemesananStatus,
        Testimoni,
        KategoriTrMyPay,
        TrMyPay,
        TrPembelianVoucher
    ]

    try:
        conn = get_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with conn.cursor() as cur:
            cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

        for model in models:
            print(f"Creating table for {model.__name__}")
            model.create_table(conn)

        with conn.cursor() as cur:
            cur.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
            """)

            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            
            tables = [row[0] for row in cur.fetchall()]
            
            for table in tables:
                cur.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table.lower()}' 
                    AND column_name = 'updated_at'
                """)
                
                if cur.fetchone():
                    trigger_name = f"update_{table}_updated_at"
                    cur.execute(f"""
                    DROP TRIGGER IF EXISTS {trigger_name} ON {table};
                    CREATE TRIGGER {trigger_name}
                        BEFORE UPDATE ON {table}
                        FOR EACH ROW
                        EXECUTE FUNCTION update_updated_at_column();
                    """)

        print("Migration completed successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    load_dotenv()
    
    migrate()