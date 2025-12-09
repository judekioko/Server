# Admin URL Endpoint Fixes - Development vs Production

## Problem Identified

The admin URL endpoints were inconsistent between development and production environments:

1. **Production**: Used `secure-admin/` as the admin URL
2. **Development**: Also used `secure-admin/` (same as production)
3. **Issue**: In development, the standard Django admin URL should be `admin/` for easier access during development

## Root Causes

1. **Hardcoded ADMIN_URL**: The `ADMIN_URL` was hardcoded to `'secure-admin/'` in `settings.py` without environment-specific logic
2. **Missing local_settings override**: The `local_settings.py` didn't override the `ADMIN_URL` for development
3. **Inconsistent LOGIN URLs**: The `LOGIN_URL` and `LOGIN_REDIRECT_URL` were using the hardcoded value

## Solutions Implemented

### 1. Updated `core/settings.py`

Added environment-specific admin URL configuration:

```python
# ========================
#  ADMIN CONFIGURATION
# ========================
# Environment-specific admin URL configuration
if IS_PRODUCTION:
    ADMIN_URL = 'secure-admin/'
else:
    ADMIN_URL = 'admin/'
```

**Benefits:**
- Production uses `secure-admin/` for security through obscurity
- Development uses standard `admin/` for easier access
- Automatic detection based on environment

### 2. Updated `core/local_settings.py`

Added explicit admin URL override for development:

```python
# Admin URL for development (override production setting)
ADMIN_URL = 'admin/'

# Update login URLs for development
LOGIN_URL = f'/{ADMIN_URL}login/'
LOGIN_REDIRECT_URL = f'/{ADMIN_URL}'
```

**Benefits:**
- Ensures development always uses `admin/` URL
- Overrides any production settings
- Provides clear documentation of development settings

### 3. Enhanced `core/urls.py` (No changes needed)

The URL configuration already uses `settings.ADMIN_URL` dynamically:

```python
urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # ... other patterns
]
```

This means the admin URL will automatically adapt based on the environment.

## Environment Detection

The system uses `IS_PRODUCTION` flag to determine the environment:

```python
IS_PRODUCTION = os.environ.get('DJANGO_ENV') == 'production' or 'masingangcdf.org' in socket.gethostname()
IS_DEVELOPMENT = not IS_PRODUCTION
```

**Development triggers:**
- Running with `python manage.py runserver`
- `DJANGO_ENV` environment variable not set to 'production'
- Hostname doesn't contain 'masingangcdf.org'

**Production triggers:**
- `DJANGO_ENV=production` environment variable set
- Hostname contains 'masingangcdf.org'

## Admin URL Endpoints

### Development
- **Admin URL**: `http://localhost:8000/admin/`
- **Login URL**: `http://localhost:8000/admin/login/`
- **Redirect URL**: `http://localhost:8000/admin/`

### Production
- **Admin URL**: `https://masingangcdf.org/secure-admin/`
- **Login URL**: `https://masingangcdf.org/secure-admin/login/`
- **Redirect URL**: `https://masingangcdf.org/secure-admin/`

## Testing

To verify the fix works correctly:

### Development
```bash
python manage.py runserver
# Visit: http://localhost:8000/admin/
# Should show Django admin login
```

### Production
```bash
export DJANGO_ENV=production
python manage.py runserver
# Visit: https://masingangcdf.org/secure-admin/
# Should show Django admin login
```

## Additional Improvements

1. **Added Admin URL to environment info output**: The settings now print the admin URL when Django starts
2. **Consistent LOGIN_URL handling**: Both development and production now properly set login URLs
3. **Clear documentation**: Added comments explaining the environment-specific configuration

## Files Modified

1. `core/settings.py` - Added environment-specific ADMIN_URL configuration
2. `core/local_settings.py` - Added explicit admin URL override for development
3. `ADMIN_URL_FIX.md` - This documentation file

## Backward Compatibility

- Existing production deployments will continue to use `secure-admin/`
- Development environments will now use the standard `admin/` URL
- No breaking changes to the API or other endpoints
