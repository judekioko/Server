# Quick Start Guide - Masinga NG-CDF Bursary Management System

Get up and running in 5 minutes!

## Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Git

## Installation (5 minutes)

### 1. Clone & Setup (1 minute)
```bash
git clone <repository-url>
cd Server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies (1 minute)
```bash
pip install -r requirements.txt
```

### 3. Configure Database (1 minute)
Edit `core/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bursary',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 4. Run Migrations (1 minute)
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Start Server (1 minute)
```bash
python manage.py runserver
```

## Access the System

- **Admin Dashboard**: http://localhost:8000/admin/
- **API Base**: http://localhost:8000/bursary/

## First Steps

### 1. Login to Admin
- URL: http://localhost:8000/admin/
- Use superuser credentials created above

### 2. Create Application Deadline
```bash
python manage.py shell
```
```python
from bursary.models import ApplicationDeadline
from datetime import datetime, timedelta

ApplicationDeadline.objects.create(
    name="2024 Bursary Round 1",
    start_date=datetime.now(),
    end_date=datetime.now() + timedelta(days=30),
    is_active=True
)
exit()
```

### 3. Test API
```bash
# Get deadline status
curl http://localhost:8000/bursary/deadline/

# Submit application
curl -X POST http://localhost:8000/bursary/apply/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "gender": "male",
    "disability": false,
    "id_number": "12345678",
    "phone_number": "0712345678",
    "guardian_phone": "0712345679",
    "guardian_id": "87654321",
    "ward": "kivaa",
    "village": "Test Village",
    "chief_name": "Chief Test",
    "chief_phone": "0712345680",
    "sub_chief_name": "Sub Chief Test",
    "sub_chief_phone": "0712345681",
    "level_of_study": "degree",
    "institution_type": "university",
    "institution_name": "Test University",
    "admission_number": "ADM001",
    "amount": 50000,
    "mode_of_study": "full-time",
    "year_of_study": "first-year",
    "family_status": "both-parents-alive",
    "confirmation": true
  }'
```

## Key Features

### Admin Dashboard
- View all applications
- Filter by ward, status, institution type
- Search by name, ID, reference number
- Bulk approve/reject applications
- Export to CSV
- View audit logs

### API Endpoints
- `POST /bursary/apply/` - Submit application
- `GET /bursary/applications/` - List applications (admin)
- `GET /bursary/applications/<ref>/` - Get application
- `PUT /bursary/applications/<ref>/update-status/` - Update status
- `GET /bursary/applications/<ref>/history/` - View history
- `GET /bursary/deadline/` - Check deadline

## Common Tasks

### Filter Applications
```
GET /bursary/applications/?ward=kivaa&status=pending
```

### Search Applications
```
GET /bursary/applications/?search=John
```

### Update Application Status
```
PUT /bursary/applications/MNG-A1B2C3D4/update-status/
{
  "status": "approved",
  "reason": "Meets criteria"
}
```

### View Status History
```
GET /bursary/applications/MNG-A1B2C3D4/history/
```

## Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
psql -U postgres

# Verify credentials in settings.py
```

### Migration Error
```bash
python manage.py migrate --fake-initial
python manage.py migrate
```

### Email Not Sending
- Check email credentials in settings.py
- For Gmail, use app-specific password
- Enable "Less secure app access"

## Documentation

- **Full Setup**: See `SETUP_GUIDE.md`
- **API Reference**: See `API_DOCUMENTATION.md`
- **Testing**: See `TESTING_GUIDE.md`
- **Improvements**: See `IMPROVEMENTS_SUMMARY.md`

## Next Steps

1. **Configure Email** (optional)
   - Update email settings in `core/settings.py`
   - Test email sending

2. **Customize Admin**
   - Modify admin templates in `templates/admin/`
   - Add custom branding

3. **Deploy to Production**
   - Follow deployment section in `SETUP_GUIDE.md`
   - Use Gunicorn + Nginx
   - Set DEBUG = False

## Support

For issues, refer to:
- `SETUP_GUIDE.md` - Installation help
- `TESTING_GUIDE.md` - Testing procedures
- `API_DOCUMENTATION.md` - API reference

---

**You're all set! Start managing bursary applications now.** 🚀
