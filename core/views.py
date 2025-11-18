from django.shortcuts import render
from django.http import JsonResponse

def health(request):
    """Health check endpoint for monitoring"""
    return JsonResponse({"status": "Backend is live"})

def home(request):
    """Render the homepage"""
    return render(request, 'index.html')
