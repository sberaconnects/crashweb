import os

DB_HOST = os.environ.get('DB_HOST', 'mariadb')
DB_USER = os.environ.get('DB_USER', 'apache')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'coredumps')
DB_PORT = os.environ.get('DB_PORT', '3306')

SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'fgklhjwkmnlcbn[sojqlkdjv')
