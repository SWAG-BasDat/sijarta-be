import psycopg2

def install_refund_triggers(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM pg_trigger 
                WHERE tgname = 'trigger_refund_mypay_on_cancel'
            );
        """)
        trigger_exists = cur.fetchone()[0]

        if not trigger_exists:
            try:
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
                
                # Create the refund function
                cur.execute("""
                    CREATE OR REPLACE FUNCTION refund_mypay_on_cancel()
                    RETURNS TRIGGER AS $$
                    DECLARE
                        current_status VARCHAR;
                        previous_status VARCHAR;
                        payment_method VARCHAR;
                        total_biaya DECIMAL;
                        pelanggan_id UUID;
                        user_id UUID;
                    BEGIN
                        SELECT Status INTO current_status FROM STATUS_PESANAN WHERE Id = NEW.IdStatus;

                        IF current_status = 'Pesanan dibatalkan' THEN
                            SELECT Status INTO previous_status
                            FROM TR_PEMESANAN_STATUS
                            WHERE IdTrPemesanan = NEW.IdTrPemesanan AND TglWaktu < NEW.TglWaktu
                            ORDER BY TglWaktu DESC
                            LIMIT 1;

                            IF previous_status = 'Mencari pekerja terdekat' THEN
                                SELECT MB.Nama INTO payment_method
                                FROM TR_PEMESANAN_JASA PJ
                                JOIN METODE_BAYAR MB ON PJ.IdMetodeBayar = MB.Id
                                WHERE PJ.Id = NEW.IdTrPemesanan;

                                IF payment_method = 'MyPay' THEN
                                    SELECT TotalBiaya, IdPelanggan INTO total_biaya, pelanggan_id
                                    FROM TR_PEMESANAN_JASA
                                    WHERE Id = NEW.IdTrPemesanan;

                                    SELECT Id INTO user_id FROM PELANGGAN WHERE Id = pelanggan_id;

                                    UPDATE "USER"
                                    SET SaldoMyPay = SaldoMyPay + total_biaya
                                    WHERE Id = user_id;
                                END IF;
                            END IF;
                        END IF;

                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """)

                # Create the trigger
                cur.execute("""
                    CREATE TRIGGER trigger_refund_mypay_on_cancel
                    AFTER INSERT ON TR_PEMESANAN_STATUS
                    FOR EACH ROW
                    EXECUTE FUNCTION refund_mypay_on_cancel();
                """)

                conn.commit()

            except Exception as e:
                conn.rollback()
                print(f"Error installing trigger: {e}")
            finally:
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)
