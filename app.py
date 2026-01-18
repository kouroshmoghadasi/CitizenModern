from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Import database configuration
try:
    from config import DB_CONFIG, FLASK_CONFIG
except ImportError:
    # Fallback configuration if config.py doesn't exist
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'database-1.cv48gkiqsk4d.ca-central-1.rds.amazonaws.com'),
        'port': os.getenv('DB_PORT', '5432'),
        'dbname': os.getenv('DB_NAME', 'citizentest'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '1X8HcEa%iP%yT_lqz1)S~#b&QoV8x{U1')
    }
    FLASK_CONFIG = {
        'host': os.getenv('FLASK_HOST', '0.0.0.0'),
        'port': int(os.getenv('FLASK_PORT', '5011')),
        'debug': os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    }

# Database connection pool (simple connection per request)
db_connected = False

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database table if it doesn't exist"""
    global db_connected
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            
            # Create table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS visitor_counter (
                    counter_id VARCHAR(50) PRIMARY KEY,
                    count INTEGER NOT NULL DEFAULT 100,
                    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Check if main counter exists
            cur.execute("SELECT count FROM visitor_counter WHERE counter_id = 'main'")
            result = cur.fetchone()
            
            if result is None:
                # Initialize counter with starting value of 100
                cur.execute("""
                    INSERT INTO visitor_counter (counter_id, count, last_updated)
                    VALUES ('main', 100, CURRENT_TIMESTAMP)
                """)
                conn.commit()
                print("Visitor counter table initialized with count = 100")
            else:
                print(f"Visitor counter already exists with count = {result[0]}")
            
            cur.close()
            conn.close()
            db_connected = True
            print("Database connected successfully!")
        else:
            db_connected = False
            print("Failed to connect to database")
    except Exception as e:
        db_connected = False
        print(f"Error initializing database: {e}")

# Initialize database on startup
init_database()

# Fallback: use in-memory counter if database is not available
in_memory_counter = 100  # Starting value

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('canadian_citizenship.html')

@app.route('/book_summary.html')
def book_summary():
    """Serve the book summary page"""
    return render_template('book_summary.html')

@app.route('/discover.pdf')
def discover_pdf():
    """Serve the Discover Canada PDF file"""
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'discover.pdf')

@app.route('/api/visitor-count', methods=['GET'])
def get_visitor_count():
    """Get current visitor count without incrementing"""
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT count, last_updated FROM visitor_counter WHERE counter_id = 'main'")
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            if result:
                return jsonify({
                    'success': True,
                    'count': result['count'],
                    'last_updated': result['last_updated'].isoformat() if result['last_updated'] else ''
                })
            else:
                # Initialize counter if it doesn't exist
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO visitor_counter (counter_id, count, last_updated)
                        VALUES ('main', %s, CURRENT_TIMESTAMP)
                    """, (in_memory_counter,))
                    conn.commit()
                    cur.close()
                    conn.close()
                    return jsonify({
                        'success': True,
                        'count': in_memory_counter,
                        'last_updated': datetime.utcnow().isoformat()
                    })
        else:
            # Fallback to in-memory counter
            return jsonify({
                'success': True,
                'count': in_memory_counter,
                'last_updated': datetime.utcnow().isoformat(),
                'warning': 'Using in-memory counter (Database not available)'
            })
    except Exception as e:
        print(f"Error getting visitor count: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'count': in_memory_counter,
            'warning': 'Database error, using in-memory counter'
        }), 200

@app.route('/api/visitor-count/increment', methods=['POST'])
def increment_visitor_count():
    """Increment visitor count by 1 and return new count"""
    global in_memory_counter
    
    try:
        conn = get_db_connection()
        if conn:
            # Use atomic update to increment counter
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # First, ensure the record exists with starting value of 100
            cur.execute("""
                INSERT INTO visitor_counter (counter_id, count, last_updated)
                VALUES ('main', 100, CURRENT_TIMESTAMP)
                ON CONFLICT (counter_id) DO NOTHING
            """)
            
            # Atomic increment using UPDATE
            cur.execute("""
                UPDATE visitor_counter
                SET count = count + 1,
                    last_updated = CURRENT_TIMESTAMP
                WHERE counter_id = 'main'
                RETURNING count, last_updated
            """)
            
            result = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            
            if result:
                return jsonify({
                    'success': True,
                    'count': result['count'],
                    'last_updated': result['last_updated'].isoformat()
                })
            else:
                # Should not happen, but handle it
                in_memory_counter += 1
                return jsonify({
                    'success': True,
                    'count': in_memory_counter,
                    'last_updated': datetime.utcnow().isoformat(),
                    'warning': 'Update returned no rows, using in-memory counter'
                })
        else:
            # Fallback to in-memory counter
            in_memory_counter += 1
            return jsonify({
                'success': True,
                'count': in_memory_counter,
                'last_updated': datetime.utcnow().isoformat(),
                'warning': 'Using in-memory counter (Database not available)'
            })
    except Exception as e:
        print(f"Error incrementing visitor count: {e}")
        # Fallback to in-memory counter
        in_memory_counter += 1
        return jsonify({
            'success': True,
            'count': in_memory_counter,
            'last_updated': datetime.utcnow().isoformat(),
            'warning': f'Database error: {str(e)}, using in-memory counter'
        }), 200

@app.route('/api/visitor-count', methods=['POST'])
def update_visitor_count():
    """Update visitor count (same as increment for convenience)"""
    return increment_visitor_count()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_status = 'disconnected'
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            db_status = 'connected'
    except:
        pass
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'in_memory_counter': in_memory_counter
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Run Flask app with configuration
    app.run(
        debug=FLASK_CONFIG['debug'],
        host=FLASK_CONFIG['host'],
        port=FLASK_CONFIG['port']
    )
