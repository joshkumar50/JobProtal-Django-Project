from django.contrib import admin
from .models import Company, Job, Application, SavedJob

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'location']
    search_fields = ['name', 'location']

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'recruiter', 'company_name', 'job_type', 'location', 'is_active', 'posted_on']
    list_filter = ['is_active', 'job_type', 'posted_on', 'recruiter']
    search_fields = ['title', 'description', 'location', 'skills', 'company_name', 'recruiter__username']
    actions = ['assign_to_me']

    @admin.action(description="Assign selected jobs to my recruiter account")
    def assign_to_me(self, request, queryset):
        if hasattr(request.user, 'profile') and request.user.profile.role == 'RECRUITER':
            count = queryset.update(recruiter=request.user)
            self.message_user(request, f"Successfully assigned {count} job(s) to {request.user.username}.")
        else:
            self.message_user(request, "Your account does not have the RECRUITER role.", level='error')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'job', 'status', 'applied_at']
    list_filter = ['status']
    search_fields = ['candidate__username', 'job__title']

@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'saved_at']
    list_filter = ['saved_at']
    search_fields = ['user__username', 'job__title']
