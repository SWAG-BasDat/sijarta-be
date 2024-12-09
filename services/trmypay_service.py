from datetime import datetime
from uuid import uuid4
from models.trmypay import TrMyPay
from services.kategoritrmypay_service import KategoriTrMyPayService
from psycopg2.extras import DictCursor


class TrMyPayService:
    def __init__(self, conn):
        self.conn = conn
        self.kategori_service = KategoriTrMyPayService(conn)

    def create_transaction(self, user_id, nama_kategori, data):
        try:
            with self.conn.cursor() as cur:
                kategori_id = self.kategori_service.get_kategori_id_by_name(nama_kategori)

                if nama_kategori == "topup MyPay":
                    nominal = data.get("nominal")
                    if not nominal or nominal <= 0:
                        raise ValueError("Nominal top-up harus lebih besar dari 0.")

                    cur.execute("""
                        UPDATE "USER"
                        SET SaldoMyPay = SaldoMyPay + %s
                        WHERE Id = %s;
                    """, (nominal, user_id))

                    cur.execute("""
                        INSERT INTO TR_MYPAY (Id, UserId, Tgl, Nominal, KategoriId)
                        VALUES (uuid_generate_v4(), %s, NOW(), %s, %s);
                    """, (user_id, nominal, kategori_id))

                    return {"message": "Top-up berhasil.", "nominal": nominal}

                elif nama_kategori == "membayar transaksi jasa":
                    # Validate and process service payment
                    id_pemesanan = data.get("id_pemesanan")
                    if not id_pemesanan:
                        raise ValueError("ID Pemesanan harus diberikan.")

                    cur.execute("""
                        SELECT pj.TotalBiaya, u.SaldoMyPay
                        FROM TR_PEMESANAN_JASA pj
                        JOIN "USER" u ON pj.IdPelanggan = u.Id
                        WHERE pj.Id = %s AND u.Id = %s;
                    """, (id_pemesanan, user_id))
                    pemesanan = cur.fetchone()

                    if not pemesanan:
                        raise Exception("Pemesanan jasa tidak ditemukan atau Anda tidak memiliki akses.")

                    total_biaya = pemesanan['TotalBiaya']
                    saldo = pemesanan['SaldoMyPay']

                    if saldo < total_biaya:
                        raise Exception("Saldo MyPay tidak mencukupi untuk melakukan pembayaran.")

                    # Deduct user balance
                    cur.execute("""
                        UPDATE "USER"
                        SET SaldoMyPay = SaldoMyPay - %s
                        WHERE Id = %s;
                    """, (total_biaya, user_id))

                    # Insert transaction
                    cur.execute("""
                        INSERT INTO TR_MYPAY (Id, UserId, Tgl, Nominal, KategoriId)
                        VALUES (uuid_generate_v4(), %s, NOW(), %s, %s);
                    """, (user_id, total_biaya, kategori_id))

                    # Update order status
                    id_status = self.get_status_id_by_name("Menunggu pekerja berangkat")
                    cur.execute("""
                        INSERT INTO TR_PEMESANAN_STATUS (IdTrPemesanan, IdStatus, TglWaktu)
                        VALUES (%s, %s, NOW());
                    """, (id_pemesanan, id_status))

                    return {"message": "Pembayaran berhasil dilakukan.", "total_biaya": total_biaya}

                elif nama_kategori == "transfer MyPay ke pengguna lain":
                    # Transfer balance to another user
                    target_user_id = data.get("target_user_id")
                    nominal = data.get("nominal")

                    if not target_user_id or not nominal or nominal <= 0:
                        raise ValueError("ID pengguna tujuan dan nominal transfer harus valid.")

                    # Deduct sender balance
                    cur.execute("""
                        SELECT SaldoMyPay FROM "USER" WHERE Id = %s;
                    """, (user_id,))
                    sender = cur.fetchone()

                    if not sender or sender['SaldoMyPay'] < nominal:
                        raise Exception("Saldo tidak mencukupi untuk melakukan transfer.")

                    cur.execute("""
                        UPDATE "USER"
                        SET SaldoMyPay = SaldoMyPay - %s
                        WHERE Id = %s;
                    """, (nominal, user_id))

                    # Add balance to target user
                    cur.execute("""
                        UPDATE "USER"
                        SET SaldoMyPay = SaldoMyPay + %s
                        WHERE Id = %s;
                    """, (nominal, target_user_id))

                    # Record transaction
                    cur.execute("""
                        INSERT INTO TR_MYPAY (Id, UserId, Tgl, Nominal, KategoriId)
                        VALUES (uuid_generate_v4(), %s, NOW(), %s, %s);
                    """, (user_id, nominal, kategori_id))

                    return {"message": "Transfer berhasil.", "nominal": nominal, "target_user_id": target_user_id}

                elif nama_kategori == "withdrawal MyPay ke rekening bank":
                    # Handle withdrawal logic
                    bank_name = data.get("bank_name")
                    account_number = data.get("account_number")
                    nominal = data.get("nominal")

                    if not bank_name or not account_number or nominal <= 0:
                        raise ValueError("Informasi penarikan tidak valid.")

                    cur.execute("""
                        SELECT SaldoMyPay FROM "USER" WHERE Id = %s;
                    """, (user_id,))
                    user = cur.fetchone()

                    if not user or user['SaldoMyPay'] < nominal:
                        raise Exception("Saldo tidak mencukupi untuk penarikan.")

                    # Deduct balance
                    cur.execute("""
                        UPDATE "USER"
                        SET SaldoMyPay = SaldoMyPay - %s
                        WHERE Id = %s;
                    """, (nominal, user_id))

                    # Record transaction
                    cur.execute("""
                        INSERT INTO TR_MYPAY (Id, UserId, Tgl, Nominal, KategoriId)
                        VALUES (uuid_generate_v4(), %s, NOW(), %s, %s);
                    """, (user_id, nominal, kategori_id))

                    return {"message": "Withdrawal berhasil.", "nominal": nominal, "bank_name": bank_name}

                else:
                    raise ValueError(f"Kategori transaksi '{nama_kategori}' tidak dikenali.")

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error saat membuat transaksi: {str(e)}")

        
    def get_transaction_form(self, user_id):
        try:
            result = {
                "nama_user": None,
                "saldo": 0,
                "kategori_transaksi": [],
                "tanggal_transaksi": None
            }

            with self.conn.cursor(cursor_factory=DictCursor) as cur:  # Gunakan DictCursor
                # Ambil data user
                cur.execute("""
                    SELECT nama, saldomypay 
                    FROM "USER" 
                    WHERE id = %s;
                """, (str(user_id),))
                user = cur.fetchone()

                if not user:
                    raise Exception(f"User dengan ID {user_id} tidak ditemukan.")

                result["nama_user"] = user["nama"]  
                result["saldo"] = user["saldomypay"]  

                kategori_transaksi = self.kategori_service.get_selected_kategori()
                result["kategori_transaksi"] = [
                    {"id": kategori["id"], "nama_kategori": kategori["namakategori"]}
                    for kategori in kategori_transaksi
                ]

                result["tanggal_transaksi"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return result

        except Exception as e:
            raise Exception(f"Error saat mengambil data form transaksi: {str(e)}")

        
    # read mypay
    def get_mypay_overview(self, user_id):
        try:
            result = {
                "no_hp": "",
                "saldo": 0,
                "riwayat_transaksi": []
            }

            with self.conn.cursor(cursor_factory=DictCursor) as cur:  # Use DictCursor
                # Ambil saldo MyPay pengguna
                cur.execute("""
                    SELECT nohp, saldomypay
                    FROM "USER"
                    WHERE id = %s;
                """, (str(user_id),))
                user_row = cur.fetchone()
                if user_row:
                    result["no_hp"] = user_row["nohp"]
                    result["saldo"] = user_row["saldomypay"]  # Access by column name

                # Ambil riwayat transaksi pengguna
                cur.execute("""
                    SELECT 
                        t.nominal,
                        t.tgl,
                        kt.namakategori
                    FROM TR_MYPAY t
                    JOIN KATEGORI_TR_MYPAY kt ON t.Kategoriid = kt.id
                    WHERE t.userid = %s
                    ORDER BY t.tgl DESC;
                """, (str(user_id),))
                transactions = cur.fetchall()

                # Format transaksi menjadi list of dictionaries
                for transaction in transactions:
                    result["riwayat_transaksi"].append({
                        "nominal": transaction["nominal"],
                        "tanggal": transaction["tgl"],
                        "kategori": transaction["namakategori"]
                    })

            return result
        except Exception as e:
            raise Exception(f"Error saat mengambil data MyPay: {str(e)}")