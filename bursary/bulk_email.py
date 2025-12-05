"""
Bulk Email System for Masinga NG-CDF Bursary Admin
--------------------------------------------------
Features:
- Detailed email templates with full application info
- Bulk email sending with threading
- Deadline reminders
- Document requests
- Admin actions for sending emails
"""

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import BursaryApplication, ApplicationDeadline

logger = logging.getLogger(__name__)


# =========================
# Bulk Email Sending Service
# =========================
class BulkEmailService:
    """
    Service for sending bulk emails concurrently
    """
    def __init__(self, max_workers=5):
        self.max_workers = max_workers

    def send_single_email(self, recipient_data: Dict) -> Dict:
        """
        Send email to a single recipient
        """
        try:
            msg = EmailMultiAlternatives(
                subject=recipient_data['subject'],
                body=recipient_data['plain_content'],
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_data['email']]
            )
            msg.attach_alternative(recipient_data['html_content'], "text/html")
            msg.send()

            logger.info(f"Email sent to {recipient_data['email']}")
            return {'success': True, 'email': recipient_data['email'], 'error': None}

        except Exception as e:
            logger.error(f"Failed to send email to {recipient_data['email']}: {str(e)}")
            return {'success': False, 'email': recipient_data['email'], 'error': str(e)}

    def send_bulk(self, recipients: List[Dict]) -> Dict:
        """
        Send emails to multiple recipients concurrently
        """
        results = {'total': len(recipients), 'success': 0, 'failed': 0, 'results': []}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.send_single_email, r): r for r in recipients}
            for future in as_completed(futures):
                result = future.result()
                results['results'].append(result)
                if result['success']:
                    results['success'] += 1
                else:
                    results['failed'] += 1

        logger.info(f"Bulk email completed: {results['success']}/{results['total']} sent")
        return results


# =========================
# Email Template Manager
# =========================
class EmailTemplateManager:
    """
    Manage email templates for all notifications
    """

    @staticmethod
    def generate_custom_email(application, subject: str, message: str = None) -> tuple:
        """
        Generate detailed email for a bursary application
        """
        submitted = application.submitted_at
        submitted_str = (timezone.localtime(submitted).strftime("%Y-%m-%d %H:%M:%S")
                         if submitted else "N/A")

        if not message:
            message = "Your bursary application has been successfully received."

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(90deg, #006400, #bb0000, #000000); 
                           color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 8px; margin-top: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                ul {{ padding-left: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Masinga NG-CDF Bursary</h1>
                </div>
                <div class="content">
                    <p>Dear <strong>{application.full_name}</strong>,</p>
                    <p>{message}</p>
                    <p><strong>Your Application Details:</strong></p>
                    <ul>
                        <li>Reference Number: {application.reference_number}</li>
                        <li>Submitted Date: {submitted_str}</li>
                        <li>Institution: {application.institution_name}</li>
                        <li>Amount Requested: KSh {application.amount}</li>
                        <li>Status: {application.status.upper()}</li>
                    </ul>
                    <p>You can use your reference number to track your application status.</p>
                    <p>If you have any questions, please contact our office.</p>
                </div>
                <div class="footer">
                    <p>Masinga NG-CDF Bursary Management System</p>
                    <p>&copy; 2024 Masinga NG-CDF. All Rights Reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_content = f"""
Dear {application.full_name},

{message}

Your Application Details:
- Reference Number: {application.reference_number}
- Submitted Date: {submitted_str}
- Institution: {application.institution_name}
- Amount Requested: KSh {application.amount}
- Status: {application.status.upper()}

You can use your reference number to track your application status.

Best regards,
Masinga NG-CDF Bursary Management System
        """.strip()

        return html_content, plain_content

    @staticmethod
    def generate_deadline_reminder(application, days_remaining: int) -> tuple:
        message = (f"This is a reminder that the bursary application deadline is in "
                   f"{days_remaining} days. Please make any necessary updates before the deadline.")
        return EmailTemplateManager.generate_custom_email(application, 
                                                           f"Deadline Reminder - {days_remaining} Days Remaining",
                                                           message)

    @staticmethod
    def generate_document_request(application, documents: List[str]) -> tuple:
        doc_list = ', '.join(documents)
        message = f"We require additional documents for your application: {doc_list}. Please submit within 7 days."
        return EmailTemplateManager.generate_custom_email(application, 
                                                           "Additional Documents Required", 
                                                           message)


# =========================
# Admin Actions
# =========================
def send_bulk_email_action(modeladmin, request, queryset):
    """Redirect admin to bulk email form"""
    selected = queryset.values_list('id', flat=True)
    request.session['selected_applications'] = list(selected)
    return redirect('admin:bulk_email_form')

send_bulk_email_action.short_description = "Send Bulk Email to Selected"


def send_deadline_reminder_action(modeladmin, request, queryset):
    """Send deadline reminder emails"""
    active_deadline = ApplicationDeadline.objects.filter(is_active=True).first()
    if not active_deadline:
        modeladmin.message_user(request, "No active deadline found", level=messages.ERROR)
        return

    days_remaining = active_deadline.days_remaining
    bulk_service = BulkEmailService()
    template_manager = EmailTemplateManager()

    recipients = []
    for app in queryset:
        html_content, plain_content = template_manager.generate_deadline_reminder(app, days_remaining)
        recipients.append({
            'email': app.email,
            'name': app.full_name,
            'subject': f"Deadline Reminder - {days_remaining} Days Remaining",
            'html_content': html_content,
            'plain_content': plain_content
        })

    results = bulk_service.send_bulk(recipients)
    modeladmin.message_user(request,
        f"Sent reminder to {results['success']}/{results['total']} applicants",
        level=messages.SUCCESS if results['success'] > 0 else messages.ERROR
    )

send_deadline_reminder_action.short_description = "Send Deadline Reminder"


# =========================
# Bulk Email Form View
# =========================
def bulk_email_form_view(request):
    """Form for composing bulk email"""
    selected_ids = request.session.get('selected_applications', [])
    applications = BursaryApplication.objects.filter(id__in=selected_ids)

    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if not subject or not message:
            messages.error(request, "Subject and message are required")
            return render(request, 'admin/bulk_email_form.html', {
                'applications': applications,
                'count': applications.count()
            })

        bulk_service = BulkEmailService()
        template_manager = EmailTemplateManager()
        recipients = []
        for app in applications:
            html_content, plain_content = template_manager.generate_custom_email(app, subject, message)
            recipients.append({
                'email': app.email,
                'name': app.full_name,
                'subject': subject,
                'html_content': html_content,
                'plain_content': plain_content
            })

        results = bulk_service.send_bulk(recipients)
        request.session.pop('selected_applications', None)
        messages.success(request, f"Sent email to {results['success']}/{results['total']} recipients")
        return redirect('admin:bursary_bursaryapplication_changelist')

    return render(request, 'admin/bulk_email_form.html', {
        'applications': applications,
        'count': applications.count()
    })


# =========================
# Bulk Email Form Template (Optional for inline rendering)
# =========================
BULK_EMAIL_TEMPLATE = """
{% extends "admin/base_site.html" %}
{% load static %}

{% block content %}
<div style="max-width: 800px; margin: 20px auto; padding: 20px;">
    <h1>Send Bulk Email</h1>
    <div style="background: #e8f5e9; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <p><strong>Recipients:</strong> {{ count }} application(s) selected</p>
    </div>
    <form method="post">
        {% csrf_token %}
        <div style="margin-bottom: 20px;">
            <label>Email Subject:</label>
            <input type="text" name="subject" required style="width: 100%; padding: 10px;">
        </div>
        <div style="margin-bottom: 20px;">
            <label>Email Message:</label>
            <textarea name="message" rows="10" required style="width: 100%; padding: 10px;"></textarea>
            <small>Recipient name and application details will be included automatically</small>
        </div>
        <div style="display: flex; gap: 10px;">
            <button type="submit" style="background: #4CAF50; color: white; padding: 10px 20px;">Send Email</button>
            <a href="{% url 'admin:bursary_bursaryapplication_changelist' %}" style="background: #666; color: white; padding: 10px 20px;">Cancel</a>
        </div>
    </form>
</div>
{% endblock %}
"""
