# ===========================
# core/views.py (CLEANED)
# ===========================
from django.http import JsonResponse

def health(request):
    """Health check endpoint for monitoring"""
    return JsonResponse({"status": "Backend is live"})