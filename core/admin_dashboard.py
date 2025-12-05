from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone
from bursary.models import BursaryApplication
from bursary.analytics import BursaryAnalytics

def admin_dashboard_view(request):
    total_apps = BursaryApplication.objects.count()
    total_amount = BursaryApplication.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_institutions = BursaryApplication.objects.values('institution_name').distinct().count()
    latest_application = BursaryApplication.objects.order_by('-submitted_at').first()

    analytics = BursaryAnalytics()

    context = {
        'total_apps': total_apps,
        'total_amount': total_amount,
        'total_institutions': total_institutions,
        'latest_submission': latest_application.submitted_at if latest_application else None,
        'today': timezone.now().date(),
        'title': 'Masinga NG-CDF Admin Dashboard',
        'overview': analytics.get_overview_stats(),
        'ward_distribution': analytics.get_ward_distribution(),
        'top_institutions': analytics.get_institution_stats(10),
        'monthly_trends': analytics.get_monthly_trends(6),
    }
    return render(request, 'admin/dashboard.html', context)
