# Masinga NG-CDF Bursary Management System

A comprehensive Django-based REST API and Admin Dashboard for managing bursary applications for the Masinga Constituency Development Fund (NG-CDF).

## 🚀 Features

### Core Features
- **Application Management**: Submit, track, and manage bursary applications
- **Admin Dashboard**: Comprehensive statistics and analytics
- **Audit Logging**: Complete history of all status changes
- **Email Notifications**: Automatic email updates for applicants
- **Deadline Management**: Set and manage application deadlines
- **Bulk Actions**: Approve/reject multiple applications at once
- **CSV Export**: Export application data for reporting

### Advanced Features
- **Pagination**: Efficient handling of large datasets
- **Advanced Filtering**: Filter by ward, institution type, family status, etc.
- **Search Functionality**: Search by name, ID, reference number, institution
- **Sorting**: Sort by submission date, amount, status
- **Permission Management**: Role-based access control (admin vs. staff)
- **Status Tracking**: Real-time application status updates
- **Granular Permissions**: Different permission levels for different user roles

## 📋 Requirements

```
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-filter==23.5
psycopg2-binary==2.9.9
python-decouple==3.8
Pillow==10.1.0
```

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Server
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Database
Update `core/settings.py` with your PostgreSQL credentials:
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

### 5. Configure Email
Update email settings in `core/settings.py`:
```python
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'Your Name <your-email@gmail.com>'
```

### 6. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser
```bash
python manage.py createsuperuser
```

### 8. Run Development Server
```bash
python manage.py runserver
```

## 📚 API Endpoints

### Application Submission
- **POST** `/bursary/apply/` - Submit new application
  - **Permission**: Public (AllowAny)
  - **Response**: Application details with reference number

### Application Retrieval
- **GET** `/bursary/applications/` - List all applications (paginated)
  - **Permission**: Admin only
  - **Query Parameters**:
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 20, max: 100)
    - `ward`: Filter by ward
    - `status`: Filter by status (pending, approved, rejected)
    - `level_of_study`: Filter by level
    - `institution_type`: Filter by type
    - `family_status`: Filter by family status
    - `search`: Search by name, ID, reference number, institution
    - `ordering`: Sort by field (submitted_at, amount, status)

- **GET** `/bursary/applications/<reference_number>/` - Get specific application
  - **Permission**: Authenticated or Read-only
  - **Response**: Complete application details with status history

### Status Management
- **PUT** `/bursary/applications/<reference_number>/update-status/` - Update application status
  - **Permission**: Admin only
  - **Request Body**:
    ```json
    {
      "status": "approved",
      "reason": "Meets all criteria"
    }
    ```
  - **Response**: Status update confirmation

- **GET** `/bursary/applications/<reference_number>/history/` - Get status change history
  - **Permission**: Admin only
  - **Response**: Complete audit log of all status changes

### Deadline Management
- **GET** `/bursary/deadline/` - Get current deadline status
  - **Permission**: Public (AllowAny)
  - **Response**: Deadline information and days remaining

### Authentication
- **POST** `/bursary/logout/` - Logout user
  - **Permission**: Authenticated
  - **Response**: Redirect to login

## 🎯 Admin Dashboard

Access the admin dashboard at `/admin/`

### Features
- **Statistics Dashboard**: Total applications, total amount, institutions, approval rate
- **Ward-wise Breakdown**: Applications and amounts by ward
- **Institution-wise Breakdown**: Top 10 institutions by application count
- **Status Overview**: Pending, approved, rejected counts
- **Deadline Status**: Current deadline information
- **Bulk Actions**: Approve/reject multiple applications
- **CSV Export**: Export filtered data
- **Audit Logs**: View all status changes with user information

## 📊 Models

### BursaryApplication
Main model for storing application data with fields for:
- Personal information (name, gender, disability, ID)
- Contact details (phone, guardian info)
- Residence details (ward, village, chief info)
- Institution details (type, name, admission info, amount)
- Family status (orphan status, parental income)
- File uploads (ID documents, admission letters, death certificates)
- Status tracking (pending, approved, rejected)

### ApplicationStatusLog
Audit log model tracking:
- Old and new status
- User who made the change
- Reason for change
- Timestamp of change

### ApplicationDeadline
Deadline management model with:
- Start and end dates
- Active/inactive status
- Properties for checking if deadline is open
- Days remaining calculation

## 🔐 Permissions

### Public Access
- Submit applications
- Check deadline status
- Retrieve own application by reference number

### Admin Access
- View all applications
- Filter and search applications
- Update application status
- View audit logs
- Manage deadlines
- Export data
- Bulk actions

### Staff Access
- View applications (read-only)
- View audit logs

## 📧 Email Notifications

The system automatically sends emails for:
1. **Application Submission**: Confirmation with reference number
2. **Status Updates**: Approval or rejection notifications
3. **Bulk Actions**: Status change notifications

## 🔍 Filtering Examples

### Filter by Ward
```
GET /bursary/applications/?ward=kivaa
```

### Filter by Status
```
GET /bursary/applications/?status=pending
```

### Search by Name
```
GET /bursary/applications/?search=John
```

### Combine Filters
```
GET /bursary/applications/?ward=masinga-central&status=approved&search=University
```

### Pagination
```
GET /bursary/applications/?page=2&page_size=50
```

## 📈 Analytics

The admin dashboard provides:
- Total applications count
- Total amount requested
- Number of institutions
- Approval rate percentage
- Ward-wise distribution
- Institution-wise distribution
- Status breakdown (pending, approved, rejected)

## 🛠️ Management Commands

### Create Application Deadline
```bash
python manage.py shell
>>> from bursary.models import ApplicationDeadline
>>> from datetime import datetime, timedelta
>>> deadline = ApplicationDeadline.objects.create(
...     name="2024 Bursary Round 1",
...     start_date=datetime.now(),
...     end_date=datetime.now() + timedelta(days=30),
...     is_active=True
... )
```

## 🐛 Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running
- Check database credentials in settings.py
- Verify database exists

### Email Not Sending
- Check email credentials
- Enable "Less secure app access" for Gmail
- Use app-specific password for Gmail
- Check EMAIL_BACKEND setting

### Migration Errors
```bash
python manage.py migrate --fake-initial
python manage.py migrate
```

## 📝 API Response Examples

### Successful Application Submission
```json
{
  "id": 1,
  "reference_number": "MNG-A1B2C3D4",
  "full_name": "John Doe",
  "status": "pending",
  "submitted_at": "2024-01-15T10:30:00Z",
  "amount": 50000
}
```

### Status Update Response
```json
{
  "message": "Application status updated from pending to approved",
  "reference_number": "MNG-A1B2C3D4",
  "new_status": "approved"
}
```

### Status History Response
```json
{
  "reference_number": "MNG-A1B2C3D4",
  "current_status": "approved",
  "history": [
    {
      "old_status": "pending",
      "new_status": "approved",
      "changed_by": "admin_user",
      "reason": "Meets all criteria",
      "changed_at": "2024-01-16T14:20:00Z"
    }
  ]
}
```

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG = False` in settings.py
- [ ] Update `ALLOWED_HOSTS` with your domain
- [ ] Use environment variables for sensitive data
- [ ] Configure proper email backend
- [ ] Set up HTTPS
- [ ] Configure static files serving
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Set up monitoring

## 📞 Support

For issues or questions, contact the development team.

## 📄 License

This project is proprietary and confidential.

## 🔄 Version History

### v2.0.0 (Current)
- Added audit logging for status changes
- Implemented deadline management
- Added email notifications
- Implemented pagination and advanced filtering
- Added granular permissions
- Enhanced admin dashboard with analytics

### v1.0.0
- Initial release with basic CRUD operations
- Admin dashboard
- CSV export functionality
