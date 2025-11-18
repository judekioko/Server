from django.shortcuts import render
from django.http import JsonResponse

def home(request):
    return render(request, 'Tertiary/index.html')

def health(request):
    return JsonResponse({'status': 'ok'})
