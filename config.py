class Config:
    # Basic Flask Configuration
    SECRET_KEY = "Norch1605"
    
    # PostgreSQL Database Configuration
    SQLALCHEMY_DATABASE_URI = 'postgresql://azriel:Ra_sy6a7e2*@31.97.67.106:5432/demo'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Konfigurasi Gmail SMTP
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'keyapkeyop@gmail.com'         # Email kamu
    MAIL_PASSWORD = 'nind plrl oikp rveu'          # App password dari Google
    MAIL_DEFAULT_SENDER = 'keyapkeyop@gmail.com'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries in development

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


