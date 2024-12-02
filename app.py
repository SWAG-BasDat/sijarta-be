import os
from dotenv import load_dotenv
import psycopg2
from flask import Flask, jsonify
from services.voucher_service import VoucherService
from services.promo_service import PromoService
from services.testimoni_service import TestimoniService
from flask import request

load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_PUBLIC_URL')

def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Inisialisasi service di sini
conn = get_connection()
voucher_service = VoucherService(conn)
promo_service = PromoService(conn)
testimoni_service = TestimoniService(conn)

# Inisialisasi route di sini
@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to Sijarta API',
        'status': 'running'
    })

@app.route('/test-connection')
def test_connection():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT version();')
        db_version = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({
            'status': 'success',
            'message': 'Successfully connected to the database',
            'database_version': db_version[0]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to connect to the database: {str(e)}'
        }), 500

@app.route('/api/discounts', methods=['GET'])
def get_all_discounts():
    try:
        vouchers = voucher_service.get_all_vouchers()
        promos = promo_service.get_all_promos()
        return jsonify({
            'vouchers': vouchers,
            'promos': promos
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vouchers/<kode>', methods=['GET'])
def get_voucher(kode):
    try:
        voucher = voucher_service.get_voucher_by_kode(kode)
        if not voucher:
            return jsonify({'error': 'Voucher not found'}), 404
        return jsonify(voucher)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/promos/<kode>', methods=['GET'])
def get_promo(kode):
    try:
        promo = promo_service.get_promo_by_kode(kode)
        if not promo:
            return jsonify({'error': 'Promo not found'}), 404
        return jsonify(promo)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/testimoni/subkategori/<uuid:id_subkategori>', methods=['GET'])
def get_testimoni_by_subkategori(id_subkategori):
    try:
        testimonis = testimoni_service.get_testimoni_by_subkategori(str(id_subkategori))
        return jsonify(testimonis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/testimoni', methods=['POST'])
def create_testimoni():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['id_tr_pemesanan', 'teks', 'rating']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        testimoni = testimoni_service.create_testimoni(
            data['id_tr_pemesanan'],
            data['teks'],
            data['rating']
        )
        return jsonify({
            'message': 'Testimonial berhasil ditambahkan',
            'testimoni': testimoni
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

if __name__ == '__main__':
    app.run(debug=True)