import datetime
from decimal import Decimal
import decimal
import json
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
from services.kategorijasa_service import KategoriJasaService
from services.user_service import UserService
from services.sesilayanan_service import SesiLayananService
from services.subkategorijasa_service import SubkategoriJasaService
from services.trmypay_service import TrMyPayService
from services.kategoritrmypay_service import KategoriTrMyPayService
from services.pemesananjasa_service import PemesananJasaService
from services.pekerjakategorijasa_service import PekerjaKategoriJasaService
from services.statuspekerjaanjasa_service import StatusPekerjaanJasaService
from services.pekerja_service import PekerjaService
from services.pelanggan_service import PelangganService
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from triggers.voucher_triggers import install_voucher_triggers
from triggers.user_triggers import install_user_triggers
from triggers.transfer_triggers import install_transfer_triggers
from triggers.mypay_triggers import install_refund_triggers


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
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],  
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
CORS(app)
DATABASE_URL = os.getenv('DATABASE_URL', os.getenv('DATABASE_PUBLIC_URL'))

def get_db():
    if 'db' not in g:
        try:
            g.db = psycopg2.connect(DATABASE_URL)
            logger.debug("Created new database connection")
            try:
                install_voucher_triggers(g.db)
                logger.info("Voucher triggers installed successfully")
            except Exception as e:
                logger.error(f"Failed to install voucher triggers: {e}", exc_info=True)     

            try:
                install_user_triggers(g.db)
                logger.info("User triggers installed successfully")
            except Exception as e:
                logger.error(f"Failed to install user triggers: {e}", exc_info=True)

            try:
                install_transfer_triggers(g.db)
                logger.info("Transfer triggers installed successfully")
                
            except Exception as e:
                logger.error(f"Failed to install voucher triggers: {e}", exc_info=True)
                
                install_refund_triggers(g.db)
                logger.info("Refund triggers installed successfully")
            except Exception as e:
                logger.error(f"Failed to install refund triggers: {e}", exc_info=True)

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
            'diskon': DiskonService(db),
            'kategorijasa': KategoriJasaService(db),
            'user': UserService(db),
            'subkategorijasa': SubkategoriJasaService(db),
            'sesilayanan': SesiLayananService(db),
            'trmypay': TrMyPayService(db),
            'kategoritrmypay': KategoriTrMyPayService(db),
            'pemesananjasa': PemesananJasaService(db),
            'pekerjakategorijasa': PekerjaKategoriJasaService(db),
            'statuspekerjaanjasa': StatusPekerjaanJasaService(db),
            'pekerja': PekerjaService(db),
            'pelanggan': PelangganService(db)
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

@app.cli.command('install-triggers')
def install_triggers_command():
    try:
        db = get_db()
        install_voucher_triggers(db)
        install_user_triggers(db)
        install_transfer_triggers(db)
        install_refund_triggers(db)
        logger.info("Sukses")
    except Exception as e:
        logger.error(f"Gbs: {e}", exc_info=True)
        raise
    
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
    
@app.route('/api/voucher', methods=['POST'])
def create_voucher():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['kode', 'jml_hari_berlaku', 'kuota_penggunaan', 'harga']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        try:
            jml_hari_berlaku = int(data['jml_hari_berlaku'])
            kuota_penggunaan = int(data['kuota_penggunaan'])
            harga = Decimal(str(data['harga'])) 
        except (ValueError, TypeError, decimal.InvalidOperation):
            return jsonify({'error': 'Invalid numeric values provided'}), 400
        
        services = get_services()
        voucher = services['voucher'].create_voucher(
            data['kode'],
            jml_hari_berlaku,
            kuota_penggunaan,
            harga
        )
        
        return jsonify({
            'message': 'Voucher berhasil dibuat',
            'voucher': {
                'kode': voucher.kode,
                'jml_hari_berlaku': voucher.jml_hari_berlaku,
                'kuota_penggunaan': voucher.kuota_penggunaan,
                'harga': float(voucher.harga) 
            }
        }), 201
        
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Create voucher failed: {e}", exc_info=True)
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
        
        required_fields = ['user_id', 'kode_voucher']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        services = get_services()
        result = services['voucher'].purchase_voucher(
            data['user_id'],
            data['kode_voucher']
        )
        
        return json.dumps(result, cls=json.JSONEncoder), 201, {'Content-Type': 'application/json'}
        
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
    
from datetime import datetime

@app.route('/api/promo', methods=['POST'])
def create_promo():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['kode', 'tgl_akhir_berlaku']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        try:
            tgl_akhir = datetime.strptime(data['tgl_akhir_berlaku'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        services = get_services()
        promo = services['promo'].create_promo(
            data['kode'],
            tgl_akhir
        )
        
        return jsonify({
            'message': 'Promo berhasil dibuat',
            'promo': {
                'kode': promo.kode,
                'tgl_akhir_berlaku': promo.tgl_akhir_berlaku.strftime('%Y-%m-%d')
            }
        }), 201
        
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Create promo failed: {e}", exc_info=True)
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
    
@app.route('/api/kategorijasa', methods=['GET'])
def get_all_kategori():
    try:
        services = get_services()
        kategorijasas = services['kategorijasa'].get_all_kategori()
        return jsonify(kategorijasas)
    except Exception as e:
        logger.error(f"Get all kategorijasas failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/kategorijasa/<uuid:id_kategorijasa>', methods=['GET'])
def get_kategori_by_id(id_kategorijasa):
    try:
        services = get_services()
        kategorijasa = services['kategorijasa'].get_kategori_by_id(str(id_kategorijasa))
        if not kategorijasa:
            return jsonify({'error': 'Kategori Jasa not found'}), 404
        return jsonify(kategorijasa)
    except Exception as e:
        logger.error(f"Get kategorijasa by ID failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/kategorijasa/<uuid:id_kategorijasa>/subkategori', methods=['GET'])
def get_subkategori_by_kategori(id_kategorijasa):
    try:
        services = get_services()
        subkategorijasas = services['kategorijasa'].get_subkategori_by_kategori(str(id_kategorijasa))
        return jsonify(subkategorijasas)
    except Exception as e:
        logger.error(f"Get subkategori by kategori failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/kategorijasa/subkategori/search', methods=['GET'])
def search_subkategori():
    try:
        keyword = request.args.get('keyword', '')
        if not keyword:
            return jsonify({'error': 'Keyword is required'}), 400
        
        services = get_services()
        subkategorijasas = services['kategorijasa'].search_subkategori(keyword)
        return jsonify(subkategorijasas)
    except Exception as e:
        logger.error(f"Search subkategori failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/subkategorijasa/<uuid:id_subkategori>', methods=['GET'])
def get_subkategori_by_id(id_subkategori):
    try:
        subkategori_service = get_services()['subkategorijasa']
        subkategori = subkategori_service.get_subkategori_by_id(id_subkategori)
        
        if not subkategori:
            return jsonify({
                'status': 'error',
                'message': 'Subcategory not found'
            }), 404

        return jsonify({
            'status': 'success',
            'data': {
                'id': subkategori['id'],
                'name': subkategori['nama_subkategori'],
                'description': subkategori['deskripsi'],
                'category': subkategori['nama_kategori'],
                'categoryid': subkategori['id_kategori']
            }
        })

    except Exception as e:
        logger.error(f"Error fetching subcategory: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch subcategory',
            'error': str(e)
        }), 500

@app.route('/api/subkategorijasa/workers/<uuid:id_kategori>', methods=['GET'])
def get_workers_by_kategori(id_kategori):
    try:
        subkategori_service = get_services()['subkategorijasa']
        workers = subkategori_service.get_pekerja_by_subkategori(id_kategori)
        
        return jsonify({
            'status': 'success',
            'data': [
                {
                    'id': worker['id'],
                    'name': worker['nama'],
                    'rating': worker['rating'],
                    'completed_orders': worker['jumlah_pesanan_selesai']
                }
                for worker in workers
            ]
        })

    except Exception as e:
        logger.error(f"Error fetching workers: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch workers',
            'error': str(e)
        }), 500
    
@app.route('/api/subkategorijasa/add_pekerja_to_kategori', methods=['POST'])
def add_pekerja_to_kategori():
    try:
        data = request.json
        required_fields = ['id', 'kategori_jasa_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        services = get_services()
        pekerja_id = services['subkategorijasa'].add_pekerja_to_kategori(
            data['id'],
            data['kategori_jasa_id']
        )
        
        return jsonify({
            'message': 'Pekerja berhasil ditambahkan',
            'pekerja_id': pekerja_id
        }), 201
        
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/api/sesilayanan/<uuid:id_subkategori>', methods=['GET'])
def get_sesi_by_subkategori(id_subkategori):
    try:
        sesi_service = get_services()['sesilayanan']
        session_subcategory = sesi_service.get_sesi_by_subkategori(id_subkategori)
        
        if not session_subcategory:
            return jsonify({"error": "No sessions found for this subcategory."}), 404
        
        sesi_list = [{"session": sesi[0], "price": sesi[1]} for sesi in session_subcategory]
        return jsonify({"data": sesi_list}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sesilayanan/add', methods=['POST'])
def add_sesi_layanan():
    try:
        data = request.json
        required_fields = ['sub_kategori_id', 'sesi', 'harga']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
            
        services = get_services()
        sesi_layanan = services['sesilayanan'].add_sesi_layanan(
            data['sub_kategori_id'],
            data['sesi'],
            data['harga']
        )

        return jsonify({
            'message': 'Sesi layanan berhasil ditambahkan',
            'pekerja': {
                'sub_kategori_id': sesi_layanan.sub_kategori_id,
                'sesi': sesi_layanan.sesi,
                'harga': sesi_layanan.harga
            }
        }), 201

    except Exception as e:
        logger.error(f"Error adding session: {e}", exc_info=True)
        return jsonify({'error': 'Failed to add session'}), 500


@app.route('/api/auth/register', methods=['POST'])
def register_user():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['nama', 'jenis_kelamin', 'no_hp', 'pwd', 'tgl_lahir', 'alamat', 'is_pekerja']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        services = get_services()
        user_id = services['user'].register_user(
            data['nama'],
            data['jenis_kelamin'],
            data['no_hp'],
            data['pwd'],
            data['tgl_lahir'],
            data['alamat'],
            data['is_pekerja'],
            data.get('nama_bank'),
            data.get('nomor_rekening'),
            data.get('npwp'),
            data.get('link_foto'),
            data.get('level')
        )
        return jsonify({'user_id': user_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Register user failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/auth/login', methods=['POST'])
def login_user():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['no_hp', 'pwd']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        services = get_services()
        user = services['user'].login(data['no_hp'], data['pwd'])
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        return jsonify(user)
    except Exception as e:
        logger.error(f"Login user failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/users', methods=['GET'])
def get_all_users():
    try:
        services = get_services()
        users = services['user'].get_all_users()

        users_dict = [user.to_dict() for user in users]
        return jsonify(users_dict)
    except Exception as e:
        logger.error(f"Get all users failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/users/<uuid:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        services = get_services()
        user = services['user'].get_user(str(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict())
    except Exception as e:
        logger.error(f"Get user failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/workers/<uuid:user_id>', methods=['GET'])
def get_pekerja(user_id):
    try:
        services = get_services()
        user = services['pekerja'].get_pekerja(str(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict())
    except Exception as e:
        logger.error(f"Get user failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/customers/<uuid:user_id>', methods=['GET'])
def get_pelanggan(user_id):
    try:
        services = get_services()
        user = services['pelanggan'].get_pelanggan(str(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict())
    except Exception as e:
        logger.error(f"Get user failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/users/<uuid:user_id>/update', methods=['PATCH'])
def update_user(user_id):
    try:
        data = request.json
        user_id = str(user_id)
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        nama = data.get('nama')
        jenis_kelamin = data.get('jenis_kelamin')
        no_hp = data.get('no_hp')
        pwd = data.get('pwd')
        tgl_lahir = data.get('tgl_lahir')
        alamat = data.get('alamat')
        is_pekerja = data.get('is_pekerja')
        nama_bank = data.get('nama_bank')
        nomor_rekening = data.get('nomor_rekening')
        npwp = data.get('npwp')
        link_foto = data.get('link_foto')
        level = data.get('level')
        
        services = get_services()
        services['user'].update_user(
            user_id,
            nama,
            jenis_kelamin,
            no_hp,
            pwd,
            tgl_lahir,
            alamat,
            is_pekerja,
            nama_bank,
            nomor_rekening,
            npwp,
            link_foto,
            level
        )

        updated_user = services['user'].get_user(user_id)
        return jsonify({
            'message': 'User updated successfully',
            'user': updated_user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Update user failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 400

    
@app.route('/api/mypay/<uuid:user_id>', methods=['GET'])
def get_mypay(user_id):
    try:
        services = get_services()
        trmypay_service = services.get('trmypay')

        if not trmypay_service:
            raise Exception("Service 'trmypay' tidak ditemukan.")

        mypay_data = trmypay_service.get_mypay_overview(user_id)

        return jsonify({
            'no_hp': mypay_data.get('no_hp', ""),
            'saldo': mypay_data.get('saldo', 0),
            'riwayat_transaksi': mypay_data.get('riwayat_transaksi', [])
        }), 200
    except Exception as e:
        logger.error(f"Error fetching MyPay data: {e}", exc_info=True)
        return jsonify({'error': f"Gagal mengambil data MyPay: {str(e)}"}), 500


@app.route('/api/mypay/form/<uuid:user_id>', methods=['GET'])
def get_mypay_form(user_id):
    try:
        services = get_services()
        trmypay_service = services.get('trmypay')
        
        if not trmypay_service:
            raise Exception("Service 'trmypay' tidak ditemukan.") 
        
        form_data = trmypay_service.get_transaction_form(str(user_id))
        return jsonify(form_data), 200
    
    except Exception as e:
        logger.error(f"Error fetching MyPay form data: {e}")
        return jsonify({'error': f"Gagal mengambil form transaksi MyPay: {str(e)}"}), 500


@app.route('/api/mypay/create-transaction/<uuid:user_id>', methods=['POST'])
def create_transaction(user_id):
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['nama_kategori', 'data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f"Missing required field: {field}"}), 400

        services = get_services()
        trmypay_service = services['trmypay']  
        result = trmypay_service.create_transaction(str(user_id), data['nama_kategori'], data['data'])
        return jsonify(result)
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/pesanan', methods=['POST'])
def create_pesanan_jasa():
    try:
        services = get_services()
        pemesanan_jasa_service = services['pemesananjasa']

        data = request.json
        tanggal_pemesanan = datetime.strptime(data['tanggal_pemesanan'], '%Y-%m-%d')
        diskon_id = data['diskon_id']
        metode_bayar_id = data['metode_bayar_id']
        pelanggan_id = data['pelanggan_id']

        pesanan_id = pemesanan_jasa_service.create_pesanan_jasa(tanggal_pemesanan, diskon_id, metode_bayar_id, pelanggan_id)
        return jsonify({'pesanan_id': pesanan_id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pesanan/<int:pelanggan_id>', methods=['GET'])
def get_pesanan_by_pelanggan(pelanggan_id):
    try:
        services = get_services()
        pemesanan_jasa_service = services['pemesananjasa']
        pesanan_list = pemesanan_jasa_service.get_pesanan_by_pelanggan(pelanggan_id)
        return jsonify(pesanan_list), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pesanan/status', methods=['PUT'])
def update_status_pesanan():
    try:
        services = get_services()
        pemesanan_jasa_service = services['pemesananjasa']

        data = request.json
        pesanan_id = data['pesanan_id']
        status = data['status']

        pemesanan_jasa_service.update_status_pesanan(pesanan_id, status)
        return jsonify({'message': 'Status updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pesanan/cancel/<int:pesanan_id>', methods=['PUT'])
def cancel_pesanan(pesanan_id):
    try:
        services = get_services()
        pemesanan_jasa_service = services['pemesananjasa']
        pemesanan_jasa_service.cancel_pesanan(pesanan_id)
        return jsonify({'message': 'Pesanan cancelled'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/pekerjaan-jasa/<uuid:pekerja_id>', methods=['GET'])
def get_pekerjaan_jasa(pekerja_id):
    try:
        services = get_services()
        pekerja_service = services.get('pekerjakategorijasa')
        if not pekerja_service:
            raise Exception("Service 'pekerjakategorijasa' tidak ditemukan.")

        kategori_jasa = pekerja_service.get_kategori_jasa(pekerja_id)
        

        kategori_id = request.args.get('kategori_id') or (kategori_jasa[0]['id'] if kategori_jasa else None)
        subkategori_id = request.args.get('subkategori_id')

        pesanan_tersedia = pekerja_service.get_pesanan_tersedia(
            pekerja_id, kategori_id, subkategori_id
        )

        subkategori_jasa = []
        if kategori_id:
            subkategori_jasa = pekerja_service.get_subkategori_jasa(kategori_id)

        return jsonify({
            'kategori_jasa': kategori_jasa,
            'subkategori_jasa': subkategori_jasa,
            'pesanan_tersedia': pesanan_tersedia
        }), 200
    except Exception as e:
        return jsonify({'error': f"Gagal mengambil data pekerjaan jasa: {str(e)}"}), 500
    
@app.route('/api/pekerjaan-jasa/<uuid:pekerja_id>/pesanan/<uuid:pesanan_id>', methods=['PUT'])
def update_pesanan(pekerja_id, pesanan_id):

    try:
        services = get_services()
        pekerja_service = services.get('pekerjakategorijasa')
        
        if not pekerja_service:
            raise Exception("Service 'pekerjakategorijasa' tidak ditemukan.")
        
        result = pekerja_service.ambil_pesanan(pekerja_id, pesanan_id)

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f"Gagal memperbarui pesanan: {str(e)}"}), 500
    

@app.route('/api/status-pekerjaan/<uuid:pekerja_id>', methods=['GET'])
def get_status_pekerjaan(pekerja_id):
    try:
        services = get_services()
        statuspekerjaan_service = services.get('statuspekerjaanjasa')

        if not statuspekerjaan_service:
            raise Exception("Service 'statuspekerjaanjasa' tidak ditemukan.")

        nama_jasa = request.args.get('nama_jasa', None)
        status = request.args.get('status', None)

        pekerjaan = statuspekerjaan_service.get_status_pekerjaan(pekerja_id, nama_jasa, status)

        return jsonify({"status_pekerjaan": pekerjaan}), 200
    except Exception as e:
        return jsonify({'error': f"Gagal mendapatkan status pekerjaan: {str(e)}"}), 500

@app.route('/api/status-pemesanan/<uuid:pekerja_id>/<uuid:pesanan_id>', methods=['PUT'])
def update_status_pemesanan(pekerja_id, pesanan_id):
    try:
        data = request.get_json()
        button_action = data.get('button_action')

        if button_action is None:
            return jsonify({"error": "Parameter 'button_action' tidak ditemukan."}), 400

        services = get_services()
        statuspekerjaan_service = services.get('statuspekerjaanjasa')

        if not statuspekerjaan_service:
            raise Exception("Service 'statuspekerjaanjasa' tidak ditemukan.")
        
        result = statuspekerjaan_service.update_status_pemesanan(
            pekerja_id, pesanan_id, button_action
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": f"Gagal memperbarui status pekerjaan: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5001)  
