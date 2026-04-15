from flask import Flask, jsonify, request, render_template, send_from_directory, redirect, session, abort, url_for
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import re
import json
import random
from collections import defaultdict
from difflib import SequenceMatcher
import string
import ipaddress
from datetime import datetime, timezone, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-this-secret-in-production-citizen-subscription')
# تا وقتی کش پاک نشده، ورود اشتراک حفظ شود (به‌جای از بین رفتن با بستن مرورگر)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=90)
CORS(app)  # Enable CORS for frontend requests
try:
    from flask_compress import Compress  # type: ignore[import-untyped]
    Compress(app)  # Gzip compression for faster responses
except ImportError:
    pass  # Run without gzip if flask-compress not installed

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

# IPهایی که در لاگ و داشبورد حضور شمرده نشوند (خودمون / ادمین). از env: EXCLUDED_VISITOR_IPS با کاما
_excluded_visitor_ips = frozenset(
    x.strip() for x in os.getenv('EXCLUDED_VISITOR_IPS', '').split(',') if x.strip()
)

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


def _is_loopback_ip(ip):
    """True برای localhost / 127.x / ::1 — نباید در لاگ یا شمارندهٔ رسمی لحاظ شود."""
    if ip is None:
        return False
    s = str(ip).strip()
    if not s:
        return False
    if s.lower() == 'localhost':
        return True
    try:
        return ipaddress.ip_address(s).is_loopback
    except ValueError:
        return s.startswith('127.')


def _is_loopback_client():
    return _is_loopback_ip(get_client_ip())


def _device_from_user_agent(ua):
    """بر اساس User-Agent برچسب دستگاه (موبایل، دسکتاپ، تبلت، ربات) برمی‌گرداند."""
    if not ua or not isinstance(ua, str):
        return '—'
    u = ua.lower()
    if 'bot' in u or 'crawler' in u or 'spider' in u or 'headless' in u:
        return 'ربات'
    if 'mobile' in u and 'tablet' not in u and 'ipad' not in u:
        return 'موبایل'
    if 'tablet' in u or 'ipad' in u:
        return 'تبلت'
    if 'android' in u and 'mobile' not in u:
        return 'تبلت'
    return 'دسکتاپ'


def _ensure_subscription_users_citizenship_columns(cur):
    """ستون‌های شهروندی را در صورت نبود اضافه می‌کند (ابتدا IF NOT EXISTS برای PG11+، وگرنه ADD معمولی)."""
    specs = (
        ("citizenship_city", "VARCHAR(150)"),
        ("citizenship_apply_date", "DATE"),
        ("citizenship_exam_date", "DATE"),
        ("citizenship_exam_score", "VARCHAR(50)"),
    )
    for col, typ in specs:
        try:
            cur.execute(
                f"ALTER TABLE subscription_users ADD COLUMN IF NOT EXISTS {col} {typ}"
            )
        except Exception:
            try:
                cur.execute(
                    f"ALTER TABLE subscription_users ADD COLUMN {col} {typ}"
                )
            except Exception:
                pass


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
                    count INTEGER NOT NULL DEFAULT 0,
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
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_visitor_log_page ON visitor_log(page_visited)
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_migrations (
                    id VARCHAR(64) PRIMARY KEY,
                    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("SELECT 1 FROM app_migrations WHERE id = 'purge_loopback_visitor_log_v1'")
            if cur.fetchone() is None:
                cur.execute("""
                    DELETE FROM visitor_log
                    WHERE COALESCE(ip_address, '') ILIKE '127.%%'
                       OR COALESCE(ip_address, '') ILIKE '::ffff:127.%%'
                       OR LOWER(TRIM(COALESCE(ip_address, ''))) IN ('::1', 'localhost')
                """)
                cur.execute(
                    "INSERT INTO app_migrations (id) VALUES ('purge_loopback_visitor_log_v1')"
                )
            cur.execute("SELECT 1 FROM app_migrations WHERE id = 'visitor_counter_remove_100_baseline_v1'")
            if cur.fetchone() is None:
                cur.execute("""
                    UPDATE visitor_counter
                    SET count = GREATEST(0, count - 100)
                    WHERE counter_id = 'main'
                """)
                cur.execute(
                    "INSERT INTO app_migrations (id) VALUES ('visitor_counter_remove_100_baseline_v1')"
                )
            cur.execute("SELECT 1 FROM app_migrations WHERE id = 'visitor_counter_default_zero_v1'")
            if cur.fetchone() is None:
                try:
                    cur.execute("ALTER TABLE visitor_counter ALTER COLUMN count SET DEFAULT 0")
                except Exception:
                    pass
                cur.execute(
                    "INSERT INTO app_migrations (id) VALUES ('visitor_counter_default_zero_v1')"
                )
            
            # --- Subscription: users (subscribers)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subscription_users (
                    id SERIAL PRIMARY KEY,
                    mobile VARCHAR(20) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # --- Subscription: current status per section (one row per user per section)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subscription_subscriptions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES subscription_users(id) ON DELETE CASCADE,
                    section VARCHAR(20) NOT NULL CHECK (section IN ('tests', 'questions_414')),
                    expiry_date DATE NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, section)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sub_expiry ON subscription_subscriptions(expiry_date)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sub_user_section ON subscription_subscriptions(user_id, section)")
            # --- Subscription: payment history
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subscription_payments (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES subscription_users(id) ON DELETE CASCADE,
                    amount INTEGER NOT NULL CHECK (amount IN (10, 15, 20)),
                    sections_purchased VARCHAR(20) NOT NULL CHECK (sections_purchased IN ('tests', 'questions_414', 'both')),
                    payment_date DATE NOT NULL,
                    payment_reference VARCHAR(100),
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_payments_user ON subscription_payments(user_id)")
            # Allow amount 15 (migration for existing DBs)
            try:
                cur.execute("ALTER TABLE subscription_payments DROP CONSTRAINT IF EXISTS subscription_payments_amount_check")
                cur.execute("ALTER TABLE subscription_payments ADD CONSTRAINT subscription_payments_amount_check CHECK (amount IN (10, 15, 20))")
            except Exception:
                pass
            # --- درخواست‌های دسترسی (وقتی کاربر «خیر» می‌زند و موبایل می‌دهد تا کد کاربر ساخته شود)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subscription_pending_requests (
                    id SERIAL PRIMARY KEY,
                    mobile VARCHAR(30) NOT NULL,
                    section VARCHAR(20) NOT NULL CHECK (section IN ('tests', 'questions_414', 'both')),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_pending_requests_created ON subscription_pending_requests(created_at DESC)")
            # --- Admin users (for /admin panel)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Ensure at least one admin exists (default: admin / admin123 - change after first login)
            cur.execute("SELECT id FROM admin_users WHERE username = %s", ('admin',))
            if cur.fetchone() is None:
                cur.execute("""
                    INSERT INTO admin_users (username, password_hash)
                    VALUES (%s, %s)
                """, ('admin', generate_password_hash(os.getenv('ADMIN_INITIAL_PASSWORD', 'admin123'))))
            # --- Site settings (e.g. subscription price)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS site_settings (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            cur.execute("SELECT value FROM site_settings WHERE key = %s", ('subscription_price_dollars',))
            if cur.fetchone() is None:
                cur.execute("INSERT INTO site_settings (key, value) VALUES ('subscription_price_dollars', '15')")
            conn.commit()
            # Allow any reasonable payment amount (was 10,15,20 only)
            try:
                cur.execute("ALTER TABLE subscription_payments DROP CONSTRAINT IF EXISTS subscription_payments_amount_check")
                cur.execute("ALTER TABLE subscription_payments ADD CONSTRAINT subscription_payments_amount_check CHECK (amount >= 5 AND amount <= 10000)")
            except Exception:
                pass
            # نام و نام خانوادگی کاربر اشتراک (برای نگهداری در بخش ادمین) — فقط در صورت نبود ستون اضافه می‌شود
            for col in ('first_name', 'last_name'):
                cur.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_schema = 'public' AND table_name = 'subscription_users' AND column_name = %s
                        ) THEN
                            ALTER TABLE subscription_users ADD COLUMN """ + col + """ VARCHAR(100);
                        END IF;
                    END $$;
                """, (col,))
            for _col_name, _col_type in (
                ("citizenship_apply_date", "DATE"),
                ("citizenship_exam_date", "DATE"),
                ("citizenship_exam_score", "VARCHAR(50)"),
                ("citizenship_city", "VARCHAR(150)"),
            ):
                cur.execute(
                    f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_schema = 'public' AND table_name = 'subscription_users' AND column_name = '{_col_name}'
                        ) THEN
                            ALTER TABLE subscription_users ADD COLUMN {_col_name} {_col_type};
                        END IF;
                    END $$;
                    """
                )
            _ensure_subscription_users_citizenship_columns(cur)
            conn.commit()
            
            # Check if main counter exists
            cur.execute("SELECT count FROM visitor_counter WHERE counter_id = 'main'")
            result = cur.fetchone()
            
            if result is None:
                cur.execute("""
                    INSERT INTO visitor_counter (counter_id, count, last_updated)
                    VALUES ('main', 0, CURRENT_TIMESTAMP)
                """)
                conn.commit()
                print("Visitor counter table initialized with count = 0")
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


def get_subscription_price():
    """مبلغ اشتراک (دلار) از site_settings. پیش‌فرض ۱۵."""
    try:
        conn = get_db_connection()
        if not conn:
            return 15
        cur = conn.cursor()
        cur.execute("SELECT value FROM site_settings WHERE key = %s", ('subscription_price_dollars',))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return int(row[0]) if str(row[0]).strip().isdigit() else 15
    except Exception:
        pass
    return 15


def set_subscription_price(amount):
    """ذخیره مبلغ اشتراک (دلار). مقدار معتبر: ۵ تا ۱۰۰۰۰."""
    try:
        a = int(amount)
        if a < 5 or a > 10000:
            return False
        conn = get_db_connection()
        if not conn:
            return False
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO site_settings (key, value) VALUES ('subscription_price_dollars', %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """, (str(a),))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception:
        return False


@app.context_processor
def inject_subscription_price():
    """مبلغ اشتراک در همهٔ قالب‌ها به‌صورت subscription_price (عدد) در دسترس است."""
    return {'subscription_price': get_subscription_price()}


def log_visitor(page_visited='/'):
    """Log visitor IP address and access time. localhost و IPهای EXCLUDED_VISITOR_IPS لاگ نمی‌شوند."""
    try:
        ip = get_client_ip()
        if _is_loopback_ip(ip):
            return
        if ip in _excluded_visitor_ips:
            return
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
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


def _visitor_exclude_sql():
    """شرط SQL برای حذف IP حلقهٔ محلی (127، ::1، …) و IPهای پیکربندی‌شده (ادمین) از آمار و تاریخچهٔ تجمیعی."""
    loopback = (
        " AND COALESCE(ip_address, '') NOT ILIKE '127.%%' "
        "AND COALESCE(ip_address, '') NOT ILIKE '::ffff:127.%%' "
        "AND LOWER(TRIM(COALESCE(ip_address, ''))) NOT IN ('::1', 'localhost')"
    )
    if not _excluded_visitor_ips:
        return loopback, ()
    placeholders = ",".join(["%s"] * len(_excluded_visitor_ips))
    return (
        loopback + " AND ip_address NOT IN (" + placeholders + ")",
        tuple(_excluded_visitor_ips),
    )


def _count_exam_section_visits():
    """تعداد بازدیدهای ثبت‌شده برای بخش آزمون‌های نمونه (فهرست + Introduction + Rights + Who We Are + Canada's History + Govern + Federal Elections + Canadian Symbols + Canada's Economy + Canada's Regions + Justice + Modern Canada + Exam1–3) از visitor_log."""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        cur = conn.cursor()
        exclude_sql, exclude_params = _visitor_exclude_sql()
        cur.execute(
            """
            SELECT COUNT(*) FROM visitor_log
            WHERE page_visited IN ('/citizenship-exams', '/citizenship-introduction', '/citizenship-rights-responsibilities', '/citizenship-who-we-are', '/citizenship-canadas-history', '/citizenship-how-canadians-govern-themselves', '/citizenship-federal-elections', '/citizenship-canadian-symbols', '/citizenship-canadas-economy', '/citizenship-canadas-regions', '/citizenship-justice-system', '/citizenship-modern-canada', '/exam1', '/exam2', '/exam3')
            """
            + exclude_sql,
            exclude_params,
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row and row[0] is not None:
            return int(row[0])
        return 0
    except Exception as e:
        print(f"Error counting exam section visits: {e}")
        return None


# Initialize database on startup
init_database()

# Fallback: use in-memory counter if database is not available
in_memory_counter = 0


@app.after_request
def add_cache_headers(response):
    """Set Cache-Control for static assets and public files to improve speed."""
    if response.status_code != 200:
        return response
    path = request.path
    if path.startswith('/static/'):
        # Static files (images, CSS, JS): cache 1 year (use versioned filenames if you change them)
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    elif path in ('/discover.pdf', '/robots.txt', '/sitemap.xml', '/site-map'):
        # PDF و فایل‌های SEO / نقشهٔ سایت: کش ۱ روز
        response.headers['Cache-Control'] = 'public, max-age=86400'
    return response


@app.route('/')
def index():
    """Serve the main HTML page (no long-lived HTML cache — تلگرام/OG باید متاهای به‌روز بگیرند)."""
    resp = app.make_response(render_template('canadian_citizenship.html'))
    resp.headers['Cache-Control'] = 'no-cache, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/book_summary.html')
def book_summary():
    """Serve the book summary page"""
    log_visitor('/book_summary.html')
    return render_template('book_summary.html')


@app.route('/book_summary')
def book_summary_short_url():
    """یک URL کانونیکال: جلوگیری از نسخهٔ تکراری بدون .html در گوگل."""
    return redirect(url_for('book_summary'), code=301)


_canada_history_timeline_cache = None


def _load_canada_history_timeline():
    global _canada_history_timeline_cache
    if _canada_history_timeline_cache is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'data', 'canada_history_timeline.json')
        with open(path, encoding='utf-8') as f:
            _canada_history_timeline_cache = json.load(f)
    return _canada_history_timeline_cache


@app.route('/canadian-history-timeline')
def canadian_history_timeline():
    """صفحهٔ مطالعه: خط زمانی رویدادهای کلیدی تاریخ کانادا (Discover Canada)."""
    log_visitor('/canadian-history-timeline')
    data = _load_canada_history_timeline()
    return render_template(
        'canadian_history_timeline.html',
        timeline=data,
        exam_section_views=_count_exam_section_visits(),
    )


@app.route('/canadian-history-timeline.html')
def canadian_history_timeline_html_alias():
    return redirect(url_for('canadian_history_timeline'), code=301)


@app.route('/index.html')
def index_html_alias():
    """نسخهٔ تکراری رایج صفحهٔ اصلی → یک کانونیکال."""
    return redirect(url_for('index'), code=301)


@app.route('/about')
def about():
    """About the site — educational notice and contact"""
    log_visitor('/about')
    return render_template('about.html')

# Cache for 414/571 questions (loaded once per process, no disk read per request)
_cache_414 = None
_cache_571 = None
_cache_introduction = None
_cache_chapter1 = None
_cache_chapter2 = None
_cache_chapter3 = None
_cache_chapter4 = None
_cache_govern = None
_cache_federal_elections = None
_cache_justice = None
_cache_canadian_symbols = None
_cache_federal_questions_226 = None
_cache_canada_economy = None
_cache_canada_regions = None
_cache_exam1 = None
_cache_exam2 = None
_cache_exam3 = None


def _load_414_questions():
    """Load 414 questions once and cache in memory."""
    global _cache_414
    if _cache_414 is not None:
        return _cache_414
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'citizenship_414_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for q in data:
                q.setdefault('q_fr', q.get('q_en'))
                q.setdefault('a_fr', q.get('a_en'))
                q.setdefault('expl_fr', q.get('expl_en'))
            _cache_414 = data
            return _cache_414
    except Exception:
        pass
    _cache_414 = []
    return _cache_414


@app.route('/citizenship-414')
def citizenship_414():
    """۴۱۴ سوال شهروندی — سوالات ۱–۲۴ رایگان؛ از ۲۵ به بعد با اشتراک."""
    log_visitor('/citizenship-414')
    all_questions = _load_414_questions()
    today = _today()
    has_414 = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_414 = True
        except Exception:
            pass
    if has_414:
        questions = all_questions
        show_paywall = False
        max_question_414 = 414
    else:
        questions = all_questions[:24] if len(all_questions) >= 24 else all_questions
        show_paywall = True
        max_question_414 = 25
    resp = app.make_response(render_template(
        'citizenship_414.html',
        questions=questions,
        show_paywall=show_paywall,
        max_question_414=max_question_414,
    ))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


def _build_en_to_fa_option_map():
    """نگاشت متن انگلیسی گزینه → فارسی: اول از فایل ۵۷۱، بعد از دادهٔ ۴۱۴."""
    en_to_fa = {}
    try:
        q414 = _load_414_questions()
        for q in q414:
            en_list = q.get('options_en') or []
            fa_list = q.get('options_fa') or []
            for j, en in enumerate(en_list):
                if j < len(fa_list) and en and fa_list[j]:
                    en_to_fa[en.strip()] = fa_list[j].strip()
    except Exception:
        pass
    for name in ('571_options_fa.json', '571_options_fa_extra.json', '571_options_fa_complete.json', '571_options_fa_q9.json', 'chapter3_options_fa.json', 'chapter4_options_fa.json', 'govern_options_fa_patch.json', 'federal_elections_options_fa_patch.json', 'justice_options_fa_patch.json', 'canadian_symbols_options_fa_patch.json'):
        path_571_fa = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', name)
        try:
            if os.path.isfile(path_571_fa):
                with open(path_571_fa, 'r', encoding='utf-8') as f:
                    extra = json.load(f)
                if isinstance(extra, dict):
                    for k, v in extra.items():
                        if k and isinstance(k, str) and not k.strip().startswith('_') and v:
                            en_to_fa[k.strip()] = v.strip()
        except Exception:
            pass
    # تطبیق نرمال‌شده: کلید lowercase و نرمال آپوستروف هم اضافه شود
    def _norm(t):
        if not t:
            return t
        t = t.strip()
        t = t.replace('\u2019', "'")  # آپوستروف یونیکد → ASCII
        return t
    for k in list(en_to_fa.keys()):
        low = k.lower()
        if low not in en_to_fa:
            en_to_fa[low] = en_to_fa[k]
        kn = _norm(k)
        if kn and kn not in en_to_fa:
            en_to_fa[kn] = en_to_fa[k]
    return en_to_fa


_cache_en_to_fr = None


def _build_en_to_fr_option_map():
    """نگاشت متن انگلیسی گزینه → فرانسوی از ۴۱۴، ۵۷۱، question_bank، فصل ۳ و ۴."""
    global _cache_en_to_fr
    if _cache_en_to_fr is not None:
        return _cache_en_to_fr
    en_to_fr = {}
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

    def add_pairs(en_list, fr_list):
        if not en_list or not fr_list or len(en_list) != len(fr_list):
            return
        for j, en in enumerate(en_list):
            if not en:
                continue
            fr = fr_list[j] if j < len(fr_list) else ''
            if not fr or not str(fr).strip():
                continue
            es = en.strip()
            fs = str(fr).strip()
            if fs.lower() == es.lower():
                continue
            en_to_fr[es] = fs

    try:
        q414 = _load_414_questions()
        for q in q414:
            add_pairs(q.get('options_en') or [], q.get('options_fr') or [])
    except Exception:
        pass
    for fn in (
        'citizenship_571_questions.json',
        'question_bank.json',
        'chapter3_questions.json',
        'chapter4_questions.json',
    ):
        path = os.path.join(static_dir, fn)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                continue
            for item in data:
                o_en = item.get('options') or item.get('options_en') or []
                o_fr = item.get('options_fr') or []
                add_pairs(o_en, o_fr)
        except Exception:
            pass
    _fr_alias_long = (
        (
            'Settlers who came to Canada from the United States during and after the American Revolution',
            'Settlers who came from the US during and after the American Revolution',
        ),
    )
    for long_k, short_k in _fr_alias_long:
        if short_k in en_to_fr and long_k not in en_to_fr:
            en_to_fr[long_k] = en_to_fr[short_k]
    for k in list(en_to_fr.keys()):
        low = k.lower()
        if low not in en_to_fr:
            en_to_fr[low] = en_to_fr[k]
        kn = k.replace('\u2019', "'").replace('\u2018', "'")
        if kn and kn not in en_to_fr:
            en_to_fr[kn] = en_to_fr[k]
    _cache_en_to_fr = en_to_fr
    return en_to_fr


_cache_en_to_fa_question_map = None
_cache_en_to_fr_question_map = None


def _build_en_to_fa_question_map():
    """نگاشت متن انگلیسی سؤال → فارسی از ۴۱۴، ۵۷۱، question_bank و فصل‌ها."""
    global _cache_en_to_fa_question_map
    if _cache_en_to_fa_question_map is not None:
        return _cache_en_to_fa_question_map
    m = {}
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

    def add_from_list(data):
        if not isinstance(data, list):
            return
        for item in data:
            if not isinstance(item, dict):
                continue
            q_en = (item.get('q') or item.get('q_en') or '').strip()
            q_fa = (item.get('q_fa') or '').strip()
            if q_en and q_fa:
                m[q_en] = q_fa

    try:
        add_from_list(_load_414_questions())
    except Exception:
        pass
    # برای ۲۲۶ فدرال، منبع اصلی ترجمه‌ها ۵۷۱ و ۴۱۴ است؛ اسکن همهٔ فصل‌ها/بانک بزرگ باعث کندی و تایم‌اوت می‌شود.
    for fn in (
        'citizenship_571_questions.json',
    ):
        path = os.path.join(static_dir, fn)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding='utf-8') as f:
                add_from_list(json.load(f))
        except Exception:
            pass
    # نسخه‌های پشتیبان ۵۷۱ (سؤال‌های حذف‌شده از فایل اصلی) فقط جاهای خالی را پر می‌کنند.
    for legacy_fn in (
        'citizenship_571_questions.json.bak_before_user_batches_20260327',
        'citizenship_571_questions.json.before_replace_20260327',
    ):
        leg_path = os.path.join(static_dir, legacy_fn)
        if not os.path.isfile(leg_path):
            continue
        try:
            with open(leg_path, encoding='utf-8') as lf:
                leg_data = json.load(lf)
            if not isinstance(leg_data, list):
                continue
            for item in leg_data:
                if not isinstance(item, dict):
                    continue
                q_en = (item.get('q') or item.get('q_en') or '').strip()
                q_fa = (item.get('q_fa') or '').strip()
                if q_en and q_fa and q_en not in m:
                    m[q_en] = q_fa
        except Exception:
            pass
    for k in list(m.keys()):
        low = k.lower()
        if low not in m:
            m[low] = m[k]
        kn = k.replace('\u2019', "'").replace('\u2018', "'")
        if kn and kn not in m:
            m[kn] = m[k]
    _cache_en_to_fa_question_map = m
    return m


def _build_en_to_fr_question_map():
    """نگاشت متن انگلیسی سؤال → فرانسوی از ۴۱۴، ۵۷۱ و فایل‌های دارای q_fr."""
    global _cache_en_to_fr_question_map
    if _cache_en_to_fr_question_map is not None:
        return _cache_en_to_fr_question_map
    m = {}
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

    def add_from_list(data):
        if not isinstance(data, list):
            return
        for item in data:
            if not isinstance(item, dict):
                continue
            q_en = (item.get('q') or item.get('q_en') or '').strip()
            q_fr = (item.get('q_fr') or '').strip()
            if not q_en or not q_fr:
                continue
            if q_fr.lower() == q_en.lower():
                continue
            m[q_en] = q_fr

    try:
        add_from_list(_load_414_questions())
    except Exception:
        pass
    for fn in (
        'citizenship_571_questions.json',
        'chapter1_questions.json',
        'chapter2_questions.json',
        'chapter3_questions.json',
        'chapter4_questions.json',
        'introduction_questions.json',
        'question_bank.json',
    ):
        path = os.path.join(static_dir, fn)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding='utf-8') as f:
                add_from_list(json.load(f))
        except Exception:
            pass
    for legacy_fn in (
        'citizenship_571_questions.json.bak_before_user_batches_20260327',
        'citizenship_571_questions.json.before_replace_20260327',
    ):
        leg_path = os.path.join(static_dir, legacy_fn)
        if not os.path.isfile(leg_path):
            continue
        try:
            with open(leg_path, encoding='utf-8') as lf:
                leg_data = json.load(lf)
            if not isinstance(leg_data, list):
                continue
            for item in leg_data:
                if not isinstance(item, dict):
                    continue
                q_en = (item.get('q') or item.get('q_en') or '').strip()
                q_fr = (item.get('q_fr') or '').strip()
                if not q_en or not q_fr or q_fr.lower() == q_en.lower():
                    continue
                if q_en not in m:
                    m[q_en] = q_fr
        except Exception:
            pass
    for k in list(m.keys()):
        low = k.lower()
        if low not in m:
            m[low] = m[k]
        kn = k.replace('\u2019', "'").replace('\u2018', "'")
        if kn and kn not in m:
            m[kn] = m[k]
    _cache_en_to_fr_question_map = m
    return m


def _option_string_lookup(mapping, text):
    """تطبیق متن گزینه با نگاشت (فارسی/فرانسه)؛ نرمال‌سازی گیومه، Kanata، نقطهٔ انتها."""
    t = text.strip() if text else ''
    if not t:
        return t

    def _try(s):
        if not s:
            return None
        if s in mapping:
            return mapping[s]
        low = s.lower()
        if low in mapping:
            return mapping[low]
        sn = s.replace('\u2019', "'").replace('\u2018', "'")
        if sn in mapping:
            return mapping[sn]
        if sn.lower() in mapping:
            return mapping[sn.lower()]
        return None

    variants = []
    u = t.replace('\u201c', '"').replace('\u201d', '"')
    u = re.sub(r'From\s+"Kanata"\s*,', 'From Kanata,', u, flags=re.IGNORECASE)
    for base in (t, u):
        if base not in variants:
            variants.append(base)
        st = base.rstrip('.')
        if st != base and st not in variants:
            variants.append(st)
    for v in variants:
        hit = _try(v)
        if hit is not None:
            return hit
    return text


def _fa_lookup(en_to_fa, text):
    """ترجمهٔ فارسی برای متن گزینه."""
    return _option_string_lookup(en_to_fa, text)


def _fr_lookup(en_to_fr, text):
    """ترجمهٔ فرانسوی برای متن گزینه (مثل آزمون‌های نمونه)."""
    return _option_string_lookup(en_to_fr, text)


def _expand_571_to_four_options(questions):
    """برای هر سوال ۵۷۱ که کمتر از ۴ گزینه دارد، با اضافه کردن گزینه‌های غلط از سایر سوالات، دقیقاً ۴ گزینه می‌سازیم. ردیف اول انگلیسی، ردیف دوم فارسی (از ۴۱۴ یا fallback به انگلیسی)."""
    if not questions:
        return questions
    en_to_fa = _build_en_to_fa_option_map()
    pool_pairs = []
    for q in questions:
        opts = q.get('options') or []
        opts_fr = q.get('options_fr') or opts
        c = q.get('correct', 0)
        en = opts[c] if opts and 0 <= c < len(opts) else ''
        fr = opts_fr[c] if opts_fr and 0 <= c < len(opts_fr) else en
        pool_pairs.append((en, fr))
    for i, q in enumerate(questions):
        opts = q.get('options') or []
        opts_fr = q.get('options_fr') or opts
        c = q.get('correct', 0)
        correct_en = opts[c] if opts and 0 <= c < len(opts) else ''
        correct_fr = opts_fr[c] if opts_fr and 0 <= c < len(opts_fr) else correct_en
        if len(opts) >= 4 and len(opts_fr) >= 4:
            q['options_en'] = opts[:4]
            q['options_fr'] = opts_fr[:4]
            q['options_fa'] = [_fa_lookup(en_to_fa, e) for e in opts[:4]]
            q['correct'] = min(c, 3)
            continue
        # سوالات دوگزینه‌ای (مثلاً True/False) را گسترش نده؛ همان دو گزینه بماند
        if len(opts) == 2 and len(opts_fr) >= 2:
            q['options_en'] = opts[:2]
            q['options_fr'] = (opts_fr or opts)[:2]
            q['options_fa'] = [_fa_lookup(en_to_fa, e) for e in opts[:2]]
            q['correct'] = min(c, 1)
            continue
        rng = random.Random(i)
        correct_pair = (correct_en, correct_fr)
        wrong_pairs = [p for p in pool_pairs if p != correct_pair]
        # ترجیح گزینه‌های با طول مشابه تا گزینه‌های پرت و نامرتبط (مثل لیست استان‌ها) کنار پاسخ کوتاه قرار نگیرند
        correct_len = len((correct_en or '').strip())
        if correct_len > 0 and len(wrong_pairs) > 3:
            similar = [p for p in wrong_pairs if p[0] and 0.25 * correct_len <= len(p[0].strip()) <= 4 * correct_len and ' e) ' not in (p[0] or '') and ' f) ' not in (p[0] or '')]
            if len(similar) >= 3:
                wrong_pairs = similar
        if len(wrong_pairs) < 3:
            wrong_pairs = wrong_pairs + [correct_pair] * (3 - len(wrong_pairs))
        rng.shuffle(wrong_pairs)
        four_pairs = [correct_pair] + wrong_pairs[:3]
        rng.shuffle(four_pairs)
        new_correct = next(idx for idx, p in enumerate(four_pairs) if p == correct_pair)
        four_en = [p[0] for p in four_pairs]
        four_fr = [p[1] for p in four_pairs]
        four_fa = [_fa_lookup(en_to_fa, e) for e in four_en]
        q['options_en'] = four_en
        q['options_fr'] = four_fr
        q['options_fa'] = four_fa
        q['correct'] = new_correct
    return questions


def _load_571_questions():
    """Load 571 questions once and cache in memory."""
    global _cache_571
    if _cache_571 is not None:
        return _cache_571
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    for name in ('citizenship_571_questions.json', 'question_bank.json'):
        path = os.path.join(base, name)
        try:
            if os.path.isfile(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for q in data:
                    if not q.get('q_fa'):
                        q['q_fa'] = q.get('q', '')
                    q.setdefault('q_fr', q.get('q', ''))
                    q.setdefault('options_fr', q.get('options', []))
                    q.setdefault('expl_fr', q.get('book_text', ''))
                data = _expand_571_to_four_options(data)
                _cache_571 = data
                return _cache_571
        except Exception:
            continue
    _cache_571 = []
    return _cache_571


def _load_introduction_questions():
    """Load Introduction (Test 103) questions once and cache in memory. options_fa from JSON if present, else 571/414 FA map."""
    global _cache_introduction
    if _cache_introduction is not None:
        return _cache_introduction
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    path = os.path.join(base, 'introduction_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            en_to_fa = _build_en_to_fa_option_map()
            for q in data:
                q.setdefault('q_fa', q.get('q', ''))
                q.setdefault('q_fr', q.get('q', ''))
                opts = q.get('options', [])
                q.setdefault('options_fr', opts)
                q['options_en'] = opts
                opts_fa = q.get('options_fa')
                if opts_fa and len(opts_fa) == len(opts):
                    q['options_fa'] = opts_fa
                else:
                    q['options_fa'] = [_fa_lookup(en_to_fa, e) for e in opts]
            _cache_introduction = data
            return _cache_introduction
    except Exception:
        pass
    _cache_introduction = []
    return _cache_introduction


def _load_exam1_questions():
    """Load Exam1 (Rights & Responsibilities sample MCQ) from static JSON."""
    global _cache_exam1
    if _cache_exam1 is not None:
        return _cache_exam1
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'exam1_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                _cache_exam1 = json.load(f)
            return _cache_exam1
    except Exception:
        pass
    _cache_exam1 = []
    return _cache_exam1


def _load_exam2_questions():
    """Load Exam2 (History of Canada sample MCQ) from static JSON. options_fa از chapter3/۴۱۴/۵۷۱ وقتی در JSON همان انگلیسی مانده پر می‌شود."""
    global _cache_exam2
    if _cache_exam2 is not None:
        return _cache_exam2
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'exam2_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            en_to_fa = _build_en_to_fa_option_map()
            en_to_fr = _build_en_to_fr_option_map()
            for q in data:
                opts_en = q.get('options_en') or q.get('options') or []
                if not opts_en:
                    continue
                q['options_en'] = opts_en
                raw_fa = q.get('options_fa') or []
                raw_fr = q.get('options_fr') or []
                merged_fa = []
                merged_fr = []
                for i, en in enumerate(opts_en):
                    en_s = (en or '').strip()
                    cur_fa = (raw_fa[i] if i < len(raw_fa) else '') or ''
                    cur_fa_s = cur_fa.strip()
                    if not cur_fa_s or cur_fa_s.lower() == en_s.lower():
                        merged_fa.append(_fa_lookup(en_to_fa, en))
                    else:
                        merged_fa.append(cur_fa)
                    cur_fr = (raw_fr[i] if i < len(raw_fr) else '') or ''
                    cur_fr_s = cur_fr.strip()
                    if not cur_fr_s or cur_fr_s.lower() == en_s.lower():
                        merged_fr.append(_fr_lookup(en_to_fr, en))
                    else:
                        merged_fr.append(cur_fr)
                q['options_fa'] = merged_fa
                q['options_fr'] = merged_fr
            _cache_exam2 = data
            return _cache_exam2
    except Exception:
        pass
    _cache_exam2 = []
    return _cache_exam2


def _load_exam3_questions():
    """Load Exam3 (Canada's History — set 2) from static JSON. options_fa مثل Exam2 از نگاشت پر می‌شود."""
    global _cache_exam3
    if _cache_exam3 is not None:
        return _cache_exam3
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'exam3_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            en_to_fa = _build_en_to_fa_option_map()
            en_to_fr = _build_en_to_fr_option_map()
            for q in data:
                opts_en = q.get('options_en') or q.get('options') or []
                if not opts_en:
                    continue
                q['options_en'] = opts_en
                raw_fa = q.get('options_fa') or []
                raw_fr = q.get('options_fr') or []
                merged_fa = []
                merged_fr = []
                for i, en in enumerate(opts_en):
                    en_s = (en or '').strip()
                    cur_fa = (raw_fa[i] if i < len(raw_fa) else '') or ''
                    cur_fa_s = cur_fa.strip()
                    if not cur_fa_s or cur_fa_s.lower() == en_s.lower():
                        merged_fa.append(_fa_lookup(en_to_fa, en))
                    else:
                        merged_fa.append(cur_fa)
                    cur_fr = (raw_fr[i] if i < len(raw_fr) else '') or ''
                    cur_fr_s = cur_fr.strip()
                    if not cur_fr_s or cur_fr_s.lower() == en_s.lower():
                        merged_fr.append(_fr_lookup(en_to_fr, en))
                    else:
                        merged_fr.append(cur_fr)
                q['options_fa'] = merged_fa
                q['options_fr'] = merged_fr
            _cache_exam3 = data
            return _cache_exam3
    except Exception:
        pass
    _cache_exam3 = []
    return _cache_exam3


def _load_chapter1_questions():
    """Load Chapter 1 (Rights and Responsibilities) questions once and cache. options_fa from JSON if present, else 571/414 FA map."""
    global _cache_chapter1
    if _cache_chapter1 is not None:
        return _cache_chapter1
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    path = os.path.join(base, 'chapter1_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            en_to_fa = _build_en_to_fa_option_map()
            for q in data:
                q.setdefault('q_fa', q.get('q', ''))
                q.setdefault('q_fr', q.get('q', ''))
                opts = q.get('options', [])
                q.setdefault('options_fr', opts)
                q['options_en'] = opts
                opts_fa = q.get('options_fa')
                if opts_fa and len(opts_fa) == len(opts):
                    q['options_fa'] = opts_fa
                else:
                    q['options_fa'] = [_fa_lookup(en_to_fa, e) for e in opts]
            _cache_chapter1 = data
            return _cache_chapter1
    except Exception:
        pass
    _cache_chapter1 = []
    return _cache_chapter1


def _load_chapter2_questions():
    """Load Chapter 2 (Who We Are) questions once and cache. options_fa from JSON if present, else FA map."""
    global _cache_chapter2
    if _cache_chapter2 is not None:
        return _cache_chapter2
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    path = os.path.join(base, 'chapter2_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            en_to_fa = _build_en_to_fa_option_map()
            for q in data:
                q.setdefault('q_fa', q.get('q', ''))
                q.setdefault('q_fr', q.get('q', ''))
                opts = q.get('options', [])
                q.setdefault('options_fr', opts)
                q['options_en'] = opts
                opts_fa = q.get('options_fa')
                if opts_fa and len(opts_fa) == len(opts):
                    q['options_fa'] = opts_fa
                else:
                    q['options_fa'] = [_fa_lookup(en_to_fa, e) for e in opts]
            _cache_chapter2 = data
            return _cache_chapter2
    except Exception:
        pass
    _cache_chapter2 = []
    return _cache_chapter2


def _load_chapter3_questions():
    """Load Chapter 3 (Canada's History) questions once and cache. options_fa from JSON if present, else FA map."""
    global _cache_chapter3
    if _cache_chapter3 is not None:
        return _cache_chapter3
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    path = os.path.join(base, 'chapter3_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            en_to_fa = _build_en_to_fa_option_map()
            for q in data:
                q.setdefault('q_fa', q.get('q', ''))
                q.setdefault('q_fr', q.get('q', ''))
                opts = q.get('options', [])
                q.setdefault('options_fr', opts)
                q['options_en'] = opts
                opts_fa = q.get('options_fa')
                if opts_fa and len(opts_fa) == len(opts):
                    q['options_fa'] = opts_fa
                else:
                    q['options_fa'] = [_fa_lookup(en_to_fa, e) for e in opts]
            _cache_chapter3 = data
            return _cache_chapter3
    except Exception:
        pass
    _cache_chapter3 = []
    return _cache_chapter3


def _load_chapter4_questions():
    """Load Chapter 4 (Modern Canada) questions once and cache. options_fa from JSON if present, else FA map."""
    global _cache_chapter4
    if _cache_chapter4 is not None:
        return _cache_chapter4
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    path = os.path.join(base, 'chapter4_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            en_to_fa = _build_en_to_fa_option_map()
            for q in data:
                q.setdefault('q_fa', q.get('q', ''))
                q.setdefault('q_fr', q.get('q', ''))
                opts = q.get('options', [])
                q.setdefault('options_fr', opts)
                q['options_en'] = opts
                opts_fa = q.get('options_fa')
                if opts_fa and len(opts_fa) == len(opts):
                    q['options_fa'] = opts_fa
                else:
                    q['options_fa'] = [_fa_lookup(en_to_fa, e) for e in opts]
            _cache_chapter4 = data
            return _cache_chapter4
    except Exception:
        pass
    _cache_chapter4 = []
    return _cache_chapter4


def _federal226_normalize_stem(s):
    """یکسان‌سازی برای تطبیق نزدیک متن فایل ۲۲۶ با کلیدهای بانک (فاصله، علامت، اعداد به‌صورت کلمه)."""
    if not s:
        return ''
    t = s.strip().lower()
    t = re.sub(r'\s+', ' ', t)
    t = t.replace('\u2019', "'").replace('\u2018', "'")
    for word, digit in (
        ('ten', '10'), ('nine', '9'), ('eight', '8'), ('seven', '7'),
        ('six', '6'), ('five', '5'), ('four', '4'), ('three', '3'),
        ('two', '2'), ('one', '1'),
    ):
        t = re.sub(rf'\b{word}\b', digit, t)
    # غلط املایی رایج در برخی نسخه‌های متن ۲۲۶
    t = re.sub(r'\bthe\s+part\s+in\s+power\b', 'the party in power', t)
    t = t.rstrip('?.! :;')
    return t


def _federal226_build_norm_q_map(en_map):
    """ایندکس نرمال‌شدهٔ سؤال → ترجمه (اولین تطبیق برنده است)."""
    out = {}
    if not en_map:
        return out
    for k, v in en_map.items():
        if not k or not v:
            continue
        nk = _federal226_normalize_stem(k)
        if nk and nk not in out:
            out[nk] = v
    return out


def _federal226_lookup_q_fa(en_map, stem, norm_index=None):
    """q_fa را با چند شکل متنی و ایندکس نرمال‌شده روی نگاشت بانک جستجو می‌کند."""
    if not stem:
        return ''
    stem = stem.strip()
    seen = set()
    variants = []

    def add(x):
        x = (x or '').strip()
        if x and x not in seen:
            seen.add(x)
            variants.append(x)

    add(stem)
    add(stem.rstrip('?').rstrip('.').strip())
    three_digit = re.sub(r'\bthree\b', '3', stem, flags=re.IGNORECASE)
    add(three_digit)
    add(three_digit.rstrip('?').rstrip('.').strip())

    for cand in variants:
        res = _fa_lookup(en_map, cand)
        cn = cand.replace('\u2019', "'").replace('\u2018', "'").strip().lower()
        rn = (res or '').replace('\u2019', "'").replace('\u2018', "'").strip().lower()
        if rn and rn != cn:
            return res
    if norm_index:
        tried = set()
        for cand in variants:
            nk = _federal226_normalize_stem(cand)
            if not nk or nk in tried:
                continue
            tried.add(nk)
            res = norm_index.get(nk)
            if not res:
                continue
            cn = cand.replace('\u2019', "'").replace('\u2018', "'").strip().lower()
            rn = res.replace('\u2019', "'").replace('\u2018', "'").strip().lower()
            if rn and rn != cn:
                return res
    return ''


def _federal226_lookup_q_fr(en_map, stem, norm_index=None):
    """مثل q_fa برای متن فرانسوی سؤال."""
    if not stem:
        return ''
    stem = stem.strip()
    seen = set()
    variants = []

    def add(x):
        x = (x or '').strip()
        if x and x not in seen:
            seen.add(x)
            variants.append(x)

    add(stem)
    add(stem.rstrip('?').rstrip('.').strip())
    three_digit = re.sub(r'\bthree\b', '3', stem, flags=re.IGNORECASE)
    add(three_digit)
    add(three_digit.rstrip('?').rstrip('.').strip())

    for cand in variants:
        res = _fr_lookup(en_map, cand)
        cn = cand.replace('\u2019', "'").replace('\u2018', "'").strip().lower()
        rn = (res or '').replace('\u2019', "'").replace('\u2018', "'").strip().lower()
        if rn and rn != cn:
            return res
    if norm_index:
        tried = set()
        for cand in variants:
            nk = _federal226_normalize_stem(cand)
            if not nk or nk in tried:
                continue
            tried.add(nk)
            res = norm_index.get(nk)
            if not res:
                continue
            cn = cand.replace('\u2019', "'").replace('\u2018', "'").strip().lower()
            rn = res.replace('\u2019', "'").replace('\u2018', "'").strip().lower()
            if rn and rn != cn:
                return res
    return ''


def _federal226_fuzzy_match_q_fr(norm_pairs, stem, min_ratio=0.91):
    """تکمیل q_fr برای سؤالات ملی وقتی نگاشت مستقیم نبود."""
    stem_n = _federal226_normalize_stem(stem)
    if not stem_n:
        return ''
    best_v = ''
    best_r = 0.0
    for nk, v in norm_pairs:
        if not nk:
            continue
        r = SequenceMatcher(None, stem_n, nk).ratio()
        if r > best_r:
            best_r = r
            best_v = v
    if best_r >= min_ratio and best_v:
        return best_v
    return ''


_cache_federal226_option_bank_index = None
_cache_federal226_combined_indexes = None
_cache_federal226_fr_opt_fuzzy = None


def _federal226_build_combined_option_indexes():
    """یک‌بار خواندن JSONها؛ سه ایندکس: q_fa از گزینه‌ها، ردیف کامل بانک، جفت‌های EN→FR برای فازی گزینه."""
    global _cache_federal226_combined_indexes, _cache_federal226_option_q_fa_index, _cache_federal226_option_bank_index, _cache_federal226_fr_opt_fuzzy
    if _cache_federal226_combined_indexes is not None:
        return _cache_federal226_combined_indexes
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    by_fa = {}
    by_bank = {}
    fr_rows = []

    def add_item(item):
        if not isinstance(item, dict):
            return
        q_en = (item.get('q') or item.get('q_en') or '').strip()
        q_fa = (item.get('q_fa') or '').strip()
        opts_en = item.get('options_en') or item.get('options') or []
        opts_fr = item.get('options_fr') or []
        if len(opts_en) < 2:
            return
        normed = [_federal226_norm_option_text(x) for x in opts_en]
        if not all(normed):
            return
        fs = frozenset(normed)
        if len(fs) < len(normed):
            return
        if q_fa:
            by_fa.setdefault(fs, []).append((q_en, q_fa))
        if len(opts_fr) == len(opts_en):
            diff_opts = 0
            for a, b in zip(opts_en, opts_fr):
                if (a or '').strip() and (b or '').strip() and (a or '').strip().lower() != (b or '').strip().lower():
                    diff_opts += 1
            if diff_opts > 0:
                q_fr = (item.get('q_fr') or '').strip()
                by_bank.setdefault(fs, []).append({
                    'q_en': q_en,
                    'q_fr': q_fr,
                    'options_fr': list(opts_fr),
                })
            for a, b in zip(opts_en, opts_fr):
                if (a or '').strip().lower() == (b or '').strip().lower():
                    continue
                na = _federal226_norm_option_text(a)
                if na:
                    fr_rows.append((na, b))

    def add_from_list(data):
        if not isinstance(data, list):
            return
        for it in data:
            add_item(it)

    try:
        add_from_list(_load_414_questions())
    except Exception:
        pass
    for fn in (
        'question_bank.json',
        'citizenship_571_questions.json',
        'introduction_questions.json',
        'chapter1_questions.json',
        'chapter2_questions.json',
        'chapter3_questions.json',
        'chapter4_questions.json',
    ):
        path = os.path.join(static_dir, fn)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding='utf-8') as f:
                add_from_list(json.load(f))
        except Exception:
            pass
    for legacy_fn in (
        'citizenship_571_questions.json.bak_before_user_batches_20260327',
        'citizenship_571_questions.json.before_replace_20260327',
    ):
        leg_path = os.path.join(static_dir, legacy_fn)
        if not os.path.isfile(leg_path):
            continue
        try:
            with open(leg_path, encoding='utf-8') as lf:
                add_from_list(json.load(lf))
        except Exception:
            pass
    exact_map = {}
    for na, fr in fr_rows:
        if na and na not in exact_map:
            exact_map[na] = fr
    by_bucket = defaultdict(list)
    for na, fr in exact_map.items():
        by_bucket[len(na) // 28].append((na, fr))
    fuzzy_cached = (exact_map, by_bucket)
    triple = (by_fa, by_bank, fuzzy_cached)
    _cache_federal226_combined_indexes = triple
    _cache_federal226_option_q_fa_index = by_fa
    _cache_federal226_option_bank_index = by_bank
    _cache_federal226_fr_opt_fuzzy = fuzzy_cached
    return triple


def _build_federal226_option_set_bank_index():
    return _federal226_build_combined_option_indexes()[1]


def _federal226_resolve_bank_row(by_fs, fs, stem):
    if not fs or not by_fs:
        return None
    rows = by_fs.get(fs)
    if not rows:
        return None
    if len(rows) == 1:
        return rows[0]
    stem_n = _federal226_normalize_stem(stem)
    best = None
    best_sc = 0.0
    for row in rows:
        sn = _federal226_normalize_stem(row.get('q_en') or '')
        if not stem_n or not sn:
            continue
        sc = SequenceMatcher(None, stem_n, sn).ratio()
        if sc > best_sc:
            best_sc = sc
            best = row
    if best_sc >= 0.5 and best:
        return best
    return rows[0]


def _federal226_provincial_template_fr(stem):
    """سؤالات استانی: متن فرانسوی الگویی (مثل فارسی)."""
    if not stem:
        return ''
    s = stem.strip().replace('\u2019', "'").replace('\u2018', "'")
    s = re.sub(r'\s+', ' ', s)
    s = s.rstrip(' \t?.!:;')

    def _p(m):
        t = (m.group(1) or '').strip().rstrip('.')
        if t.lower().startswith('the '):
            t = t[4:].strip()
        return t

    rules = (
        (r'(?is)^What is the capital city of (?:the )?(.+)$', lambda m: f'Quelle est la capitale de {_p(m)} ?'),
        (r'(?is)^What is the name of the leader of the Opposition in (.+)$', lambda m: f'Quel est le nom du chef de l’opposition en {_p(m)} ?'),
        (r'(?is)^What is the name of the Lieutenant-Governor of (.+)$', lambda m: f'Quel est le nom du lieutenant-gouverneur de {_p(m)} ?'),
        (r'(?is)^What is the name of the Premier of (.+)$', lambda m: f'Quel est le nom du premier ministre de {_p(m)} ?'),
        (r'(?is)^What is the name of the Commissioner of (.+)$', lambda m: f'Quel est le nom du commissaire de {_p(m)} ?'),
        (r'(?is)^Which political party is in power in (.+)$', lambda m: f'Quel parti politique est au pouvoir en {_p(m)} ?'),
        (r'(?is)^What three industries are important to (.+)\'s economy today$', lambda m: f'Quelles sont les trois industries importantes pour l’économie de {_p(m)} aujourd’hui ?'),
        (r'(?is)^Which three natural resources are important to (.+)\'s economy today$', lambda m: f'Quelles sont les trois ressources naturelles importantes pour l’économie de {_p(m)} aujourd’hui ?'),
        (r'(?is)^What is the name of the Mayor of Richmond, British Columbia$', lambda m: 'Quel est le nom du maire de Richmond (Colombie-Britannique) ?'),
        (r'(?is)^Name the federal electoral districts in Richmond, British Columbia$', lambda m: 'Nommez les circonscriptions électorales fédérales de Richmond (C.-B.).'),
        (r'(?is)^Name the members of Parliament for Richmond, British Columbia and the parties they belong to .+$', lambda m: 'Nommez les députés fédéraux de Richmond et les partis auxquels ils appartiennent.'),
        (r'(?is)^Name the Members of the Legislative Assembly for Richmond, British Columbia and the parties they belong to .+$', lambda m: 'Nommez les députés à l’Assemblée législative de Richmond et les partis auxquels ils appartiennent.'),
        (r'(?is)^Name three city councillors for Richmond, British Columbia$', lambda m: 'Nommez trois conseillers municipaux de Richmond (C.-B.).'),
        (r'(?is)^Why is British Columbia known as Canada\'s Pacific Gateway$', lambda m: 'Pourquoi la Colombie-Britannique est-elle connue comme la porte du Pacifique du Canada ?'),
        (r'(?is)^Why is British Columbia known as Canadas Pacific Gateway$', lambda m: 'Pourquoi la Colombie-Britannique est-elle connue comme la porte du Pacifique du Canada ?'),
    )
    for pat, fmt in rules:
        m = re.match(pat, s)
        if m:
            try:
                return fmt(m)
            except Exception:
                continue
    return ''


def _build_federal226_fr_option_fuzzy_list():
    return _federal226_build_combined_option_indexes()[2]


def _federal226_fuzzy_fr_option(cached, oen, min_ratio=0.86):
    exact_map, by_bucket = cached
    on = _federal226_norm_option_text(oen)
    if not on or len(on) < 18:
        return ''
    if on in exact_map:
        return exact_map[on]
    bi = len(on) // 28
    cand = []
    for k in (bi - 1, bi, bi + 1):
        cand.extend(by_bucket.get(k, ()))
    best_fr = ''
    best_r = 0.0
    for na, fr in cand:
        r = SequenceMatcher(None, on, na).ratio()
        if r > best_r:
            best_r = r
            best_fr = fr
    return best_fr if best_r >= min_ratio else ''


def _federal226_q_fa_patch_lookup(patch, stem, patch_norm=None):
    """ترجمهٔ دستی از static/federal_questions_226_q_fa_patch.json (کلید = متن دقیق سؤال در فایل ۲۲۶)."""
    if not stem or not patch:
        return ''
    s = stem.strip()
    if s in patch:
        return patch[s]
    t = s.rstrip('?').rstrip('.').strip()
    if t in patch:
        return patch[t]
    td = re.sub(r'\bthree\b', '3', s, flags=re.IGNORECASE)
    if td in patch:
        return patch[td]
    td = td.rstrip('?').rstrip('.').strip()
    if td in patch:
        return patch[td]
    if patch_norm:
        nn = _federal226_normalize_stem(s)
        if nn in patch_norm:
            return patch_norm[nn]
    return ''


_cache_federal226_option_q_fa_index = None


def _federal226_norm_option_text(o):
    """متن گزینه را برای امضای مجموعهٔ گزینه‌ها نرمال می‌کند."""
    if not o:
        return ''
    t = str(o).strip().lower()
    t = re.sub(r'\s*\(\s*correct answer\s*\)\s*', '', t, flags=re.IGNORECASE).strip()
    t = re.sub(r'\s+', ' ', t)
    t = t.replace('\u2019', "'").replace('\u2018', "'")
    t = t.rstrip('.!? ')
    return t


def _build_federal226_option_set_q_fa_index():
    return _federal226_build_combined_option_indexes()[0]


def _federal226_resolve_q_fa_by_options(by_fs, fs, stem):
    if not fs or not by_fs:
        return ''
    cands = by_fs.get(fs)
    if not cands:
        return ''
    if len(cands) == 1:
        return cands[0][1]
    stem_n = _federal226_normalize_stem(stem)
    best_fa = ''
    best_sc = 0.0
    for q_en, q_fa in cands:
        sn = _federal226_normalize_stem(q_en)
        if not stem_n or not sn:
            continue
        sc = SequenceMatcher(None, stem_n, sn).ratio()
        if sc > best_sc:
            best_sc = sc
            best_fa = q_fa
    if best_sc >= 0.5 and best_fa:
        return best_fa
    return ''


def _federal226_unique_norm_fa_pairs(en_map):
    """یک (نرمال‌شده، q_fa) به ازای هر شکل انگلیسی یکتا برای تطبیق فازی."""
    by_nk = {}
    for k, v in en_map.items():
        if not k or not v:
            continue
        nk = _federal226_normalize_stem(k)
        if nk and nk not in by_nk:
            by_nk[nk] = v
    return list(by_nk.items())


def _federal226_fuzzy_match_q_fa(norm_pairs, stem, min_ratio=0.91):
    """آخرین تلاش برای سؤالات ملی وقتی متن یا گزینه با بانک اختلاف جزئی دارد."""
    stem_n = _federal226_normalize_stem(stem)
    if not stem_n:
        return ''
    best_v = ''
    best_r = 0.0
    for nk, v in norm_pairs:
        if not nk:
            continue
        r = SequenceMatcher(None, stem_n, nk).ratio()
        if r > best_r:
            best_r = r
            best_v = v
    if best_r >= min_ratio and best_v:
        return best_v
    return ''


def _federal226_provincial_template_fa(stem):
    """برای سؤالات استانی (معمولاً خارج بانک ملی) ترجمهٔ الگویی قابل‌فهم."""
    if not stem:
        return ''
    s = stem.strip().replace('\u2019', "'").replace('\u2018', "'")
    s = re.sub(r'\s+', ' ', s)
    s = s.rstrip(' \t?.!:;')

    def _p(m):
        t = (m.group(1) or '').strip().rstrip('.')
        if t.lower().startswith('the '):
            t = t[4:].strip()
        return t

    rules = (
        (
            r'(?is)^What is the capital city of (?:the )?(.+)$',
            lambda m: f'پایتخت {_p(m)} کدام شهر است؟',
        ),
        (
            r'(?is)^What is the name of the leader of the Opposition in (.+)$',
            lambda m: f'نام رهبر اپوزسیون در {_p(m)} چیست؟',
        ),
        (
            r'(?is)^What is the name of the Lieutenant-Governor of (.+)$',
            lambda m: f'نام فرماندار کل {_p(m)} چیست؟',
        ),
        (
            r'(?is)^What is the name of the Premier of (.+)$',
            lambda m: f'نام نخست‌وزیر {_p(m)} چیست؟',
        ),
        (
            r'(?is)^What is the name of the Commissioner of (.+)$',
            lambda m: f'نام کمیسیونر {_p(m)} چیست؟',
        ),
        (
            r'(?is)^Which political party is in power in (.+)$',
            lambda m: f'کدام حزب در {_p(m)} در قدرت است؟',
        ),
        (
            r'(?is)^What three industries are important to (.+)\'s economy today$',
            lambda m: f'سه صنعت مهم در اقتصاد امروز {_p(m)} کدامند؟',
        ),
        (
            r'(?is)^Which three natural resources are important to (.+)\'s economy today$',
            lambda m: f'سه منبع طبیعی مهم در اقتصاد امروز {_p(m)} کدامند؟',
        ),
        (
            r'(?is)^What is the name of the Mayor of Richmond, British Columbia$',
            lambda m: 'نام شهردار ریچموند در بریتیش کلمبیا چیست؟',
        ),
        (
            r'(?is)^Name the federal electoral districts in Richmond, British Columbia$',
            lambda m: 'نام حوزه‌های انتخابیاتی فدرال ریچموند در بریتیش کلمبیا را بگویید.',
        ),
        (
            r'(?is)^Name the members of Parliament for Richmond, British Columbia and the parties they belong to .+$',
            lambda m: 'نام نمایندگان پارلمان فدرال ریچموند و احزابشان چیست؟',
        ),
        (
            r'(?is)^Name the Members of the Legislative Assembly for Richmond, British Columbia and the parties they belong to .+$',
            lambda m: 'نام نمایندگان مجلس قانونگذاری ریچموند و احزابشان چیست؟',
        ),
        (
            r'(?is)^Name three city councillors for Richmond, British Columbia$',
            lambda m: 'نام سه عضو شورای شهر ریچموند در بریتیش کلمبیا را بگویید.',
        ),
        (
            r'(?is)^Why is British Columbia known as Canada\'s Pacific Gateway$',
            lambda m: 'چرا بریتیش کلمبیا به‌عنوان دروازهٔ اقیانوس آرام کانادا شناخته می‌شود؟',
        ),
        (
            r'(?is)^Why is British Columbia known as Canadas Pacific Gateway$',
            lambda m: 'چرا بریتیش کلمبیا به‌عنوان دروازهٔ اقیانوس آرام کانادا شناخته می‌شود؟',
        ),
    )
    for pat, fmt in rules:
        m = re.match(pat, s)
        if m:
            try:
                return fmt(m)
            except Exception:
                continue
    return ''


def _load_federal_questions_226():
    """Load the 226 Federal Questions from a plain-text file and cache.

    File format: numbered questions + indented options; correct option contains '(correct answer)'.
    Returns: list[{ "num", "q", "q_fa", "q_fr", "options_en", "options_fr", "correct" }]
    """
    global _cache_federal_questions_226
    if _cache_federal_questions_226 is not None:
        return _cache_federal_questions_226

    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    path = os.path.join(base, 'federal_questions_226.txt')

    try:
        if not os.path.isfile(path):
            _cache_federal_questions_226 = []
            return _cache_federal_questions_226

        with open(path, 'r', encoding='utf-8') as f:
            raw_lines = [ln.rstrip('\n') for ln in f]

        questions = []
        cur = None

        def _flush():
            nonlocal cur
            if not cur:
                return
            # Only keep questions that have at least 2 options.
            if cur.get('q') and len(cur.get('options', [])) >= 2:
                if cur.get('correct') is None:
                    cur['correct'] = -1
                # Normalize to the same shape as other chapter templates.
                cur['q_fa'] = cur.get('q_fa') or ''
                cur['q_fr'] = cur.get('q_fr') or cur.get('q') or ''
                cur['options_en'] = list(cur.get('options', []))
                cur['options_fr'] = list(cur.get('options_fr') or cur.get('options', []))
                questions.append(cur)
            cur = None

        for ln in raw_lines:
            s = ln.strip()
            if not s:
                continue

            # Ignore title line
            if s.lower() == "226 federal questions":
                continue

            # New question line: "123. Question text"
            m = re.match(r'^(\d{1,3})\.\s+(.*)$', s)
            if m:
                _flush()
                cur = {
                    'num': int(m.group(1)),
                    'q': m.group(2).strip(),
                    'options': [],
                    'correct': None,
                }
                continue

            # Skip section headers like "Provincial Questions"
            if re.match(r'^(provincial questions)\s*$', s, flags=re.IGNORECASE):
                continue

            # Options are lines that are not question headers. Treat as option text.
            if cur is None:
                continue

            opt = s
            is_correct = False
            if '(correct answer)' in opt.lower():
                # Remove marker (case-insensitive)
                opt = re.sub(r'\s*\(\s*correct answer\s*\)\s*', '', opt, flags=re.IGNORECASE).strip()
                is_correct = True

            cur['options'].append(opt)
            if is_correct:
                cur['correct'] = len(cur['options']) - 1

        _flush()
        en_to_fa_q = _build_en_to_fa_question_map()
        en_to_fr_q = _build_en_to_fr_question_map()
        en_to_fr_opt = _build_en_to_fr_option_map()
        q_fa_patch = {}
        patch_path = os.path.join(base, 'federal_questions_226_q_fa_patch.json')
        try:
            if os.path.isfile(patch_path):
                with open(patch_path, 'r', encoding='utf-8') as pf:
                    raw_patch = json.load(pf)
                if isinstance(raw_patch, dict):
                    for pk, pv in raw_patch.items():
                        if pk and pv and isinstance(pk, str) and isinstance(pv, str) and not pk.strip().startswith('_'):
                            q_fa_patch[pk.strip()] = pv.strip()
        except Exception:
            pass
        norm_q_fa = _federal226_build_norm_q_map(en_to_fa_q)
        norm_q_fr = _federal226_build_norm_q_map(en_to_fr_q)
        patch_norm = {}
        for pk, pv in q_fa_patch.items():
            nn = _federal226_normalize_stem(pk)
            if nn and nn not in patch_norm:
                patch_norm[nn] = pv
        for q in questions:
            stem = (q.get('q') or '').strip()
            q_fa = _federal226_q_fa_patch_lookup(q_fa_patch, stem, patch_norm) if stem else ''
            if not q_fa:
                q_fa = _federal226_lookup_q_fa(en_to_fa_q, stem, norm_q_fa)
            # اگر ترجمه‌ای در بانک نباشد، lookup همان انگلیسی را برمی‌گرداند؛ در بلوک RTL خراب دیده می‌شود.
            stem_n = stem.replace('\u2019', "'").replace('\u2018', "'")
            fa_n = (q_fa or '').replace('\u2019', "'").replace('\u2018', "'")
            if stem and fa_n.strip().lower() == stem_n.strip().lower():
                q['q_fa'] = ''
            else:
                q['q_fa'] = q_fa
            q['q_fr'] = _federal226_lookup_q_fr(en_to_fr_q, stem, norm_q_fr)
            opts_en = q.get('options_en') or []
            q['options_fr'] = [_fr_lookup(en_to_fr_opt, o) for o in opts_en]
        # نکتهٔ عملکرد: ساخت ایندکس‌های سنگین/تطبیق فازی گزینه‌ها برای این صفحه باعث کندی شدید و تایم‌اوت می‌شود.
        # برای باز شدن سریع صفحه، فقط از نگاشت‌های مستقیم سؤال/گزینه استفاده می‌کنیم؛ موارد خاص را با patch تکمیل می‌کنیم.
        # سؤالات استانی (از شمارهٔ ۱۴۷) معمولاً در بانک ملی q_fa ندارند؛ تطبیق فازی فقط برای ملی تا اشتباه بین استان‌ها نشود.
        norm_pairs = _federal226_unique_norm_fa_pairs(en_to_fa_q)
        for q in questions:
            if (q.get('q_fa') or '').strip():
                continue
            n = q.get('num') or 0
            if n >= 147:
                continue
            stem = (q.get('q') or '').strip()
            q_fa = _federal226_fuzzy_match_q_fa(norm_pairs, stem, 0.91)
            if not q_fa:
                continue
            stem_n = stem.replace('\u2019', "'").replace('\u2018', "'")
            fa_n = (q_fa or '').replace('\u2019', "'").replace('\u2018', "'")
            if stem and fa_n.strip().lower() == stem_n.strip().lower():
                continue
            q['q_fa'] = q_fa
        for q in questions:
            if (q.get('q_fa') or '').strip():
                continue
            if (q.get('num') or 0) < 147:
                continue
            stem = (q.get('q') or '').strip()
            q_fa = _federal226_provincial_template_fa(stem)
            if q_fa:
                q['q_fa'] = q_fa
        # --- فرانسوی: الگوی استانی + پر کردن گزینه با نگاشت مستقیم ---
        for q in questions:
            if (q.get('num') or 0) < 147:
                continue
            stem = (q.get('q') or '').strip()
            qfr = (q.get('q_fr') or '').strip()
            if qfr and qfr.lower() != stem.lower():
                continue
            hit = _federal226_provincial_template_fr(stem)
            if hit:
                q['q_fr'] = hit
        for q in questions:
            opts_en = q.get('options_en') or []
            if not opts_en:
                continue
            ofr = list(q.get('options_fr') or [])
            if len(ofr) < len(opts_en):
                ofr = ofr + [opts_en[i] for i in range(len(ofr), len(opts_en))]
            ofr = ofr[: len(opts_en)]
            for i, oen in enumerate(opts_en):
                oen_s = (oen or '').strip()
                cur = (ofr[i] if i < len(ofr) else '') or ''
                if oen_s and cur.strip().lower() == oen_s.lower():
                    alt = _fr_lookup(en_to_fr_opt, oen)
                    if alt.strip().lower() != oen_s.lower():
                        ofr[i] = alt
            q['options_fr'] = ofr
        _cache_federal_questions_226 = questions
        return _cache_federal_questions_226
    except Exception:
        _cache_federal_questions_226 = []
        return _cache_federal_questions_226


def _load_govern_questions():
    """Load How Canadians Govern Themselves questions (Discover Canada); same shape as Introduction JSON."""
    global _cache_govern
    if _cache_govern is not None:
        return _cache_govern
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    path = os.path.join(base, 'govern_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            en_to_fa = _build_en_to_fa_option_map()
            for q in data:
                q.setdefault('q_fa', q.get('q', ''))
                q.setdefault('q_fr', q.get('q', ''))
                opts = q.get('options', [])
                q.setdefault('options_fr', opts)
                q['options_en'] = opts
                opts_fa = q.get('options_fa')
                if opts_fa and len(opts_fa) == len(opts):
                    q['options_fa'] = opts_fa
                else:
                    q['options_fa'] = [_fa_lookup(en_to_fa, e) for e in opts]
            _cache_govern = data
            return _cache_govern
    except Exception:
        pass
    _cache_govern = []
    return _cache_govern


def _load_federal_elections_questions():
    """Load Chapter 6 / Federal Elections questions (same shape as govern JSON)."""
    global _cache_federal_elections
    if _cache_federal_elections is not None:
        return _cache_federal_elections
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    path = os.path.join(base, 'federal_elections_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            en_to_fa = _build_en_to_fa_option_map()
            for q in data:
                q.setdefault('q_fa', q.get('q', ''))
                q.setdefault('q_fr', q.get('q', ''))
                opts = q.get('options', [])
                q.setdefault('options_fr', opts)
                q['options_en'] = opts
                opts_fa = q.get('options_fa')
                if opts_fa and len(opts_fa) == len(opts):
                    q['options_fa'] = opts_fa
                else:
                    q['options_fa'] = [_fa_lookup(en_to_fa, e) for e in opts]
            _cache_federal_elections = data
            return _cache_federal_elections
    except Exception:
        pass
    _cache_federal_elections = []
    return _cache_federal_elections


def _load_justice_questions():
    """Load Chapter 7 / The Justice System questions (same shape as govern JSON)."""
    global _cache_justice
    if _cache_justice is not None:
        return _cache_justice
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    path = os.path.join(base, 'justice_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            en_to_fa = _build_en_to_fa_option_map()
            for q in data:
                q.setdefault('q_fa', q.get('q', ''))
                q.setdefault('q_fr', q.get('q', ''))
                opts = q.get('options', [])
                q.setdefault('options_fr', opts)
                q['options_en'] = opts
                opts_fa = q.get('options_fa')
                if opts_fa and len(opts_fa) == len(opts):
                    q['options_fa'] = opts_fa
                else:
                    q['options_fa'] = [_fa_lookup(en_to_fa, e) for e in opts]
            _cache_justice = data
            return _cache_justice
    except Exception:
        pass
    _cache_justice = []
    return _cache_justice


def _load_canadian_symbols_questions():
    """Load Chapter 8 / Canadian Symbols questions (same shape as govern JSON)."""
    global _cache_canadian_symbols
    if _cache_canadian_symbols is not None:
        return _cache_canadian_symbols
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    path = os.path.join(base, 'canadian_symbols_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            en_to_fa = _build_en_to_fa_option_map()
            for q in data:
                q.setdefault('q_fa', q.get('q', ''))
                q.setdefault('q_fr', q.get('q', ''))
                opts = q.get('options', [])
                q.setdefault('options_fr', opts)
                q['options_en'] = opts
                opts_fa = q.get('options_fa')
                if opts_fa and len(opts_fa) == len(opts):
                    q['options_fa'] = opts_fa
                else:
                    q['options_fa'] = [_fa_lookup(en_to_fa, e) for e in opts]
            _cache_canadian_symbols = data
            return _cache_canadian_symbols
    except Exception:
        pass
    _cache_canadian_symbols = []
    return _cache_canadian_symbols


def _load_canada_economy_questions():
    """Load Chapter 9 / Canada's Economy questions (same shape as Canadian Symbols JSON)."""
    global _cache_canada_economy
    if _cache_canada_economy is not None:
        return _cache_canada_economy
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    path = os.path.join(base, 'chapter9_canada_economy_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            en_to_fa = _build_en_to_fa_option_map()
            for q in data:
                q.setdefault('q_fa', q.get('q', ''))
                q.setdefault('q_fr', q.get('q', ''))
                opts = q.get('options', [])
                q.setdefault('options_fr', opts)
                q['options_en'] = opts
                opts_fa = q.get('options_fa')
                if opts_fa and len(opts_fa) == len(opts):
                    q['options_fa'] = opts_fa
                else:
                    q['options_fa'] = [_fa_lookup(en_to_fa, e) for e in opts]
            _cache_canada_economy = data
            return _cache_canada_economy
    except Exception:
        pass
    _cache_canada_economy = []
    return _cache_canada_economy


def _load_canada_regions_questions():
    """Load Chapter 10 / Canada's Regions questions (same shape as Economy JSON)."""
    global _cache_canada_regions
    if _cache_canada_regions is not None:
        return _cache_canada_regions
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    path = os.path.join(base, 'chapter10_canada_regions_questions.json')
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            en_to_fa = _build_en_to_fa_option_map()
            for q in data:
                q.setdefault('q_fa', q.get('q', ''))
                q.setdefault('q_fr', q.get('q', ''))
                opts = q.get('options', [])
                q.setdefault('options_fr', opts)
                q['options_en'] = opts
                opts_fa = q.get('options_fa')
                if opts_fa and len(opts_fa) == len(opts):
                    q['options_fa'] = opts_fa
                else:
                    q['options_fa'] = [_fa_lookup(en_to_fa, e) for e in opts]
            _cache_canada_regions = data
            return _cache_canada_regions
    except Exception:
        pass
    _cache_canada_regions = []
    return _cache_canada_regions


@app.route('/citizenship-571')
def citizenship_571():
    """۵۷۱ سوال — ۲۱ سوال اول رایگان؛ ادامه با اشتراک (همان سشن ۴۱۴)."""
    log_visitor('/citizenship-571')
    all_questions = _load_571_questions()
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    if has_access:
        questions = all_questions
        show_paywall = False
        max_question_571 = len(all_questions)
    else:
        if len(all_questions) <= 21:
            questions = all_questions
            show_paywall = False
            max_question_571 = len(all_questions)
        else:
            questions = all_questions[:21]
            show_paywall = True
            max_question_571 = 22
    resp = app.make_response(render_template(
        'citizenship_571.html',
        questions=questions,
        show_paywall=show_paywall,
        max_question_571=max_question_571,
        citizenship_571_total=len(all_questions),
    ))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/citizenship-how-canadians-govern-themselves')
def citizenship_how_canadians_govern_themselves():
    """How Canadians Govern Themselves — سه سوال اول رایگان؛ از چهارم با اشتراک ۴۱۴."""
    log_visitor('/citizenship-how-canadians-govern-themselves')
    all_govern = _load_govern_questions()
    n = len(all_govern)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    if has_access:
        govern_questions = all_govern
        show_paywall_govern = False
        max_visible_govern = n
    elif n <= 3:
        govern_questions = all_govern
        show_paywall_govern = False
        max_visible_govern = n
    else:
        govern_questions = all_govern[:3]
        show_paywall_govern = True
        max_visible_govern = 4
    return render_template(
        'citizenship_how_canadians_govern_themselves.html',
        govern_questions=govern_questions,
        max_question_govern=n,
        max_visible_govern=max_visible_govern,
        show_paywall_govern=show_paywall_govern,
        exam_section_views=_count_exam_section_visits(),
    )


@app.route('/citizenship-federal-elections')
def citizenship_federal_elections():
    """Federal Elections (Chapter 6) — پنج سوال اول رایگان؛ از ششم با اشتراک ۴۱۴."""
    log_visitor('/citizenship-federal-elections')
    all_fe = _load_federal_elections_questions()
    n_fe = len(all_fe)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    if has_access:
        fe_questions = all_fe
        show_paywall_fe = False
        max_visible_fe = n_fe
    elif n_fe <= 5:
        fe_questions = all_fe
        show_paywall_fe = False
        max_visible_fe = n_fe
    else:
        fe_questions = all_fe[:5]
        show_paywall_fe = True
        max_visible_fe = 6
    return render_template(
        'citizenship_federal_elections.html',
        fe_questions=fe_questions,
        max_question_fe=n_fe,
        max_visible_fe=max_visible_fe,
        show_paywall_fe=show_paywall_fe,
        exam_section_views=_count_exam_section_visits(),
    )


@app.route('/citizenship-canadian-symbols')
def citizenship_canadian_symbols():
    """Canadian Symbols (Chapter 8) — پنج سوال اول رایگان؛ از ششم با اشتراک ۴۱۴."""
    log_visitor('/citizenship-canadian-symbols')
    all_sym = _load_canadian_symbols_questions()
    n_sym = len(all_sym)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    if has_access:
        sym_questions = all_sym
        show_paywall_sym = False
        max_visible_sym = n_sym
    elif n_sym <= 5:
        sym_questions = all_sym
        show_paywall_sym = False
        max_visible_sym = n_sym
    else:
        sym_questions = all_sym[:5]
        show_paywall_sym = True
        max_visible_sym = 6
    return render_template(
        'citizenship_canadian_symbols.html',
        sym_questions=sym_questions,
        max_question_sym=n_sym,
        max_visible_sym=max_visible_sym,
        show_paywall_sym=show_paywall_sym,
        exam_section_views=_count_exam_section_visits(),
    )


@app.route('/citizenship-categorized-tests')
def citizenship_categorized_tests():
    """URL قدیمی: هدایت به فهرست آزمون‌ها یا صفحات جدا (با هش در مرورگر)."""
    log_visitor('/citizenship-categorized-tests')
    resp = app.make_response(render_template('citizenship_categorized_tests.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    # تقویت canonical برای GSC (همراه با <link rel="canonical"> در قالب)
    base = _seo_base_url().rstrip('/')
    resp.headers['Link'] = f'<{base}/citizenship-exams>; rel="canonical"'
    return resp


@app.route('/citizenship-introduction')
def citizenship_introduction():
    """صفحه Introduction — سوالات ۱–۳ رایگان؛ از ۴ به بعد با اشتراک (همان ۴۱۴)."""
    log_visitor('/citizenship-introduction')
    all_questions = _load_introduction_questions()
    n = len(all_questions)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    if has_access:
        questions = all_questions
        show_paywall = False
        max_visible_intro = n
    else:
        questions = all_questions[:3] if n >= 3 else all_questions
        show_paywall = True
        max_visible_intro = 4
    return render_template(
        'citizenship_introduction.html',
        questions=questions,
        max_question_intro=n,
        max_visible_intro=max_visible_intro,
        show_paywall=show_paywall,
        exam_section_views=_count_exam_section_visits(),
    )


@app.route('/citizenship-exams')
def citizenship_exams():
    """فهرست آزمون‌های نمونه (Introduction، Rights، Justice، Exam1، Exam2، Exam3، …)."""
    log_visitor('/citizenship-exams')
    return render_template(
        'citizenship_exams.html',
        exam_section_views=_count_exam_section_visits(),
    )


@app.route('/citizenship-exam-report')
def citizenship_exam_report():
    """صفحهٔ فهرست قبولی از تاریخ ۲۵ ژانویه ۲۰۲۶؛ فیلتر تاریخ امتحان + نمره در _get_citizenship_exam_report_rows."""
    log_visitor('/citizenship-exam-report')
    resp = app.make_response(
        render_template(
            'citizenship_exam_report.html',
            report_rows=_get_citizenship_exam_report_rows(),
            waiting_rows=_get_citizenship_exam_waiting_rows(),
        )
    )
    resp.headers['Cache-Control'] = 'public, max-age=120'
    return resp


@app.route('/exam1')
def exam1():
    """Exam1 — Rights and Responsibilities (doc-based MCQ). سوالات ۱ تا ۵ رایگان؛ از ۶ به بعد با اشتراک بستهٔ ۴۱۴."""
    log_visitor('/exam1')
    all_questions = _load_exam1_questions()
    n = len(all_questions)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    free_n = 5
    if has_access:
        questions = all_questions
        show_paywall = False
        max_visible = n
    else:
        questions = all_questions[:free_n] if n >= free_n else all_questions
        show_paywall = n > free_n
        max_visible = free_n + (1 if show_paywall else 0)
    resp = app.make_response(render_template(
        'exam1.html',
        questions=questions,
        max_question_exam1=n,
        max_visible_exam1=max_visible,
        show_paywall=show_paywall,
        free_count=free_n,
        exam_section_views=_count_exam_section_visits(),
    ))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/exam2')
def exam2():
    """Exam2 — History of Canada (doc-based MCQ). سوالات ۱ تا ۵ رایگان؛ از ۶ به بعد با اشتراک بستهٔ ۴۱۴."""
    log_visitor('/exam2')
    all_questions = _load_exam2_questions()
    n = len(all_questions)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    free_n = 5
    if has_access:
        questions = all_questions
        show_paywall = False
        max_visible = n
    else:
        questions = all_questions[:free_n] if n >= free_n else all_questions
        show_paywall = n > free_n
        max_visible = free_n + (1 if show_paywall else 0)
    resp = app.make_response(render_template(
        'exam2.html',
        questions=questions,
        max_question_exam2=n,
        max_visible_exam2=max_visible,
        show_paywall=show_paywall,
        free_count=free_n,
        exam_section_views=_count_exam_section_visits(),
    ))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/exam3')
def exam3():
    """Exam3 — Canada's History (set 2, doc-based MCQ). سوالات ۱ تا ۵ رایگان؛ از ۶ به بعد با اشتراک بستهٔ ۴۱۴."""
    log_visitor('/exam3')
    all_questions = _load_exam3_questions()
    n = len(all_questions)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    free_n = 5
    if has_access:
        questions = all_questions
        show_paywall = False
        max_visible = n
    else:
        questions = all_questions[:free_n] if n >= free_n else all_questions
        show_paywall = n > free_n
        max_visible = free_n + (1 if show_paywall else 0)
    resp = app.make_response(render_template(
        'exam3.html',
        questions=questions,
        max_question_exam3=n,
        max_visible_exam3=max_visible,
        show_paywall=show_paywall,
        free_count=free_n,
        exam_section_views=_count_exam_section_visits(),
    ))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/citizenship-rights-responsibilities')
def citizenship_rights_responsibilities():
    """صفحه Rights and Responsibilities of Citizenship (Chapter 1) — سوالات ۱–۲ رایگان؛ از ۳ به بعد با اشتراک. No print / No select."""
    log_visitor('/citizenship-rights-responsibilities')
    all_questions = _load_chapter1_questions()
    n = len(all_questions)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    if has_access:
        questions = all_questions
        show_paywall = False
        max_visible_ch1 = n
    else:
        questions = all_questions[:2] if n >= 2 else all_questions
        show_paywall = True
        max_visible_ch1 = 3
    return render_template(
        'citizenship_rights_responsibilities.html',
        questions=questions,
        max_question_ch1=n,
        max_visible_ch1=max_visible_ch1,
        show_paywall=show_paywall,
        exam_section_views=_count_exam_section_visits(),
    )


@app.route('/citizenship-justice-system')
def citizenship_justice_system():
    """The Justice System (Chapter 7) — پنج سوال اول رایگان؛ بقیه با اشتراک ۴۱۴."""
    log_visitor('/citizenship-justice-system')
    all_questions = _load_justice_questions()
    n = len(all_questions)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    if has_access:
        questions = all_questions
        show_paywall = False
        max_visible_justice = n
    elif n <= 5:
        questions = all_questions
        show_paywall = False
        max_visible_justice = n
    else:
        questions = all_questions[:5]
        show_paywall = True
        max_visible_justice = 6
    resp = app.make_response(
        render_template(
            'citizenship_justice_system.html',
            questions=questions,
            max_question_justice=n,
            max_visible_justice=max_visible_justice,
            show_paywall=show_paywall,
            exam_section_views=_count_exam_section_visits(),
        )
    )
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/citizenship-who-we-are')
def citizenship_who_we_are():
    """صفحه Who We Are (Chapter 2) — سوالات ۱–۲ رایگان؛ از ۳ به بعد با اشتراک. No print / No select."""
    log_visitor('/citizenship-who-we-are')
    all_questions = _load_chapter2_questions()
    n = len(all_questions)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    if has_access:
        questions = all_questions
        show_paywall = False
        max_visible_ch2 = n
    else:
        questions = all_questions[:2] if n >= 2 else all_questions
        show_paywall = True
        max_visible_ch2 = 3
    return render_template(
        'citizenship_who_we_are.html',
        questions=questions,
        max_question_ch2=n,
        max_visible_ch2=max_visible_ch2,
        show_paywall=show_paywall,
        exam_section_views=_count_exam_section_visits(),
    )


@app.route('/citizenship-canadas-history')
def citizenship_canadas_history():
    """صفحه Canada's History (Chapter 3) — پنج سوال اول رایگان؛ از ششم با اشتراک ۴۱۴."""
    log_visitor('/citizenship-canadas-history')
    all_questions = _load_chapter3_questions()
    n = len(all_questions)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    if has_access:
        questions = all_questions
        show_paywall = False
        max_visible_ch3 = n
    elif n <= 5:
        questions = all_questions
        show_paywall = False
        max_visible_ch3 = n
    else:
        questions = all_questions[:5]
        show_paywall = True
        max_visible_ch3 = 6
    return render_template(
        'citizenship_canadas_history.html',
        questions=questions,
        max_question_ch3=n,
        max_visible_ch3=max_visible_ch3,
        show_paywall=show_paywall,
        exam_section_views=_count_exam_section_visits(),
    )


@app.route('/citizenship-modern-canada')
def citizenship_modern_canada():
    """صفحه Modern Canada (Chapter 4) — سوالات ۱–۲ رایگان؛ از ۳ به بعد با اشتراک. No print / No select."""
    log_visitor('/citizenship-modern-canada')
    all_questions = _load_chapter4_questions()
    n = len(all_questions)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    if has_access:
        questions = all_questions
        show_paywall = False
        max_visible_ch4 = n
    else:
        questions = all_questions[:2] if n >= 2 else all_questions
        show_paywall = True
        max_visible_ch4 = 3
    return render_template(
        'citizenship_modern_canada.html',
        questions=questions,
        max_question_ch4=n,
        max_visible_ch4=max_visible_ch4,
        show_paywall=show_paywall,
        exam_section_views=_count_exam_section_visits(),
    )


@app.route('/federal-questions-226')
def federal_questions_226():
    """A single page that lists the 226 Federal Questions."""
    log_visitor('/federal-questions-226')
    questions = _load_federal_questions_226()
    return render_template(
        'federal_questions_226.html',
        questions=questions,
        total=len(questions),
        exam_section_views=_count_exam_section_visits(),
    )


@app.route('/citizenship-canadas-economy')
def citizenship_canadas_economy():
    """Canada's Economy (Chapter 9) — پنج سوال اول رایگان؛ از ششم با اشتراک ۴۱۴."""
    log_visitor('/citizenship-canadas-economy')
    all_econ = _load_canada_economy_questions()
    n_econ = len(all_econ)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    if has_access:
        econ_questions = all_econ
        show_paywall_econ = False
        max_visible_econ = n_econ
    elif n_econ <= 5:
        econ_questions = all_econ
        show_paywall_econ = False
        max_visible_econ = n_econ
    else:
        econ_questions = all_econ[:5]
        show_paywall_econ = True
        max_visible_econ = 6
    resp = app.make_response(
        render_template(
            'citizenship_canadas_economy.html',
            econ_questions=econ_questions,
            max_question_econ=n_econ,
            max_visible_econ=max_visible_econ,
            show_paywall_econ=show_paywall_econ,
            exam_section_views=_count_exam_section_visits(),
        )
    )
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/citizenship-canadas-regions')
def citizenship_canadas_regions():
    """Canada's Regions (Chapter 10) — پنج سوال اول رایگان؛ از ششم با اشتراک ۴۱۴."""
    log_visitor('/citizenship-canadas-regions')
    all_reg = _load_canada_regions_questions()
    n_reg = len(all_reg)
    today = _today()
    has_access = False
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                has_access = True
        except Exception:
            pass
    if has_access:
        reg_questions = all_reg
        show_paywall_reg = False
        max_visible_reg = n_reg
    elif n_reg <= 5:
        reg_questions = all_reg
        show_paywall_reg = False
        max_visible_reg = n_reg
    else:
        reg_questions = all_reg[:5]
        show_paywall_reg = True
        max_visible_reg = 6
    resp = app.make_response(
        render_template(
            'citizenship_canadas_regions.html',
            reg_questions=reg_questions,
            max_question_reg=n_reg,
            max_visible_reg=max_visible_reg,
            show_paywall_reg=show_paywall_reg,
            exam_section_views=_count_exam_section_visits(),
        )
    )
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


# Official IRCC study guide PDF — use as HTTP canonical for our mirror to avoid GSC "duplicate without user-selected canonical".
_IRCC_DISCOVER_CANADA_PDF = 'https://www.canada.ca/content/dam/ircc/migration/ircc/english/pdf/pub/discover.pdf'


@app.route('/discover.pdf')
def discover_pdf():
    """Serve the Discover Canada PDF (mirror). Canonical header points to IRCC — same document, preferred URL for indexing."""
    root = os.path.dirname(os.path.abspath(__file__))
    resp = send_from_directory(root, 'discover.pdf')
    resp.headers['Link'] = f'<{_IRCC_DISCOVER_CANADA_PDF}>; rel="canonical"'
    return resp

def _google_search_console_verify_file(filename):
    """فایل HTML دانلودی گوگل باید کنار app.py باشد؛ نام دقیق همان چیزی است که Search Console می‌دهد."""
    root = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(root, filename)
    if not os.path.isfile(path):
        abort(404)
    return send_from_directory(root, filename, mimetype='text/html; charset=utf-8')


@app.route('/googlee38c49b065f08d79.html')
def google_verification_legacy():
    return _google_search_console_verify_file('googlee38c49b065f08d79.html')


@app.route('/googlebd799b5068006263.html')
def google_verification_bd799():
    return _google_search_console_verify_file('googlebd799b5068006263.html')


@app.route('/manifest.webmanifest')
def webapp_manifest():
    """Web App Manifest for PWA (Add to Home Screen / نصب اپ)."""
    base = _seo_base_url()
    manifest = {
        'id': base + '/',
        'name': 'آزمون شهروندی کانادا | CitizenTest',
        'short_name': 'CitizenTest',
        'description': 'CitizenTest (discovercanadatest.com) — آزمون تمرینی شهروندی کانادا به فارسی، انگلیسی و فرانسه؛ ۱۰۰ تست، بانک ۴۱۴ و ۵۷۱ سوال و خلاصه Discover Canada.',
        'start_url': base + '/',
        'scope': base + '/',
        'display': 'standalone',
        'orientation': 'any',
        'theme_color': '#0f172a',
        'background_color': '#ffffff',
        'lang': 'fa',
        'dir': 'rtl',
        'categories': ['education', 'reference'],
        'icons': [
            {'src': base + '/static/images/logo.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': base + '/static/images/logo.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': base + '/static/images/logo.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
    }
    return jsonify(manifest), 200, {'Content-Type': 'application/manifest+json; charset=utf-8'}


def _resolved_seo_canonical_base():
    """اگر باید canonical ثابت باشد، https://... بدون اسلش آخر؛ وگرنه رشتهٔ خالی.

    ۱) متغیر محیطی SEO_CANONICAL_BASE (اختیاری، برای دامنهٔ دیگر یا staging)
    ۲) وگرنه اگر Host همان دامنهٔ production است → https://discovercanadatest.com
       (نیازی به تنظیم AWS نیست)
    """
    env = (os.getenv('SEO_CANONICAL_BASE') or '').strip().rstrip('/')
    if env:
        return env
    # پشت پروکسی/لودبالانسر ممکن است request.host داخلی باشد؛ برای OG/preview دامنهٔ واقعی را از X-Forwarded-Host بگیر.
    fwd_host = (request.headers.get('X-Forwarded-Host') or '').split(',')[0].strip()
    host_raw = fwd_host or (request.host or '')
    host = host_raw.split(':')[0].lower()
    if host in ('discovercanadatest.com', 'www.discovercanadatest.com'):
        return 'https://discovercanadatest.com'
    return ''


def _seo_base_url():
    """Base URL for canonical, og:url, sitemap, manifest."""
    fixed = _resolved_seo_canonical_base()
    if fixed:
        return fixed
    # ساخت base URL با احترام به هدرهای پروکسی (برای اینکه OG image با دامنهٔ عمومی ساخته شود)
    proto = (request.headers.get('X-Forwarded-Proto') or request.scheme or 'http').split(',')[0].strip()
    host = (request.headers.get('X-Forwarded-Host') or request.host or '').split(',')[0].strip()
    if not host:
        return request.host_url.rstrip('/')
    return f'{proto}://{host}'.rstrip('/')


@app.before_request
def _enforce_canonical_host_redirect():
    """با پایهٔ canonical ثابت، Host غیرهم‌راستا (مثلاً www در حالی که apex استاندارد است) → 301."""
    fixed = _resolved_seo_canonical_base()
    if not fixed:
        return None
    try:
        from urllib.parse import urlparse

        parsed = urlparse(fixed if '://' in fixed else f'https://{fixed}')
        canonical_host = (parsed.netloc or '').split(':')[0].lower()
    except Exception:
        return None
    if not canonical_host:
        return None
    path = request.path or '/'
    if path.startswith('/static/'):
        return None
    req_host = (request.host or '').split(':')[0].lower()
    if not req_host or req_host == canonical_host:
        return None
    suffix = request.full_path
    if not suffix.startswith('/'):
        suffix = '/' + suffix
    return redirect(fixed + suffix, code=301)


@app.context_processor
def inject_seo_base_url():
    """همهٔ قالب‌ها: {{ seo_base_url() }} برای canonical و og:image مطلق با HTTPS پشت پروکسی."""
    # با زیاد کردن این عدد بعد از دیپلوی، URL تصویر OG عوض می‌شود و تلگرام/واتساپ گاهی پیش‌نمایش را دوباره می‌کشند.
    return dict(seo_base_url=_seo_base_url, og_preview_version=os.getenv('OG_PREVIEW_VERSION', '6'))


@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt for search engines with dynamic sitemap URL"""
    base = _seo_base_url()
    body = f'''User-agent: *
Allow: /
Disallow: /admin
Disallow: /api/

Sitemap: {base}/sitemap.xml
'''
    return body, 200, {'Content-Type': 'text/plain; charset=utf-8'}


# یک منبع برای sitemap.xml و صفحهٔ HTML /site-map (لینک داخلی و خزیدن گوگل)
_SITEMAP_PAGE_DEFS = [
    {'path': '/', 'changefreq': 'daily', 'priority': '1.0', 'label_fa': 'صفحهٔ اصلی — ۱۰۰ تست تمرینی', 'label_en': 'Home'},
    {'path': '/site-map', 'changefreq': 'monthly', 'priority': '0.55', 'label_fa': 'نقشهٔ سایت (فهرست همهٔ صفحات)', 'label_en': 'HTML sitemap'},
    {'path': '/about', 'changefreq': 'monthly', 'priority': '0.6', 'label_fa': 'دربارهٔ سایت و تماس', 'label_en': 'About'},
    {'path': '/book_summary.html', 'changefreq': 'weekly', 'priority': '0.9', 'label_fa': 'خلاصهٔ کتاب Discover Canada (سه زبان)', 'label_en': 'Book summary'},
    {'path': '/canadian-history-timeline', 'changefreq': 'monthly', 'priority': '0.82', 'label_fa': 'خط زمانی تاریخ کانادا (Discover Canada)', 'label_en': 'Canadian history timeline (study page)'},
    {'path': '/citizenship-414', 'changefreq': 'weekly', 'priority': '0.9', 'label_fa': '۴۱۴ سوال شهروندی', 'label_en': '414 questions'},
    {'path': '/citizenship-571', 'changefreq': 'weekly', 'priority': '0.9', 'label_fa': '۵۷۱ سوال شهروندی', 'label_en': '571 questions'},
    {'path': '/citizenship-exams', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': 'فهرست آزمون‌های نمونه (فصل‌به‌فصل)', 'label_en': 'Sample exams index'},
    {'path': '/citizenship-introduction', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': 'آزمون Introduction', 'label_en': 'Introduction'},
    {'path': '/citizenship-rights-responsibilities', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': 'آزمون Rights and Responsibilities', 'label_en': 'Rights & responsibilities'},
    {'path': '/citizenship-who-we-are', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': 'آزمون Who We Are', 'label_en': 'Who we are'},
    {'path': '/citizenship-canadas-history', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': "آزمون Canada's History", 'label_en': "Canada's history"},
    {'path': '/citizenship-how-canadians-govern-themselves', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': 'آزمون How Canadians Govern', 'label_en': 'How Canadians govern'},
    {'path': '/citizenship-federal-elections', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': 'آزمون Federal Elections', 'label_en': 'Federal elections'},
    {'path': '/citizenship-canadian-symbols', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': 'آزمون Canadian Symbols', 'label_en': 'Canadian symbols'},
    {'path': '/citizenship-canadas-economy', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': "آزمون Canada's Economy", 'label_en': "Canada's economy"},
    {'path': '/citizenship-canadas-regions', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': "آزمون Canada's Regions", 'label_en': "Canada's regions"},
    {'path': '/citizenship-justice-system', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': 'آزمون Justice System', 'label_en': 'Justice system'},
    {'path': '/citizenship-modern-canada', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': 'آزمون Modern Canada', 'label_en': 'Modern Canada'},
    {'path': '/exam1', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': 'Exam1 — Rights & Responsibilities', 'label_en': 'Exam 1'},
    {'path': '/exam2', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': "Exam2 — Canada's History", 'label_en': 'Exam 2'},
    {'path': '/exam3', 'changefreq': 'weekly', 'priority': '0.85', 'label_fa': "Exam3 — Canada's History (نمونهٔ دوم)", 'label_en': 'Exam 3'},
    {'path': '/citizenship-exam-report', 'changefreq': 'weekly', 'priority': '0.55', 'label_fa': 'لیست قبولی آزمون شهروندی', 'label_en': 'Exam pass list'},
]


@app.route('/site-map')
def html_site_map():
    """نقشهٔ سایت HTML — لینک داخلی برای خزنده‌ها و کاربران (مکمل sitemap.xml)."""
    log_visitor('/site-map')
    return render_template('site_map.html', site_map_pages=_SITEMAP_PAGE_DEFS)


@app.route('/sitemap.xml')
def sitemap():
    """Serve sitemap.xml for SEO with lastmod for crawlers"""
    base = _seo_base_url()
    lastmod = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
'''
    for entry in _SITEMAP_PAGE_DEFS:
        path = entry['path']
        changefreq = entry['changefreq']
        priority = entry['priority']
        xml += f'''  <url>
    <loc>{base}{path}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>
'''
    xml += '</urlset>'
    return xml, 200, {'Content-Type': 'application/xml; charset=utf-8'}

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
                        'last_updated': datetime.now(timezone.utc).isoformat()
                    })
        else:
            # Fallback to in-memory counter
            return jsonify({
                'success': True,
                'count': in_memory_counter,
                'last_updated': datetime.now(timezone.utc).isoformat(),
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

    if _is_loopback_client():
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute(
                    "SELECT count, last_updated FROM visitor_counter WHERE counter_id = 'main'"
                )
                row = cur.fetchone()
                cur.close()
                conn.close()
                if row:
                    lu = row['last_updated']
                    return jsonify({
                        'success': True,
                        'count': row['count'],
                        'last_updated': lu.isoformat() if lu else '',
                    })
        except Exception:
            pass
        return jsonify({
            'success': True,
            'count': in_memory_counter,
            'last_updated': datetime.now(timezone.utc).isoformat(),
        })

    log_visitor('/api/visitor-count/increment')

    try:
        conn = get_db_connection()
        if conn:
            # Use atomic update to increment counter
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                INSERT INTO visitor_counter (counter_id, count, last_updated)
                VALUES ('main', 0, CURRENT_TIMESTAMP)
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
                    'last_updated': datetime.now(timezone.utc).isoformat(),
                    'warning': 'Update returned no rows, using in-memory counter'
                })
        else:
            # Fallback to in-memory counter
            in_memory_counter += 1
            return jsonify({
                'success': True,
                'count': in_memory_counter,
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'warning': 'Using in-memory counter (Database not available)'
            })
    except Exception as e:
        print(f"Error incrementing visitor count: {e}")
        # Fallback to in-memory counter
        in_memory_counter += 1
        return jsonify({
            'success': True,
            'count': in_memory_counter,
            'last_updated': datetime.now(timezone.utc).isoformat(),
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

        exclude_sql, exclude_params = _visitor_exclude_sql()

        conn = get_db_connection()
        if conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            if ip_filter and _is_loopback_ip(ip_filter):
                logs = []
                total = 0
            elif ip_filter:
                cur.execute("""
                    SELECT log_id, ip_address, access_time, page_visited, user_agent, referer
                    FROM visitor_log
                    WHERE ip_address = %s
                    """ + exclude_sql + """
                    ORDER BY access_time DESC
                    LIMIT %s OFFSET %s
                """, (ip_filter,) + exclude_params + (limit, offset))
                logs = cur.fetchall()
                cur.execute("""
                    SELECT COUNT(*) as total FROM visitor_log
                    WHERE ip_address = %s
                    """ + exclude_sql,
                    (ip_filter,) + exclude_params)
                total = cur.fetchone()['total']
            else:
                cur.execute("""
                    SELECT log_id, ip_address, access_time, page_visited, user_agent, referer
                    FROM visitor_log
                    WHERE 1=1
                    """ + exclude_sql + """
                    ORDER BY access_time DESC
                    LIMIT %s OFFSET %s
                """, exclude_params + (limit, offset))
                logs = cur.fetchall()
                cur.execute(
                    "SELECT COUNT(*) as total FROM visitor_log WHERE 1=1" + exclude_sql,
                    exclude_params,
                )
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
            exclude_sql, exclude_params = _visitor_exclude_sql()

            cur.execute(
                "SELECT COUNT(*) as total_visits FROM visitor_log WHERE 1=1" + exclude_sql,
                exclude_params,
            )
            total_visits = cur.fetchone()['total_visits']

            cur.execute(
                "SELECT COUNT(DISTINCT ip_address) as unique_ips FROM visitor_log WHERE 1=1"
                + exclude_sql,
                exclude_params,
            )
            unique_ips = cur.fetchone()['unique_ips']

            cur.execute(
                """
                SELECT COUNT(*) as visits_today
                FROM visitor_log
                WHERE DATE(access_time) = CURRENT_DATE
                """
                + exclude_sql,
                exclude_params,
            )
            visits_today = cur.fetchone()['visits_today']

            cur.execute(
                """
                SELECT ip_address, COUNT(*) as visit_count
                FROM visitor_log
                WHERE 1=1
                """
                + exclude_sql
                + """
                GROUP BY ip_address
                ORDER BY visit_count DESC
                LIMIT 10
                """,
                exclude_params,
            )
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


# ---------- Subscription (اشتراک تست‌ها و سوالات ۴۱۴) ----------
def _today():
    return date.today()


# حداقل تاریخ امتحان برای فهرست عمومی قبولی (فقط ردیف‌های با تاریخ امتحان >= این مقدار)
_CITIZENSHIP_PASS_LIST_EXAM_SINCE = date(2026, 1, 25)


def _parse_optional_date(value):
    """Accept YYYY-MM-DD or empty; return date or None."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def _exam_score_as_float(raw):
    """اولین عدد قابل‌تفسیر از رشتهٔ نمره (مثلاً ۲۰، ۱۹٪، 85)؛ وگرنه None."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    fa_digits = '۰۱۲۳۴۵۶۷۸۹'
    en_digits = '0123456789'
    s = s.translate(str.maketrans(fa_digits, en_digits))
    m = re.search(r'([0-9]+(?:[.,][0-9]+)?)', s)
    if not m:
        return None
    try:
        return float(m.group(1).replace(',', '.'))
    except ValueError:
        return None


def _get_citizenship_exam_report_rows(min_exclusive=14.0, limit=800, exam_since=None):
    """فهرست عمومی قبولی: تاریخ امتحان از exam_since (پیش‌فرض ۲۵ ژانویه ۲۰۲۶) تا امروز + آستانهٔ عددی نمره فقط در کد."""
    if exam_since is None:
        exam_since = _CITIZENSHIP_PASS_LIST_EXAM_SINCE
    rows_out = []
    try:
        conn = get_db_connection()
        if not conn:
            return []
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT first_name, last_name, citizenship_city,
                   citizenship_apply_date, citizenship_exam_date, citizenship_exam_score
            FROM subscription_users
            WHERE citizenship_exam_date IS NOT NULL
              AND citizenship_exam_date >= %s
              AND citizenship_exam_score IS NOT NULL
              AND TRIM(citizenship_exam_score) <> ''
            ORDER BY citizenship_exam_date DESC, id DESC
            LIMIT %s
            """,
            (exam_since, limit),
        )
        raw = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        return []

    for r in raw:
        sc = _exam_score_as_float(r.get('citizenship_exam_score'))
        if sc is None or sc <= min_exclusive:
            continue
        ed_raw = r.get('citizenship_exam_date')
        exam_d = ed_raw if isinstance(ed_raw, date) else _parse_optional_date(ed_raw)
        if exam_d is None:
            continue
        fn = (r.get('first_name') or '').strip()
        ln = (r.get('last_name') or '').strip()
        name = ' '.join(x for x in (fn, ln) if x) or '—'
        city = (r.get('citizenship_city') or '').strip() or '—'
        ad = r.get('citizenship_apply_date')
        if hasattr(ad, 'isoformat'):
            ad = ad.isoformat()
        ed = ed_raw.isoformat() if hasattr(ed_raw, 'isoformat') else str(ed_raw)
        apply_disp = (str(ad)[:10] if ad else '') or '—'
        exam_disp = (str(ed)[:10] if ed else '') or '—'
        score_disp = str(r.get('citizenship_exam_score') or '').strip()
        rows_out.append({
            'name': name,
            'city': city,
            'apply': apply_disp,
            'exam': exam_disp,
            'score': score_disp,
            '_sort_score': sc,
            '_exam_d': exam_d,
        })
    rows_out.sort(key=lambda x: (x['_exam_d'], x['_sort_score'], x['name']), reverse=True)
    for x in rows_out:
        del x['_sort_score']
        del x['_exam_d']
    return rows_out


def _get_citizenship_exam_waiting_rows(limit=800):
    """پرداخت‌کنندگان با حداقل یک ردیف در subscription_payments که هنوز نمرهٔ امتحان ثبت نکرده‌اند."""
    rows_out = []
    try:
        conn = get_db_connection()
        if not conn:
            return []
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT u.first_name, u.last_name, u.citizenship_city,
                   u.citizenship_apply_date, u.citizenship_exam_date
            FROM subscription_users u
            WHERE EXISTS (SELECT 1 FROM subscription_payments p WHERE p.user_id = u.id)
              AND (
                    u.citizenship_exam_score IS NULL
                    OR TRIM(COALESCE(u.citizenship_exam_score, '')) = ''
                  )
            ORDER BY u.id DESC
            LIMIT %s
            """,
            (limit,),
        )
        raw = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        return []

    for r in raw:
        fn = (r.get('first_name') or '').strip()
        ln = (r.get('last_name') or '').strip()
        name = ' '.join(x for x in (fn, ln) if x) or '—'
        city = (r.get('citizenship_city') or '').strip() or '—'
        ad = r.get('citizenship_apply_date')
        if hasattr(ad, 'isoformat'):
            ad = ad.isoformat()
        apply_disp = (str(ad)[:10] if ad else '') or '—'
        ed_raw = r.get('citizenship_exam_date')
        if hasattr(ed_raw, 'isoformat'):
            ed_raw = ed_raw.isoformat()
        exam_disp = (str(ed_raw)[:10] if ed_raw else '') or '—'
        rows_out.append({'name': name, 'city': city, 'apply': apply_disp, 'exam': exam_disp})
    return rows_out


@app.route('/api/subscription/status', methods=['GET'])
def api_subscription_status():
    """Return current session subscription status for both sections."""
    today = _today()
    out = {
        'tests': False,
        'tests_expiry': None,
        'questions_414': False,
        'questions_414_expiry': None,
    }
    if session.get('sub_tests_expiry'):
        try:
            exp = session['sub_tests_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                out['tests'] = True
                out['tests_expiry'] = exp.isoformat() if hasattr(exp, 'isoformat') else str(exp)
        except Exception:
            pass
    if session.get('sub_414_expiry'):
        try:
            exp = session['sub_414_expiry']
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp >= today:
                out['questions_414'] = True
                out['questions_414_expiry'] = exp.isoformat() if hasattr(exp, 'isoformat') else str(exp)
        except Exception:
            pass
    return jsonify(out)

@app.route('/api/subscription/login', methods=['POST'])
def api_subscription_login():
    """Validate mobile + password and ensure subscription for the requested section; set session and return success."""
    data = request.get_json() or {}
    mobile = (data.get('mobile') or '').strip()
    password = (data.get('password') or '').strip()
    section = (data.get('section') or '').strip()  # 'tests' or 'questions_414'
    if not mobile or not password:
        return jsonify({'success': False, 'error': 'کد کاربری و کلمه عبور الزامی است.'}), 200
    if section not in ('tests', 'questions_414'):
        return jsonify({'success': False, 'error': 'ورودی نامعتبر.'}), 200
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'خطای اتصال به پایگاه داده.'}), 200
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, password_hash FROM subscription_users WHERE mobile = %s", (mobile,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row or not check_password_hash(row['password_hash'], password):
            return jsonify({'success': False, 'error': 'کد کاربری یا کلمه عبور اشتباه است.'}), 200
        user_id = row['id']
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'خطای اتصال.'}), 200
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT section, expiry_date FROM subscription_subscriptions
            WHERE user_id = %s AND status = 'active' AND expiry_date >= %s
        """, (user_id, _today()))
        subs = cur.fetchall()
        cur.close()
        conn.close()
        expiry_by_section = {r['section']: r['expiry_date'] for r in subs}
        exp = expiry_by_section.get(section)
        if not exp:
            return jsonify({'success': False, 'error': 'اشتراک منقضی شده یا خریداری نشده است.'}), 200
        if isinstance(exp, datetime):
            exp = exp.date()
        session.permanent = True  # کوکی ورود تا ۹۰ روز (یا تا پاک کردن کش) حفظ شود
        session['sub_user_id'] = user_id
        session['sub_mobile'] = mobile
        if section == 'tests':
            session['sub_tests_expiry'] = exp.isoformat()
        else:
            session['sub_414_expiry'] = exp.isoformat()
        # If they have the other section too, set it so we don't ask again
        for s, e in expiry_by_section.items():
            if isinstance(e, datetime):
                e = e.date()
            if s == 'tests' and e >= _today():
                session['sub_tests_expiry'] = e.isoformat()
            elif s == 'questions_414' and e >= _today():
                session['sub_414_expiry'] = e.isoformat()
        return jsonify({'success': True, 'message': 'ورود موفق.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200


@app.route('/api/subscription/request-access', methods=['POST'])
def api_subscription_request_access():
    """ثبت درخواست دسترسی (موبایل) وقتی کاربر «خیر» می‌زند — کد کاربر همان موبایل خواهد بود."""
    data = request.get_json() or request.form or {}
    mobile = (data.get('mobile') or '').strip()
    section = (data.get('section') or 'tests').strip()
    if section not in ('tests', 'questions_414', 'both'):
        section = 'tests'
    if not mobile or len(mobile) < 5:
        return jsonify({'success': False, 'error': 'شماره موبایل معتبر وارد کنید.'}), 200
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'خطای اتصال.'}), 200
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO subscription_pending_requests (mobile, section) VALUES (%s, %s)",
            (mobile, section)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'درخواست ثبت شد. پس از واریز، کد کاربری شما همین شماره خواهد بود و رمز عبور برای شما ارسال می‌شود.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200


# ---------- Admin panel ----------
def _admin_required(f):
    from functools import wraps
    @wraps(f)
    def inner(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin')
        return f(*args, **kwargs)
    return inner

@app.route('/admin')
def admin_index():
    if session.get('admin_logged_in'):
        return redirect('/admin/dashboard')
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.form or request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    if not username or not password:
        return redirect('/admin?error=empty')
    try:
        conn = get_db_connection()
        if not conn:
            return redirect('/admin?error=db')
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, password_hash FROM admin_users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row or not check_password_hash(row['password_hash'], password):
            return redirect('/admin?error=invalid')
        session['admin_logged_in'] = True
        session['admin_username'] = username
        return redirect('/admin/dashboard')
    except Exception:
        return redirect('/admin?error=error')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect('/admin')


def _subscription_expiry_as_date(expiry_val):
    if expiry_val is None:
        return None
    if isinstance(expiry_val, datetime):
        return expiry_val.date()
    return expiry_val


def _days_until_expiry(expiry_val, today):
    """تعداد روز از امروز تا تاریخ انقضا (همان روز انقضا → ۰)."""
    d = _subscription_expiry_as_date(expiry_val)
    if d is None:
        return None
    return (d - today).days


def _admin_days_bar_percent(days_remaining):
    """عرض نوار نسبی: ۳۰ روز = ۱۰۰٪؛ بیشتر همان ۱۰۰٪؛ حداقل ~۶٪ برای دیده شدن."""
    if days_remaining is None or days_remaining < 0:
        return 0
    capped = min(int(days_remaining), 30)
    pct = int(round(100 * capped / 30))
    return min(100, max(6, pct))


def _admin_days_expiry_tier(days_remaining):
    """کلاس رنگی نوار: critical / warning / caution / ok."""
    if days_remaining is None:
        return 'muted'
    if days_remaining <= 3:
        return 'critical'
    if days_remaining <= 7:
        return 'warning'
    if days_remaining <= 14:
        return 'caution'
    return 'ok'


def _fetch_active_subscription_users_for_admin():
    """
    کاربرانی که حداقل یک ردیف اشتراک فعال با انقضا >= امروز دارند.
    تاریخ انقضای واحد (هر دو بسته معمولاً یکی است؛ MAX از ردیف‌های فعال).
    """
    today = _today()
    rows_out = []
    conn = get_db_connection()
    if not conn:
        return rows_out
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        _ensure_subscription_users_citizenship_columns(cur)
        conn.commit()
        cur.execute(
            """
            SELECT u.id, u.mobile, u.first_name, u.last_name,
                   (SELECT MAX(expiry_date) FROM subscription_subscriptions
                    WHERE user_id = u.id AND status = 'active' AND expiry_date >= %s) AS subscription_expiry
            FROM subscription_users u
            WHERE EXISTS (
                SELECT 1 FROM subscription_subscriptions s
                WHERE s.user_id = u.id AND s.status = 'active' AND s.expiry_date >= %s
            )
            ORDER BY (
                SELECT MIN(s.expiry_date) FROM subscription_subscriptions s
                WHERE s.user_id = u.id AND s.status = 'active' AND s.expiry_date >= %s
            ) ASC NULLS LAST, u.id DESC
            """,
            (today, today, today),
        )
        for r in cur.fetchall():
            exp = r.get('subscription_expiry')
            days_left = _days_until_expiry(exp, today)
            rows_out.append(
                {
                    'id': r['id'],
                    'mobile': r['mobile'],
                    'first_name': r.get('first_name') or '',
                    'last_name': r.get('last_name') or '',
                    'subscription_expiry': exp.isoformat()
                    if exp is not None and hasattr(exp, 'isoformat')
                    else None,
                    'days_remaining': days_left,
                    'days_bar_pct': _admin_days_bar_percent(days_left),
                    'days_tier': _admin_days_expiry_tier(days_left),
                }
            )
        cur.close()
    except Exception as ex:
        print(f"admin active subscribers: {ex}")
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return rows_out


@app.route('/admin/dashboard')
@_admin_required
def admin_dashboard():
    active_subscription_users = _fetch_active_subscription_users_for_admin()
    return render_template(
        'admin_dashboard.html',
        active_subscription_users=active_subscription_users,
    )


@app.route('/admin/exam-visitor-stats')
@_admin_required
def admin_exam_visitor_stats():
    """صفحهٔ جداگانهٔ آمار بازدید بخش آزمون‌های نمونه (فهرست فصل‌ها + Exam1–3)، همان دادهٔ API visitor-dashboard."""
    return render_template('admin_exam_visitor_stats.html')


@app.route('/admin/visitor-activity')
@_admin_required
def admin_visitor_activity():
    """صفحهٔ جداگانه: بازدید روزانه، IPهای پرتعداد، آخرین لاگ‌ها (بدون جدول تفصیلی آزمون نمونه)."""
    return render_template('admin_visitor_activity.html')


@app.route('/admin/api/change-password', methods=['POST'])
@_admin_required
def admin_api_change_password():
    """تغییر رمز عبور ادمین (ورود با رمز فعلی لازم است)."""
    username = session.get('admin_username')
    if not username:
        return jsonify({'success': False, 'error': 'ورود کنید.'}), 200
    data = request.get_json() or request.form or {}
    current = (data.get('current_password') or '').strip()
    new_pass = (data.get('new_password') or '').strip()
    if not current or not new_pass:
        return jsonify({'success': False, 'error': 'رمز فعلی و رمز جدید الزامی است.'}), 200
    if len(new_pass) < 6:
        return jsonify({'success': False, 'error': 'رمز جدید حداقل ۶ کاراکتر باشد.'}), 200
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'خطای DB'}), 500
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, password_hash FROM admin_users WHERE username = %s", (username,))
        row = cur.fetchone()
        if not row or not check_password_hash(row['password_hash'], current):
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'رمز فعلی اشتباه است.'}), 200
        cur.execute("UPDATE admin_users SET password_hash = %s WHERE id = %s",
                    (generate_password_hash(new_pass), row['id']))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'رمز با موفقیت عوض شد.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200


@app.route('/admin/api/pending-requests', methods=['GET'])
@_admin_required
def admin_api_pending_requests():
    """لیست درخواست‌های دسترسی (موبایل افرادی که «خیر» زدند و موبایل دادند)."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, mobile, section, created_at
            FROM subscription_pending_requests
            ORDER BY created_at DESC
            LIMIT 200
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for r in rows:
            if r.get('created_at') and hasattr(r['created_at'], 'isoformat'):
                r['created_at'] = r['created_at'].isoformat()
        return jsonify({'success': True, 'pending': rows}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/api/visitor-dashboard', methods=['GET'])
@_admin_required
def admin_api_visitor_dashboard():
    """داشبورد حضور: بازدید به تفکیک روز، IPهای پرتعداد، و جزئیات هر IP. localhost و EXCLUDED_VISITOR_IPS در آمار نمی‌آیند."""
    ip_filter = request.args.get('ip', '').strip() or None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor(cursor_factory=RealDictCursor)
        exclude_sql, exclude_params = _visitor_exclude_sql()

        if ip_filter:
            # جزئیات یک IP: در چه روزهایی، اولین/آخرین بازدید هر روز، تعداد درخواست، تخمین مدت (دقیقه)
            cur.execute("""
                SELECT DATE(access_time) AS day,
                       MIN(access_time) AS first_time,
                       MAX(access_time) AS last_time,
                       COUNT(*) AS visit_count
                FROM visitor_log
                WHERE ip_address = %s
                GROUP BY DATE(access_time)
                ORDER BY day DESC
                LIMIT 90
            """, (ip_filter,))
            days = cur.fetchall()
            out = []
            for row in days:
                first = row['first_time']
                last = row['last_time']
                duration_min = 0
                if first and last and hasattr(first, 'timestamp') and hasattr(last, 'timestamp'):
                    duration_min = max(0, int((last.timestamp() - first.timestamp()) / 60))
                out.append({
                    'date': row['day'].isoformat() if hasattr(row['day'], 'isoformat') else str(row['day']),
                    'first_time': first.isoformat() if first and hasattr(first, 'isoformat') else str(first),
                    'last_time': last.isoformat() if last and hasattr(last, 'isoformat') else str(last),
                    'visit_count': row['visit_count'],
                    'duration_minutes': duration_min,
                })
            cur.close()
            conn.close()
            return jsonify({'success': True, 'ip': ip_filter, 'days': out}), 200

        # خلاصه داشبورد: ۳۰ روز اخیر، IPهای پرتعداد، آخرین لاگ‌ها (بدون IPهای خودمون)
        cur.execute("""
            SELECT DATE(access_time) AS day,
                   COUNT(*) AS total_visits,
                   COUNT(DISTINCT ip_address) AS unique_ips
            FROM visitor_log
            WHERE access_time >= CURRENT_DATE - INTERVAL '30 days'
            """ + exclude_sql + """
            GROUP BY DATE(access_time)
            ORDER BY day DESC
            LIMIT 30
        """, exclude_params)
        visits_per_day = cur.fetchall()
        for row in visits_per_day:
            if hasattr(row.get('day'), 'isoformat'):
                row['day'] = row['day'].isoformat()

        cur.execute("""
            SELECT ip_address,
                   COUNT(*) AS total_visits,
                   MIN(access_time) AS first_seen,
                   MAX(access_time) AS last_seen,
                   COUNT(DISTINCT DATE(access_time)) AS days_active
            FROM visitor_log
            WHERE 1=1
            """ + exclude_sql + """
            GROUP BY ip_address
            ORDER BY total_visits DESC
            LIMIT 100
        """, exclude_params)
        top_ips = cur.fetchall()
        for row in top_ips:
            for k in ('first_seen', 'last_seen'):
                if row.get(k) and hasattr(row[k], 'isoformat'):
                    row[k] = row[k].isoformat()

        # پرکاربردترین user_agent (دیوایس) به ازای هر IP
        cur.execute("""
            SELECT ip_address, user_agent, COUNT(*) AS cnt
            FROM visitor_log
            WHERE 1=1
            """ + exclude_sql + """
            GROUP BY ip_address, user_agent
        """, exclude_params)
        ua_by_ip = {}
        for r in cur.fetchall():
            ip_key = r['ip_address']
            if ip_key not in ua_by_ip:
                ua_by_ip[ip_key] = []
            ua_by_ip[ip_key].append((r['user_agent'] or '', r['cnt']))
        for row in top_ips:
            uas = ua_by_ip.get(row['ip_address'], [])
            row['device'] = _device_from_user_agent(max(uas, key=lambda x: x[1])[0]) if uas else '—'

        cur.execute("""
            SELECT log_id, ip_address, access_time, page_visited, user_agent
            FROM visitor_log
            WHERE 1=1
            """ + exclude_sql + """
            ORDER BY access_time DESC
            LIMIT 100
        """, exclude_params)
        recent = cur.fetchall()
        for row in recent:
            if row.get('access_time') and hasattr(row['access_time'], 'isoformat'):
                row['access_time'] = row['access_time'].isoformat()
            row['device'] = _device_from_user_agent(row.get('user_agent') or '')

        # آمار بخش آزمون نمونه: /citizenship-exams، …، /citizenship-federal-elections، /citizenship-canadian-symbols، /citizenship-justice-system، … (همان حذف IP ادمین‌ها)
        exam_section = None
        try:
            cur.execute(
                """
                SELECT COUNT(*) AS total_hits,
                       COUNT(DISTINCT ip_address) AS unique_ips
                FROM visitor_log
                WHERE page_visited IN ('/citizenship-exams', '/citizenship-introduction', '/citizenship-rights-responsibilities', '/citizenship-who-we-are', '/citizenship-canadas-history', '/citizenship-how-canadians-govern-themselves', '/citizenship-federal-elections', '/citizenship-canadian-symbols', '/citizenship-canadas-economy', '/citizenship-canadas-regions', '/citizenship-justice-system', '/citizenship-modern-canada', '/exam1', '/exam2', '/exam3')
                """
                + exclude_sql,
                exclude_params,
            )
            ex_tot = cur.fetchone()
            cur.execute(
                """
                SELECT page_visited, COUNT(*) AS cnt
                FROM visitor_log
                WHERE page_visited IN ('/citizenship-exams', '/citizenship-introduction', '/citizenship-rights-responsibilities', '/citizenship-who-we-are', '/citizenship-canadas-history', '/citizenship-how-canadians-govern-themselves', '/citizenship-federal-elections', '/citizenship-canadian-symbols', '/citizenship-canadas-economy', '/citizenship-canadas-regions', '/citizenship-justice-system', '/citizenship-modern-canada', '/exam1', '/exam2', '/exam3')
                """
                + exclude_sql
                + """
                GROUP BY page_visited
                """,
                exclude_params,
            )
            by_page = {r["page_visited"]: int(r["cnt"]) for r in cur.fetchall()}
            cur.execute(
                """
                SELECT DATE(access_time) AS day,
                       SUM(CASE WHEN page_visited = '/citizenship-exams' THEN 1 ELSE 0 END) AS hub_hits,
                       SUM(CASE WHEN page_visited = '/citizenship-introduction' THEN 1 ELSE 0 END) AS intro_hits,
                       SUM(CASE WHEN page_visited = '/citizenship-rights-responsibilities' THEN 1 ELSE 0 END) AS rights_hits,
                       SUM(CASE WHEN page_visited = '/citizenship-who-we-are' THEN 1 ELSE 0 END) AS who_we_are_hits,
                       SUM(CASE WHEN page_visited = '/citizenship-canadas-history' THEN 1 ELSE 0 END) AS canadas_history_hits,
                       SUM(CASE WHEN page_visited = '/citizenship-how-canadians-govern-themselves' THEN 1 ELSE 0 END) AS govern_hits,
                       SUM(CASE WHEN page_visited = '/citizenship-federal-elections' THEN 1 ELSE 0 END) AS federal_elections_hits,
                       SUM(CASE WHEN page_visited = '/citizenship-canadian-symbols' THEN 1 ELSE 0 END) AS canadian_symbols_hits,
                       SUM(CASE WHEN page_visited = '/citizenship-canadas-economy' THEN 1 ELSE 0 END) AS canadas_economy_hits,
                       SUM(CASE WHEN page_visited = '/citizenship-canadas-regions' THEN 1 ELSE 0 END) AS canadas_regions_hits,
                       SUM(CASE WHEN page_visited = '/citizenship-justice-system' THEN 1 ELSE 0 END) AS justice_hits,
                       SUM(CASE WHEN page_visited = '/citizenship-modern-canada' THEN 1 ELSE 0 END) AS modern_canada_hits,
                       SUM(CASE WHEN page_visited = '/exam1' THEN 1 ELSE 0 END) AS exam1_hits,
                       SUM(CASE WHEN page_visited = '/exam2' THEN 1 ELSE 0 END) AS exam2_hits,
                       SUM(CASE WHEN page_visited = '/exam3' THEN 1 ELSE 0 END) AS exam3_hits
                FROM visitor_log
                WHERE page_visited IN ('/citizenship-exams', '/citizenship-introduction', '/citizenship-rights-responsibilities', '/citizenship-who-we-are', '/citizenship-canadas-history', '/citizenship-how-canadians-govern-themselves', '/citizenship-federal-elections', '/citizenship-canadian-symbols', '/citizenship-canadas-economy', '/citizenship-canadas-regions', '/citizenship-justice-system', '/citizenship-modern-canada', '/exam1', '/exam2', '/exam3')
                  AND access_time >= CURRENT_DATE - INTERVAL '30 days'
                """
                + exclude_sql
                + """
                GROUP BY DATE(access_time)
                ORDER BY day DESC
                LIMIT 30
                """,
                exclude_params,
            )
            exam_per_day = cur.fetchall()
            for er in exam_per_day:
                d = er.get("day")
                if d and hasattr(d, "isoformat"):
                    er["day"] = d.isoformat()
                er["hub_hits"] = int(er["hub_hits"] or 0)
                er["intro_hits"] = int(er["intro_hits"] or 0)
                er["rights_hits"] = int(er["rights_hits"] or 0)
                er["who_we_are_hits"] = int(er["who_we_are_hits"] or 0)
                er["canadas_history_hits"] = int(er["canadas_history_hits"] or 0)
                er["govern_hits"] = int(er["govern_hits"] or 0)
                er["federal_elections_hits"] = int(er["federal_elections_hits"] or 0)
                er["canadian_symbols_hits"] = int(er["canadian_symbols_hits"] or 0)
                er["canadas_economy_hits"] = int(er["canadas_economy_hits"] or 0)
                er["canadas_regions_hits"] = int(er["canadas_regions_hits"] or 0)
                er["justice_hits"] = int(er["justice_hits"] or 0)
                er["modern_canada_hits"] = int(er["modern_canada_hits"] or 0)
                er["exam1_hits"] = int(er["exam1_hits"] or 0)
                er["exam2_hits"] = int(er["exam2_hits"] or 0)
                er["exam3_hits"] = int(er["exam3_hits"] or 0)
            exam_section = {
                "total_hits": int(ex_tot["total_hits"] or 0) if ex_tot else 0,
                "unique_ips": int(ex_tot["unique_ips"] or 0) if ex_tot else 0,
                "hits_citizenship_exams": int(by_page.get("/citizenship-exams", 0)),
                "hits_citizenship_introduction": int(by_page.get("/citizenship-introduction", 0)),
                "hits_citizenship_rights": int(by_page.get("/citizenship-rights-responsibilities", 0)),
                "hits_citizenship_who_we_are": int(by_page.get("/citizenship-who-we-are", 0)),
                "hits_citizenship_canadas_history": int(by_page.get("/citizenship-canadas-history", 0)),
                "hits_citizenship_how_canadians_govern": int(by_page.get("/citizenship-how-canadians-govern-themselves", 0)),
                "hits_citizenship_federal_elections": int(by_page.get("/citizenship-federal-elections", 0)),
                "hits_citizenship_canadian_symbols": int(by_page.get("/citizenship-canadian-symbols", 0)),
                "hits_citizenship_canadas_economy": int(by_page.get("/citizenship-canadas-economy", 0)),
                "hits_citizenship_canadas_regions": int(by_page.get("/citizenship-canadas-regions", 0)),
                "hits_citizenship_justice": int(by_page.get("/citizenship-justice-system", 0)),
                "hits_citizenship_modern_canada": int(by_page.get("/citizenship-modern-canada", 0)),
                "hits_exam1": int(by_page.get("/exam1", 0)),
                "hits_exam2": int(by_page.get("/exam2", 0)),
                "hits_exam3": int(by_page.get("/exam3", 0)),
                "per_day": exam_per_day,
            }
        except Exception as ex_err:
            print(f"exam_section stats: {ex_err}")
            exam_section = None

        cur.close()
        conn.close()
        return jsonify({
            'success': True,
            'visits_per_day': visits_per_day,
            'top_ips': top_ips,
            'recent_logs': recent,
            'exam_section': exam_section,
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/api/users', methods=['GET'])
@_admin_required
def admin_api_users():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor(cursor_factory=RealDictCursor)
        _ensure_subscription_users_citizenship_columns(cur)
        conn.commit()
        cur.execute("""
            SELECT u.id, u.mobile, u.first_name, u.last_name, u.notes, u.created_at,
                   u.citizenship_city, u.citizenship_apply_date, u.citizenship_exam_date, u.citizenship_exam_score,
                   (SELECT COUNT(*)::int FROM subscription_payments WHERE user_id = u.id) AS payment_count,
                   (SELECT expiry_date FROM subscription_subscriptions WHERE user_id = u.id AND section = 'tests' AND status = 'active' ORDER BY expiry_date DESC LIMIT 1) AS tests_expiry,
                   (SELECT expiry_date FROM subscription_subscriptions WHERE user_id = u.id AND section = 'questions_414' AND status = 'active' ORDER BY expiry_date DESC LIMIT 1) AS questions_414_expiry
            FROM subscription_users u
            ORDER BY u.id DESC
        """)
        users = cur.fetchall()
        cur.close()
        conn.close()
        for u in users:
            for k in list(u.keys()):
                if hasattr(u[k], 'isoformat'):
                    u[k] = u[k].isoformat()
        return jsonify({'success': True, 'users': users}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/api/users/change-password', methods=['POST'])
@_admin_required
def admin_api_users_change_password():
    """تغییر رمز عبور یک کاربر اشتراک (با user_id و رمز جدید)."""
    data = request.get_json() or request.form or {}
    try:
        user_id = int(data.get('user_id') or 0)
    except Exception:
        user_id = 0
    new_password = (data.get('new_password') or '').strip()
    if not user_id or not new_password:
        return jsonify({'success': False, 'error': 'user_id و رمز جدید الزامی است.'}), 200
    if len(new_password) < 4:
        return jsonify({'success': False, 'error': 'رمز جدید حداقل ۴ کاراکتر باشد.'}), 200
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor()
        cur.execute(
            "UPDATE subscription_users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (generate_password_hash(new_password), user_id)
        )
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'کاربر یافت نشد.'}), 200
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'رمز کاربر با موفقیت عوض شد.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200


@app.route('/admin/api/users/reset-password', methods=['POST'])
@_admin_required
def admin_api_users_reset_password():
    """بازنشانی رمز کاربر به یک رمز موقت تصادفی؛ رمز جدید در پاسخ برمی‌گردد تا ادمین به کاربر بگوید."""
    data = request.get_json() or request.form or {}
    try:
        user_id = int(data.get('user_id') or 0)
    except Exception:
        user_id = 0
    if not user_id:
        return jsonify({'success': False, 'error': 'کاربر را انتخاب کنید.'}), 200
    # حداکثر ۸ حرف، حتماً شامل عدد
    chars = list(string.ascii_letters + string.digits)
    new_password = random.choice(string.digits) + ''.join(random.choices(chars, k=7))
    new_password = ''.join(random.sample(new_password, len(new_password)))
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor()
        cur.execute(
            "UPDATE subscription_users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (generate_password_hash(new_password), user_id)
        )
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'کاربر یافت نشد.'}), 200
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'رمز بازنشانی شد. این رمز را به کاربر بدهید.', 'password': new_password}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200


@app.route('/admin/api/users/add', methods=['POST'])
@_admin_required
def admin_api_users_add():
    data = request.get_json() or request.form or {}
    mobile = (data.get('mobile') or '').strip()
    password = (data.get('password') or '').strip()
    first_name = (data.get('first_name') or '').strip()[:100]
    last_name = (data.get('last_name') or '').strip()[:100]
    free_access = data.get('free_access') in (True, 'true', '1', 1)
    if not mobile or not password:
        return jsonify({'success': False, 'error': 'موبایل و رمز عبور الزامی است.'}), 200
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor()
        cur.execute("INSERT INTO subscription_users (mobile, password_hash, first_name, last_name) VALUES (%s, %s, %s, %s) RETURNING id",
                    (mobile, generate_password_hash(password), first_name or None, last_name or None))
        row = cur.fetchone()
        user_id = row[0]
        if free_access:
            exp = _today() + timedelta(days=365)
            for sec in ('tests', 'questions_414'):
                cur.execute("""
                    INSERT INTO subscription_subscriptions (user_id, section, expiry_date, status)
                    VALUES (%s, %s, %s, 'active')
                    ON CONFLICT (user_id, section) DO UPDATE SET
                    expiry_date = EXCLUDED.expiry_date, updated_at = CURRENT_TIMESTAMP
                """, (user_id, sec, exp))
        conn.commit()
        cur.close()
        conn.close()
        msg = 'کاربر اضافه شد.' + (' دسترسی رایگان یک‌ساله برای کل بسته فعال شد.' if free_access else '')
        return jsonify({'success': True, 'id': user_id, 'message': msg}), 200
    except psycopg2.IntegrityError:
        return jsonify({'success': False, 'error': 'این شماره موبایل قبلاً ثبت شده است.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200


@app.route('/admin/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
@_admin_required
def admin_api_users_update(user_id):
    """PUT: به‌روزرسانی پروفایل و اختیاری انقضا. DELETE: حذف کاربر فقط در صورت نداشتن ردیف پرداخت."""
    if request.method == 'DELETE':
        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'error': 'DB'}), 500
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM subscription_payments WHERE user_id = %s",
                (user_id,),
            )
            pay_n = cur.fetchone()[0]
            if pay_n > 0:
                cur.close()
                conn.close()
                return jsonify(
                    {
                        'success': False,
                        'error': 'این کاربر دارای سابقهٔ پرداخت است؛ حذف مجاز نیست.',
                    }
                ), 200
            cur.execute("DELETE FROM subscription_users WHERE id = %s", (user_id,))
            if cur.rowcount == 0:
                conn.rollback()
                cur.close()
                conn.close()
                return jsonify({'success': False, 'error': 'کاربر یافت نشد.'}), 200
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'success': True, 'message': 'کاربر حذف شد.'}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 200

    data = request.get_json() or request.form or {}
    first_name = (data.get('first_name') or '').strip()[:100]
    last_name = (data.get('last_name') or '').strip()[:100]
    city = (data.get('citizenship_city') or '').strip()[:150]
    apply_d = _parse_optional_date(data.get('citizenship_apply_date'))
    exam_d = _parse_optional_date(data.get('citizenship_exam_date'))
    exam_score = (data.get('citizenship_exam_score') or '').strip()[:50]
    if data.get('citizenship_apply_date') and str(data.get('citizenship_apply_date')).strip() and apply_d is None:
        return jsonify({'success': False, 'error': 'تاریخ اپلای نامعتبر است (فرمت YYYY-MM-DD).'}), 200
    if data.get('citizenship_exam_date') and str(data.get('citizenship_exam_date')).strip() and exam_d is None:
        return jsonify({'success': False, 'error': 'تاریخ امتحان نامعتبر است (فرمت YYYY-MM-DD).'}), 200
    subscription_exp = None
    if 'expiry_date' in data:
        exp_s = str(data.get('expiry_date') or '').strip()
        if exp_s:
            subscription_exp = _parse_optional_date(exp_s)
            if subscription_exp is None:
                return jsonify({'success': False, 'error': 'تاریخ انقضای اشتراک نامعتبر است (فرمت YYYY-MM-DD).'}), 200
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor()
        _ensure_subscription_users_citizenship_columns(cur)
        conn.commit()
        cur.execute(
            """UPDATE subscription_users SET
               first_name = NULLIF(%s, ''),
               last_name = NULLIF(%s, ''),
               citizenship_city = NULLIF(%s, ''),
               citizenship_apply_date = %s,
               citizenship_exam_date = %s,
               citizenship_exam_score = NULLIF(%s, ''),
               updated_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (first_name or None, last_name or None, city or None, apply_d, exam_d, exam_score or None, user_id)
        )
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'کاربر یافت نشد.'}), 200
        if subscription_exp is not None:
            for section in ('tests', 'questions_414'):
                cur.execute(
                    """
                    INSERT INTO subscription_subscriptions (user_id, section, expiry_date, status)
                    VALUES (%s, %s, %s, 'active')
                    ON CONFLICT (user_id, section) DO UPDATE SET
                    expiry_date = EXCLUDED.expiry_date, updated_at = CURRENT_TIMESTAMP
                    """,
                    (user_id, section, subscription_exp),
                )
        conn.commit()
        cur.close()
        conn.close()
        msg = 'اطلاعات کاربر به‌روز شد.'
        if subscription_exp is not None:
            msg += ' انقضای اشتراک (تست‌ها و ۴۱۴) نیز به‌روز شد.'
        return jsonify({'success': True, 'message': msg}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200


@app.route('/admin/api/users/bulk-update-names', methods=['POST'])
@_admin_required
def admin_api_users_bulk_update_names():
    """ورود گروهی نام و نام خانوادگی. بدنه: { "rows": [ {"mobile": "09...", "first_name": "...", "last_name": "..."}, ... ] }"""
    data = request.get_json() or {}
    rows = data.get('rows') or []
    if not isinstance(rows, list) or len(rows) > 500:
        return jsonify({'success': False, 'error': 'حداکثر ۵۰۰ ردیف در هر بار ارسال مجاز است.'}), 200
    updated = 0
    errors = []
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor()
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            mobile = (row.get('mobile') or '').strip()
            first_name = (row.get('first_name') or '').strip()[:100]
            last_name = (row.get('last_name') or '').strip()[:100]
            if not mobile:
                continue
            cur.execute(
                "UPDATE subscription_users SET first_name = NULLIF(%s, ''), last_name = NULLIF(%s, ''), updated_at = CURRENT_TIMESTAMP WHERE mobile = %s",
                (first_name or None, last_name or None, mobile)
            )
            if cur.rowcount:
                updated += 1
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'نام‌ها به‌روز شد. تعداد به‌روزرسانی: ' + str(updated), 'updated': updated}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200


@app.route('/admin/api/payments', methods=['GET'])
@_admin_required
def admin_api_payments():
    user_id = request.args.get('user_id', type=int)
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if user_id:
            cur.execute("""
                SELECT p.id, p.user_id, u.mobile, u.first_name, u.last_name, p.amount, p.sections_purchased, p.payment_date, p.payment_reference, p.notes, p.created_at
                FROM subscription_payments p JOIN subscription_users u ON u.id = p.user_id WHERE p.user_id = %s ORDER BY p.id DESC
            """, (user_id,))
        else:
            cur.execute("""
                SELECT p.id, p.user_id, u.mobile, u.first_name, u.last_name, p.amount, p.sections_purchased, p.payment_date, p.payment_reference, p.notes, p.created_at
                FROM subscription_payments p JOIN subscription_users u ON u.id = p.user_id ORDER BY p.id DESC LIMIT 200
            """)
        payments = cur.fetchall()
        cur.close()
        conn.close()
        for p in payments:
            for k in list(p.keys()):
                v = p[k]
                if v is not None and hasattr(v, 'isoformat'):
                    p[k] = v.isoformat()
        return jsonify({'success': True, 'payments': payments}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/api/settings/subscription-price', methods=['GET'])
@_admin_required
def admin_api_settings_subscription_price_get():
    """برگرداندن مبلغ فعلی اشتراک (دلار)."""
    return jsonify({'success': True, 'amount': get_subscription_price()}), 200


@app.route('/admin/api/settings/subscription-price', methods=['POST'])
@_admin_required
def admin_api_settings_subscription_price_post():
    """ذخیره مبلغ اشتراک (دلار). بدنه: { \"amount\": 20 }"""
    data = request.get_json() or request.form or {}
    try:
        amount = int(data.get('amount', 0))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'مبلغ نامعتبر'}), 200
    if amount < 5 or amount > 10000:
        return jsonify({'success': False, 'error': 'مبلغ باید بین ۵ تا ۱۰۰۰۰ باشد'}), 200
    if set_subscription_price(amount):
        return jsonify({'success': True, 'amount': amount, 'message': 'مبلغ ذخیره شد.'}), 200
    return jsonify({'success': False, 'error': 'خطا در ذخیره'}), 200


@app.route('/admin/api/payments/add', methods=['POST'])
@_admin_required
def admin_api_payments_add():
    data = request.get_json() or request.form or {}
    user_id = data.get('user_id')
    if user_id is not None:
        try:
            user_id = int(user_id)
        except Exception:
            user_id = None
    amount = data.get('amount')
    if amount is not None:
        try:
            amount = int(amount)
        except Exception:
            amount = None
    sections_purchased = (data.get('sections_purchased') or '').strip()
    payment_date_s = (data.get('payment_date') or '').strip()
    payment_reference = (data.get('payment_reference') or '').strip()[:100]
    notes = (data.get('notes') or '').strip()
    # کل بسته؛ مبلغ بین ۵ تا ۱۰۰۰۰ دلار
    if not user_id or sections_purchased != 'both':
        return jsonify({'success': False, 'error': 'ورودی نامعتبر. فقط ثبت پرداخت کل بسته امکان‌پذیر است.'}), 200
    if amount is None or amount < 5 or amount > 10000:
        return jsonify({'success': False, 'error': 'مبلغ نامعتبر. عدد بین ۵ تا ۱۰۰۰۰ وارد کنید.'}), 200
    try:
        pay_date = date.fromisoformat(payment_date_s) if payment_date_s else _today()
    except Exception:
        pay_date = _today()
    expiry = pay_date + timedelta(days=30)
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor()
        first_name = (data.get('first_name') or '').strip()[:100]
        last_name = (data.get('last_name') or '').strip()[:100]
        # فقط فیلدهای پرشده را به‌روز کن؛ خالی نفرست تا نام/نام خانوادگی قبلی پاک نشود
        if first_name or last_name:
            cur.execute(
                """
                UPDATE subscription_users SET
                    first_name = COALESCE(NULLIF(%s, ''), first_name),
                    last_name = COALESCE(NULLIF(%s, ''), last_name),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (first_name, last_name, user_id),
            )
        cur.execute("INSERT INTO subscription_payments (user_id, amount, sections_purchased, payment_date, payment_reference, notes) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id, amount, sections_purchased, pay_date, payment_reference or None, notes or None))
        sections_to_update = ['tests', 'questions_414']  # کل بسته
        for sec in sections_to_update:
            cur.execute("""
                INSERT INTO subscription_subscriptions (user_id, section, expiry_date, status)
                VALUES (%s, %s, %s, 'active')
                ON CONFLICT (user_id, section) DO UPDATE SET
                expiry_date = GREATEST(subscription_subscriptions.expiry_date, EXCLUDED.expiry_date),
                updated_at = CURRENT_TIMESTAMP
            """, (user_id, sec, expiry))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'پرداخت ثبت شد و اشتراک به‌روز شد.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200


@app.route('/admin/api/payments/<int:pay_id>', methods=['GET'])
@_admin_required
def admin_api_payment_get(pay_id):
    """برگرداندن یک پرداخت (برای فرم ویرایش)."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, user_id, amount, sections_purchased, payment_date, payment_reference, notes
            FROM subscription_payments WHERE id = %s
        """, (pay_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return jsonify({'success': False, 'error': 'پرداخت یافت نشد.'}), 200
        for k in list(row.keys()):
            v = row[k]
            if v is not None and hasattr(v, 'isoformat'):
                row[k] = v.isoformat()
        return jsonify({'success': True, 'payment': dict(row)}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/api/payments/<int:pay_id>', methods=['PUT'])
@_admin_required
def admin_api_payments_update(pay_id):
    """ویرایش یک پرداخت: مبلغ، تاریخ پرداخت، کد واریز، یادداشت."""
    data = request.get_json() or request.form or {}
    try:
        amount = int(data.get('amount'))
    except (TypeError, ValueError):
        amount = None
    payment_date_s = (data.get('payment_date') or '').strip()
    payment_reference = (data.get('payment_reference') or '').strip()[:100]
    notes = (data.get('notes') or '').strip()
    if amount is None or amount < 5 or amount > 10000:
        return jsonify({'success': False, 'error': 'مبلغ نامعتبر (۵ تا ۱۰۰۰۰)'}), 200
    try:
        pay_date = date.fromisoformat(payment_date_s) if payment_date_s else None
    except Exception:
        pay_date = None
    if not pay_date:
        return jsonify({'success': False, 'error': 'تاریخ پرداخت نامعتبر'}), 200
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor()
        cur.execute("""
            UPDATE subscription_payments
            SET amount = %s, payment_date = %s, payment_reference = %s, notes = %s
            WHERE id = %s
        """, (amount, pay_date, payment_reference or None, notes or None, pay_id))
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'پرداخت یافت نشد.'}), 200
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'پرداخت به‌روز شد.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200


@app.route('/admin/api/payments/<int:pay_id>', methods=['DELETE'])
@_admin_required
def admin_api_payments_delete(pay_id):
    """حذف یک پرداخت (برای اصلاح اشتباه). اشتراک خودکار برگشت داده نمی‌شود؛ در صورت نیاز از «تنظیم انقضا» استفاده کنید."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor()
        cur.execute("DELETE FROM subscription_payments WHERE id = %s", (pay_id,))
        if cur.rowcount == 0:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'پرداخت یافت نشد.'}), 200
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'پرداخت حذف شد. در صورت نیاز انقضای کاربر را دستی تنظیم کنید.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200


@app.route('/admin/api/subscription/set', methods=['POST'])
@_admin_required
def admin_api_subscription_set():
    """تنظیم دستی تاریخ انقضا برای یک کاربر — هر دو (تست و ۴۱۴) به همین تاریخ تنظیم می‌شوند."""
    data = request.get_json() or request.form or {}
    try:
        user_id = int(data.get('user_id') or 0)
    except Exception:
        user_id = 0
    expiry_s = (data.get('expiry_date') or '').strip()
    if not user_id:
        return jsonify({'success': False, 'error': 'کاربر الزامی است.'}), 200
    try:
        exp = date.fromisoformat(expiry_s) if expiry_s else _today()
    except Exception:
        exp = _today()
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor()
        for section in ('tests', 'questions_414'):
            cur.execute("""
                INSERT INTO subscription_subscriptions (user_id, section, expiry_date, status)
                VALUES (%s, %s, %s, 'active')
                ON CONFLICT (user_id, section) DO UPDATE SET
                expiry_date = EXCLUDED.expiry_date, updated_at = CURRENT_TIMESTAMP
            """, (user_id, section, exp))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'انقضا به‌روز شد.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200


@app.route('/admin/api/subscription/grant-free', methods=['POST'])
@_admin_required
def admin_api_subscription_grant_free():
    """اعطای دسترسی رایگان یک‌ساله به کل بسته (لطف — بدون ثبت پرداخت)."""
    data = request.get_json() or request.form or {}
    try:
        user_id = int(data.get('user_id') or 0)
    except Exception:
        user_id = 0
    if not user_id:
        return jsonify({'success': False, 'error': 'user_id الزامی است.'}), 200
    exp = _today() + timedelta(days=365)
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB'}), 500
        cur = conn.cursor()
        for sec in ('tests', 'questions_414'):
            cur.execute("""
                INSERT INTO subscription_subscriptions (user_id, section, expiry_date, status)
                VALUES (%s, %s, %s, 'active')
                ON CONFLICT (user_id, section) DO UPDATE SET
                expiry_date = EXCLUDED.expiry_date, updated_at = CURRENT_TIMESTAMP
            """, (user_id, sec, exp))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'دسترسی رایگان یک‌ساله برای کل بسته اعطا شد.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5011 ))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
