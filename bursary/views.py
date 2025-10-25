# views.py
from rest_framework import generics, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import BursaryApplication, ApplicationStatusLog, ApplicationDeadline
from .serializers import BursaryApplicationSerializer
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for list views"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# Create Application
class BursaryApplicationCreateView(generics.CreateAPIView):
    queryset = BursaryApplication.objects.all()
    serializer_class = BursaryApplicationSerializer
    permission_classes = [permissions.AllowAny]  # applicants don't need auth

    def perform_create(self, serializer):
        """Override to send confirmation email"""
        instance = serializer.save()
        self.send_confirmation_email(instance)

    def send_confirmation_email(self, application):
        """Send confirmation email to applicant"""
        try:
            subject = f"Bursary Application Received - Reference: {application.reference_number}"
            message = f"""
Dear {application.full_name},

Your bursary application has been successfully received.

Reference Number: {application.reference_number}
Submitted Date: {application.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}
Institution: {application.institution_name}
Amount Requested: KSh {application.amount:,}

You can use your reference number to track your application status.

Best regards,
Masinga NG-CDF Bursary Management System
            """
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [application.phone_number],  # In production, use email field
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error sending email: {e}")


# List Applications (Admin Only) with Pagination and Filtering
class BursaryApplicationListView(generics.ListAPIView):
    queryset = BursaryApplication.objects.all().order_by("-submitted_at")
    serializer_class = BursaryApplicationSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ward', 'level_of_study', 'institution_type', 'family_status', 'status']
    search_fields = ['full_name', 'id_number', 'reference_number', 'institution_name']
    ordering_fields = ['submitted_at', 'amount', 'status']


# Retrieve Application by Reference Number
class BursaryApplicationDetailView(generics.RetrieveAPIView):
    queryset = BursaryApplication.objects.all()
    serializer_class = BursaryApplicationSerializer
    lookup_field = "reference_number"
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# Update Application Status with Audit Logging
class BursaryApplicationUpdateStatusView(generics.UpdateAPIView):
    queryset = BursaryApplication.objects.all()
    serializer_class = BursaryApplicationSerializer
    lookup_field = "reference_number"
    permission_classes = [permissions.IsAdminUser]

    def update(self, request, *args, **kwargs):
        """Update status and create audit log"""
        instance = self.get_object()
        old_status = instance.status
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')

        if new_status and new_status != old_status:
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

            # Send notification email
            self.send_status_update_email(instance, new_status)

            return Response({
                'message': f'Application status updated from {old_status} to {new_status}',
                'reference_number': instance.reference_number,
                'new_status': new_status
            })

        return Response({'error': 'No status change'}, status=status.HTTP_400_BAD_REQUEST)

    def send_status_update_email(self, application, new_status):
        """Send status update email to applicant"""
        try:
            status_messages = {
                'approved': 'Your bursary application has been APPROVED!',
                'rejected': 'Your bursary application has been REJECTED.',
                'pending': 'Your bursary application is under review.'
            }

            subject = f"Bursary Application Status Update - {application.reference_number}"
            message = f"""
Dear {application.full_name},

{status_messages.get(new_status, 'Your application status has been updated.')}

Reference Number: {application.reference_number}
New Status: {new_status.upper()}
Institution: {application.institution_name}

For more information, please contact the Masinga NG-CDF office.

Best regards,
Masinga NG-CDF Bursary Management System
            """
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [application.phone_number],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error sending status update email: {e}")


# Get Application Status History
@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def application_status_history(request, reference_number):
    """Get complete status change history for an application"""
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
        return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)


# Get Application Deadline Status
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def deadline_status(request):
    """Get current application deadline status"""
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


# Logout view
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('admin_login')
