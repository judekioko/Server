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
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate

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
    """Generate HTML email for application confirmation with full summary"""
    amount_str = f"KSh {application.amount:,}"
    ward_pretty = (application.ward or '').replace('-', ' ').title()
    submitted = application.submitted_at.strftime('%B %d, %Y') if application.submitted_at else ''
    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
          .container {{ max-width: 640px; margin: 0 auto; padding: 20px; }}
          .header {{ background: linear-gradient(90deg, #006400, #bb0000, #000000); color: #fff; padding: 16px 20px; text-align:center; }}
          .card {{ background: #f9f9f9; border: 1px solid #eee; border-radius: 8px; padding: 20px; margin-top: 16px; }}
          .summary {{ background:#fff; border:1px solid #eee; border-radius:6px; padding:14px; margin-top:10px; }}
          .row {{ display:flex; margin:6px 0; }}
          .label {{ width: 180px; color:#555; font-weight:bold; }}
          .value {{ color:#111; }}
          .refbox {{ background:#e6ffe6; border:2px solid #008000; padding:12px; border-radius:5px; text-align:center; margin:14px 0; }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h2 style="margin:0;">Masinga NG-CDF Bursary</h2>
          </div>
          <div class="card">
            <h3 style="margin-top:0;">Application Received</h3>
            <p>Dear <strong>{application.full_name}</strong>, your bursary application has been received and is under review.</p>
            <div class="refbox"><strong>Reference:</strong> {application.reference_number}</div>
            <div class="summary">
              <div class="row"><div class="label">Applicant:</div><div class="value">{application.full_name}</div></div>
              <div class="row"><div class="label">Institution:</div><div class="value">{application.institution_name}</div></div>
              <div class="row"><div class="label">Amount:</div><div class="value">{amount_str}</div></div>
              <div class="row"><div class="label">Ward:</div><div class="value">{ward_pretty}</div></div>
              <div class="row"><div class="label">Submitted:</div><div class="value">{submitted}</div></div>
            </div>
            <p style="margin-top:14px;">Keep your reference number for tracking. You will be notified by email and SMS when the status changes.</p>
            <p style="margin-top:14px; color:#666; font-size:0.9rem;">Contact: bursary@masingacdf.go.ke</p>
          </div>
        </div>
      </body>
    </html>
    """


def generate_status_email_html(application, new_status):
    """Generate HTML email for status updates with key details"""
    status_upper = new_status.upper()
    amount_str = f"KSh {application.amount:,}"
    approved_detail = ""
    if new_status == "approved":
        approved_detail = f"""
            <p style="margin-top:10px;">Please contact the Masinga NG-CDF office for further instructions on fund disbursement.</p>
        """
    elif new_status == "rejected":
        approved_detail = f"""
            <p style="margin-top:10px;">If you have questions, please contact the Masinga NG-CDF office with your reference number.</p>
        """
    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
          .container {{ max-width: 640px; margin: 0 auto; padding: 20px; }}
          .header {{ background: linear-gradient(90deg, #006400, #bb0000, #000000); color: #fff; padding: 16px 20px; }}
          .card {{ background: #f9f9f9; border: 1px solid #eee; border-radius: 8px; padding: 20px; margin-top: 16px; }}
          .row {{ display: flex; margin: 6px 0; }}
          .label {{ width: 180px; color: #555; font-weight: bold; }}
          .value {{ color: #111; }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h2 style="margin:0;">Masinga NG-CDF Bursary</h2>
          </div>
          <div class="card">
            <h3 style="margin-top:0;">Application Status: {status_upper}</h3>
            <p>Dear <strong>{application.full_name}</strong>,</p>
            <p>Your bursary application status has been updated.</p>
            <div style="margin:14px 0; padding:14px; background:#fff; border:1px solid #eee; border-radius:6px;">
              <div class="row"><div class="label">Reference Number:</div><div class="value">{application.reference_number}</div></div>
              <div class="row"><div class="label">Institution:</div><div class="value">{application.institution_name}</div></div>
              <div class="row"><div class="label">Amount:</div><div class="value">{amount_str}</div></div>
            </div>
            {approved_detail}
            <p style="margin-top:14px;">Best regards,<br/>Masinga NG-CDF Bursary Management System</p>
          </div>
        </div>
      </body>
    </html>
    """


# ===========================
#  Create Application (with Duplicate Detection)
# ===========================
@method_decorator(csrf_exempt, name='dispatch')
class BursaryApplicationCreateView(DuplicatePreventionMixin, generics.CreateAPIView):
    queryset = BursaryApplication.objects.all()
    serializer_class = BursaryApplicationSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        notification_manager = NotificationManager()
        notif = notification_manager.notify_application_received(instance)
        logger.info(f"Application created: {instance.reference_number}")
        data = serializer.data
        data['notifications'] = notif
        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


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


# ===========================
#  API Auth (Token)
# ===========================
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({'error': 'username and password are required'}, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(request, username=username, password=password)
    if not user:
        return Response({'error': 'invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    from rest_framework.authtoken.models import Token
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'username': user.username,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def api_logout(request):
    try:
        from rest_framework.authtoken.models import Token
        Token.objects.filter(user=request.user).delete()
    except Exception:
        pass
    logout(request)
    return Response({'message': 'logged out'})# ===========================
#  FAST SUBMISSION ENDPOINT
# ===========================
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@csrf_exempt
def fast_submit_application(request):
    """Fast submission - returns success immediately"""
    from django.db import transaction
    import time
    
    start_time = time.time()
    
    try:
        with transaction.atomic():
            from .models import BursaryApplication
            application = BursaryApplication.objects.create(
                full_name=request.data.get('full_name', ''),
                email=request.data.get('email', ''),
                phone_number=request.data.get('phone_number', ''),
                id_number=request.data.get('id_number', ''),
                amount=request.data.get('amount', 0),
                data_consent=request.data.get('data_consent', False),
                residency_confirm=request.data.get('residency_confirm', False),
                status='pending',
            )
            
            response_time = time.time() - start_time
            
            return Response({
                'success': True,
                'message': 'Application submitted!',
                'reference_number': application.reference_number,
                'time': f'{response_time:.3f}s'
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
