from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from bursary.models import BursaryApplication
from django.db.models import Sum, Count
from django.utils import timezone

def admin_dashboard_view(request):
    total_apps = BursaryApplication.objects.count()
    total_amount = BursaryApplication.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_institutions = BursaryApplication.objects.values('institution_name').distinct().count()
    latest_application = BursaryApplication.objects.order_by('-submitted_at').first()

    context = {
        'total_apps': total_apps,
        'total_amount': total_amount,
        'total_institutions': total_institutions,
        'latest_submission': latest_application.submitted_at if latest_application else None,
        'today': timezone.now().date(),
        'title': 'Masinga NG-CDF Admin Dashboard'
    }
    return render(request, 'admin/dashboard.html', context)
