from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Sum, Count
from django.template.response import TemplateResponse
from django.urls import path
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.html import format_html

import csv
from datetime import datetime

from .models import BursaryApplication, ApplicationStatusLog, ApplicationDeadline


# =============================
# Export Selected Applications
# =============================
def export_to_csv(modeladmin, request, queryset):
    """
    Export selected BursaryApplication rows to CSV.
    Safe for None values, formats dates, and boolean fields.
    """
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
            obj.guardian_id or '',
            obj.ward or '',
            obj.village or '',
            obj.chief_name or '',
            obj.chief_phone or '',
            obj.sub_chief_name or '',
            obj.sub_chief_phone or '',
            obj.level_of_study or '',
            obj.institution_type or '',
            obj.institution_name or '',
            obj.admission_number or '',
            obj.amount if obj.amount is not None else '',
            obj.mode_of_study or '',
            obj.year_of_study or '',
            obj.family_status or '',
            obj.father_income if obj.father_income is not None else '',
            obj.mother_income if obj.mother_income is not None else '',
            obj.status or '',
            submitted_str
        ])
    return response

export_to_csv.short_description = "Export selected applications to CSV"


# =============================
# Bulk Actions with Email Notifications
# =============================
def _get_application_recipient_email(application) -> str | None:
    """
    Determine the correct recipient email from the application.
    Adjust field names if your model differs.
    """
    # Try common field names; adjust this to your model
    for field in ('email', 'applicant_email', 'guardian_email'):
        if hasattr(application, field):
            value = getattr(application, field)
            if value:
                return value
    return None


@admin.action(description="Mark selected applications as Approved")
def mark_approved(modeladmin, request, queryset):
    count = queryset.count()
    for app in queryset:
        old_status = app.status
        app.status = "approved"
        app.save()

        # Create audit log
        ApplicationStatusLog.objects.create(
            application=app,
            old_status=old_status,
            new_status="approved",
            changed_by=request.user,
            reason="Bulk approval action"
        )

        # Send email notification
        send_approval_email(app)

    modeladmin.message_user(request, f"{count} applications marked as approved.")


@admin.action(description="Mark selected applications as Rejected")
def mark_rejected(modeladmin, request, queryset):
    count = queryset.count()
    for app in queryset:
        old_status = app.status
        app.status = "rejected"
        app.save()

        # Create audit log
        ApplicationStatusLog.objects.create(
            application=app,
            old_status=old_status,
            new_status="rejected",
            changed_by=request.user,
            reason="Bulk rejection action"
        )

        # Send email notification
        send_rejection_email(app)

    modeladmin.message_user(request, f"{count} applications marked as rejected.")


# =============================
# Email Notification Functions
# =============================
def send_approval_email(application):
    """Send approval notification email to the applicant if email is present."""
    try:
        recipient = _get_application_recipient_email(application)
        if not recipient:
            return  # No email on record; skip sending

        approved_amount = f"KSh {application.amount:,}" if application.amount is not None else "N/A"

        subject = f"Bursary Application Approved - {application.reference_number}"
        message = f"""
Dear {application.full_name},

Congratulations! Your bursary application has been APPROVED.

Reference Number: {application.reference_number}
Institution: {application.institution_name}
Approved Amount: {approved_amount}

Please contact the Masinga NG-CDF office for further instructions on fund disbursement.

Best regards,
Masinga NG-CDF Bursary Management System
        """.strip()

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=True,
        )
    except Exception as e:
        # Log to console; for production integrate with logging
        print(f"Error sending approval email: {e}")


def send_rejection_email(application):
    """Send rejection notification email to the applicant if email is present."""
    try:
        recipient = _get_application_recipient_email(application)
        if not recipient:
            return  # No email on record; skip sending

        subject = f"Bursary Application Status - {application.reference_number}"
        message = f"""
Dear {application.full_name},

Thank you for your bursary application. Unfortunately, your application has not been approved at this time.

Reference Number: {application.reference_number}
Institution: {application.institution_name}

For more information or to appeal this decision, please contact the Masinga NG-CDF office.

Best regards,
Masinga NG-CDF Bursary Management System
        """.strip()

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error sending rejection email: {e}")


# =============================
# Inline Admin for Status Logs
# =============================

class ApplicationStatusLogInline(admin.TabularInline):
    model = ApplicationStatusLog
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False


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
        "status_badge",
        "reference_number",
        "submitted_at",
    )
    search_fields = ("full_name", "id_number", "reference_number", "institution_name")
    list_filter = ("ward", "level_of_study", "institution_type", "family_status", "status", "submitted_at")
    readonly_fields = ("reference_number", "submitted_at", "status_history")
    actions = [export_to_csv, mark_approved, mark_rejected]
    inlines = [ApplicationStatusLogInline]

    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'gender', 'disability', 'id_number', 'id_upload_front', 'id_upload_back')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'guardian_phone', 'guardian_id')
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
        """Display status with color coding safely."""
        colors = {
            'pending': '#FFA500',
            'approved': '#008000',
            'rejected': '#FF0000'
        }
        color = colors.get(obj.status, '#808080')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            getattr(obj, 'get_status_display', lambda: obj.status)()
        )
    status_badge.short_description = 'Status'

    def status_history(self, obj):
        """Display status change history safely as HTML."""
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
        return format_html('<ul style="margin: 0; padding-left: 20px;">{}</ul>', format_html(''.join(items_html)))
    status_history.short_description = 'Status Change History'


# =============================
# Application Deadline Admin
# =============================
@admin.register(ApplicationDeadline)
class ApplicationDeadlineAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active', 'is_open_badge', 'days_remaining')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Deadline Information', {
            'fields': ('name', 'start_date', 'end_date', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_open_badge(self, obj):
        """Display if deadline is currently open with safe HTML."""
        if obj.is_open:
            return format_html('<span style="background-color: #008000; color: white; padding: 3px 10px; border-radius: 3px;">OPEN</span>')
        return format_html('<span style="background-color: #FF0000; color: white; padding: 3px 10px; border-radius: 3px;">CLOSED</span>')
    is_open_badge.short_description = 'Status'

    def days_remaining(self, obj):
        """Display days remaining."""
        if obj.is_open:
            return f"{obj.days_remaining} days"
        return "Deadline passed"
    days_remaining.short_description = 'Days Remaining'


# =============================
# Application Status Log Admin (Read-only)
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
        return False


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

    # Ward-wise breakdown
    ward_stats = BursaryApplication.objects.values('ward').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-count')

    # Institution-wise breakdown
    institution_stats = BursaryApplication.objects.values('institution_name').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-count')[:10]

    # Active deadline
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
        'institution_stats': institution_stats,
        'active_deadline': active_deadline,
        'approval_rate': round((approved_count / total_apps * 100), 2) if total_apps > 0 else 0,
    }
    return TemplateResponse(request, "admin/index.html", context)


# =============================
# Override Django Admin Homepage
# =============================
admin.site.index_template = "admin/index.html"

_original_get_urls = admin.site.get_urls


def _new_get_urls():
    urls = _original_get_urls()
    custom_urls = [path('', custom_admin_dashboard, name='admin-dashboard')]
    return custom_urls + urls


admin.site.get_urls = _new_get_urls