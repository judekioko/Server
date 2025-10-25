# Testing Guide - Masinga NG-CDF Bursary Management System

## Testing Overview

This guide covers manual testing, API testing, and automated testing for the bursary management system.

## Manual Testing

### 1. Admin Dashboard Testing

#### Test Case 1: Admin Login
1. Navigate to `http://localhost:8000/admin/`
2. Enter superuser credentials
3. **Expected**: Dashboard loads with statistics

#### Test Case 2: View Applications
1. Click on "Bursary Applications" in admin
2. **Expected**: List of all applications with filters and search

#### Test Case 3: Filter Applications
1. Use ward filter dropdown
2. Select "Kivaa"
3. **Expected**: Only applications from Kivaa ward displayed

#### Test Case 4: Search Applications
1. Enter "John" in search box
2. **Expected**: Applications with "John" in name displayed

#### Test Case 5: Update Application Status
1. Click on an application
2. Change status to "Approved"
3. Click Save
4. **Expected**: Status updated, audit log created

#### Test Case 6: Export to CSV
1. Select multiple applications
2. Choose "Export selected applications to CSV"
3. Click Go
4. **Expected**: CSV file downloaded

### 2. API Testing

#### Using cURL

**Test Application Submission:**
```bash
curl -X POST http://localhost:8000/bursary/apply/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
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

**Test Get Deadline:**
```bash
curl http://localhost:8000/bursary/deadline/
```

#### Using Postman

1. **Create Collection**: "Bursary API"
2. **Create Requests**:
   - POST /bursary/apply/
   - GET /bursary/applications/
   - GET /bursary/applications/{ref_number}/
   - PUT /bursary/applications/{ref_number}/update-status/
   - GET /bursary/deadline/

3. **Test Each Endpoint**:
   - Verify response status codes
   - Check response structure
   - Validate data types

### 3. Email Testing

#### Test Email Configuration

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email',
    'This is a test email from the bursary system.',
    settings.DEFAULT_FROM_EMAIL,
    ['test@example.com'],
    fail_silently=False,
)
```

#### Test Application Submission Email

1. Submit a new application via API
2. Check email inbox for confirmation
3. **Expected**: Email received with reference number

#### Test Status Update Email

1. Update application status to "Approved"
2. Check email inbox
3. **Expected**: Status update email received

## Automated Testing

### Unit Tests

Create `bursary/tests.py`:

```python
from django.test import TestCase
from django.contrib.auth.models import User
from .models import BursaryApplication, ApplicationDeadline, ApplicationStatusLog
from datetime import datetime, timedelta

class BursaryApplicationModelTest(TestCase):
    def setUp(self):
        self.app = BursaryApplication.objects.create(
            full_name="Test User",
            gender="male",
            disability=False,
            id_number="12345678",
            phone_number="0712345678",
            guardian_phone="0712345679",
            guardian_id="87654321",
            ward="kivaa",
            village="Test Village",
            chief_name="Chief Test",
            chief_phone="0712345680",
            sub_chief_name="Sub Chief Test",
            sub_chief_phone="0712345681",
            level_of_study="degree",
            institution_type="university",
            institution_name="Test University",
            admission_number="ADM001",
            amount=50000,
            mode_of_study="full-time",
            year_of_study="first-year",
            family_status="both-parents-alive",
            confirmation=True
        )

    def test_reference_number_generated(self):
        """Test that reference number is generated on save"""
        self.assertIsNotNone(self.app.reference_number)
        self.assertTrue(self.app.reference_number.startswith("MNG-"))

    def test_application_string_representation(self):
        """Test string representation of application"""
        expected = f"{self.app.full_name} - {self.app.admission_number}"
        self.assertEqual(str(self.app), expected)

    def test_default_status_is_pending(self):
        """Test that default status is pending"""
        self.assertEqual(self.app.status, "pending")


class ApplicationDeadlineModelTest(TestCase):
    def setUp(self):
        self.deadline = ApplicationDeadline.objects.create(
            name="Test Deadline",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            is_active=True
        )

    def test_deadline_is_open(self):
        """Test that deadline is open"""
        self.assertTrue(self.deadline.is_open)

    def test_days_remaining(self):
        """Test days remaining calculation"""
        self.assertGreater(self.deadline.days_remaining, 0)

    def test_deadline_string_representation(self):
        """Test string representation of deadline"""
        self.assertIn("Test Deadline", str(self.deadline))


class ApplicationStatusLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.app = BursaryApplication.objects.create(
            full_name="Test User",
            gender="male",
            disability=False,
            id_number="12345678",
            phone_number="0712345678",
            guardian_phone="0712345679",
            guardian_id="87654321",
            ward="kivaa",
            village="Test Village",
            chief_name="Chief Test",
            chief_phone="0712345680",
            sub_chief_name="Sub Chief Test",
            sub_chief_phone="0712345681",
            level_of_study="degree",
            institution_type="university",
            institution_name="Test University",
            admission_number="ADM001",
            amount=50000,
            mode_of_study="full-time",
            year_of_study="first-year",
            family_status="both-parents-alive",
            confirmation=True
        )
        self.log = ApplicationStatusLog.objects.create(
            application=self.app,
            old_status="pending",
            new_status="approved",
            changed_by=self.user,
            reason="Test reason"
        )

    def test_status_log_creation(self):
        """Test status log creation"""
        self.assertEqual(self.log.old_status, "pending")
        self.assertEqual(self.log.new_status, "approved")

    def test_status_log_string_representation(self):
        """Test string representation of status log"""
        expected = f"{self.app.reference_number}: pending → approved"
        self.assertEqual(str(self.log), expected)
```

### API Tests

Create `bursary/test_api.py`:

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import BursaryApplication
import json

class BursaryApplicationAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

    def test_create_application(self):
        """Test creating a new application"""
        data = {
            "full_name": "Test User",
            "gender": "male",
            "disability": False,
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
            "confirmation": True
        }
        response = self.client.post(
            '/bursary/apply/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('reference_number', response.json())

    def test_list_applications_requires_auth(self):
        """Test that list endpoint requires authentication"""
        response = self.client.get('/bursary/applications/')
        self.assertEqual(response.status_code, 403)

    def test_list_applications_with_auth(self):
        """Test listing applications with authentication"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/bursary/applications/')
        self.assertEqual(response.status_code, 200)

    def test_get_deadline(self):
        """Test getting deadline status"""
        response = self.client.get('/bursary/deadline/')
        self.assertEqual(response.status_code, 200)
```

### Run Tests

```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test bursary.tests

# Run specific test class
python manage.py test bursary.tests.BursaryApplicationModelTest

# Run specific test method
python manage.py test bursary.tests.BursaryApplicationModelTest.test_reference_number_generated

# Run with verbose output
python manage.py test --verbosity=2

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## Performance Testing

### Load Testing with Locust

Create `locustfile.py`:

```python
from locust import HttpUser, task, between

class BursaryUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_deadline(self):
        self.client.get("/bursary/deadline/")

    @task
    def get_applications(self):
        self.client.get("/bursary/applications/")
```

Run load test:
```bash
pip install locust
locust -f locustfile.py --host=http://localhost:8000
```

## Security Testing

### SQL Injection Test

Try submitting:
```
' OR '1'='1
```

**Expected**: No SQL injection vulnerability

### XSS Test

Try submitting:
```
<script>alert('XSS')</script>
```

**Expected**: Script tags escaped or removed

### CSRF Protection Test

1. Submit form without CSRF token
2. **Expected**: 403 Forbidden error

## Browser Testing

### Test Browsers
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

### Test Cases
1. Admin dashboard loads correctly
2. Forms submit properly
3. Filters work as expected
4. Pagination works
5. File uploads work
6. Responsive design on mobile

## Checklist

- [ ] All unit tests pass
- [ ] All API tests pass
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] CSRF protection working
- [ ] Email notifications sending
- [ ] Pagination working
- [ ] Filtering working
- [ ] Search working
- [ ] Sorting working
- [ ] Admin dashboard displaying correctly
- [ ] CSV export working
- [ ] Status updates creating audit logs
- [ ] Deadline status endpoint working
- [ ] Performance acceptable under load

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_DB: bursary
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python manage.py test
```

## Support

For testing issues, contact the development team.
