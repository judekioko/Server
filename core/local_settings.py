# local_settings.py
"""
Local development settings override
"""

# Simple settings for local development
DEBUG = True
ALLOWED_HOSTS = ['*']

# Admin URL for development (override production setting)
ADMIN_URL = 'admin/'

# Email settings for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Security settings for development
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

# Update login URLs for development
LOGIN_URL = f'/{ADMIN_URL}login/'
LOGIN_REDIRECT_URL = f'/{ADMIN_URL}'
