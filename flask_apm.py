import os
import time
import random
import sqlite3
from flask import Flask, jsonify, request
from elasticapm.contrib.flask import ElasticAPM
import elasticapm
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# APM Configuration - Use environment variables
app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': os.getenv('ELASTIC_APM_SERVICE_NAME', 'flask-apm-demo'),
    'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL', 'http://localhost:8200'),
    'SECRET_TOKEN': os.getenv('ELASTIC_APM_SECRET_TOKEN', ''),
    'ENVIRONMENT': os.getenv('ENVIRONMENT', 'development'),
    'DEBUG': os.getenv('ELASTIC_APM_DEBUG', 'true').lower() == 'true',
    'CAPTURE_BODY': 'all',  # Capture request bodies
    'TRANSACTION_SAMPLE_RATE': 1.0,  # Sample 100% of transactions
}

apm = ElasticAPM(app)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('demo.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product TEXT NOT NULL,
            amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()


@app.route('/')
def home():
    """Simple home endpoint"""
    elasticapm.label(endpoint='home', version='1.0')
    return jsonify({
        'message': 'Welcome to APM Demo Service',
        'endpoints': [
            '/',
            '/health',
            '/api/users',
            '/api/users/<id>',
            '/api/orders',
            '/api/slow',
            '/api/error',
            '/api/random-error',
            '/api/external-call',
            '/api/complex-operation'
        ]
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'flask-apm-demo'})


@app.route('/api/users', methods=['GET', 'POST'])
def users():
    """Get all users or create a new user"""
    if request.method == 'POST':
        # Create user with custom span
        with elasticapm.capture_span('create_user', 'db.sqlite'):
            data = request.get_json()
            conn = sqlite3.connect('demo.db')
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (name, email) VALUES (?, ?)',
                (data.get('name'), data.get('email'))
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()

            elasticapm.label(user_id=user_id, operation='create')
            return jsonify({'id': user_id, 'message': 'User created'}), 201
    else:
        # Get all users with custom span
        with elasticapm.capture_span('fetch_all_users', 'db.sqlite'):
            conn = sqlite3.connect('demo.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, email, created_at FROM users')
            users = [
                {'id': row[0], 'name': row[1], 'email': row[2], 'created_at': row[3]}
                for row in cursor.fetchall()
            ]
            conn.close()

            elasticapm.label(user_count=len(users))
            return jsonify(users)


@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    """Get a specific user by ID"""
    with elasticapm.capture_span('fetch_user_by_id', 'db.sqlite'):
        conn = sqlite3.connect('demo.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, created_at FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            elasticapm.label(user_id=user_id, found=True)
            return jsonify({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'created_at': row[3]
            })
        else:
            elasticapm.label(user_id=user_id, found=False)
            return jsonify({'error': 'User not found'}), 404


@app.route('/api/orders', methods=['GET', 'POST'])
def orders():
    """Get all orders or create a new order"""
    if request.method == 'POST':
        with elasticapm.capture_span('create_order', 'db.sqlite'):
            data = request.get_json()
            conn = sqlite3.connect('demo.db')
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO orders (user_id, product, amount) VALUES (?, ?, ?)',
                (data.get('user_id'), data.get('product'), data.get('amount'))
            )
            conn.commit()
            order_id = cursor.lastrowid
            conn.close()

            elasticapm.label(order_id=order_id, amount=data.get('amount'))
            return jsonify({'id': order_id, 'message': 'Order created'}), 201
    else:
        with elasticapm.capture_span('fetch_all_orders', 'db.sqlite'):
            conn = sqlite3.connect('demo.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.id, o.user_id, u.name, o.product, o.amount, o.created_at
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id
            ''')
            orders = [
                {
                    'id': row[0],
                    'user_id': row[1],
                    'user_name': row[2],
                    'product': row[3],
                    'amount': row[4],
                    'created_at': row[5]
                }
                for row in cursor.fetchall()
            ]
            conn.close()

            elasticapm.label(order_count=len(orders))
            return jsonify(orders)


@app.route('/api/slow')
def slow_endpoint():
    """Simulates a slow operation"""
    duration = random.uniform(1.0, 3.0)

    with elasticapm.capture_span('slow_processing', 'custom'):
        elasticapm.label(duration_seconds=round(duration, 2))
        time.sleep(duration)

    return jsonify({
        'message': 'Slow operation completed',
        'duration': round(duration, 2)
    })


@app.route('/api/error')
def error_endpoint():
    """Intentionally raises an error"""
    elasticapm.label(endpoint='error', intentional=True)
    raise ValueError("This is an intentional error for APM testing")


@app.route('/api/random-error')
def random_error():
    """Randomly raises an error (50% chance)"""
    if random.random() < 0.5:
        elasticapm.label(error_occurred=True)
        raise RuntimeError("Random error occurred!")
    else:
        elasticapm.label(error_occurred=False)
        return jsonify({'message': 'Success! No error this time.'})


@app.route('/api/external-call')
def external_call():
    """Makes an external HTTP call"""
    with elasticapm.capture_span('external_api_call', 'external.http'):
        try:
            # Call a public API
            response = requests.get('https://api.github.com/repos/elastic/apm-agent-python', timeout=5)
            elasticapm.label(
                status_code=response.status_code,
                response_time_ms=int(response.elapsed.total_seconds() * 1000)
            )

            if response.status_code == 200:
                data = response.json()
                return jsonify({
                    'repo': data.get('full_name'),
                    'stars': data.get('stargazers_count'),
                    'forks': data.get('forks_count')
                })
            else:
                return jsonify({'error': 'Failed to fetch data'}), 502
        except Exception as e:
            elasticapm.capture_exception()
            return jsonify({'error': str(e)}), 500


@app.route('/api/complex-operation')
def complex_operation():
    """Simulates a complex operation with multiple spans"""

    # Step 1: Validate input
    with elasticapm.capture_span('validate_input', 'custom'):
        time.sleep(0.1)
        elasticapm.label(validation='passed')

    # Step 2: Fetch data from database
    with elasticapm.capture_span('fetch_data', 'db.sqlite'):
        conn = sqlite3.connect('demo.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM orders')
        order_count = cursor.fetchone()[0]
        conn.close()
        time.sleep(0.2)

    # Step 3: Process data
    with elasticapm.capture_span('process_data', 'custom'):
        time.sleep(0.3)
        result = {
            'total_users': user_count,
            'total_orders': order_count,
            'avg_orders_per_user': round(order_count / user_count, 2) if user_count > 0 else 0
        }
        elasticapm.label(users=user_count, orders=order_count)

    # Step 4: Generate report
    with elasticapm.capture_span('generate_report', 'custom'):
        time.sleep(0.15)
        result['report_generated'] = True

    return jsonify(result)


@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler"""
    # APM automatically captures exceptions, but we can add custom labels
    elasticapm.label(error_type=type(e).__name__)
    elasticapm.capture_exception()

    return jsonify({
        'error': str(e),
        'type': type(e).__name__
    }), 500


if __name__ == '__main__':
    print("Starting Flask APM Demo Service...")
    print(f"APM Service Name: {app.config['ELASTIC_APM']['SERVICE_NAME']}")
    print(f"APM Server URL: {app.config['ELASTIC_APM']['SERVER_URL']}")
    app.run(debug=True, host='0.0.0.0', port=5000)
