import psycopg2

def install_transfer_triggers(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM pg_trigger 
                WHERE tgname = 'trigger_transfer_honor_on_completion'
            );
        """)
        transfer_honor_exists = cur.fetchone()[0]

        if not transfer_honor_exists:
            try:
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)

                cur.execute("""
                    CREATE OR REPLACE FUNCTION transfer_honor_on_completion()
                    RETURNS TRIGGER AS $$
                    DECLARE
                        current_status VARCHAR;
                        kategori_id UUID;
                        total_biaya DECIMAL;
                        pekerja_id UUID;
                        user_id UUID;
                        already_processed BOOLEAN;
                    BEGIN
                        SELECT Status INTO current_status FROM STATUS_PESANAN WHERE Id = NEW.IdStatus;
        
                        IF current_status = 'Pesanan selesai' THEN
                            SELECT EXISTS (
                                SELECT 1 
                                FROM TR_MYPAY TM
                                JOIN TR_PEMESANAN_JASA TPJ ON TM.UserId = TPJ.IdPekerja
                                WHERE TPJ.Id = NEW.IdTrPemesanan 
                                  AND TM.KategoriId = (SELECT Id FROM KATEGORI_TR_MYPAY WHERE NamaKategori = 'menerima honor transaksi jasa')
                            ) INTO already_processed;
        
                            IF NOT already_processed THEN
                                SELECT TotalBiaya, IdPekerja INTO total_biaya, pekerja_id
                                FROM TR_PEMESANAN_JASA
                                WHERE Id = NEW.IdTrPemesanan;
        
                                SELECT Id INTO user_id 
                                FROM "USER"
                                WHERE Id = pekerja_id;
        
                                SELECT Id INTO kategori_id
                                FROM KATEGORI_TR_MYPAY
                                WHERE NamaKategori = 'menerima honor transaksi jasa';
        
                                UPDATE "USER"
                                SET SaldoMyPay = SaldoMyPay + total_biaya
                                WHERE Id = user_id;

                                INSERT INTO TR_MYPAY (Id, UserId, Tgl, Nominal, KategoriId) 
                                VALUES (uuid_generate_v4(), user_id, CURRENT_DATE, total_biaya, kategori_id);
                            END IF;
                        END IF;
        
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """)

                cur.execute("""
                    CREATE TRIGGER trigger_transfer_honor_on_completion
                    AFTER INSERT ON TR_PEMESANAN_STATUS
                    FOR EACH ROW
                    EXECUTE FUNCTION transfer_honor_on_completion();
                """)

                conn.commit()
                print("Trigger 'trigger_transfer_honor_on_completion' berhasil dibuat.")
                
            except Exception as e:
                conn.rollback()
                print(f"Error installing 'trigger_transfer_honor_on_completion': {e}")
            finally:
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)