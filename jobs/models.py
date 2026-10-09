from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

class Company(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company')
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Job(models.Model):
    JOB_TYPE_CHOICES = (
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Remote', 'Remote'),
        ('Contract', 'Contract'),
    )

    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=200)
    # NOTE: Two sources of truth for company name exist:
    #   1. This free-text field (set at job creation)
    #   2. job.recruiter.company.name (linked Company object)
    # Templates currently prefer this field when present, falling back to
    # the linked Company. Future refactor: drop this field entirely or
    # auto-populate it in Job.save() from the recruiter's Company.
    company_name = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=150)
    salary = models.CharField(max_length=100, blank=True, null=True)
    skills = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES, default='Full-time')
    posted_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-posted_on']

    def __str__(self):
        return self.title

    @property
    def formatted_salary(self):
        if not self.salary:
            return ""
        
        import re
        
        def format_inr(match):
            s = match.group(0).replace(',', '')
            if len(s) > 3:
                s = re.sub(r'(\d)(?=(\d{2})+(?!\d))', r'\1,', s[:-3]) + ',' + s[-3:]
            return f"₹{s}"
            
        text = self.salary.replace('$', '').replace('₹', '')
        formatted = re.sub(r'\b\d+(?:,\d+)*\b', format_inr, text)
        
        if 'per annum' not in formatted.lower() and 'lpa' not in formatted.lower():
            formatted += ' per annum'
            
        return formatted

class Application(models.Model):
    STATUS_CHOICES = (
        ('APPLIED', 'Applied'),
        ('SHORTLISTED', 'Shortlisted'),
        ('REJECTED', 'Rejected'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    resume = models.FileField(
        upload_to='resumes/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLIED')
    applied_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-applied_at']
        unique_together = ('job', 'candidate')

    def __str__(self):
        return f"{self.candidate.username} - {self.job.title}"

class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"
