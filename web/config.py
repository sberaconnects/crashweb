import os

DB_HOST     = os.environ.get('DB_HOST', 'mariadb')
DB_USER     = os.environ.get('DB_USER', 'apache')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME     = os.environ.get('DB_NAME', 'coredumps')
DB_PORT     = os.environ.get('DB_PORT', '3306')

SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is required. "
        "Set it to a long random string before starting the app."
    )

COREDUMP_DIR     = os.environ.get('COREDUMP_DIR', '/var/www/html/coredumps')
SDK_DIR          = os.environ.get('SDK_DIR', '/var/www/sdks')
SDK_BASE_URL     = os.environ.get('SDK_BASE_URL', '').rstrip('/')
SDK_PACKAGE_NAME = os.environ.get('SDK_PACKAGE_NAME', '')
SDK_SYSROOT_SUBPATH = os.environ.get('SDK_SYSROOT_SUBPATH', '')

GITHUB_REPO = os.environ.get('GITHUB_REPO', '')
