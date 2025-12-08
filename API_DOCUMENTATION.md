# Bursary Management System - API Documentation

## Base URL
```
http://localhost:8000/bursary/
```

## Authentication
- Session-based authentication for admin endpoints
- Public endpoints require no authentication
- Include session cookies for authenticated requests

## Response Format
All responses are in JSON format.

---

## 1. Submit Bursary Application

### Endpoint
```
POST /bursary/apply/
```

### Permission
Public (AllowAny)

### Request Body
```json
{
  "full_name": "John Doe",
  "gender": "male",
  "disability": false,
  "id_number": "12345678",
  "id_upload_front": "<file>",
  "id_upload_back": "<file>",
  "phone_number": "0712345678",
  "guardian_phone": "0712345679",
  "guardian_id": "87654321",
  "ward": "kivaa",
  "village": "Sample Village",
  "chief_name": "Chief Name",
  "chief_phone": "0712345680",
  "sub_chief_name": "Sub Chief Name",
  "sub_chief_phone": "0712345681",
  "level_of_study": "degree",
  "institution_type": "university",
  "institution_name": "University of Nairobi",
  "admission_number": "ADM001",
  "amount": 50000,
  "mode_of_study": "full-time",
  "year_of_study": "first-year",
  "admission_letter": "<file>",
  "family_status": "both-parents-alive",
  "father_income": "low",
  "mother_income": "medium",
  "confirmation": true
}
```

### Response (201 Created)
```json
{
  "id": 1,
  "full_name": "John Doe",
  "gender": "male",
  "disability": false,
  "id_number": "12345678",
  "phone_number": "0712345678",
  "guardian_phone": "0712345679",
  "guardian_id": "87654321",
  "ward": "kivaa",
  "village": "Sample Village",
  "chief_name": "Chief Name",
  "chief_phone": "0712345680",
  "sub_chief_name": "Sub Chief Name",
  "sub_chief_phone": "0712345681",
  "level_of_study": "degree",
  "institution_type": "university",
  "institution_name": "University of Nairobi",
  "admission_number": "ADM001",
  "amount": 50000,
  "mode_of_study": "full-time",
  "year_of_study": "first-year",
  "family_status": "both-parents-alive",
  "father_income": "low",
  "mother_income": "medium",
  "confirmation": true,
  "reference_number": "MNG-A1B2C3D4",
  "submitted_at": "2024-01-15T10:30:00Z",
  "status": "pending",
  "status_logs": []
}
```

### Error Response (400 Bad Request)
```json
{
  "field_name": ["Error message"]
}
```

---

## 2. List All Applications

### Endpoint
```
GET /bursary/applications/
```

### Permission
Admin only (IsAdminUser)

### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| page | integer | Page number | ?page=1 |
| page_size | integer | Items per page (max 100) | ?page_size=20 |
| ward | string | Filter by ward | ?ward=kivaa |
| status | string | Filter by status | ?status=pending |
| level_of_study | string | Filter by level | ?level_of_study=degree |
| institution_type | string | Filter by type | ?institution_type=university |
| family_status | string | Filter by family status | ?family_status=both-parents-alive |
| search | string | Search by name, ID, ref, institution | ?search=John |
| ordering | string | Sort field | ?ordering=-submitted_at |

### Valid Filter Values

**Ward:**
- kivaa
- masinga-central
- ndithini
- ekalakala
- muthesya

**Status:**
- pending
- approved
- rejected

**Level of Study:**
- degree
- certificate
- diploma
- artisan

**Institution Type:**
- college
- university

**Family Status:**
- both-parents-alive
- single-parent
- partial-orphan
- total-orphan

**Ordering Fields:**
- submitted_at (default: -submitted_at)
- amount
- status

### Response (200 OK)
```json
{
  "count": 150,
  "next": "http://localhost:8000/bursary/applications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "full_name": "John Doe",
      "gender": "male",
      "disability": false,
      "id_number": "12345678",
      "phone_number": "0712345678",
      "guardian_phone": "0712345679",
      "guardian_id": "87654321",
      "ward": "kivaa",
      "village": "Sample Village",
      "chief_name": "Chief Name",
      "chief_phone": "0712345680",
      "sub_chief_name": "Sub Chief Name",
      "sub_chief_phone": "0712345681",
      "level_of_study": "degree",
      "institution_type": "university",
      "institution_name": "University of Nairobi",
      "admission_number": "ADM001",
      "amount": 50000,
      "mode_of_study": "full-time",
      "year_of_study": "first-year",
      "family_status": "both-parents-alive",
      "father_income": "low",
      "mother_income": "medium",
      "confirmation": true,
      "reference_number": "MNG-A1B2C3D4",
      "submitted_at": "2024-01-15T10:30:00Z",
      "status": "pending",
      "status_logs": []
    }
  ]
}
```

### Example Requests

**Get pending applications from Kivaa ward:**
```
GET /bursary/applications/?ward=kivaa&status=pending
```

**Search for applications from University of Nairobi:**
```
GET /bursary/applications/?search=University%20of%20Nairobi
```

**Get approved applications sorted by amount (highest first):**
```
GET /bursary/applications/?status=approved&ordering=-amount
```

---

## 3. Get Specific Application

### Endpoint
```
GET /bursary/applications/<reference_number>/
```

### Permission
Authenticated or Read-only

### URL Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| reference_number | string | Application reference number |

### Response (200 OK)
```json
{
  "id": 1,
  "full_name": "John Doe",
  "gender": "male",
  "disability": false,
  "id_number": "12345678",
  "phone_number": "0712345678",
  "guardian_phone": "0712345679",
  "guardian_id": "87654321",
  "ward": "kivaa",
  "village": "Sample Village",
  "chief_name": "Chief Name",
  "chief_phone": "0712345680",
  "sub_chief_name": "Sub Chief Name",
  "sub_chief_phone": "0712345681",
  "level_of_study": "degree",
  "institution_type": "university",
  "institution_name": "University of Nairobi",
  "admission_number": "ADM001",
  "amount": 50000,
  "mode_of_study": "full-time",
  "year_of_study": "first-year",
  "family_status": "both-parents-alive",
  "father_income": "low",
  "mother_income": "medium",
  "confirmation": true,
  "reference_number": "MNG-A1B2C3D4",
  "submitted_at": "2024-01-15T10:30:00Z",
  "status": "pending",
  "status_logs": []
}
```

### Error Response (404 Not Found)
```json
{
  "detail": "Not found."
}
```

---

## 4. Update Application Status

### Endpoint
```
PUT /bursary/applications/<reference_number>/update-status/
```

### Permission
Admin only (IsAdminUser)

### URL Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| reference_number | string | Application reference number |

### Request Body
```json
{
  "status": "approved",
  "reason": "Meets all criteria and has strong academic record"
}
```

### Response (200 OK)
```json
{
  "message": "Application status updated from pending to approved",
  "reference_number": "MNG-A1B2C3D4",
  "new_status": "approved"
}
```

### Error Response (400 Bad Request)
```json
{
  "error": "No status change"
}
```

### Error Response (404 Not Found)
```json
{
  "detail": "Not found."
}
```

---

## 5. Get Application Status History

### Endpoint
```
GET /bursary/applications/<reference_number>/history/
```

### Permission
Admin only (IsAdminUser)

### URL Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| reference_number | string | Application reference number |

### Response (200 OK)
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
    },
    {
      "old_status": null,
      "new_status": "pending",
      "changed_by": "System",
      "reason": null,
      "changed_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Error Response (404 Not Found)
```json
{
  "error": "Application not found"
}
```

---

## 6. Get Application Deadline Status

### Endpoint
```
GET /bursary/deadline/
```

### Permission
Public (AllowAny)

### Response (200 OK - Deadline Active)
```json
{
  "is_open": true,
  "name": "2024 Bursary Round 1",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-02-28T23:59:59Z",
  "days_remaining": 15
}
```

### Response (200 OK - No Active Deadline)
```json
{
  "is_open": false,
  "message": "No active application deadline"
}
```

---

## 7. Logout

### Endpoint
```
POST /bursary/logout/
```

### Permission
Authenticated

### Response (302 Redirect)
Redirects to admin login page

---

## Error Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | Resource not found |
| 500 | Server Error | Internal server error |

---

## Rate Limiting

Currently no rate limiting is implemented. For production, consider implementing:
- Per-user rate limits
- Per-IP rate limits
- Throttling for public endpoints

---

## Pagination

Default page size: 20 items
Maximum page size: 100 items

Example paginated response:
```json
{
  "count": 150,
  "next": "http://localhost:8000/bursary/applications/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Filtering Examples

### Example 1: Get all pending applications from Masinga Central ward
```
GET /bursary/applications/?ward=masinga-central&status=pending
```

### Example 2: Search for applications from a specific student
```
GET /bursary/applications/?search=John%20Doe
```

### Example 3: Get approved applications sorted by amount (highest first)
```
GET /bursary/applications/?status=approved&ordering=-amount
```

### Example 4: Get applications from universities, page 2, 50 per page
```
GET /bursary/applications/?institution_type=university&page=2&page_size=50
```

### Example 5: Get applications from orphans
```
GET /bursary/applications/?family_status=total-orphan
```

---

## Field Validation

### Required Fields
- full_name (max 255 chars)
- gender (male/female)
- id_number (max 50 chars, unique)
- id_upload_front (file)
- phone_number (max 15 chars)
- guardian_phone (max 15 chars)
- guardian_id (max 50 chars)
- ward (one of: kivaa, masinga-central, ndithini, ekalakala, muthesya)
- village (max 100 chars)
- chief_name (max 255 chars)
- chief_phone (max 15 chars)
- sub_chief_name (max 255 chars)
- sub_chief_phone (max 15 chars)
- level_of_study (degree/certificate/diploma/artisan)
- institution_type (college/university)
- institution_name (max 255 chars)
- admission_number (max 100 chars)
- amount (positive integer)
- mode_of_study (full-time/part-time)
- year_of_study (first-year/second-year/third-year/final-year)
- family_status (both-parents-alive/single-parent/partial-orphan/total-orphan)
- confirmation (boolean)

### Optional Fields
- disability (boolean, default: false)
- id_upload_back (file)
- admission_letter (file)
- father_death_certificate (file)
- mother_death_certificate (file)
- father_income (low/medium/high)
- mother_income (low/medium/high)

---

## Webhook Events (Future Implementation)

Planned webhook events:
- application.submitted
- application.status_changed
- application.approved
- application.rejected
- deadline.created
- deadline.updated

---

## Best Practices

1. **Always include pagination parameters** for list endpoints
2. **Use search instead of filtering** when possible for better performance
3. **Cache deadline status** on client side (updates rarely)
4. **Implement retry logic** for failed requests
5. **Use reference numbers** for tracking, not IDs
6. **Validate file uploads** on client side before submission
7. **Handle timezone conversions** for timestamps

---

## Support

For API issues or questions, contact the development team.
