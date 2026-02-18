import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY не установлен в .env файле")

    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    FLASK_APP = os.environ.get('FLASK_APP', 'app.py')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'

    # PostgreSQL
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME')

    if not all([DB_USER, DB_PASSWORD, DB_NAME]):
        raise ValueError("DB_USER, DB_PASSWORD и DB_NAME должны быть установлены в .env файле")

    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('POOL_SIZE', 10)),
        'pool_recycle': int(os.environ.get('POOL_RECYCLE', 3600)),
        'pool_pre_ping': True,
    }

    # Upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/images/products')
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,gif').split(','))

    # Pagination
    PRODUCTS_PER_PAGE = int(os.environ.get('PRODUCTS_PER_PAGE', 20))
    ORDERS_PER_PAGE = int(os.environ.get('ORDERS_PER_PAGE', 15))