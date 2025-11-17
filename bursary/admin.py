"""
Enhanced Admin with all features:
- CSV Export
- Bulk Email
- SMS Notifications  
- Duplicate Detection
- Status Management
"""

import logging
from urllib import request
from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Sum, Count
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from django.contrib import messages

import importlib
import csv

logger = logging.getLogger(__name__)

from .models import BursaryApplication, ApplicationStatusLog, ApplicationDeadline
from .bulk_email import (
    send_bulk_email_action,
    send_deadline_reminder_action,
    bulk_email_form_view
)
from .sms_service import NotificationManager

# =============================
# Duplicate Detection Fallback
# =============================
try:
    dup_module = importlib.import_module('.duplicate_detection', package=__package__)
    find_all_duplicates = getattr(dup_module, 'find_all_duplicates')
except Exception:
    def find_all_duplicates(modeladmin, request, queryset):
        messages.warning(request, "Duplicate detection feature is unavailable.")
    find_all_duplicates.short_description = "Find duplicate applications (unavailable)"

# =============================
# CSV Export Action
# =============================
def export_to_csv(modeladmin, request, queryset):
    """Export selected applications to CSV - Optimized for large datasets"""
    import io

    # Use StringIO for better memory handling with large datasets
    output = io.StringIO()
    writer = csv.writer(output)

    # CSV Headers
    headers = [
        'Reference Number', 'Full Name', 'Gender', 'Disability', 'ID Number',
        'Phone Number', 'Guardian Phone', 'Guardian ID', 'Ward', 'Village',
        'Chief Name', 'Chief Phone', 'Sub Chief Name', 'Sub Chief Phone',
        'Level of Study', 'Institution Type', 'Institution Name', 'Admission Number',
        'Amount', 'Mode of Study', 'Year of Study', 'Family Status',
        'Father Income', 'Mother Income', 'Status', 'Submitted At',
        'Email', 'Confirmation', 'Data Consent', 'Communication Consent'
    ]
    writer.writerow(headers)

    # Process in batches for large datasets (e.g., 6000+ records)
    batch_size = 1000
    total_processed = 0

    for start in range(0, queryset.count(), batch_size):
        end = start + batch_size
        batch = queryset[start:end]

        for obj in batch:
            submitted = obj.submitted_at
            if submitted:
                submitted = timezone.localtime(submitted) if timezone.is_aware(submitted) else submitted
                submitted_str = submitted.strftime('%Y-%m-%d %H:%M:%S')
            else:
                submitted_str = ''

            writer.writerow([
                obj.reference_number or '',
                obj.full_name or '',
                obj.gender or '',
                'Yes' if getattr(obj, 'disability', False) else 'No',
                obj.id_number or '',
                obj.phone_number or '',
                obj.guardian_phone or '',
                getattr(obj, 'guardian_id', '') or '',
                obj.ward or '',
                obj.village or '',
                getattr(obj, 'chief_name', '') or '',
                getattr(obj, 'chief_phone', '') or '',
                getattr(obj, 'sub_chief_name', '') or '',
                getattr(obj, 'sub_chief_phone', '') or '',
                getattr(obj, 'level_of_study', '') or '',
                getattr(obj, 'institution_type', '') or '',
                obj.institution_name or '',
                getattr(obj, 'admission_number', '') or '',
                obj.amount if obj.amount is not None else '',
                getattr(obj, 'mode_of_study', '') or '',
                getattr(obj, 'year_of_study', '') or '',
                getattr(obj, 'family_status', '') or '',
                getattr(obj, 'father_income', '') or '',
                getattr(obj, 'mother_income', '') or '',
                obj.status or '',
                submitted_str,
                obj.email or '',
                'Yes' if getattr(obj, 'confirmation', False) else 'No',
                'Yes' if getattr(obj, 'confirmation', False) else 'No',
                'Yes' if getattr(obj, 'confirmation', False) else 'No'
            ])

        total_processed += len(batch)
        # Optional: Add progress logging for very large exports
        if total_processed % 5000 == 0:
            print(f"Processed {total_processed} records...")

    # Create HTTP response
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="bursary_applications_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    return response

export_to_csv.short_description = "Export selected to CSV (Optimized for 6000+ records)"

# =============================
# Bulk Status Actions
# =============================
def _bulk_status_change(request, queryset, status):
    """Internal helper to update status and notify"""
    notification_manager = NotificationManager()
    count = 0

    for app in queryset.filter(status='pending'):
        old_status = app.status
        app.status = status
        app.save()

        # Log status change
        ApplicationStatusLog.objects.create(
            application=app,
            old_status=old_status,
            new_status=status,
            changed_by=request.user,
            reason=f"Bulk {status}"
        )

        # Send notifications
        try:
            notification_manager.notify_status_change(app, status)
            count += 1
        except Exception as e:
            messages.warning(request, f"Failed to notify {app.full_name}: {str(e)}")

    messages.success(request, f"{count} applications {status} and notified")

@admin.action(description="Approve selected applications")
def mark_approved(modeladmin, request, queryset):
    _bulk_status_change(request, queryset, "approved")

@admin.action(description="Reject selected applications")
def mark_rejected(modeladmin, request, queryset):
    _bulk_status_change(request, queryset, "rejected")

# =============================
# Inline Admin for Status Logs
# =============================
class ApplicationStatusLogInline(admin.TabularInline):
    model = ApplicationStatusLog
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'reason', 'changed_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

# =============================
# Bursary Application Admin
# =============================
# ✅ Add this action function ABOVE the BursaryApplicationAdmin class

@admin.action(description="Force delete selected applications (Cannot be undone)")
def force_delete_applications(modeladmin, request, queryset):
    queryset.delete()


@admin.register(BursaryApplication)
class BursaryApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "full_name", "id_number", "email", "ward", "institution_name",
        "amount", "status_badge", "reference_number", "submitted_at"
    )
    search_fields = ("full_name", "id_number", "email", "reference_number", "institution_name")
    list_filter = ("ward", "level_of_study", "institution_type", "family_status", "status", "submitted_at", "disability")
    readonly_fields = ("reference_number", "submitted_at", "status_history")
    list_per_page = 100  # Show more items per page for bulk operations

    actions = [
        export_to_csv,
        mark_approved,
        mark_rejected,
        send_bulk_email_action,
        send_deadline_reminder_action,
        find_all_duplicates,
        force_delete_applications,  # ✅ now properly defined and working
    ]

    def get_actions(self, request):
        """Override to add export all action"""
        actions = super().get_actions(request)
        actions['export_all_to_csv'] = (self.export_all_to_csv, 'export_all_to_csv', 'Export ALL applications to CSV')
        return actions

    def export_all_to_csv(self, request, queryset):
        """Export ALL applications to CSV, not just selected ones"""
        from django.db.models import Q
        all_queryset = self.model.objects.all().order_by('-submitted_at')
        return export_to_csv(self, request, all_queryset)
    export_all_to_csv.short_description = "Export ALL applications to CSV (6000+ records)"

    inlines = [ApplicationStatusLogInline]

    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'gender', 'disability', 'id_number', 'id_upload_front', 'id_upload_back')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number', 'guardian_phone', 'guardian_id')
        }),
        ('Residence Details', {
            'fields': ('ward', 'village', 'chief_name', 'chief_phone', 'sub_chief_name', 'sub_chief_phone')
        }),
        ('Institution Details', {
            'fields': ('level_of_study', 'institution_type', 'institution_name', 'admission_number', 'amount', 'mode_of_study', 'year_of_study', 'admission_letter')
        }),
        ('Family Details', {
            'fields': ('family_status', 'father_income', 'mother_income', 'father_death_certificate', 'mother_death_certificate')
        }),
        ('Application Status', {
            'fields': ('status', 'reference_number', 'submitted_at', 'confirmation', 'status_history')
        }),
    )

    def status_badge(self, obj):
        colors = {'pending': '#FFA500', 'approved': '#008000', 'rejected': '#FF0000'}
        color = colors.get(obj.status, '#808080')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def status_history(self, obj):
        logs = ApplicationStatusLog.objects.filter(application=obj).order_by('-changed_at')
        if not logs:
            return "No status changes yet"
        items_html = []
        for log in logs:
            changed_by = log.changed_by.username if log.changed_by else 'System'
            ts = timezone.localtime(log.changed_at) if timezone.is_aware(log.changed_at) else log.changed_at
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else ''
            items_html.append(format_html(
                '<li>{} - {} → {} (by {})</li>',
                ts_str,
                log.old_status or "N/A",
                log.new_status,
                changed_by
            ))
        return format_html('<ul style="margin:0;padding-left:20px;">{}</ul>', format_html(''.join(items_html)))
    status_history.short_description = 'Status History'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [path('bulk-email/', self.admin_site.admin_view(bulk_email_form_view), name='bulk_email_form')]
        return custom_urls + urls

# =============================
# Application Deadline Admin
# =============================
@admin.register(ApplicationDeadline)
class ApplicationDeadlineAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active', 'is_open_badge', 'days_remaining')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Deadline Information', {'fields': ('name', 'start_date', 'end_date', 'is_active')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def is_open_badge(self, obj):
        if obj.is_open:
            return format_html('<span style="background-color:#008000;color:white;padding:5px 12px;border-radius:4px;">OPEN</span>')
        return format_html('<span style="background-color:#FF0000;color:white;padding:5px 12px;border-radius:4px;">CLOSED</span>')
    is_open_badge.short_description = 'Status'

    def days_remaining(self, obj):
        return f"{obj.days_remaining} days" if obj.is_open else "Expired"
    days_remaining.short_description = 'Days Remaining'

# =============================
# Application Status Log Admin
# =============================
@admin.register(ApplicationStatusLog)
class ApplicationStatusLogAdmin(admin.ModelAdmin):
    list_display = ('application', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('new_status', 'changed_at', 'changed_by')
    search_fields = ('application__reference_number', 'application__full_name')
    readonly_fields = ('application', 'old_status', 'new_status', 'changed_by', 'reason', 'changed_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


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

    ward_stats = BursaryApplication.objects.values('ward').annotate(
        count=Count('id'), total_amount=Sum('amount')
    ).order_by('-count')

    active_deadline = ApplicationDeadline.objects.filter(is_active=True).first()

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
        'ward_stats': ward_stats,
        'active_deadline': active_deadline,
        'approval_rate': round((approved_count / total_apps * 100), 2) if total_apps > 0 else 0,
    }
    return TemplateResponse(request, "admin/index.html", context)

# Override default admin dashboard
admin.site.index_template = "admin/index.html"
_original_get_urls = admin.site.get_urls
def _new_get_urls():
    urls = _original_get_urls()
    custom_urls = [path('', custom_admin_dashboard, name='admin-dashboard')]
    return custom_urls + urls
admin.site.get_urls = _new_get_urls
