from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile
from jobs.models import Company, Job, Application, SavedJob
from django.core.files.uploadedfile import SimpleUploadedFile

class Command(BaseCommand):
    help = 'Seeds the database with realistic sample recruiters, candidates, companies, jobs, applications, and saved jobs.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recruiter',
            type=str,
            help='Assign seeded demo jobs to an existing recruiter username after seeding.',
        )

    def handle(self, *args, **options):
        self.stdout.write("Seeding realistic data...")

        # Clear existing data to prevent duplicates on multiple runs (optional but good for seed)
        # We will just use get_or_create though, to not destroy user data unless needed, but let's just make realistic unique data.

        # Create Recruiters
        recruiters_data = [
            {'username': 'sarah_hr', 'email': 'sarah@techcorp.com', 'first_name': 'Sarah', 'last_name': 'Connor'},
            {'username': 'michael_rec', 'email': 'michael@innovatellc.com', 'first_name': 'Michael', 'last_name': 'Scott'},
            {'username': 'jessica_tech', 'email': 'jessica@futureai.com', 'first_name': 'Jessica', 'last_name': 'Alba'},
        ]

        recruiters = []
        for data in recruiters_data:
            user, created = User.objects.get_or_create(username=data['username'], email=data['email'])
            if created:
                user.set_password('password123')
                user.first_name = data['first_name']
                user.last_name = data['last_name']
                user.save()
                user.profile.role = 'RECRUITER'
                user.profile.save()
            recruiters.append(user)

        # Create Companies
        companies_data = [
            {'owner': recruiters[0], 'name': 'TechCorp Solutions', 'location': 'New York, NY', 'website': 'https://techcorp.example.com', 'description': 'A leading provider of enterprise software solutions.'},
            {'owner': recruiters[1], 'name': 'Innovate LLC', 'location': 'Austin, TX', 'website': 'https://innovate.example.com', 'description': 'Fast-growing startup focusing on consumer mobile applications.'},
            {'owner': recruiters[2], 'name': 'Future AI', 'location': 'San Francisco, CA', 'website': 'https://futureai.example.com', 'description': 'Research and development company advancing artificial intelligence.'},
        ]

        companies = []
        for data in companies_data:
            company, _ = Company.objects.get_or_create(owner=data['owner'], defaults={
                'name': data['name'],
                'location': data['location'],
                'website': data['website'],
                'description': data['description']
            })
            companies.append(company)

        # Create Candidates
        candidates_data = [
            {'username': 'john_dev', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe', 'bio': 'Passionate backend developer with 5 years of Python experience.'},
            {'username': 'jane_frontend', 'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith', 'bio': 'Creative frontend engineer who loves React and CSS.'},
            {'username': 'alex_data', 'email': 'alex@example.com', 'first_name': 'Alex', 'last_name': 'Johnson', 'bio': 'Data scientist with a knack for machine learning and analytics.'},
        ]

        candidates = []
        for data in candidates_data:
            user, created = User.objects.get_or_create(username=data['username'], email=data['email'])
            if created:
                user.set_password('password123')
                user.first_name = data['first_name']
                user.last_name = data['last_name']
                user.save()
                user.profile.role = 'CANDIDATE'
                user.profile.bio = data['bio']
                user.profile.save()
            candidates.append(user)

        # Create Jobs
        jobs_data = [
            {'recruiter': recruiters[0], 'title': 'Senior Python Developer', 'company_name': 'TCS', 'job_type': 'Full-time', 'skills': 'Python, Django, PostgreSQL, Docker', 'location': 'Bangalore', 'salary': '1300000 - 1800000', 'description': 'We are looking for an experienced backend engineer to scale our core APIs...'},
            {'recruiter': recruiters[0], 'title': 'DevOps Engineer', 'company_name': 'Infosys', 'job_type': 'Contract', 'skills': 'AWS, Kubernetes, CI/CD', 'location': 'Pune', 'salary': '1200000', 'description': 'Join our infrastructure team to help maintain our high-availability services...'},
            {'recruiter': recruiters[1], 'title': 'React Developer', 'company_name': 'Wipro', 'job_type': 'Full-time', 'skills': 'React, Tailwind CSS, TypeScript', 'location': 'Chennai', 'salary': '800000 - 1200000', 'description': 'Help us build beautiful and responsive consumer applications using the latest web technologies...'},
            {'recruiter': recruiters[2], 'title': 'Data Analyst', 'company_name': 'Swiggy', 'job_type': 'Full-time', 'skills': 'Python, SQL, Pandas', 'location': 'Hyderabad', 'salary': '600000 - 900000', 'description': 'Push the boundaries of what is possible with data...'},
            {'recruiter': recruiters[2], 'title': 'Python Developer', 'company_name': 'Zomato', 'job_type': 'Remote', 'skills': 'SQL, Django, Python', 'location': 'Guntur', 'salary': '700000 - 1100000', 'description': 'Build robust data pipelines to support our application...'},
        ]

        jobs = []
        for data in jobs_data:
            job, _ = Job.objects.get_or_create(
                recruiter=data['recruiter'], title=data['title'],
                defaults={
                    'company_name': data['company_name'],
                    'job_type': data['job_type'],
                    'skills': data['skills'],
                    'location': data['location'],
                    'salary': data['salary'],
                    'description': data['description']
                }
            )
            jobs.append(job)

        # Create Applications
        dummy_resume = SimpleUploadedFile("resume.pdf", b"file_content", content_type="application/pdf")
        
        # John applies to Backend and ML
        Application.objects.get_or_create(job=jobs[0], candidate=candidates[0], defaults={'resume': dummy_resume, 'status': 'APPLIED'})
        Application.objects.get_or_create(job=jobs[3], candidate=candidates[0], defaults={'resume': dummy_resume, 'status': 'REJECTED'})
        
        # Jane applies to Frontend
        Application.objects.get_or_create(job=jobs[2], candidate=candidates[1], defaults={'resume': dummy_resume, 'status': 'SHORTLISTED'})

        # Alex applies to ML and Data Engineer
        Application.objects.get_or_create(job=jobs[3], candidate=candidates[2], defaults={'resume': dummy_resume, 'status': 'SHORTLISTED'})
        Application.objects.get_or_create(job=jobs[4], candidate=candidates[2], defaults={'resume': dummy_resume, 'status': 'APPLIED'})

        # Create Saved Jobs
        SavedJob.objects.get_or_create(user=candidates[0], job=jobs[1])
        SavedJob.objects.get_or_create(user=candidates[1], job=jobs[0])
        SavedJob.objects.get_or_create(user=candidates[2], job=jobs[2])

        self.stdout.write(self.style.SUCCESS("Successfully seeded realistic data!"))

        recruiter_username = options.get('recruiter')
        if recruiter_username:
            from django.core.management import call_command
            self.stdout.write(f"Assigning demo jobs to {recruiter_username}...")
            call_command('assign_demo_jobs', recruiter_username)
