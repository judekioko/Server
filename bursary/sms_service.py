# bursary/sms_service.py
"""
SMS Notification Service using Africa's Talking API
Sends SMS notifications for application status updates
"""

import os
import logging
from typing import Optional, Dict, List
try:
    import africastalking
except Exception:
    africastalking = None

logger = logging.getLogger(__name__)


class SMSService:
    """
    SMS Service using Africa's Talking API
    """
    
    def __init__(self):
        self.username = os.environ.get('AFRICASTALKING_USERNAME', 'sandbox')
        self.api_key = os.environ.get('AFRICASTALKING_API_KEY')

        if africastalking is None:
            logger.warning("Africa's Talking SDK not installed; SMS disabled")
            self.enabled = False
            return

        if not self.api_key:
            logger.warning("Africa's Talking API key not configured")
            self.enabled = False
            return
        
        try:
            africastalking.initialize(self.username, self.api_key)
            self.sms = africastalking.SMS
            self.enabled = True
            logger.info("SMS Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SMS service: {str(e)}")
            self.enabled = False
    
    def format_phone_number(self, phone: str) -> str:
        """
        Format phone number to international format (+254...)
        """
        # Remove spaces and dashes
        phone = phone.replace(' ', '').replace('-', '')
        
        # Handle different formats
        if phone.startswith('254'):
            return f'+{phone}'
        elif phone.startswith('0'):
            return f'+254{phone[1:]}'
        elif phone.startswith('+254'):
            return phone
        else:
            # Assume it's already in correct format
            return f'+254{phone}'
    
    def send_sms(self, phone: str, message: str) -> Dict:
        """
        Send SMS to a single recipient
        
        Returns:
            {
                'success': bool,
                'message': str,
                'details': dict
            }
        """
        if not self.enabled:
            logger.warning("SMS service not enabled")
            return {
                'success': False,
                'message': 'SMS service not configured',
                'details': None
            }
        
        try:
            # Format phone number
            formatted_phone = self.format_phone_number(phone)
            
            # Send SMS
            response = self.sms.send(message, [formatted_phone])
            
            logger.info(f"SMS sent to {formatted_phone}: {response}")
            
            return {
                'success': True,
                'message': 'SMS sent successfully',
                'details': response
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'details': None
            }
    
    def send_bulk_sms(self, recipients: List[Dict[str, str]]) -> Dict:
        """
        Send SMS to multiple recipients
        
        Args:
            recipients: [{'phone': '0712345678', 'message': 'Hello'}]
        
        Returns:
            {
                'total': int,
                'success': int,
                'failed': int,
                'results': list
            }
        """
        results = {
            'total': len(recipients),
            'success': 0,
            'failed': 0,
            'results': []
        }
        
        for recipient in recipients:
            phone = recipient.get('phone')
            message = recipient.get('message')
            
            result = self.send_sms(phone, message)
            
            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
            
            results['results'].append({
                'phone': phone,
                'status': 'sent' if result['success'] else 'failed',
                'details': result
            })
        
        return results


# =========================
# SMS Templates
# =========================
class SMSTemplates:
    """
    SMS message templates for different notifications
    """
    
    @staticmethod
    def application_received(reference_number: str, full_name: str) -> str:
        """SMS for application confirmation"""
        return (
            f"Dear {full_name},\n"
            f"Your bursary application has been received.\n"
            f"Reference: {reference_number}\n"
            f"You will be notified of the outcome.\n"
            f"- Masinga NG-CDF"
        )
    
    @staticmethod
    def application_approved(reference_number: str, full_name: str, amount: int) -> str:
        """SMS for approval notification"""
        return (
            f"Congratulations {full_name}!\n"
            f"Your bursary application ({reference_number}) has been APPROVED.\n"
            f"Amount: KSh {amount:,}\n"
            f"Visit our office for disbursement details.\n"
            f"- Masinga NG-CDF"
        )
    
    @staticmethod
    def application_rejected(reference_number: str, full_name: str) -> str:
        """SMS for rejection notification"""
        return (
            f"Dear {full_name},\n"
            f"Your bursary application ({reference_number}) was not approved at this time.\n"
            f"Contact our office for more information.\n"
            f"- Masinga NG-CDF"
        )
    
    @staticmethod
    def deadline_reminder(days_remaining: int) -> str:
        """SMS for deadline reminder"""
        return (
            f"Reminder: Masinga NG-CDF Bursary application deadline is in {days_remaining} days.\n"
            f"Apply now at [your-website.com]\n"
            f"- Masinga NG-CDF"
        )
    
    @staticmethod
    def custom_message(message: str) -> str:
        """Custom SMS message"""
        return f"{message}\n- Masinga NG-CDF"


# =========================
# Notification Manager
# =========================
class NotificationManager:
    """
    Manages all notifications (Email + SMS)
    """
    
    def __init__(self):
        self.sms_service = SMSService()
    
    def notify_application_received(self, application):
        """
        Send confirmation notification (Email + SMS) and return delivery results
        """
        from .views import send_html_email, generate_confirmation_email_html

        results = {
            'email_sent': False,
            'sms_sent': False,
            'email_error': None,
            'sms_error': None,
        }

        try:
            subject = f"Application Received - {application.reference_number}"
            plain_content = f"Dear {application.full_name}, your application has been received."
            html_content = generate_confirmation_email_html(application)
            results['email_sent'] = send_html_email(
                subject=subject,
                html_content=html_content,
                plain_content=plain_content,
                recipient_list=[application.email]
            )
        except Exception as e:
            logger.error(f"Email notification failed: {str(e)}")
            results['email_error'] = str(e)

        try:
            message = SMSTemplates.application_received(
                application.reference_number,
                application.full_name
            )
            sms_res = self.sms_service.send_sms(application.phone_number, message)
            results['sms_sent'] = bool(sms_res.get('success'))
            if not results['sms_sent']:
                results['sms_error'] = sms_res.get('message')
            guardian_message = (
                f"Dear Guardian,\n"
                f"{application.full_name} has submitted a bursary application.\n"
                f"Reference: {application.reference_number}\n"
                f"- Masinga NG-CDF"
            )
            self.sms_service.send_sms(application.guardian_phone, guardian_message)
        except Exception as e:
            logger.error(f"SMS notification failed: {str(e)}")
            results['sms_error'] = str(e)

        return results
    
    def notify_status_change(self, application, new_status):
        """
        Send status change notification (Email + SMS)
        """
        from .views import send_html_email, generate_status_email_html
        
        # Send Email
        try:
            subject = f"Application Status Update - {application.reference_number}"
            html_content = generate_status_email_html(application, new_status)
            plain_content = f"Your application status has been updated to: {new_status}"
            
            send_html_email(
                subject=subject,
                html_content=html_content,
                plain_content=plain_content,
                recipient_list=[application.email]
            )
        except Exception as e:
            logger.error(f"Email notification failed: {str(e)}")
        
        # Send SMS
        try:
            if new_status == 'approved':
                message = SMSTemplates.application_approved(
                    application.reference_number,
                    application.full_name,
                    application.amount
                )
            elif new_status == 'rejected':
                message = SMSTemplates.application_rejected(
                    application.reference_number,
                    application.full_name
                )
            else:
                message = f"Dear {application.full_name}, your application status: {new_status.upper()}"
            
            self.sms_service.send_sms(application.phone_number, message)
            
        except Exception as e:
            logger.error(f"SMS notification failed: {str(e)}")


# =========================
# Management Command for Bulk SMS
# =========================
"""
Create: bursary/management/commands/send_bulk_sms.py

from django.core.management.base import BaseCommand
from bursary.sms_service import SMSService, SMSTemplates
from bursary.models import BursaryApplication

class Command(BaseCommand):
    help = 'Send bulk SMS to all applicants'

    def add_arguments(self, parser):
        parser.add_argument('--status', type=str, help='Filter by status')
        parser.add_argument('--message', type=str, help='Custom message')

    def handle(self, *args, **options):
        sms_service = SMSService()
        
        # Get applications
        queryset = BursaryApplication.objects.all()
        if options['status']:
            queryset = queryset.filter(status=options['status'])
        
        # Prepare recipients
        recipients = []
        for app in queryset:
            message = options['message'] or f"Dear {app.full_name}, update from Masinga NG-CDF"
            recipients.append({
                'phone': app.phone_number,
                'message': SMSTemplates.custom_message(message)
            })
        
        # Send bulk SMS
        results = sms_service.send_bulk_sms(recipients)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Sent SMS to {results['success']}/{results['total']} recipients"
            )
        )
"""


# =========================
# Add to requirements.txt:
# =========================
"""
africastalking==1.2.5
"""

# =========================
# Add to .env:
# =========================
"""
# Africa's Talking SMS
AFRICASTALKING_USERNAME=your-username
AFRICASTALKING_API_KEY=your-api-key
"""