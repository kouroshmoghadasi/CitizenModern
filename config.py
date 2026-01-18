"""
Database Configuration
برای امنیت بهتر، می‌توانید از environment variables استفاده کنید
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

# Flask Configuration
FLASK_CONFIG = {
    'host': os.getenv('FLASK_HOST', '0.0.0.0'),
    'port': int(os.getenv('FLASK_PORT', '5011')),
    'debug': os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
}
