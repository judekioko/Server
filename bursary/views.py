# views.py
from rest_framework import generics, permissions
from .models import BursaryApplication
from .serializers import BursaryApplicationSerializer
from django.contrib.auth import logout
from django.shortcuts import redirect

# Create Application
class BursaryApplicationCreateView(generics.CreateAPIView):
    queryset = BursaryApplication.objects.all()
    serializer_class = BursaryApplicationSerializer
    permission_classes = [permissions.AllowAny]  # applicants don't need auth


# List Applications (Admin Only)
class BursaryApplicationListView(generics.ListAPIView):
    queryset = BursaryApplication.objects.all().order_by("-submitted_at")
    serializer_class = BursaryApplicationSerializer
    permission_classes = [permissions.IsAdminUser]  # restrict to admin


# Retrieve Application by Reference Number
class BursaryApplicationDetailView(generics.RetrieveAPIView):
    queryset = BursaryApplication.objects.all()
    serializer_class = BursaryApplicationSerializer
    lookup_field = "reference_number"  # allows search by ref number
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# Logout view (should be outside the class)
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('admin_login')
