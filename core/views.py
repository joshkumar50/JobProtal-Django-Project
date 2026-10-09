from django.shortcuts import render
from jobs.models import Job

def home(request):
    latest_jobs = Job.objects.filter(is_active=True).order_by('-posted_on')[:6]
    return render(request, 'core/home.html', {'latest_jobs': latest_jobs})
