# Setup Guide - Masinga NG-CDF Bursary Management System

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)
- Git

## Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Server
```

### 2. Create Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL Database

**Create a new database:**
```sql
CREATE DATABASE bursary;
CREATE USER bursary_user WITH PASSWORD 'your_secure_password';
ALTER ROLE bursary_user SET client_encoding TO 'utf8';
ALTER ROLE bursary_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE bursary_user SET default_transaction_deferrable TO on;
ALTER ROLE bursary_user SET timezone TO 'Africa/Nairobi';
GRANT ALL PRIVILEGES ON DATABASE bursary TO bursary_user;
```

### 5. Update Settings

Edit `core/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bursary',
        'USER': 'bursary_user',
        'PASSWORD': 'your_secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 6. Configure Email Settings

Edit `core/settings.py`:

**For Gmail:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Use app-specific password
DEFAULT_FROM_EMAIL = 'Masinga NG-CDF <your-email@gmail.com>'
```

**For Other Email Providers:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.your-provider.com'
EMAIL_PORT = 587  # or 465 for SSL
EMAIL_USE_TLS = True  # or False if using SSL
EMAIL_HOST_USER = 'your-email@domain.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'Masinga NG-CDF <your-email@domain.com>'
```

### 7. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 9. Create Application Deadline

```bash
python manage.py shell
```

Then in the Python shell:
```python
from bursary.models import ApplicationDeadline
from datetime import datetime, timedelta

deadline = ApplicationDeadline.objects.create(
    name="2024 Bursary Round 1",
    start_date=datetime.now(),
    end_date=datetime.now() + timedelta(days=30),
    is_active=True
)
print(f"Deadline created: {deadline}")
exit()
```

### 10. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 11. Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## Verification

### Check Installation

1. **Admin Dashboard**: Visit `http://localhost:8000/admin/`
   - Login with superuser credentials
   - Verify all models are visible

2. **API Endpoints**: Test endpoints using curl or Postman
   ```bash
   curl http://localhost:8000/bursary/deadline/
   ```

3. **Database**: Verify tables were created
   ```sql
   \dt  -- in PostgreSQL shell
   ```

## Configuration Files

### Environment Variables (Optional)

Create a `.env` file in the project root:

```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_NAME=bursary
DATABASE_USER=bursary_user
DATABASE_PASSWORD=your_secure_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

Then update `settings.py` to use these variables:

```python
from decouple import config

DEBUG = config('DEBUG', default=True, cast=bool)
SECRET_KEY = config('SECRET_KEY')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST'),
        'PORT': config('DATABASE_PORT'),
    }
}
```

## Troubleshooting

### Issue: PostgreSQL Connection Error

**Solution:**
1. Verify PostgreSQL is running
2. Check database credentials
3. Ensure database exists
4. Test connection:
   ```bash
   psql -U bursary_user -d bursary -h localhost
   ```

### Issue: Migration Errors

**Solution:**
```bash
python manage.py migrate --fake-initial
python manage.py migrate
```

### Issue: Email Not Sending

**Solution:**
1. Check email credentials
2. For Gmail, enable "Less secure app access" or use app-specific password
3. Test email configuration:
   ```bash
   python manage.py shell
   from django.core.mail import send_mail
   send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
   ```

### Issue: Static Files Not Loading

**Solution:**
```bash
python manage.py collectstatic --clear --noinput
```

### Issue: Permission Denied on Media Files

**Solution:**
```bash
chmod -R 755 media/
chmod -R 755 uploads/
```

## Production Deployment

### Security Checklist

- [ ] Set `DEBUG = False`
- [ ] Update `ALLOWED_HOSTS` with your domain
- [ ] Use environment variables for sensitive data
- [ ] Set strong `SECRET_KEY`
- [ ] Configure HTTPS/SSL
- [ ] Set up proper logging
- [ ] Configure database backups
- [ ] Set up monitoring and alerts
- [ ] Use a production WSGI server (Gunicorn, uWSGI)
- [ ] Use a reverse proxy (Nginx, Apache)

### Production Settings

```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
}
```

### Using Gunicorn

```bash
pip install gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

### Using Nginx

Create `/etc/nginx/sites-available/bursary`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/project/staticfiles/;
    }

    location /media/ {
        alias /path/to/project/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Database Backup

### Backup PostgreSQL Database

```bash
pg_dump -U bursary_user -d bursary > backup.sql
```

### Restore PostgreSQL Database

```bash
psql -U bursary_user -d bursary < backup.sql
```

## Regular Maintenance

### Clear Old Sessions

```bash
python manage.py clearsessions
```

### Check System Health

```bash
python manage.py check
```

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

## Support

For setup issues, contact the development team or refer to Django documentation at https://docs.djangoproject.com/
