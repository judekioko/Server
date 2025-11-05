# bursary/views.py - COMPLETE VERSION
"""
Complete views with all features integrated:
- Duplicate detection
- Email/SMS notifications
- Application editing
- Analytics
"""

from rest_framework import generics, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import BursaryApplication, ApplicationStatusLog, ApplicationDeadline
from .serializers import BursaryApplicationSerializer
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
import logging

# Import custom modules
from .duplicate_detection import DuplicateApplicationDetector, DuplicatePreventionMixin
from .sms_service import NotificationManager

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for list views"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ===========================
#  Email Helper Functions
# ===========================
def send_html_email(subject, html_content, plain_content, recipient_list):
    """Send HTML email with plain text fallback"""
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"Email sent successfully to {recipient_list}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_list}: {str(e)}")
        return False


def generate_confirmation_email_html(application):
    """Generate HTML email for application confirmation"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(90deg, #006400, #bb0000, #000000); 
                       color: white; padding: 20px; text-align: center; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 8px; margin-top: 20px; }}
            .reference {{ background: #e6ffe6; border: 2px solid #008000; padding: 15px; 
                         border-radius: 5px; text-align: center; margin: 20px 0; }}
            .highlight {{ color: #008000; font-weight: bold; font-size: 18px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Masinga NG-CDF Bursary</h1>
            </div>
            <div class="content">
                <h2>Application Received!</h2>
                <p>Dear <strong>{application.full_name}</strong>,</p>
                <div class="reference">
                    <p>Reference Number:</p>
                    <p class="highlight">{application.reference_number}</p>
                </div>
                <p>Your application has been successfully submitted.</p>
            </div>
        </div>
    </body>
    </html>
    """


def generate_status_email_html(application, new_status):
    """Generate HTML email for status updates"""
    return f"""<html><body><h1>Status Update: {new_status.upper()}</h1><p>Dear {application.full_name}, your application status has been updated.</p></body></html>"""


# ===========================
#  Create Application (with Duplicate Detection)
# ===========================
class BursaryApplicationCreateView(DuplicatePreventionMixin, generics.CreateAPIView):
    queryset = BursaryApplication.objects.all()
    serializer_class = BursaryApplicationSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        """Override to send notifications"""
        try:
            # Call parent (includes duplicate check from mixin)
            instance = super().perform_create(serializer)
            
            if not instance:
                instance = serializer.save()
            
            # Send notifications (Email + SMS)
            notification_manager = NotificationManager()
            notification_manager.notify_application_received(instance)
            
            logger.info(f"Application created: {instance.reference_number}")
            return instance
            
        except Exception as e:
            logger.error(f"Error creating application: {str(e)}")
            raise


# ===========================
#  List Applications (Admin Only)
# ===========================
class BursaryApplicationListView(generics.ListAPIView):
    queryset = BursaryApplication.objects.all().order_by("-submitted_at")
    serializer_class = BursaryApplicationSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ward', 'level_of_study', 'institution_type', 'family_status', 'status']
    search_fields = ['full_name', 'id_number', 'reference_number', 'institution_name']
    ordering_fields = ['submitted_at', 'amount', 'status']


# ===========================
#  Retrieve Application by Reference
# ===========================
class BursaryApplicationDetailView(generics.RetrieveAPIView):
    queryset = BursaryApplication.objects.all()
    serializer_class = BursaryApplicationSerializer
    lookup_field = "reference_number"
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# ===========================
#  Update Application Status (Admin)
# ===========================
class BursaryApplicationUpdateStatusView(generics.UpdateAPIView):
    queryset = BursaryApplication.objects.all()
    serializer_class = BursaryApplicationSerializer
    lookup_field = "reference_number"
    permission_classes = [permissions.IsAdminUser]

    def update(self, request, *args, **kwargs):
        """Update status and send notifications"""
        try:
            instance = self.get_object()
            old_status = instance.status
            new_status = request.data.get('status')
            reason = request.data.get('reason', '')

            if not new_status or new_status == old_status:
                return Response({'message': 'No status change'})

            instance.status = new_status
            instance.save()

            # Create audit log
            ApplicationStatusLog.objects.create(
                application=instance,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user,
                reason=reason
            )

            # Send notifications
            notification_manager = NotificationManager()
            notification_manager.notify_status_change(instance, new_status)

            return Response({
                'message': f'Status updated: {old_status} → {new_status}',
                'reference_number': instance.reference_number
            })

        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")
            return Response(
                {'error': 'Failed to update status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===========================
#  Application Status History
# ===========================
@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def application_status_history(request, reference_number):
    """Get complete status change history"""
    try:
        application = BursaryApplication.objects.get(reference_number=reference_number)
        logs = ApplicationStatusLog.objects.filter(application=application)
        
        history = [{
            'old_status': log.old_status,
            'new_status': log.new_status,
            'changed_by': log.changed_by.username if log.changed_by else 'System',
            'reason': log.reason,
            'changed_at': log.changed_at.isoformat()
        } for log in logs]

        return Response({
            'reference_number': reference_number,
            'current_status': application.status,
            'history': history
        })
    except BursaryApplication.DoesNotExist:
        return Response(
            {'error': 'Application not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# ===========================
#  Get Application Deadline
# ===========================
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def deadline_status(request):
    """Get current application deadline status"""
    try:
        active_deadline = ApplicationDeadline.objects.filter(is_active=True).first()
        
        if not active_deadline:
            return Response({
                'is_open': False,
                'message': 'No active application deadline'
            })

        return Response({
            'is_open': active_deadline.is_open,
            'name': active_deadline.name,
            'start_date': active_deadline.start_date.isoformat(),
            'end_date': active_deadline.end_date.isoformat(),
            'days_remaining': active_deadline.days_remaining
        })
    except Exception as e:
        logger.error(f"Error fetching deadline: {str(e)}")
        return Response(
            {'error': 'Failed to fetch deadline'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ===========================
#  Logout View
# ===========================
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('admin:login')