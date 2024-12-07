import os
import sys
import logging
from dotenv import load_dotenv
import psycopg2
from flask import Flask, jsonify, request, g
from services.voucher_service import VoucherService
from services.promo_service import PromoService
from services.testimoni_service import TestimoniService
from services.diskon_service import DiskonService
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

port = os.getenv('PORT', '5000')
logger.info(f"Configured to use PORT: {port}")

if os.path.exists('.env'):
    load_dotenv()

app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

DATABASE_URL = os.getenv('DATABASE_URL', os.getenv('DATABASE_PUBLIC_URL'))

def get_db():
    if 'db' not in g:
        try:
            g.db = psycopg2.connect(DATABASE_URL)
            logger.debug("Created new database connection")
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}", exc_info=True)
            raise
    return g.db

def get_services():
    if 'services' not in g:
        db = get_db()
        g.services = {
            'voucher': VoucherService(db),
            'promo': PromoService(db),
            'testimoni': TestimoniService(db),
            'diskon': DiskonService(db)
        }
        logger.debug("Created new service instances")
    return g.services

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
        logger.debug("Closed database connection")

def verify_database():
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT version();')
                version = cur.fetchone()[0]
                logger.info(f"Connected to PostgreSQL: {version}")
        return True
    except Exception as e:
        logger.error(f"Database verification failed: {e}", exc_info=True)
        return False

if not verify_database():
    raise RuntimeError("Failed to verify database connection")

@app.before_request
def before_request():
    try:
        db = get_db()
        with db.cursor() as cur:
            cur.execute('SELECT 1')
    except Exception as e:
        logger.error(f"Before request database check failed: {e}")
        return jsonify({'error': 'Database connection error'}), 500

@app.route('/health')
def health_check():
    try:
        db = get_db()
        with db.cursor() as cur:
            cur.execute('SELECT version()')
            version = cur.fetchone()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'version': version[0] if version else None
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
    
@app.route('/')
def home():
    try:
        db = get_db()
        with db.cursor() as cur:
            cur.execute('SELECT 1')
        return jsonify({
            'message': 'Welcome to Sijarta API',
            'status': 'running',
            'database': 'connected'
        })
    except Exception as e:
        logger.error(f"Home route error: {e}", exc_info=True)
        return jsonify({
            'message': 'Welcome to Sijarta API',
            'status': 'running',
            'database': f'error: {str(e)}'
        })

@app.route('/test-connection')
def test_connection():
    try:
        db = get_db()
        with db.cursor() as cur:
            cur.execute('SELECT version();')
            db_version = cur.fetchone()
        return jsonify({
            'status': 'success',
            'message': 'Successfully connected to the database',
            'database_version': db_version[0]
        })
    except Exception as e:
        logger.error(f"Test connection failed: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Failed to connect to the database: {str(e)}'
        }), 500

@app.route('/api/discounts', methods=['GET'])
def get_all_discounts():
    try:
        services = get_services()
        vouchers = services['voucher'].get_all_vouchers()
        promos = services['promo'].get_all_promos()
        return jsonify({
            'vouchers': vouchers,
            'promos': promos
        })
    except Exception as e:
        logger.error(f"Get all discounts failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/vouchers', methods=['GET'])
def get_all_vouchers():
    try:
        services = get_services()
        vouchers = services['voucher'].get_all_vouchers()
        return jsonify(vouchers)
    except Exception as e:
        logger.error(f"Get all vouchers failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/vouchers/<kode>', methods=['GET'])
def get_voucher(kode):
    try:
        services = get_services()
        voucher = services['voucher'].get_voucher_by_kode(kode)
        if not voucher:
            return jsonify({'error': 'Voucher not found'}), 404
        return jsonify(voucher)
    except Exception as e:
        logger.error(f"Get voucher failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/vouchers/user/<uuid:user_id>', methods=['GET'])
def get_user_vouchers(user_id):
    try:
        services = get_services()
        vouchers = services['voucher'].get_user_vouchers(str(user_id))
        return jsonify(vouchers)
    except Exception as e:
        logger.error(f"Get user vouchers failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/vouchers/purchase', methods=['POST'])
def purchase_voucher():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['user_id', 'kode_voucher', 'metode_bayar_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        services = get_services()
        result = services['voucher'].purchase_voucher(
            data['user_id'],
            data['kode_voucher'],
            data['metode_bayar_id']
        )
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Purchase voucher failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/promos', methods=['GET'])
def get_all_promos():
    try:
        services = get_services()
        promos = services['promo'].get_all_promos()
        return jsonify(promos)
    except Exception as e:
        logger.error(f"Get all promos failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/promos/<kode>', methods=['GET'])
def get_promo(kode):
    try:
        services = get_services()
        promo = services['promo'].get_promo_by_kode(kode)
        if not promo:
            return jsonify({'error': 'Promo not found'}), 404
        return jsonify(promo)
    except Exception as e:
        logger.error(f"Get promo failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/testimoni/subkategori/<uuid:id_subkategori>', methods=['GET'])
def get_testimoni_by_subkategori(id_subkategori):
    try:
        services = get_services()
        testimonis = services['testimoni'].get_testimoni_by_subkategori(str(id_subkategori))
        return jsonify(testimonis)
    except Exception as e:
        logger.error(f"Get testimoni by subkategori failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/testimoni/<uuid:id_tr_pemesanan>', methods=['GET'])
def get_testimoni_by_order(id_tr_pemesanan):
    try:
        services = get_services()
        testimoni = services['testimoni'].get_testimoni_by_order(str(id_tr_pemesanan))
        if not testimoni:
            return jsonify({'error': 'Testimoni not found'}), 404
        return jsonify(testimoni)
    except Exception as e:
        logger.error(f"Get testimoni by order failed: {e}", exc_info=True)
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
        
        services = get_services()
        testimoni = services['testimoni'].create_testimoni(
            data['id_tr_pemesanan'],
            data['teks'],
            data['rating']
        )
        return jsonify({
            'message': 'Testimonial berhasil ditambahkan',
            'testimoni': testimoni
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Create testimoni failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/testimoni/<uuid:id_tr_pemesanan>', methods=['DELETE'])
def delete_testimoni(id_tr_pemesanan):
    try:
        services = get_services()
        result = services['testimoni'].delete_testimoni(str(id_tr_pemesanan))
        return jsonify({
            'message': 'Testimonial berhasil dihapus',
            'testimoni': result
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Delete testimoni failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/diskon', methods=['GET'])
def get_all_diskon():
    try:
        services = get_services()
        diskons = services['diskon'].get_all_diskon()
        return jsonify(diskons)
    except Exception as e:
        logger.error(f"Get all diskon failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/diskon/<kode>', methods=['GET'])
def get_diskon(kode):
    try:
        services = get_services()
        diskon = services['diskon'].get_diskon_by_kode(kode)
        if not diskon:
            return jsonify({'error': 'Diskon not found'}), 404
        return jsonify(diskon)
    except Exception as e:
        logger.error(f"Get diskon failed: {e}", exc_info=True)
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

        services = get_services()
        diskon = services['diskon'].create_diskon(
            data['kode'],
            data['potongan'],
            data['min_tr_pemesanan']
        )
        
        return jsonify({
            'message': 'Diskon berhasil dibuat',
            'diskon': {
                'kode': diskon.kode,
                'potongan': diskon.potongan,
                'min_tr_pemesanan': diskon.min_tr_pemesanan
            }
        }), 201
    except Exception as e:
        logger.error(f"Create diskon failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 400

@app.route('/api/diskon/<kode>', methods=['PUT'])
def update_diskon(kode):
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        services = get_services()
        services['diskon'].update_diskon(
            kode,
            data.get('potongan'),
            data.get('min_tr_pemesanan')
        )
        return jsonify({'message': 'Diskon berhasil diupdate'})
    except Exception as e:
        logger.error(f"Update diskon failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 400

@app.route('/api/diskon/<kode>', methods=['DELETE'])
def delete_diskon(kode):
    try:
        services = get_services()
        services['diskon'].delete_diskon(kode)
        return jsonify({'message': 'Diskon berhasil dihapus'})
    except Exception as e:
        logger.error(f"Delete diskon failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)