from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Sum
from django.template.response import TemplateResponse
from django.urls import path
from .models import BursaryApplication
import csv

# =============================
# Export Selected Applications
# =============================
def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bursary_applications.csv"'
    writer = csv.writer(response)

    # Headers
    writer.writerow([
        'Reference Number', 'Full Name', 'Gender', 'Disability', 'ID Number',
        'Phone Number', 'Guardian Phone', 'Guardian ID', 'Ward', 'Village',
        'Chief Name', 'Chief Phone', 'Sub Chief Name', 'Sub Chief Phone',
        'Level of Study', 'Institution Type', 'Institution Name', 'Admission Number',
        'Amount', 'Mode of Study', 'Year of Study', 'Family Status',
        'Father Income', 'Mother Income', 'Status', 'Submitted At'
    ])

    # Data
    for obj in queryset:
        writer.writerow([
            obj.reference_number,
            obj.full_name,
            obj.gender,
            'Yes' if obj.disability else 'No',
            obj.id_number,
            obj.phone_number,
            obj.guardian_phone,
            obj.guardian_id,
            obj.ward,
            obj.village,
            obj.chief_name,
            obj.chief_phone,
            obj.sub_chief_name,
            obj.sub_chief_phone,
            obj.level_of_study,
            obj.institution_type,
            obj.institution_name,
            obj.admission_number,
            obj.amount,
            obj.mode_of_study,
            obj.year_of_study,
            obj.family_status,
            obj.father_income or 'N/A',
            obj.mother_income or 'N/A',
            obj.status,
            obj.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    return response

export_to_csv.short_description = "Export selected applications to CSV"

# =============================
# Bulk Actions
# =============================
@admin.action(description="Mark selected applications as Approved")
def mark_approved(modeladmin, request, queryset):
    queryset.update(status="approved")

@admin.action(description="Mark selected applications as Rejected")
def mark_rejected(modeladmin, request, queryset):
    queryset.update(status="rejected")

# =============================
# Bursary Application Admin
# =============================
@admin.register(BursaryApplication)
class BursaryApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "id_number",
        "ward",
        "institution_name",
        "amount",
        "status",
        "reference_number",
        "submitted_at",
    )
    search_fields = ("full_name", "id_number", "reference_number", "institution_name")
    list_filter = ("ward", "level_of_study", "institution_type", "family_status", "status")
    readonly_fields = ("reference_number", "submitted_at")
    actions = [export_to_csv, mark_approved, mark_rejected]

# =============================
# Custom Admin Dashboard
# =============================
def custom_admin_dashboard(request):
    total_apps = BursaryApplication.objects.count()
    total_amount = BursaryApplication.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_institutions = BursaryApplication.objects.values('institution_name').distinct().count()
    latest_app = BursaryApplication.objects.order_by('-submitted_at').first()
    pending_count = BursaryApplication.objects.filter(status="pending").count()
    approved_count = BursaryApplication.objects.filter(status="approved").count()
    rejected_count = BursaryApplication.objects.filter(status="rejected").count()

    context = {
        **admin.site.each_context(request),
        'title': 'Masinga NG-CDF Admin Dashboard',
        'total_apps': total_apps,
        'total_amount': total_amount,
        'total_institutions': total_institutions,
        'latest_submission': latest_app.submitted_at if latest_app else None,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    return TemplateResponse(request, "admin/index.html", context)

# =============================
# Override Django Admin Homepage
# =============================
admin.site.index_template = "admin/index.html"

original_get_urls = admin.site.get_urls
def new_get_urls():
    urls = original_get_urls()
    custom_urls = [path('', custom_admin_dashboard, name='admin-dashboard')]
    return custom_urls + urls
admin.site.get_urls = new_get_urls
