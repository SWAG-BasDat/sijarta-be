import os
from dotenv import load_dotenv
import psycopg2
from flask import Flask, jsonify

load_dotenv()
app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_PUBLIC_URL')


def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

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

if __name__ == '__main__':
    app.run(debug=True)