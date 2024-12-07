from datetime import datetime
from uuid import uuid4
from models.trmypay import TrMyPay
from kategoritrmypay_service import KategoriTrMyPayService

class TrMyPayService:
    def _init_(self, conn):
        self.conn = conn
        self.kategori_service = KategoriTrMyPayService(conn)

    def create_transaction(self, user_id, nama_kategori, data):
        """
        Creates a transaction for a given category.
        :param user_id: ID of the user performing the transaction.
        :param nama_kategori: Name of the category for the transaction (e.g., 'topup MyPay').
        :param data: Additional data specific to the transaction type (e.g., nominal, id_pemesanan).
        :return: Result message or details of the created transaction.
        """
        try:
            with self.conn.cursor() as cur:
                # Get category ID from the category name
                kategori_id = self.kategori_service.get_kategori_id_by_name(nama_kategori)

                # Handle transactions based on category
                if nama_kategori == "topup MyPay":
                    # Update user balance and insert transaction
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
        """
        Mengambil data form transaksi MyPay (nama user, saldo, kategori transaksi, tanggal transaksi)
        :param user_id: ID user yang akan melakukan transaksi.
        :return: Dictionary berisi data form transaksi.
        """
        try:
            result = {
                "nama_user": None,
                "saldo": 0,
                "kategori_transaksi": [],
                "tanggal_transaksi": None
            }

            with self.conn.cursor() as cur:
                # Ambil data user
                cur.execute("""
                    SELECT Nama, SaldoMyPay 
                    FROM "USER" 
                    WHERE Id = %s;
                """, (user_id,))
                user = cur.fetchone()

                if not user:
                    raise Exception(f"User dengan ID {user_id} tidak ditemukan.")

                result["nama_user"] = user['Nama']
                result["saldo"] = user['SaldoMyPay']

                # Ambil semua kategori transaksi
                result["kategori_transaksi"] = self.kategori_service.get_all_kategori()

                # Tambahkan tanggal transaksi (tanggal saat ini)
                result["tanggal_transaksi"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return result

        except Exception as e:
            raise Exception(f"Error saat mengambil data form transaksi: {str(e)}")

        
    #read mypay
    def get_mypay_overview(self, user_id):
        """
        Mengambil informasi saldo dan riwayat transaksi pengguna berdasarkan database SIJARTA.
        :param user_id: UUID dari pengguna.
        :return: Dictionary berisi saldo dan daftar riwayat transaksi.
        """
        try:
            result = {
                "saldo": 0,
                "riwayat_transaksi": []
            }

            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT SaldoMyPay
                    FROM "USER"
                    WHERE Id = %s;
                """, (str(user_id),))
                saldo_row = cur.fetchone()
                if saldo_row:
                    result["saldo"] = saldo_row['SaldoMyPay']

                cur.execute("""
                    SELECT 
                        t.Nominal,
                        t.Tgl,
                        kt.NamaKategori
                    FROM TR_MYPAY t
                    JOIN KATEGORI_TR_MYPAY kt ON t.KategoriId = kt.Id
                    WHERE t.UserId = %s
                    ORDER BY t.Tgl DESC;
                """, (str(user_id),))
                transactions = cur.fetchall()

                for transaction in transactions:
                    result["riwayat_transaksi"].append({
                        "nominal": transaction['Nominal'],
                        "tanggal": transaction['Tgl'],
                        "kategori": transaction['NamaKategori']
                    })

            return result
        except Exception as e:
            raise Exception(f"Error saat mengambil data MyPay: {str(e)}")
    

