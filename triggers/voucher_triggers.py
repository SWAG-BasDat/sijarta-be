import psycopg2

def install_voucher_triggers(conn):
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
                    CREATE OR REPLACE FUNCTION validate_voucher(
                        p_voucher_code VARCHAR,
                        p_usage_date DATE
                    ) RETURNS BOOLEAN AS $$
                    DECLARE
                        v_kuota_penggunaan INT;
                        v_jml_hari_berlaku INT;
                        v_telah_digunakan INT;
                        v_earliest_purchase DATE;
                    BEGIN
                        SELECT v.KuotaPenggunaan, v.JmlHariBerlaku
                        INTO v_kuota_penggunaan, v_jml_hari_berlaku
                        FROM VOUCHER v
                        WHERE v.Kode = p_voucher_code;

                        IF NOT FOUND THEN
                            RAISE EXCEPTION 'Voucher dengan kode % tidak ditemukan', p_voucher_code;
                        END IF;

                        SELECT MIN(TglAwal)
                        INTO v_earliest_purchase
                        FROM TR_PEMBELIAN_VOUCHER
                        WHERE IdVoucher = p_voucher_code;

                        IF (v_earliest_purchase + v_jml_hari_berlaku) < p_usage_date THEN
                            RAISE EXCEPTION 'Voucher % telah kedaluwarsa', p_voucher_code;
                        END IF;

                        SELECT COUNT(*)
                        INTO v_telah_digunakan
                        FROM TR_PEMESANAN_JASA
                        WHERE IdDiskon = p_voucher_code;

                        IF v_telah_digunakan >= v_kuota_penggunaan THEN
                            RAISE EXCEPTION 'Voucher % telah mencapai batas maksimal penggunaan', p_voucher_code;
                        END IF;

                        RETURN TRUE;

                        EXCEPTION
                            WHEN OTHERS THEN
                                RAISE;
                    END;
                    $$ LANGUAGE plpgsql;
                """)

                cur.execute("""
                    CREATE OR REPLACE FUNCTION validate_voucher_before_order()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1
                            FROM VOUCHER v
                            WHERE v.Kode = NEW.IdDiskon
                        ) THEN
                            PERFORM validate_voucher(NEW.IdDiskon, NEW.TglPemesanan);
                        END IF;

                        RETURN NEW;

                        EXCEPTION
                            WHEN OTHERS THEN
                                RAISE;
                    END;
                    $$ LANGUAGE plpgsql;
                """)

                cur.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_trigger 
                            WHERE tgname = 'validate_voucher_trigger'
                        ) THEN
                            CREATE TRIGGER validate_voucher_trigger
                            BEFORE INSERT OR UPDATE ON TR_PEMESANAN_JASA
                            FOR EACH ROW
                            EXECUTE FUNCTION validate_voucher_before_order();
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