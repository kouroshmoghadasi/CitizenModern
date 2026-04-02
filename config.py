"""
Database Configuration
برای امنیت بهتر، می‌توانید از environment variables استفاده کنید

SEO: برای discovercanadatest.com معمولاً نیازی به متغیر نیست (در app.py خودکار ست می‌شود).
فقط اگر دامنهٔ دیگری یا staging دارید، در سرور بگذارید، مثال:
  SEO_CANONICAL_BASE=https://example.com
"""
import os

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'database-1.cv48gkiqsk4d.ca-central-1.rds.amazonaws.com'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'citizentest'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '1X8HcEa%iP%yT_lqz1)S~#b&QoV8x{U1')
}
