"""
Django settings for core project - Multi-environment Configuration
Supports: Local Development, Staging, and Production
"""

import os
import sys
import logging  # ADD THIS IMPORT
from pathlib import Path
from dotenv import load_dotenv
import socket

# Load environment variables
load_dotenv()

# ========================
#  BASE CONFIGURATION
# ========================
BASE_DIR = Path(__file__).resolve().parent.parent

# ========================
#  ENVIRONMENT DETECTION
# ========================
# Detect environment
IS_LOCAL = 'runserver' in sys.argv or 'test' in sys.argv
IS_PRODUCTION = os.environ.get('DJANGO_ENV') == 'production' or 'masingangcdf.org' in socket.gethostname()
IS_DEVELOPMENT = not IS_PRODUCTION

# ========================
#  SECURITY CONFIGURATION
# ========================
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production-for-local-only')

# Set DEBUG based on environment
if IS_LOCAL:
    DEBUG = True
elif os.environ.get('DEBUG'):
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
else:
    DEBUG = False

# ========================
#  HOST CONFIGURATION
# ========================
ALLOWED_HOSTS = []

if IS_PRODUCTION:
    ALLOWED_HOSTS = [
        '102.212.245.22',                    # Your VPS IP
        'server.masingangcdf.org',           # Server hostname
        'masingangcdf.org',                  # Main domain
        'www.masingangcdf.org',              # WWW domain
        'localhost',
        '127.0.0.1',
        '[::1]',
    ]
elif IS_DEVELOPMENT:
    ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', '0.0.0.0']

# ========================
#  APPLICATION DEFINITION
# ========================
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    
    # Local apps
    'bursary.apps.BursaryConfig',
]

# ========================
#  MIDDLEWARE
# ========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'

# ========================
#  TEMPLATES
# ========================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ========================
#  DATABASE CONFIGURATION
# ========================
if IS_PRODUCTION:
    # Production: PostgreSQL on Truehost VPS
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'bursary_db'),
            'USER': os.environ.get('DB_USER', 'bursary_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'StrongPass2025!'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),  # On server, use localhost
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CONN_MAX_AGE': 300,
            'OPTIONS': {
                'connect_timeout': 10,
                'client_encoding': 'UTF8',
            }
        }
    }
else:
    # Development/Staging: SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ========================
#  PASSWORD VALIDATION
# ========================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ========================
#  INTERNATIONALIZATION
# ========================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# ========================
#  STATIC & MEDIA FILES
# ========================
STATIC_URL = '/static/'

if IS_PRODUCTION:
    STATIC_ROOT = '/var/www/masingangcdf.org/static'
    MEDIA_ROOT = '/var/www/masingangcdf.org/media'
else:
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    MEDIA_ROOT = BASE_DIR / 'media'

STATICFILES_DIRS = [BASE_DIR / 'static']

# Whitenoise for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000
WHITENOISE_USE_FINDERS = True

# Media files
MEDIA_URL = '/media/'

# File upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880    # 5MB

# ========================
#  CORS CONFIGURATION
# ========================
CORS_ALLOW_CREDENTIALS = True

if IS_PRODUCTION:
    CORS_ALLOWED_ORIGINS = [
        'http://masingangcdf.org',
        'https://masingangcdf.org',
        'http://www.masingangcdf.org',
        'https://www.masingangcdf.org',
        'http://102.212.245.22',
        'https://102.212.245.22',
    ]
    CORS_ALLOW_ALL_ORIGINS = False
else:
    CORS_ALLOW_ALL_ORIGINS = True

# ========================
#  SECURITY CONFIGURATION
# ========================
if IS_PRODUCTION:
    # Production security settings
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    
    # Cookie settings
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Trusted origins for CSRF
    CSRF_TRUSTED_ORIGINS = [
        'https://masingangcdf.org',
        'https://www.masingangcdf.org',
        'https://102.212.245.22',
    ]
else:
    # Development security settings
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

# Session settings
SESSION_COOKIE_AGE = 3600
SESSION_SAVE_EVERY_REQUEST = True
X_FRAME_OPTIONS = 'DENY'

# ========================
#  REST FRAMEWORK CONFIG
# ========================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ] if DEBUG else [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '5000/hour',
        'user': '10000/hour',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# ========================
#  EMAIL CONFIGURATION
# ========================
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'bursary@masingangcdf.org')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_TIMEOUT = 30

DEFAULT_FROM_EMAIL = f'Masinga NG-CDF Bursary <{EMAIL_HOST_USER if not DEBUG else "dev@localhost"}>'

# ========================
#  LOGGING CONFIGURATION
# ========================
# Filter to handle emoji encoding issues on Windows
class NoUnicodeFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, str):
            # Replace common emojis with text equivalents
            emoji_replacements = {
                '✅': '[OK]',
                '🔄': '[RELOAD]',
                '🚀': '[LAUNCH]',
                '❌': '[ERROR]',
                '⚠️': '[WARNING]',
                '🔧': '[SETUP]',
                '📊': '[STATS]',
                '🔔': '[NOTIFY]',
                '📧': '[EMAIL]',
                '💾': '[SAVE]',
                '🔍': '[SEARCH]',
                '📱': '[MOBILE]',
                '🌐': '[WEB]',
                '🛡️': '[SECURITY]',
            }
            for emoji, replacement in emoji_replacements.items():
                record.msg = record.msg.replace(emoji, replacement)
        return True

if IS_PRODUCTION:
    LOG_DIR = '/var/www/logs/django'
    os.makedirs(LOG_DIR, exist_ok=True)
    
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'no_unicode': {
                '()': NoUnicodeFilter,
            }
        },
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_DIR, 'masinga.log'),
                'maxBytes': 1024 * 1024 * 10,
                'backupCount': 10,
                'formatter': 'verbose',
                'filters': ['no_unicode'],
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_DIR, 'error.log'),
                'maxBytes': 1024 * 1024 * 10,
                'backupCount': 10,
                'formatter': 'verbose',
                'filters': ['no_unicode'],
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'filters': ['no_unicode'],
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': True,
            },
            'bursary': {
                'handlers': ['console', 'file', 'error_file'],
                'level': 'DEBUG' if DEBUG else 'INFO',
                'propagate': False,
            },
        },
    }
else:
    # Simple console logging for development
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'no_unicode': {
                '()': NoUnicodeFilter,
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'filters': ['no_unicode'],
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
            },
            'bursary': {
                'handlers': ['console'],
                'level': 'DEBUG',
            },
        },
    }

# ========================
#  CACHE CONFIGURATION
# ========================
if IS_PRODUCTION:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/0',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 100,
                    'retry_on_timeout': True,
                }
            },
            'KEY_PREFIX': 'masinga_bursary',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

# ========================
#  ADMIN CONFIGURATION
# ========================
ADMIN_URL = 'secure-admin/'

# ========================
#  APPLICATION SETTINGS
# ========================
BURSARY_SETTINGS = {
    'MAX_APPLICATIONS_PER_USER': 1,
    'EDIT_WINDOW_HOURS': 24,
    'MIN_AMOUNT': 1000,
    'MAX_AMOUNT': 100000,
    'DEFAULT_STATUS': 'pending',
    'ALLOWED_FILE_TYPES': ['pdf', 'jpg', 'jpeg', 'png'],
    'MAX_FILE_SIZE_MB': 5,
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = f'/{ADMIN_URL}login/'
LOGIN_REDIRECT_URL = f'/{ADMIN_URL}'
LOGOUT_REDIRECT_URL = '/'

# ========================
#  ENVIRONMENT INFO
# ========================
if __name__ == '__main__' or 'runserver' in sys.argv:
    print(f"\n{'='*60}")
    print(f"Django Settings Loaded")
    print(f"{'='*60}")
    print(f"Environment: {'PRODUCTION' if IS_PRODUCTION else 'DEVELOPMENT'}")
    print(f"Debug Mode: {'ON' if DEBUG else 'OFF'}")
    print(f"Database: {'PostgreSQL' if IS_PRODUCTION else 'SQLite'}")
    print(f"Allowed Hosts: {ALLOWED_HOSTS[:3]}{'...' if len(ALLOWED_HOSTS) > 3 else ''}")
    print(f"Static Root: {STATIC_ROOT}")
    print(f"Media Root: {MEDIA_ROOT}")
    print(f"{'='*60}\n")

# Load local settings if they exist (for overrides)
try:
    from .local_settings import *
    print("[INFO] local_settings.py loaded successfully")
except ImportError:
    pass