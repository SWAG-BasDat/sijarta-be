import psycopg2

def install_user_triggers(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM pg_trigger 
                WHERE tgname = 'validate_voucher_trigger'
            );
        """)
        trigger_exists = cur.fetchone()[0]

        if not trigger_exists:
            try:
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
                
                cur.execute("""
                    CREATE OR REPLACE FUNCTION check_nohp_registered() RETURNS TRIGGER AS $$
                    BEGIN
                        IF EXISTS (SELECT 1 FROM "USER" WHERE nohp = NEW.nohp) THEN 
                            RAISE EXCEPTION 'Mobile number already registered';
                        END IF;
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """)

                cur.execute("""
                    CREATE OR REPLACE FUNCTION check_pekerja_combination() RETURNS TRIGGER AS $$
                    BEGIN
                        IF EXISTS (SELECT 1 FROM pekerja WHERE namabank = NEW.namabank AND nomorrekening = NEW.nomorrekening) THEN
                            RAISE EXCEPTION 'Combination of nama bank and nomor rekening already exists';
                        END IF;
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """)

                cur.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_trigger 
                            WHERE tgname = 'check_nohp_unique'
                        ) THEN
                            CREATE OR REPLACE TRIGGER check_nohp_unique 
                                BEFORE INSERT ON "USER" 
                                FOR EACH ROW
                                EXECUTE FUNCTION check_nohp_registered();
                        END IF;
                    END;
                    $$;
                """)

                cur.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_trigger 
                            WHERE tgname = 'check_pekerja_combination_unique'
                        ) THEN
                            CREATE OR REPLACE TRIGGER check_pekerja_combination_unique 
                                BEFORE INSERT ON pekerja
                                FOR EACH ROW
                                EXECUTE FUNCTION check_pekerja_combination();
                        END IF;
                    END;
                    $$;
                """)

                conn.commit()

            except Exception as e:
                conn.rollback()
                print(f"Error installing trigger: {e}")
            finally:
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)
