import os
from dotenv import load_dotenv
import psycopg2
from flask import Flask, jsonify
from services.voucher_service import VoucherService
from services.promo_service import PromoService
from services.testimoni_service import TestimoniService
from services.diskon_service import DiskonService
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
diskon_service = DiskonService(conn)

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

# Voucher Routes
@app.route('/api/vouchers/<kode>', methods=['GET'])
def get_voucher(kode):
    try:
        voucher = voucher_service.get_voucher_by_kode(kode)
        if not voucher:
            return jsonify({'error': 'Voucher not found'}), 404
        return jsonify(voucher)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vouchers/user/<uuid:user_id>', methods=['GET'])
def get_user_vouchers(user_id):
    try:
        vouchers = voucher_service.get_user_vouchers(str(user_id))
        return jsonify(vouchers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vouchers/purchase', methods=['POST'])
def purchase_voucher():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['user_id', 'kode_voucher']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        result = voucher_service.purchase_voucher_with_mypay(
            data['user_id'],
            data['kode_voucher']
        )
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Promo Routes
@app.route('/api/promos/<kode>', methods=['GET'])
def get_promo(kode):
    try:
        promo = promo_service.get_promo_by_kode(kode)
        if not promo:
            return jsonify({'error': 'Promo not found'}), 404
        return jsonify(promo)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Testimoni Routes
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

@app.route('/api/testimoni/<uuid:id_tr_pemesanan>', methods=['DELETE'])
def delete_testimoni(id_tr_pemesanan):
    try:
        result = testimoni_service.delete_testimoni(str(id_tr_pemesanan))
        return jsonify({
            'message': 'Testimonial berhasil dihapus',
            'testimoni': result
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Diskon Routes
@app.route('/api/diskon', methods=['GET'])
def get_all_diskon():
    try:
        diskons = diskon_service.get_all_diskon()
        return jsonify(diskons)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/diskon/<kode>', methods=['GET'])
def get_diskon(kode):
    try:
        diskon = diskon_service.get_diskon_by_kode(kode)
        if not diskon:
            return jsonify({'error': 'Diskon not found'}), 404
        return jsonify(diskon)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/diskon', methods=['POST'])
def create_diskon():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['kode', 'potongan', 'min_tr_pemesanan']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        diskon = diskon_service.create_diskon(
            data['kode'],
            data['potongan'],
            data['min_tr_pemesanan']
        )
        return jsonify({
            'message': 'Diskon berhasil dibuat',
            'diskon': diskon.__dict__
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/diskon/<kode>', methods=['PUT'])
def update_diskon(kode):
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        diskon_service.update_diskon(
            kode,
            data.get('potongan'),
            data.get('min_tr_pemesanan')
        )
        return jsonify({'message': 'Diskon berhasil diupdate'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/diskon/<kode>', methods=['DELETE'])
def delete_diskon(kode):
    try:
        diskon_service.delete_diskon(kode)
        return jsonify({'message': 'Diskon berhasil dihapus'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)