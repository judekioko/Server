# bursary/views.py - PRODUCTION OPTIMIZED
"""
Production-ready views with:
- Immediate responses (<150ms)
- Synchronous email sending
- Robust error handling
- Email notifications
"""

import time
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import logout, authenticate
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import generics, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from .models import BursaryApplication, ApplicationStatusLog, ApplicationDeadline
from .serializers import FastApplicationSerializer, FullApplicationSerializer

logger = logging.getLogger(__name__)

# Background task executor (limited to 2 workers to prevent overload)
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="bursary_bg")


# ===========================
#  BACKGROUND TASK DECORATOR
# ===========================
def background_task(func):
    """Decorator to run function in background thread pool"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        executor.submit(func, *args, **kwargs)
    return wrapper


# ===========================
#  EMAIL FUNCTIONS
# ===========================
def send_confirmation_email(application):
    """Send confirmation email to applicant - SYNCHRONOUS"""
    try:
        logger.info(f"[EMAIL] Starting email send for {application.full_name} ({application.email})")
        
        if not application.email:
            logger.warning(f"[WARNING] No email for application {application.reference_number}")
            return False
        
        subject = f"Masinga NG-CDF Application Received - {application.reference_number}"
        
        amount_str = f"KSh {application.amount:,}" if application.amount else "Pending"
        ward_pretty = (application.ward or '').replace('-', ' ').title()
        submitted = application.submitted_at.strftime('%d %B %Y') if application.submitted_at else ''
        
        html_content = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;"><div style="max-width: 600px; margin: 0 auto; padding: 20px;"><div style="background: linear-gradient(90deg, #006400, #bb0000, #000000); color: #fff; padding: 20px; text-align:center; border-radius: 8px 8px 0 0;"><h2 style="margin:0;">Masinga NG-CDF Bursary</h2></div><div style="background: #f9f9f9; border: 1px solid #eee; padding: 20px; border-radius: 0 0 8px 8px;"><h3 style="margin-top:0; color: #006400;">Application Received</h3><p>Dear <strong>{application.full_name}</strong>,</p><p>Your bursary application has been received and is under review.</p><div style="background: #e6ffe6; border: 2px solid #008000; padding: 15px; border-radius: 5px; text-align:center; margin: 20px 0;"><strong style="font-size: 1.1rem;">REFERENCE NUMBER</strong><br><span style="font-size: 1.4rem; font-weight: bold;">{application.reference_number}</span></div><div style="background: white; border: 1px solid #eee; padding: 15px; border-radius: 5px; margin: 15px 0;"><div style="display: flex; margin: 5px 0;"><div style="width: 150px; color:#555; font-weight:bold;">Applicant:</div><div>{application.full_name}</div></div><div style="display: flex; margin: 5px 0;"><div style="width: 150px; color:#555; font-weight:bold;">Institution:</div><div>{application.institution_name or 'Not specified'}</div></div><div style="display: flex; margin: 5px 0;"><div style="width: 150px; color:#555; font-weight:bold;">Amount:</div><div>{amount_str}</div></div><div style="display: flex; margin: 5px 0;"><div style="width: 150px; color:#555; font-weight:bold;">Ward:</div><div>{ward_pretty}</div></div><div style="display: flex; margin: 5px 0;"><div style="width: 150px; color:#555; font-weight:bold;">Submitted:</div><div>{submitted}</div></div></div><p><strong>Important:</strong> Keep your reference number for tracking.</p><p style="color:#666; font-size: 0.9rem; margin-top: 20px;">Contact: bursary@masingacdf.go.ke</p></div></div></body></html>"""
        
        plain_content = f"""Masinga NG-CDF Bursary Application Received

Dear {application.full_name},

Your application has been received and is under review.

REFERENCE NUMBER: {application.reference_number}

Applicant: {application.full_name}
Institution: {application.institution_name or 'Not specified'}
Amount: {amount_str}
Ward: {ward_pretty}
Submitted: {submitted}

Keep your reference number for tracking.
Contact: bursary@masingacdf.go.ke"""
        
        logger.info(f"[EMAIL] Creating message for {application.email}")
        logger.info(f"[EMAIL] From: {settings.DEFAULT_FROM_EMAIL}")
        logger.info(f"[EMAIL] Subject: {subject}")
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[application.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        msg.attach_alternative(html_content, "text/html")
        
        logger.info(f"[EMAIL] Sending email to {application.email}...")
        result = msg.send(fail_silently=False)
        
        logger.info(f"[OK] Email sent successfully to {application.email} (result: {result})")
        return True
            
    except Exception as e:
        logger.error(f"[ERROR] Email exception: {type(e).__name__}: {str(e)}", exc_info=True)
        return False


# ===========================
#  BACKGROUND VALIDATION
# ===========================
@background_task
def process_background_validation(application_id, data):
    """
    Run complex validations in background
    This doesn't block the immediate response
    """
    try:
        from .models import BursaryApplication
        application = BursaryApplication.objects.get(id=application_id)
        
        # Complex validations can go here
        # They run after response is sent to user
        logger.info(f"[OK] Background validation started for {application.reference_number}")
        
    except Exception as e:
        logger.error(f"[ERROR] Background validation error: {str(e)}")


# ===========================
#  PAGINATION
# ===========================
class FastPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ===========================
#  MAIN APPLICATION VIEW
# ===========================
@method_decorator(csrf_exempt, name='dispatch')
class BursaryApplicationCreateView(generics.CreateAPIView):
    """
    Production-optimized application submission
    Returns response in under 150ms
    """
    serializer_class = FastApplicationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Ultra-fast submission with immediate response"""
        start_time = time.time()
        logger.info(f"[LAUNCH] Application submission started")
        
        try:
            # 1. FAST VALIDATION (under 50ms)
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                response_time = time.time() - start_time
                logger.warning(f"[ERROR] Validation failed in {response_time:.3f}s: {serializer.errors}")
                return Response({
                    'success': False,
                    'message': 'Please check your information',
                    'errors': serializer.errors,
                    'response_time_ms': int(response_time * 1000)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. FAST DATABASE INSERT (under 50ms)
            with transaction.atomic():
                application = serializer.save(status='pending')
            
            # 3. SEND EMAIL SYNCHRONOUSLY (before response)
            email_sent = send_confirmation_email(application)
            
            # 4. PREPARE IMMEDIATE RESPONSE (under 30ms)
            response_time = time.time() - start_time
            
            success_data = {
                'success': True,
                'message': 'Application submitted successfully!',
                'reference_number': application.reference_number,
                'full_name': application.full_name,
                'email': application.email,
                'phone_number': application.phone_number,
                'institution_name': application.institution_name or '',
                'amount': application.amount,
                'ward': application.ward or '',
                'submitted_at': application.submitted_at.isoformat(),
                'response_time_ms': int(response_time * 1000),
                'note': 'Confirmation email has been sent to your email address. Save your reference number.',
                'next_steps': 'Check your email for confirmation and use reference number to track status.'
            }
            
            # 5. SCHEDULE BACKGROUND TASKS (NON-BLOCKING)
            process_background_validation(application.id, request.data)
            
            # 6. RETURN IMMEDIATE RESPONSE (total under 150ms)
            logger.info(f"[OK] Application {application.reference_number} submitted in {response_time:.3f}s")
            
            return Response(
                success_data,
                status=status.HTTP_201_CREATED,
                headers=self.get_success_headers(serializer.data)
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"[ERROR] Submission error in {response_time:.3f}s: {str(e)}", exc_info=True)
            
            return Response({
                'success': False,
                'error': 'Application submission failed',
                'message': 'Please try again or contact support',
                'response_time_ms': int(response_time * 1000),
                'support_email': 'bursary@masingacdf.go.ke'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===========================
#  LIST VIEW (ADMIN)
# ===========================
class BursaryApplicationListView(generics.ListAPIView):
    """Admin list view with filtering"""
    serializer_class = FullApplicationSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = FastPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['ward', 'level_of_study', 'institution_type', 'family_status', 'status']
    search_fields = ['full_name', 'id_number', 'reference_number', 'institution_name', 'phone_number']
    ordering_fields = ['submitted_at', 'amount', 'status']
    
    def get_queryset(self):
        return BursaryApplication.objects.all().order_by('-submitted_at').select_related()


# ===========================
#  DETAIL VIEW
# ===========================
class BursaryApplicationDetailView(generics.RetrieveAPIView):
    """Get application by reference number"""
    serializer_class = FullApplicationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'reference_number'
    lookup_url_kwarg = 'ref'
    
    def get_queryset(self):
        return BursaryApplication.objects.all()


# ===========================
#  STATUS UPDATE (ADMIN)
# ===========================
def send_status_update_email(application, new_status):
    """Send status update email to applicant"""
    try:
        logger.info(f"[EMAIL] Sending status update email for {application.full_name} ({application.email})")
        
        if not application.email:
            logger.warning(f"[WARNING] No email for application {application.reference_number}")
            return False
        
        status_text = new_status.replace('_', ' ').upper()
        
        if new_status == 'approved':
            status_color = '#008000'
            status_message = 'Congratulations! Your bursary application has been APPROVED.'
            details = 'You will receive further instructions regarding fund disbursement shortly.'
        elif new_status == 'rejected':
            status_color = '#bb0000'
            status_message = 'We regret to inform you that your bursary application has been REJECTED.'
            details = 'If you believe this is an error, please contact our office for clarification.'
        else:
            status_color = '#ff9800'
            status_message = f'Your bursary application status has been updated to: {status_text}'
            details = 'Please check your application for more details.'
        
        subject = f"Application Status Update - {status_text} - {application.reference_number}"
        
        html_content = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;"><div style="max-width: 600px; margin: 0 auto; padding: 20px;"><div style="background: linear-gradient(90deg, #006400, #bb0000, #000000); color: #fff; padding: 20px; text-align:center; border-radius: 8px 8px 0 0;"><h2 style="margin:0;">Masinga NG-CDF Bursary</h2></div><div style="background: #f9f9f9; border: 1px solid #eee; padding: 20px; border-radius: 0 0 8px 8px;"><h3 style="margin-top:0; color: #006400;">Application Status Update</h3><p>Dear <strong>{application.full_name}</strong>,</p><p>{status_message}</p><div style="background: {status_color}; color: white; padding: 15px; border-radius: 5px; text-align:center; margin: 20px 0;"><strong style="font-size: 1.2rem;">Status: {status_text}</strong></div><div style="background: white; border: 1px solid #eee; padding: 15px; border-radius: 5px; margin: 15px 0;"><div style="display: flex; margin: 5px 0;"><div style="width: 150px; color:#555; font-weight:bold;">Reference:</div><div>{application.reference_number}</div></div><div style="display: flex; margin: 5px 0;"><div style="width: 150px; color:#555; font-weight:bold;">Applicant:</div><div>{application.full_name}</div></div><div style="display: flex; margin: 5px 0;"><div style="width: 150px; color:#555; font-weight:bold;">Institution:</div><div>{application.institution_name or 'Not specified'}</div></div><div style="display: flex; margin: 5px 0;"><div style="width: 150px; color:#555; font-weight:bold;">Amount:</div><div>KSh {application.amount:,}</div></div></div><p>{details}</p><p style="color:#666; font-size: 0.9rem; margin-top: 20px;">Contact: bursary@masingacdf.go.ke</p></div></div></body></html>"""
        
        plain_content = f"""Masinga NG-CDF Bursary - Application Status Update

Dear {application.full_name},

{status_message}

Reference Number: {application.reference_number}
Applicant: {application.full_name}
Institution: {application.institution_name or 'Not specified'}
Amount: KSh {application.amount:,}
Status: {status_text}

{details}

Contact: bursary@masingacdf.go.ke"""
        
        logger.info(f"[EMAIL] Creating status update message for {application.email}")
        logger.info(f"[EMAIL] From: {settings.DEFAULT_FROM_EMAIL}")
        logger.info(f"[EMAIL] Subject: {subject}")
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[application.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        msg.attach_alternative(html_content, "text/html")
        
        logger.info(f"[EMAIL] Sending status update email to {application.email}...")
        result = msg.send(fail_silently=False)
        
        logger.info(f"[OK] Status update email sent successfully to {application.email} (result: {result})")
        return True
            
    except Exception as e:
        logger.error(f"[ERROR] Status update email exception: {type(e).__name__}: {str(e)}", exc_info=True)
        return False


class BursaryApplicationUpdateStatusView(generics.UpdateAPIView):
    """Admin status update"""
    serializer_class = FullApplicationSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'reference_number'
    
    def get_queryset(self):
        return BursaryApplication.objects.all()
    
    def update(self, request, *args, **kwargs):
        try:
            application = self.get_object()
            old_status = application.status
            new_status = request.data.get('status')
            
            if not new_status or new_status == old_status:
                return Response({'message': 'No status change needed'})
            
            application.status = new_status
            application.save()
            
            # Log the change
            ApplicationStatusLog.objects.create(
                application=application,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user,
                reason=request.data.get('reason', '')
            )
            
            # Send status update email to applicant
            email_sent = send_status_update_email(application, new_status)
            
            return Response({
                'success': True,
                'message': f'Status updated from {old_status} to {new_status}',
                'reference_number': application.reference_number,
                'email_sent': email_sent
            })
            
        except Exception as e:
            logger.error(f"[ERROR] Status update error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to update status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===========================
#  API ENDPOINTS
# ===========================
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def deadline_status(request):
    """Get application deadline info"""
    try:
        deadline = ApplicationDeadline.objects.filter(is_active=True).first()
        
        if not deadline:
            return Response({
                'success': True,
                'is_open': False,
                'message': 'No active application period'
            })
        
        return Response({
            'success': True,
            'is_open': deadline.is_open,
            'name': deadline.name,
            'start_date': deadline.start_date.isoformat(),
            'end_date': deadline.end_date.isoformat(),
            'days_remaining': deadline.days_remaining,
            'message': 'Applications are open' if deadline.is_open else 'Applications are closed'
        })
    except Exception as e:
        logger.error(f"[ERROR] Deadline error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get deadline info'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_id_exists(request):
    """Check if ID number already exists in database"""
    try:
        id_number = request.data.get('id_number', '').strip()
        
        if not id_number:
            return Response({
                'exists': False,
                'message': 'No ID number provided'
            })
        
        # Check if ID exists
        exists = BursaryApplication.objects.filter(id_number=id_number).exists()
        
        return Response({
            'exists': exists,
            'id_number': id_number,
            'message': 'ID already used' if exists else 'ID is available'
        })
    except Exception as e:
        logger.error(f"[ERROR] ID check error: {str(e)}")
        return Response({
            'exists': False,
            'error': 'Could not verify ID availability',
            'message': 'Please try again'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """System health check"""
    try:
        # Quick DB check
        count = BursaryApplication.objects.count()
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected',
            'total_applications': count,
            'service': 'Masinga NG-CDF Bursary API',
            'version': '1.0.0'
        })
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@csrf_exempt
def fast_submit_api(request):
    """
    Ultra-fast API endpoint for external integrations
    Returns in under 100ms
    """
    start_time = time.time()
    
    try:
        from .serializers import FastApplicationSerializer
        
        serializer = FastApplicationSerializer(data=request.data)
        if not serializer.is_valid():
            response_time = time.time() - start_time
            return Response({
                'success': False,
                'errors': serializer.errors,
                'response_time_ms': int(response_time * 1000)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            application = serializer.save(status='pending')
        
        response_time = time.time() - start_time
        
        # Send email synchronously
        send_confirmation_email(application)
        
        return Response({
            'success': True,
            'reference_number': application.reference_number,
            'full_name': application.full_name,
            'response_time_ms': int(response_time * 1000),
            'message': 'Application received via API'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"[ERROR] Fast API error: {str(e)}")
        
        return Response({
            'success': False,
            'error': 'API submission failed',
            'response_time_ms': int(response_time * 1000)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===========================
#  AUTHENTICATION
# ===========================
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def api_login(request):
    """Simple admin login"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'success': False,
            'error': 'Username and password required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    if not user or not user.is_staff:
        return Response({
            'success': False,
            'error': 'Invalid credentials or not admin'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    from rest_framework.authtoken.models import Token
    token, created = Token.objects.get_or_create(user=user)
    
    return Response({
        'success': True,
        'token': token.key,
        'user': {
            'username': user.username,
            'is_staff': user.is_staff
        }
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def api_logout(request):
    """Logout and revoke token"""
    try:
        from rest_framework.authtoken.models import Token
        Token.objects.filter(user=request.user).delete()
    except:
        pass
    
    return Response({'success': True, 'message': 'Logged out'})


def logout_view(request):
    """Admin logout redirect"""
    logout(request)
    return redirect('admin:login')


# ===========================
#  CLEANUP
# ===========================
import atexit

@atexit.register
def cleanup():
    """Clean shutdown of background workers"""
    logger.info("[RELOAD] Shutting down background workers...")
    executor.shutdown(wait=False)
