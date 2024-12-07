from datetime import date
from uuid import uuid4
from models.trmypay import TrMyPay
from kategoritrmypay_service import KategoriTrMyPayService

class TrMyPayService:
    def _init_(self, conn):
        self.conn = conn
        self.kategori_service = KategoriTrMyPayService(conn)

    def create_trmypay(self, user_id, nama_kategori, data):
        transaction_id = uuid4()
        today = date.today()

        try:
            kategori_id = self.kategori_service.get_kategori_id_by_name(nama_kategori)

            with self.conn.cursor() as cur:
                # Insert data based on category
                if nama_kategori.lower() == 'topup mypay':
                    # State 1: TopUp
                    nominal = data['nominal']
                    cur.execute("""
                        INSERT INTO TR_MYPAY (Id, UserId, Tgl, Nominal, KategoriId)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (str(transaction_id), str(user_id), today, nominal, str(kategori_id)))

                    response = {
                        "type": "TopUp",
                        "transaction_id": transaction_id,
                        "nominal": nominal
                    }

                elif nama_kategori.lower() == 'membayar transaksi jasa':
                    # State 2: Payment for a service
                    service_id = data['service_id']
                    nominal = data['nominal']
                    cur.execute("""
                        INSERT INTO TR_MYPAY (Id, UserId, Tgl, Nominal, KategoriId)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (str(transaction_id), str(user_id), today, nominal, str(kategori_id)))

                    response = {
                        "type": "Payment",
                        "transaction_id": transaction_id,
                        "service_id": service_id,
                        "nominal": nominal
                    }

                elif nama_kategori.lower() == 'transfer mypay ke pengguna lain':
                    # State 3: Transfer
                    target_user_id = data['target_user_id']

                    # Fetch target phone from USER table
                    cur.execute("SELECT NoHP FROM USER WHERE Id = %s;", (target_user_id,))
                    target_user = cur.fetchone()
                    if not target_user:
                        raise Exception(f"Target user with ID {target_user_id} not found.")
                    target_phone = target_user['NoHP']

                    nominal = data['nominal']
                    cur.execute("""
                        INSERT INTO TR_MYPAY (Id, UserId, Tgl, Nominal, KategoriId)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (str(transaction_id), str(user_id), today, nominal, str(kategori_id)))

                    response = {
                        "type": "Transfer",
                        "transaction_id": transaction_id,
                        "target_phone": target_phone,
                        "nominal": nominal
                    }

                elif nama_kategori.lower() == 'withdrawal mypay ke rekening bank':
                    # State 4: Withdrawal
                    pekerja_id = data['pekerja_id']

                    # Fetch bank name and account number from PEKERJA table
                    cur.execute("""
                        SELECT NamaBank, NomorRekening FROM PEKERJA WHERE Id = %s;
                    """, (pekerja_id,))
                    pekerja = cur.fetchone()
                    if not pekerja:
                        raise Exception(f"Pekerja with ID {pekerja_id} not found.")
                    bank_name = pekerja['NamaBank']
                    account_number = pekerja['NomorRekening']

                    nominal = data['nominal']
                    cur.execute("""
                        INSERT INTO TR_MYPAY (Id, UserId, Tgl, Nominal, KategoriId)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (str(transaction_id), str(user_id), today, nominal, str(kategori_id)))

                    response = {
                        "type": "Withdrawal",
                        "transaction_id": transaction_id,
                        "bank_name": bank_name,
                        "account_number": account_number,
                        "nominal": nominal
                    }

                else:
                    raise Exception(f"Kategori transaksi '{nama_kategori}' tidak valid.")

                self.conn.commit()
                return response
        
        except Exception as e:
            self.conn.rollback()
            raise e
        
#butuh adjust lagi apakah buat ngeshow hasil createnya mending difunction ini atau gabung sama create di "response"nya
    def read_trmypay(self, transaction_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT * FROM TR_MYPAY WHERE Id = %s;", (str(transaction_id),))
                transaction = cur.fetchone()

                if not transaction:
                    raise Exception(f"Transaction with ID {transaction_id} not found.")

                if transaction['KategoriId'] == self.kategori_service.get_kategori_id_by_name('TopUp MyPay'):
                    return {
                        'type': 'TopUp',
                        'nominal': transaction['Nominal']
                    }
                elif transaction['KategoriId'] == self.kategori_service.get_kategori_id_by_name('Membayar Transaksi Jasa'):
                    return {
                        'type': 'Payment',
                        'service_id': transaction['ServiceId'],
                        'nominal': transaction['Nominal']
                    }
                elif transaction['KategoriId'] == self.kategori_service.get_kategori_id_by_name('Transfer MyPay ke Pengguna Lain'):
                    return {
                        'type': 'Transfer',
                        'target_phone': transaction['TargetPhone'],
                        'nominal': transaction['Nominal']
                    }
                elif transaction['KategoriId'] == self.kategori_service.get_kategori_id_by_name('Withdrawal MyPay ke Rekening Bank'):
                    return {
                        'type': 'Withdrawal',
                        'bank_name': transaction['BankName'],
                        'account_number': transaction['AccountNumber'],
                        'nominal': transaction['Nominal']
                    }
                else:
                    raise Exception("Unknown transaction type.")
        except Exception as e:
            raise e
        
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
    

