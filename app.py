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
    from config import DB_CONFIG
except ImportError:
    # Fallback configuration if config.py doesn't exist
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'database-1.cv48gkiqsk4d.ca-central-1.rds.amazonaws.com'),
        'port': os.getenv('DB_PORT', '5432'),
        'dbname': os.getenv('DB_NAME', 'citizentest'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '1X8HcEa%iP%yT_lqz1)S~#b&QoV8x{U1')
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

def get_client_ip():
    """Get client IP address from request"""
    if request.headers.get('X-Forwarded-For'):
        # If behind a proxy, get the first IP
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr
    return ip

def init_database():
    """Initialize database tables if they don't exist"""
    global db_connected
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            
            # Create visitor_counter table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS visitor_counter (
                    counter_id VARCHAR(50) PRIMARY KEY,
                    count INTEGER NOT NULL DEFAULT 100,
                    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create visitor_log table to track IP addresses and access times
            cur.execute("""
                CREATE TABLE IF NOT EXISTS visitor_log (
                    log_id SERIAL PRIMARY KEY,
                    ip_address VARCHAR(45) NOT NULL,
                    access_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    page_visited VARCHAR(255),
                    user_agent TEXT,
                    referer TEXT
                )
            """)
            
            # Create index on IP and access_time for faster queries
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_visitor_log_ip ON visitor_log(ip_address)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_visitor_log_time ON visitor_log(access_time)
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
            print("Database connected successfully! Visitor log table created.")
        else:
            db_connected = False
            print("Failed to connect to database")
    except Exception as e:
        db_connected = False
        print(f"Error initializing database: {e}")

def log_visitor(page_visited='/'):
    """Log visitor IP address and access time"""
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            ip = get_client_ip()
            user_agent = request.headers.get('User-Agent', '')
            referer = request.headers.get('Referer', '')
            
            cur.execute("""
                INSERT INTO visitor_log (ip_address, access_time, page_visited, user_agent, referer)
                VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s)
            """, (ip, page_visited, user_agent, referer))
            conn.commit()
            cur.close()
            conn.close()
    except Exception as e:
        print(f"Error logging visitor: {e}")

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
    log_visitor('/book_summary.html')
    return render_template('book_summary.html')

@app.route('/citizenship-441')
def citizenship_441():
    """Serve the 441 citizenship questions educational page (bilingual FA/EN, RTL)"""
    log_visitor('/citizenship-441')
    return render_template('citizenship_441.html')

@app.route('/discover.pdf')
def discover_pdf():
    """Serve the Discover Canada PDF file"""
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'discover.pdf')

@app.route('/googlee38c49b065f08d79.html')
def google_verification():
    """Serve Google Search Console verification file"""
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'googlee38c49b065f08d79.html')

@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt file for search engines"""
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'robots.txt'), 200, {'Content-Type': 'text/plain'}

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
    
    # Log the visit when counter is incremented
    log_visitor('/api/visitor-count/increment')
    
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

@app.route('/api/visitor-log', methods=['GET'])
def get_visitor_log():
    """Get visitor log with IP addresses and access times"""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        ip_filter = request.args.get('ip', None)
        
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            if ip_filter:
                # Filter by IP address
                cur.execute("""
                    SELECT log_id, ip_address, access_time, page_visited, user_agent, referer
                    FROM visitor_log
                    WHERE ip_address = %s
                    ORDER BY access_time DESC
                    LIMIT %s OFFSET %s
                """, (ip_filter, limit, offset))
            else:
                # Get all logs
                cur.execute("""
                    SELECT log_id, ip_address, access_time, page_visited, user_agent, referer
                    FROM visitor_log
                    ORDER BY access_time DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
            
            logs = cur.fetchall()
            
            # Get total count
            if ip_filter:
                cur.execute("SELECT COUNT(*) as total FROM visitor_log WHERE ip_address = %s", (ip_filter,))
            else:
                cur.execute("SELECT COUNT(*) as total FROM visitor_log")
            total = cur.fetchone()['total']
            
            cur.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'logs': [dict(log) for log in logs],
                'total': total,
                'limit': limit,
                'offset': offset
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 500
    except Exception as e:
        print(f"Error getting visitor log: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/visitor-stats', methods=['GET'])
def get_visitor_stats():
    """Get visitor statistics"""
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get total visits
            cur.execute("SELECT COUNT(*) as total_visits FROM visitor_log")
            total_visits = cur.fetchone()['total_visits']
            
            # Get unique IPs
            cur.execute("SELECT COUNT(DISTINCT ip_address) as unique_ips FROM visitor_log")
            unique_ips = cur.fetchone()['unique_ips']
            
            # Get visits today
            cur.execute("""
                SELECT COUNT(*) as visits_today 
                FROM visitor_log 
                WHERE DATE(access_time) = CURRENT_DATE
            """)
            visits_today = cur.fetchone()['visits_today']
            
            # Get top IPs
            cur.execute("""
                SELECT ip_address, COUNT(*) as visit_count
                FROM visitor_log
                GROUP BY ip_address
                ORDER BY visit_count DESC
                LIMIT 10
            """)
            top_ips = cur.fetchall()
            
            cur.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'total_visits': total_visits,
                'unique_ips': unique_ips,
                'visits_today': visits_today,
                'top_ips': [dict(ip) for ip in top_ips]
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 500
    except Exception as e:
        print(f"Error getting visitor stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5011 ))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
