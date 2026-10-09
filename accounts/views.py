from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import UserRegistrationForm, UserUpdateForm, ProfileUpdateForm
from .decorators import recruiter_required, candidate_required
from jobs.models import Job, Application

class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        # Profile is created by signal, update the role
        user.profile.role = form.cleaned_data['role']
        user.profile.save()
        
        login(self.request, user)
        messages.success(self.request, f"Welcome {user.username}! Your account has been created.")
        return redirect(self.success_url)

@login_required
def dashboard(request):
    """Redirects to the appropriate dashboard based on user role."""
    if request.user.profile.role == 'RECRUITER':
        return redirect('recruiter_dashboard')
    else:
        return redirect('candidate_dashboard')

@recruiter_required
def recruiter_dashboard(request):
    jobs = Job.objects.filter(recruiter=request.user)
    applications = Application.objects.filter(job__in=jobs).order_by('-applied_at')
    
    total_jobs = jobs.count()
    active_jobs = jobs.filter(is_active=True).count()
    total_applicants = applications.count()
    
    context = {
        'jobs': jobs,
        'applications': applications[:5],
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applicants': total_applicants,
    }
    return render(request, 'accounts/dashboard_recruiter.html', context)

@candidate_required
def candidate_dashboard(request):
    applications = Application.objects.filter(candidate=request.user)
    return render(request, 'accounts/dashboard_candidate.html', {'applications': applications})

@login_required
def profile_update(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('dashboard')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'accounts/profile_update.html', context)
