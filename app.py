import os
from dotenv import load_dotenv
import psycopg2
from flask import Flask, jsonify

load_dotenv()
app = Flask(__name__)

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.route('/test-connection')
def test_connection():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Test doang yak
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

if __name__ == '__main__':
    app.run(debug=True)