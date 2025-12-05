# bursary/analytics.py
"""
Advanced Analytics Dashboard for Bursary Applications
"""

from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from typing import Dict, List
import json


class BursaryAnalytics:
    """
    Comprehensive analytics for bursary applications
    """
    
    def __init__(self, queryset=None):
        from .models import BursaryApplication
        self.queryset = queryset or BursaryApplication.objects.all()
    
    def get_overview_stats(self) -> Dict:
        """
        Get high-level overview statistics
        """
        from time import time
        global _overview_cache
        try:
            cache_entry = _overview_cache
        except NameError:
            _overview_cache = {'ts': 0, 'data': None}
            cache_entry = _overview_cache
        if time() - cache_entry['ts'] < 300 and cache_entry['data'] is not None:
            return cache_entry['data']
        stats = self.queryset.aggregate(
            total_applications=Count('id'),
            total_amount_requested=Sum('amount'),
            average_amount=Avg('amount'),
            pending_count=Count('id', filter=Q(status='pending')),
            approved_count=Count('id', filter=Q(status='approved')),
            rejected_count=Count('id', filter=Q(status='rejected')),
            approved_amount=Sum('amount', filter=Q(status='approved')),
        )
        
        # Calculate percentages
        total = stats['total_applications'] or 1  # Avoid division by zero
        stats['approval_rate'] = round((stats['approved_count'] / total) * 100, 2)
        stats['rejection_rate'] = round((stats['rejected_count'] / total) * 100, 2)
        stats['pending_rate'] = round((stats['pending_count'] / total) * 100, 2)
        
        _overview_cache = {'ts': time(), 'data': stats}
        return stats
    
    def get_ward_distribution(self) -> List[Dict]:
        """
        Get application distribution by ward
        """
        ward_stats = self.queryset.values('ward').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            approved=Count('id', filter=Q(status='approved')),
            pending=Count('id', filter=Q(status='pending')),
            rejected=Count('id', filter=Q(status='rejected'))
        ).order_by('-count')
        
        return list(ward_stats)
    
    def get_institution_stats(self, limit=10) -> List[Dict]:
        """
        Get top institutions by application count
        """
        institution_stats = self.queryset.values('institution_name', 'institution_type').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            average_amount=Avg('amount'),
            approved_count=Count('id', filter=Q(status='approved'))
        ).order_by('-count')[:limit]
        
        return list(institution_stats)
    
    def get_level_of_study_distribution(self) -> List[Dict]:
        """
        Get distribution by level of study
        """
        level_stats = self.queryset.values('level_of_study').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            average_amount=Avg('amount')
        ).order_by('-count')
        
        return list(level_stats)
    
    def get_gender_distribution(self) -> Dict:
        """
        Get gender distribution with statistics
        """
        gender_stats = self.queryset.values('gender').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            approved=Count('id', filter=Q(status='approved'))
        )
        
        total = self.queryset.count() or 1
        
        result = {}
        for stat in gender_stats:
            gender = stat['gender']
            result[gender] = {
                **stat,
                'percentage': round((stat['count'] / total) * 100, 2)
            }
        
        return result
    
    def get_family_status_distribution(self) -> List[Dict]:
        """
        Get distribution by family status
        """
        family_stats = self.queryset.values('family_status').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            approved=Count('id', filter=Q(status='approved'))
        ).order_by('-count')
        
        return list(family_stats)
    
    def get_disability_stats(self) -> Dict:
        """
        Get statistics for applicants with disabilities
        """
        disability_count = self.queryset.filter(disability=True).count()
        total = self.queryset.count() or 1
        
        disability_stats = self.queryset.filter(disability=True).aggregate(
            count=Count('id'),
            total_amount=Sum('amount'),
            approved=Count('id', filter=Q(status='approved'))
        )
        
        return {
            **disability_stats,
            'percentage': round((disability_count / total) * 100, 2)
        }
    
    def get_submission_timeline(self, days=30) -> List[Dict]:
        """
        Get daily submission counts for the last N days
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        timeline = self.queryset.filter(
            submitted_at__gte=cutoff_date
        ).annotate(
            date=TruncDate('submitted_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        return list(timeline)
    
    def get_monthly_trends(self, months=6) -> List[Dict]:
        """
        Get monthly application trends
        """
        cutoff_date = timezone.now() - timedelta(days=months*30)
        
        trends = self.queryset.filter(
            submitted_at__gte=cutoff_date
        ).annotate(
            month=TruncMonth('submitted_at')
        ).values('month').annotate(
            total_applications=Count('id'),
            approved=Count('id', filter=Q(status='approved')),
            rejected=Count('id', filter=Q(status='rejected')),
            total_amount=Sum('amount')
        ).order_by('month')
        
        return list(trends)
    
    def get_amount_distribution(self) -> Dict:
        """
        Get distribution of requested amounts
        """
        ranges = [
            (0, 10000, '0-10K'),
            (10000, 30000, '10K-30K'),
            (30000, 50000, '30K-50K'),
            (50000, 100000, '50K-100K'),
            (100000, float('inf'), '100K+')
        ]
        
        distribution = {}
        for min_amount, max_amount, label in ranges:
            count = self.queryset.filter(
                amount__gte=min_amount,
                amount__lt=max_amount
            ).count()
            
            distribution[label] = count
        
        return distribution
    
    def get_processing_time_stats(self) -> Dict:
        """
        Calculate average processing time for applications
        """
        from .models import ApplicationStatusLog
        
        # Get applications with status changes
        processed_apps = ApplicationStatusLog.objects.filter(
            new_status__in=['approved', 'rejected']
        ).values('application').annotate(
            processing_time=F('changed_at') - F('application__submitted_at')
        )
        
        if not processed_apps:
            return {
                'average_days': 0,
                'fastest_days': 0,
                'slowest_days': 0
            }
        
        times = [pt['processing_time'].days for pt in processed_apps]
        
        return {
            'average_days': round(sum(times) / len(times), 1),
            'fastest_days': min(times),
            'slowest_days': max(times)
        }
    
    def get_comprehensive_report(self) -> Dict:
        """
        Get complete analytics report
        """
        return {
            'overview': self.get_overview_stats(),
            'ward_distribution': self.get_ward_distribution(),
            'top_institutions': self.get_institution_stats(),
            'level_distribution': self.get_level_of_study_distribution(),
            'gender_stats': self.get_gender_distribution(),
            'family_status': self.get_family_status_distribution(),
            'disability_stats': self.get_disability_stats(),
            'amount_distribution': self.get_amount_distribution(),
            'processing_time': self.get_processing_time_stats(),
            'monthly_trends': self.get_monthly_trends(),
            'generated_at': timezone.now().isoformat()
        }


# =========================
# Analytics API Views
# =========================
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAdminUser])
def analytics_overview(request):
    """Get overview analytics"""
    analytics = BursaryAnalytics()
    return Response(analytics.get_overview_stats())


@api_view(['GET'])
@permission_classes([IsAdminUser])
def analytics_comprehensive(request):
    """Get comprehensive analytics report"""
    from .models import BursaryApplication
    
    # Allow filtering
    queryset = BursaryApplication.objects.all()
    
    # Filter by date range
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if start_date:
        queryset = queryset.filter(submitted_at__gte=start_date)
    if end_date:
        queryset = queryset.filter(submitted_at__lte=end_date)
    
    # Filter by status
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # Filter by ward
    ward = request.query_params.get('ward')
    if ward:
        queryset = queryset.filter(ward=ward)
    
    analytics = BursaryAnalytics(queryset)
    return Response(analytics.get_comprehensive_report())


@api_view(['GET'])
@permission_classes([IsAdminUser])
def export_analytics_csv(request):
    """Export analytics as CSV"""
    from django.http import HttpResponse
    import csv
    
    analytics = BursaryAnalytics()
    overview = analytics.get_overview_stats()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="analytics_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Metric', 'Value'])
    
    for key, value in overview.items():
        writer.writerow([key.replace('_', ' ').title(), value])
    
    return response


@api_view(['GET'])
@permission_classes([IsAdminUser])
def export_applications_csv(request):
    """Export applications to CSV with optional filters, optimized for large datasets"""
    from django.http import StreamingHttpResponse
    import csv
    import io
    from .models import BursaryApplication

    qs = BursaryApplication.objects.all().order_by('-submitted_at')

    # Filters
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    status_filter = request.query_params.get('status')
    ward = request.query_params.get('ward')

    if start_date:
        qs = qs.filter(submitted_at__gte=start_date)
    if end_date:
        qs = qs.filter(submitted_at__lte=end_date)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if ward:
        qs = qs.filter(ward=ward)

    headers = [
        'Reference Number','Full Name','Gender','Disability','ID Number',
        'Phone Number','Guardian Phone','Guardian ID','Ward','Village',
        'Chief Name','Chief Phone','Sub Chief Name','Sub Chief Phone',
        'Level of Study','Institution Type','Institution Name','Admission Number',
        'Amount','Mode of Study','Year of Study','Family Status',
        'Father Income','Mother Income','Status','Submitted At',
        'Email','Confirmation','Data Consent','Communication Consent'
    ]

    def row_iter():
        # UTF-8 BOM for Excel compatibility
        yield '\ufeff'
        # Write header
        sio = io.StringIO()
        w = csv.writer(sio)
        w.writerow(headers)
        yield sio.getvalue()
        batch_size = 1000
        total = qs.count()
        for start in range(0, total, batch_size):
            for obj in qs[start:start+batch_size]:
                submitted = obj.submitted_at
                if submitted:
                    from django.utils import timezone as tz
                    submitted = tz.localtime(submitted) if tz.is_aware(submitted) else submitted
                    submitted_str = submitted.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    submitted_str = ''
                sio = io.StringIO()
                w = csv.writer(sio)
                w.writerow([
                    obj.reference_number or '',
                    obj.full_name or '',
                    obj.gender or '',
                    'Yes' if getattr(obj, 'disability', False) else 'No',
                    obj.id_number or '',
                    obj.phone_number or '',
                    obj.guardian_phone or '',
                    getattr(obj, 'guardian_id', '') or '',
                    obj.ward or '',
                    obj.village or '',
                    getattr(obj, 'chief_name', '') or '',
                    getattr(obj, 'chief_phone', '') or '',
                    getattr(obj, 'sub_chief_name', '') or '',
                    getattr(obj, 'sub_chief_phone', '') or '',
                    getattr(obj, 'level_of_study', '') or '',
                    getattr(obj, 'institution_type', '') or '',
                    obj.institution_name or '',
                    getattr(obj, 'admission_number', '') or '',
                    obj.amount if obj.amount is not None else '',
                    getattr(obj, 'mode_of_study', '') or '',
                    getattr(obj, 'year_of_study', '') or '',
                    getattr(obj, 'family_status', '') or '',
                    getattr(obj, 'father_income', '') or '',
                    getattr(obj, 'mother_income', '') or '',
                    obj.status or '',
                    submitted_str,
                    obj.email or '',
                    'Yes' if getattr(obj, 'confirmation', False) else 'No',
                    'Yes' if getattr(obj, 'data_consent', False) else 'No',
                    'Yes' if getattr(obj, 'communication_consent', False) else 'No'
                ])
                yield sio.getvalue()

    resp = StreamingHttpResponse(row_iter(), content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename="bursary_applications.csv"'
    return resp

@api_view(['GET'])
@permission_classes([IsAdminUser])
def export_applications_xlsx(request):
    from django.http import HttpResponse
    from openpyxl import Workbook
    from .models import BursaryApplication
    qs = BursaryApplication.objects.all().order_by('-submitted_at')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    status_filter = request.query_params.get('status')
    ward = request.query_params.get('ward')
    if start_date:
        qs = qs.filter(submitted_at__gte=start_date)
    if end_date:
        qs = qs.filter(submitted_at__lte=end_date)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if ward:
        qs = qs.filter(ward=ward)
    wb = Workbook()
    ws = wb.active
    ws.title = 'Applications'
    headers = [
        'Reference Number','Full Name','Gender','Disability','ID Number',
        'Phone Number','Guardian Phone','Guardian ID','Ward','Village',
        'Chief Name','Chief Phone','Sub Chief Name','Sub Chief Phone',
        'Level of Study','Institution Type','Institution Name','Admission Number',
        'Amount','Mode of Study','Year of Study','Family Status',
        'Father Income','Mother Income','Status','Submitted At',
        'Email','Confirmation','Data Consent','Communication Consent'
    ]
    ws.append(headers)
    from django.utils import timezone as tz
    for obj in qs.iterator():
        submitted = obj.submitted_at
        if submitted:
            submitted = tz.localtime(submitted) if tz.is_aware(submitted) else submitted
            submitted_str = submitted.strftime('%Y-%m-%d %H:%M:%S')
        else:
            submitted_str = ''
        ws.append([
            obj.reference_number or '',
            obj.full_name or '',
            obj.gender or '',
            'Yes' if getattr(obj, 'disability', False) else 'No',
            obj.id_number or '',
            obj.phone_number or '',
            obj.guardian_phone or '',
            getattr(obj, 'guardian_id', '') or '',
            obj.ward or '',
            obj.village or '',
            getattr(obj, 'chief_name', '') or '',
            getattr(obj, 'chief_phone', '') or '',
            getattr(obj, 'sub_chief_name', '') or '',
            getattr(obj, 'sub_chief_phone', '') or '',
            getattr(obj, 'level_of_study', '') or '',
            getattr(obj, 'institution_type', '') or '',
            obj.institution_name or '',
            getattr(obj, 'admission_number', '') or '',
            obj.amount if obj.amount is not None else '',
            getattr(obj, 'mode_of_study', '') or '',
            getattr(obj, 'year_of_study', '') or '',
            getattr(obj, 'family_status', '') or '',
            getattr(obj, 'father_income', '') or '',
            getattr(obj, 'mother_income', '') or '',
            obj.status or '',
            submitted_str,
            obj.email or '',
            'Yes' if getattr(obj, 'confirmation', False) else 'No',
            'Yes' if getattr(obj, 'data_consent', False) else 'No',
            'Yes' if getattr(obj, 'communication_consent', False) else 'No'
        ])
    from io import BytesIO
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    resp = HttpResponse(stream.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="bursary_applications.xlsx"'
    return resp


# =========================
# Analytics Dashboard View (HTML)
# =========================
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def analytics_dashboard_view(request):
    """
    Render analytics dashboard page
    """
    from .models import BursaryApplication
    
    analytics = BursaryAnalytics()
    
    context = {
        'overview': analytics.get_overview_stats(),
        'ward_distribution': analytics.get_ward_distribution(),
        'top_institutions': analytics.get_institution_stats(5),
        'gender_stats': analytics.get_gender_distribution(),
        'disability_stats': analytics.get_disability_stats(),
        'monthly_trends': analytics.get_monthly_trends(6),
        'title': 'Bursary Analytics Dashboard'
    }
    
    return render(request, 'admin/dashboard.html', context)


# =========================
# Add to urls.py
# =========================
"""
from .analytics import (
    analytics_overview,
    analytics_comprehensive,
    export_analytics_csv,
    analytics_dashboard_view
)

urlpatterns += [
    path('analytics/overview/', analytics_overview, name='analytics-overview'),
    path('analytics/comprehensive/', analytics_comprehensive, name='analytics-comprehensive'),
    path('analytics/export-csv/', export_analytics_csv, name='analytics-export'),
    path('analytics/dashboard/', analytics_dashboard_view, name='analytics-dashboard'),
]
"""


# =========================
# Dashboard Template (Simplified)
# =========================
ANALYTICS_DASHBOARD_TEMPLATE = """
{% extends "admin/base_site.html" %}
{% load static %}

{% block extrahead %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
    .analytics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }
    .stat-card {
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #006400;
    }
    .stat-label {
        color: #666;
        font-size: 0.9rem;
    }
    .chart-container {
        background: white;
        padding: 20px;
        border-radius: 8px;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
{% endblock %}

{% block content %}
<h1>Bursary Analytics Dashboard</h1>

<div class="analytics-grid">
    <div class="stat-card">
        <div class="stat-value">{{ overview.total_applications }}</div>
        <div class="stat-label">Total Applications</div>
    </div>
    
    <div class="stat-card">
        <div class="stat-value">{{ overview.approval_rate }}%</div>
        <div class="stat-label">Approval Rate</div>
    </div>
    
    <div class="stat-card">
        <div class="stat-value">KSh {{ overview.total_amount_requested|floatformat:0 }}</div>
        <div class="stat-label">Total Requested</div>
    </div>
    
    <div class="stat-card">
        <div class="stat-value">KSh {{ overview.approved_amount|floatformat:0 }}</div>
        <div class="stat-label">Total Approved</div>
    </div>
</div>

<div class="chart-container">
    <h2>Applications by Ward</h2>
    <canvas id="wardChart"></canvas>
</div>

<div class="chart-container">
    <h2>Gender Distribution</h2>
    <canvas id="genderChart"></canvas>
</div>

<script>
// Ward Chart
const wardCtx = document.getElementById('wardChart').getContext('2d');
new Chart(wardCtx, {
    type: 'bar',
    data: {
        labels: {{ ward_distribution|safe }}.map(w => w.ward),
        datasets: [{
            label: 'Applications',
            data: {{ ward_distribution|safe }}.map(w => w.count),
            backgroundColor: '#006400'
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: { beginAtZero: true }
        }
    }
});

// Gender Chart
const genderCtx = document.getElementById('genderChart').getContext('2d');
new Chart(genderCtx, {
    type: 'pie',
    data: {
        labels: Object.keys({{ gender_stats|safe }}),
        datasets: [{
            data: Object.values({{ gender_stats|safe }}).map(g => g.count),
            backgroundColor: ['#006400', '#bb0000']
        }]
    }
});
</script>
{% endblock %}
"""