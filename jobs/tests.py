from django.test import TestCase
from django.contrib.auth.models import User
from .models import Company, Job, Application, SavedJob
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.db import transaction

class JobsTestCase(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(username='recruiter', password='password')
        self.candidate = User.objects.create_user(username='candidate', password='password')
        
        self.company = Company.objects.create(
            owner=self.recruiter,
            name='Test Company'
        )
        
        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title='Software Engineer',
            location='Remote'
        )

    def test_company_creation(self):
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(self.company.owner, self.recruiter)

    def test_job_creation(self):
        self.assertEqual(Job.objects.count(), 1)
        self.assertEqual(self.job.title, 'Software Engineer')

    def test_application_creation(self):
        pdf_resume = SimpleUploadedFile("resume.pdf", b"file_content", content_type="application/pdf")
        app = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            resume=pdf_resume
        )
        self.assertEqual(Application.objects.count(), 1)
        self.assertEqual(app.status, 'APPLIED')

    def test_application_pdf_validation(self):
        txt_resume = SimpleUploadedFile("resume.txt", b"file_content", content_type="text/plain")
        app = Application(
            job=self.job,
            candidate=self.candidate,
            resume=txt_resume
        )
        # Should raise ValidationError due to FileExtensionValidator
        with self.assertRaises(ValidationError):
            app.full_clean()

    def test_saved_job_creation(self):
        saved_job = SavedJob.objects.create(user=self.candidate, job=self.job)
        self.assertEqual(SavedJob.objects.count(), 1)
        
    def test_unique_constraints(self):
        SavedJob.objects.create(user=self.candidate, job=self.job)
        with transaction.atomic():
            with self.assertRaises(Exception):
                SavedJob.objects.create(user=self.candidate, job=self.job)
                
        pdf_resume = SimpleUploadedFile("resume.pdf", b"file_content", content_type="application/pdf")
        Application.objects.create(job=self.job, candidate=self.candidate, resume=pdf_resume)
        with transaction.atomic():
            with self.assertRaises(Exception):
                Application.objects.create(job=self.job, candidate=self.candidate, resume=pdf_resume)

class JobCRUDTestCase(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(username='recruiter1', password='password123', email='r1@example.com')
        self.recruiter.profile.role = 'RECRUITER'
        self.recruiter.profile.save()
        
        self.candidate = User.objects.create_user(username='candidate1', password='password123', email='c1@example.com')
        self.candidate.profile.role = 'CANDIDATE'
        self.candidate.profile.save()

        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title='Old Job',
            description='Old Description',
            location='Old Location'
        )

    def test_job_create_view(self):
        self.client.login(username='recruiter1', password='password123')
        response = self.client.post('/jobs/create/', data={
            'title': 'New Job',
            'description': 'New Description',
            'location': 'New Location',
            'skills': 'Python',
            'salary': '$100k',
            'job_type': 'Full-time'
        })
        self.assertRedirects(response, '/accounts/dashboard/', fetch_redirect_response=False)
        self.assertTrue(Job.objects.filter(title='New Job').exists())

    def test_job_update_view(self):
        self.client.login(username='recruiter1', password='password123')
        response = self.client.post(f'/jobs/{self.job.id}/update/', data={
            'title': 'Updated Job',
            'description': 'Updated Description',
            'location': 'Updated Location',
            'job_type': 'Remote'
        })
        self.assertRedirects(response, '/accounts/dashboard/', fetch_redirect_response=False)
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, 'Updated Job')

    def test_job_delete_view(self):
        self.client.login(username='recruiter1', password='password123')
        response = self.client.post(f'/jobs/{self.job.id}/delete/')
        self.assertRedirects(response, '/accounts/dashboard/', fetch_redirect_response=False)
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())

    def test_job_toggle_active_view(self):
        self.client.login(username='recruiter1', password='password123')
        self.assertTrue(self.job.is_active)
        response = self.client.post(f'/jobs/{self.job.id}/toggle/')
        self.assertRedirects(response, '/accounts/dashboard/', fetch_redirect_response=False)
        self.job.refresh_from_db()
        self.assertFalse(self.job.is_active)

    def test_inactive_job_hidden_from_public_detail(self):
        self.job.is_active = False
        self.job.save()
        response = self.client.get(f'/jobs/{self.job.id}/')
        self.assertEqual(response.status_code, 404)

    def test_recruiter_can_view_own_inactive_job(self):
        self.job.is_active = False
        self.job.save()
        self.client.login(username='recruiter1', password='password123')
        response = self.client.get(f'/jobs/{self.job.id}/')
        self.assertEqual(response.status_code, 200)

    def test_permissions(self):
        self.client.login(username='candidate1', password='password123')
        
        # Candidate tries to create job
        response = self.client.get('/jobs/create/')
        self.assertEqual(response.status_code, 302)
        
        # Candidate tries to edit job
        response = self.client.get(f'/jobs/{self.job.id}/update/')
        self.assertEqual(response.status_code, 302)

class ApplicationFlowTestCase(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(username='recruiter1', password='password123', email='r1@example.com')
        self.recruiter.profile.role = 'RECRUITER'
        self.recruiter.profile.save()
        
        self.candidate = User.objects.create_user(username='candidate1', password='password123', email='c1@example.com')
        self.candidate.profile.role = 'CANDIDATE'
        self.candidate.profile.save()

        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title='Test Job',
            description='Test Description',
            location='Test Location'
        )

    def test_successful_application(self):
        self.client.login(username='candidate1', password='password123')
        pdf_resume = SimpleUploadedFile("resume.pdf", b"dummy pdf content", content_type="application/pdf")
        
        response = self.client.post(f'/jobs/{self.job.id}/apply/', {'resume': pdf_resume})
        self.assertRedirects(response, '/accounts/dashboard/', fetch_redirect_response=False)
        self.assertEqual(Application.objects.count(), 1)
        self.assertEqual(Application.objects.first().candidate, self.candidate)

    def test_duplicate_application_prevention(self):
        pdf_resume = SimpleUploadedFile("resume.pdf", b"dummy pdf content", content_type="application/pdf")
        Application.objects.create(job=self.job, candidate=self.candidate, resume=pdf_resume)
        
        self.client.login(username='candidate1', password='password123')
        pdf_resume2 = SimpleUploadedFile("resume2.pdf", b"dummy pdf content", content_type="application/pdf")
        response = self.client.post(f'/jobs/{self.job.id}/apply/', {'resume': pdf_resume2})
        
        # Should redirect to dashboard and show a warning
        self.assertRedirects(response, '/accounts/dashboard/', fetch_redirect_response=False)
        self.assertEqual(Application.objects.count(), 1) # Still 1

    def test_pdf_validation_in_view(self):
        self.client.login(username='candidate1', password='password123')
        txt_resume = SimpleUploadedFile("resume.txt", b"dummy txt content", content_type="text/plain")
        
        response = self.client.post(f'/jobs/{self.job.id}/apply/', {'resume': txt_resume})
        self.assertEqual(response.status_code, 200) # Form validation failed, re-renders page
        self.assertContains(response, "Allowed extensions are: pdf")
        self.assertEqual(Application.objects.count(), 0)

class ApplicantManagementTestCase(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(username='recruiter1', password='password123', email='r1@example.com')
        self.recruiter.profile.role = 'RECRUITER'
        self.recruiter.profile.save()
        
        self.candidate = User.objects.create_user(username='candidate1', password='password123', email='c1@example.com')
        self.candidate.profile.role = 'CANDIDATE'
        self.candidate.profile.save()

        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title='Test Job',
            description='Test Description',
            location='Test Location'
        )
        
        pdf_resume = SimpleUploadedFile("resume.pdf", b"dummy pdf content", content_type="application/pdf")
        self.application = Application.objects.create(job=self.job, candidate=self.candidate, resume=pdf_resume)

    def test_status_change_and_email(self):
        self.client.login(username='recruiter1', password='password123')
        
        from django.core import mail
        
        response = self.client.post(f'/jobs/application/{self.application.id}/status/SHORTLISTED/')
        self.assertRedirects(response, f'/jobs/{self.job.id}/applicants/', fetch_redirect_response=False)
        
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'SHORTLISTED')
        
        # Test if email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"Update on your application for {self.job.title}")
        self.assertIn("Shortlisted", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ['c1@example.com'])

class SavedJobsTestCase(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(username='recruiter1', password='password123', email='r1@example.com')
        self.recruiter.profile.role = 'RECRUITER'
        self.recruiter.profile.save()
        
        self.candidate = User.objects.create_user(username='candidate1', password='password123', email='c1@example.com')
        self.candidate.profile.role = 'CANDIDATE'
        self.candidate.profile.save()

        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title='Test Job to Save',
            description='Test Description',
            location='Test Location'
        )

    def test_save_and_unsave_job(self):
        self.client.login(username='candidate1', password='password123')
        
        # Save Job
        response = self.client.post(f'/jobs/{self.job.id}/save/')
        self.assertRedirects(response, f'/jobs/{self.job.id}/', fetch_redirect_response=False)
        self.assertTrue(SavedJob.objects.filter(user=self.candidate, job=self.job).exists())
        
        # Unsave Job
        response = self.client.post(f'/jobs/{self.job.id}/save/')
        self.assertRedirects(response, f'/jobs/{self.job.id}/', fetch_redirect_response=False)
        self.assertFalse(SavedJob.objects.filter(user=self.candidate, job=self.job).exists())

    def test_saved_jobs_view(self):
        self.client.login(username='candidate1', password='password123')
        SavedJob.objects.create(user=self.candidate, job=self.job)
        
        response = self.client.get('/jobs/saved/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Job to Save')

class CompanyProfileTestCase(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(username='recruiter1', password='password123', email='r1@example.com')
        self.recruiter.profile.role = 'RECRUITER'
        self.recruiter.profile.save()
        
        self.company = Company.objects.create(
            owner=self.recruiter,
            name='Tech Corp',
            location='New York',
            description='Tech solutions'
        )

        self.candidate = User.objects.create_user(username='candidate1', password='password123', email='c1@example.com')
        self.candidate.profile.role = 'CANDIDATE'
        self.candidate.profile.save()

    def test_company_detail_view(self):
        # Create an active job for the company
        Job.objects.create(recruiter=self.recruiter, title='Company Job 1', location='NY', description='Desc')
        
        response = self.client.get(f'/jobs/company/{self.company.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tech Corp')
        self.assertContains(response, 'Company Job 1')

    def test_company_update_permissions(self):
        # Unauthenticated
        response = self.client.get('/jobs/company/')
        self.assertEqual(response.status_code, 302)
        
        # Candidate should be forbidden (redirected to login via user_passes_test)
        self.client.login(username='candidate1', password='password123')
        response = self.client.get('/jobs/company/')
        self.assertEqual(response.status_code, 302)
        
        # Recruiter should access their company update form
        self.client.login(username='recruiter1', password='password123')
        response = self.client.get('/jobs/company/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tech Corp')

    def test_company_update_post(self):
        self.client.login(username='recruiter1', password='password123')
        response = self.client.post('/jobs/company/', {
            'name': 'New Tech Corp',
            'location': 'San Francisco',
            'website': 'https://example.com'
        })
        self.assertRedirects(response, '/accounts/dashboard/', fetch_redirect_response=False)
        self.company.refresh_from_db()
        self.assertEqual(self.company.name, 'New Tech Corp')
        self.assertEqual(self.company.location, 'San Francisco')

class JobSearchTestCase(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(username='recruiter1', password='password123', email='r1@example.com')
        Job.objects.create(recruiter=self.recruiter, title='Backend Developer', skills='Python Django', location='Remote', description='Backend job')
        Job.objects.create(recruiter=self.recruiter, title='Frontend Developer', skills='React Tailwind', location='Remote', description='Frontend job')
        Job.objects.create(recruiter=self.recruiter, title='Data Scientist', skills='Machine Learning', location='New York', description='Data job')

    def test_search_by_title(self):
        response = self.client.get('/jobs/?q=Backend')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Backend Developer')
        self.assertNotContains(response, 'Frontend Developer')

    def test_search_by_description(self):
        response = self.client.get('/jobs/?q=Python')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Backend Developer')

    def test_search_by_location(self):
        response = self.client.get('/jobs/?location=York')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Data Scientist')
        self.assertNotContains(response, 'Frontend Developer')
