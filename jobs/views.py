from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from .models import Job, Application, Company, SavedJob
from .forms import ApplicationForm
from django.utils.decorators import method_decorator
from accounts.decorators import recruiter_required, candidate_required

class JobListView(ListView):
    model = Job
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True).order_by('-posted_on')
        query = self.request.GET.get('q')
        location = self.request.GET.get('location')
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(company_name__icontains=query) |
                Q(skills__icontains=query) |
                Q(description__icontains=query)
            )
            
        if location:
            queryset = queryset.filter(location__icontains=location)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['location'] = self.request.GET.get('location', '')
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'CANDIDATE':
            saved_job_ids = SavedJob.objects.filter(user=self.request.user).values_list('job_id', flat=True)
            context['saved_job_ids'] = list(saved_job_ids)
        else:
            context['saved_job_ids'] = []
        return context

class JobDetailView(DetailView):
    model = Job
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'

    def get_queryset(self):
        qs = Job.objects.all()
        if self.request.user.is_authenticated:
            return qs.filter(
                Q(is_active=True) |
                Q(recruiter=self.request.user)
            )
        return qs.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['has_applied'] = Application.objects.filter(job=self.object, candidate=self.request.user).exists()
            context['has_saved'] = SavedJob.objects.filter(job=self.object, user=self.request.user).exists()
        return context

@method_decorator(recruiter_required, name='dispatch')
class JobCreateView(CreateView):
    model = Job
    template_name = 'jobs/job_form.html'
    fields = ['title', 'company_name', 'job_type', 'description', 'skills', 'location', 'salary']
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.recruiter = self.request.user
        messages.success(self.request, "Job posted successfully!")
        return super().form_valid(form)

@method_decorator(recruiter_required, name='dispatch')
class JobUpdateView(UpdateView):
    model = Job
    template_name = 'jobs/job_form.html'
    fields = ['title', 'company_name', 'job_type', 'description', 'skills', 'location', 'salary']
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        return Job.objects.filter(recruiter=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Job updated successfully!")
        return super().form_valid(form)

@method_decorator(recruiter_required, name='dispatch')
class JobDeleteView(DeleteView):
    model = Job
    template_name = 'jobs/job_confirm_delete.html'
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        return Job.objects.filter(recruiter=self.request.user)
        
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Job deleted successfully!")
        return super().delete(request, *args, **kwargs)

@method_decorator(recruiter_required, name='dispatch')
class JobToggleActiveView(View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, recruiter=request.user)
        job.is_active = not job.is_active
        job.save()
        status = "activated" if job.is_active else "deactivated"
        messages.success(request, f"Job {status} successfully!")
        return redirect('dashboard')

@method_decorator(recruiter_required, name='dispatch')
class CompanyUpdateView(UpdateView):
    model = Company
    template_name = 'jobs/company_form.html'
    fields = ['name', 'logo', 'website', 'location', 'description']
    success_url = reverse_lazy('dashboard')

    def get_object(self, queryset=None):
        company, created = Company.objects.get_or_create(owner=self.request.user, defaults={'name': 'Your Company Name'})
        return company

    def form_valid(self, form):
        messages.success(self.request, "Company profile updated successfully!")
        return super().form_valid(form)

class CompanyDetailView(DetailView):
    model = Company
    template_name = 'jobs/company_detail.html'
    context_object_name = 'company'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add all active jobs for this company
        context['company_jobs'] = Job.objects.filter(recruiter__company=self.object, is_active=True).order_by('-posted_on')
        return context

@candidate_required
def apply_to_job(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)
    
    if Application.objects.filter(job=job, candidate=request.user).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.candidate = request.user
            from django.db import IntegrityError
            try:
                application.save()
            except IntegrityError:
                messages.warning(request, "You have already applied for this job.")
                return redirect('dashboard')
            messages.success(request, f"You have successfully applied to {job.title}!")
            return redirect('dashboard')
    else:
        form = ApplicationForm()
    
    return render(request, 'jobs/apply.html', {'job': job, 'form': form})

@method_decorator(recruiter_required, name='dispatch')
class JobApplicantsView(DetailView):
    model = Job
    template_name = 'jobs/job_applicants.html'
    context_object_name = 'job'
    
    def get_queryset(self):
        return Job.objects.filter(recruiter=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        status_filter = self.request.GET.get('status')
        applications = self.object.applications.all()
        if status_filter in dict(Application.STATUS_CHOICES):
            applications = applications.filter(status=status_filter)
            
        context['applications'] = applications
        context['status_filter'] = status_filter
        context['status_choices'] = Application.STATUS_CHOICES
        return context

@method_decorator(recruiter_required, name='dispatch')
class ChangeApplicationStatusView(View):
    def post(self, request, pk, status):
        application = get_object_or_404(Application, pk=pk, job__recruiter=request.user)
        
        if status in dict(Application.STATUS_CHOICES):
            application.status = status
            application.save()
            messages.success(request, f"Application status updated to {application.get_status_display()}.")
            
            # Send email notification
            subject = f"Update on your application for {application.job.title}"
            company_name = (
                application.job.company_name
                or getattr(getattr(application.job.recruiter, 'company', None), 'name', None)
                or application.job.recruiter.username
            )
            message = (
                f"Hello {application.candidate.first_name},\n\n"
                f"Your application status for the position of {application.job.title} "
                f"at {company_name} has been updated to: {application.get_status_display()}.\n\n"
                f"Thank you for applying!"
            )
            
            from django.core.mail import send_mail
            from django.conf import settings
            
            send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@jobportal.com'),
                [application.candidate.email],
                fail_silently=True,
            )
        else:
            messages.error(request, "Invalid status.")
            
        return redirect('job_applicants', pk=application.job.pk)

@method_decorator(candidate_required, name='dispatch')
class ToggleSavedJobView(View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, is_active=True)
        saved_job, created = SavedJob.objects.get_or_create(user=request.user, job=job)
        
        if not created:
            saved_job.delete()
            messages.success(request, f"Removed '{job.title}' from saved jobs.")
        else:
            messages.success(request, f"Saved '{job.title}' to your saved jobs.")
            
        # Redirect back to where they came from, or dashboard
        next_url = request.POST.get('next', 'job_detail')
        if next_url == 'saved_jobs':
            return redirect('saved_jobs')
        elif next_url == 'job_list':
            return redirect('job_list')
        return redirect('job_detail', pk=pk)

@method_decorator(candidate_required, name='dispatch')
class SavedJobListView(ListView):
    model = SavedJob
    template_name = 'jobs/saved_jobs.html'
    context_object_name = 'saved_jobs'
    
    def get_queryset(self):
        return SavedJob.objects.filter(user=self.request.user).select_related('job', 'job__recruiter', 'job__recruiter__company').order_by('-saved_at')
