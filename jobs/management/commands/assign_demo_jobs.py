from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from jobs.models import Job, Company, Application, SavedJob

# Default demo recruiter usernames created by seed_data
DEMO_RECRUITERS = ['sarah_hr', 'michael_rec', 'jessica_tech']


class Command(BaseCommand):
    help = (
        'Safely reassigns demo jobs and associates company profiles to a target recruiter account. '
        'Preserves all applicant records, resumes, and saved jobs.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'target',
            nargs='?',
            type=str,
            default=None,
            help='Target recruiter username to receive ownership of demo jobs (e.g. "Recruiter").'
        )
        parser.add_argument(
            '--recruiter', '-r',
            type=str,
            dest='recruiter_opt',
            help='Alternative flag to specify the target recruiter username.'
        )
        parser.add_argument(
            '--from', '-f',
            dest='from_recruiter',
            type=str,
            help='Only transfer jobs from this specific source recruiter (e.g. "sarah_hr").'
        )
        parser.add_argument(
            '--job-ids',
            nargs='+',
            type=int,
            help='Transfer only specific job IDs (e.g. --job-ids 1 2 4).'
        )
        parser.add_argument(
            '--company-name',
            type=str,
            help='Set or update the company name for the target recruiter (e.g. "TechCorp Solutions").'
        )
        parser.add_argument(
            '--sync-company',
            action='store_true',
            default=True,
            help='Ensure target recruiter has an active, populated Company record (default: True).'
        )
        parser.add_argument(
            '--include-all',
            action='store_true',
            default=False,
            help='Allow transferring jobs not created by sample demo recruiters (safety guard).'
        )
        parser.add_argument(
            '--list', '-l',
            action='store_true',
            help='List current jobs, their current owners, companies, and applicant counts without modifying anything.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the transfer and display planned changes without modifying the database.'
        )

    def handle(self, *args, **options):
        # 1. Handle --list flag
        if options['list']:
            self.list_current_jobs()
            return

        # 2. Determine target recruiter username
        target_username = options['target'] or options['recruiter_opt']
        if not target_username:
            # If no target specified, show helpful guidance and available recruiters
            self.stdout.write(self.style.WARNING("No target recruiter username provided."))
            self.print_available_recruiters()
            self.stdout.write(
                "\nUsage:\n"
                "  python manage.py assign_demo_jobs <username>\n"
                "  python manage.py assign_demo_jobs --recruiter <username>\n"
                "  python manage.py assign_demo_jobs --list\n"
            )
            return

        # 3. Validate target user
        target_user = self.get_and_validate_target_user(target_username)

        # 4. Resolve source jobs to transfer
        jobs_to_transfer = self.resolve_jobs(options)

        if not jobs_to_transfer.exists():
            self.stdout.write(self.style.WARNING("No matching jobs found to transfer."))
            return

        is_dry_run = options['dry_run']
        if is_dry_run:
            self.stdout.write(self.style.NOTICE("=== DRY RUN MODE: No database changes will be committed ==="))

        # 5. Perform the transfer inside an atomic transaction
        with transaction.atomic():
            transferred_records = []
            for job in jobs_to_transfer:
                prev_recruiter = job.recruiter.username
                app_count = job.applications.count()
                saved_count = job.saved_by.count()

                if not is_dry_run:
                    job.recruiter = target_user
                    job.save(update_fields=['recruiter'])

                transferred_records.append({
                    'id': job.id,
                    'title': job.title,
                    'company_name': job.company_name,
                    'from': prev_recruiter,
                    'to': target_user.username,
                    'applications': app_count,
                    'saved': saved_count,
                    'is_active': job.is_active,
                })

            # 6. Synchronize / associate Company record for target recruiter
            company_status = self.sync_target_company(
                target_user=target_user,
                custom_name=options.get('company_name'),
                is_dry_run=is_dry_run
            )

            if is_dry_run:
                # Force rollback in dry run
                transaction.set_rollback(True)

        # 7. Print summary report
        self.print_summary(target_user, transferred_records, company_status, is_dry_run)

    def list_current_jobs(self):
        self.stdout.write(self.style.SUCCESS("\n--- Existing Jobs in Database ---"))
        jobs = Job.objects.all().select_related('recruiter').order_by('id')
        if not jobs.exists():
            self.stdout.write("No jobs found in database.")
            return

        header = f"{'ID':<4} | {'Title':<28} | {'Company':<20} | {'Recruiter':<16} | {'Applicants':<10} | {'Status'}"
        self.stdout.write(header)
        self.stdout.write("-" * len(header))
        for j in jobs:
            status = "Active" if j.is_active else "Inactive"
            comp = j.company_name or (j.recruiter.company.name if hasattr(j.recruiter, 'company') else '-')
            self.stdout.write(f"{j.id:<4} | {j.title[:28]:<28} | {comp[:20]:<20} | {j.recruiter.username:<16} | {j.applications.count():<10} | {status}")
        self.stdout.write("")

    def print_available_recruiters(self):
        recruiters = User.objects.filter(profile__role='RECRUITER').order_by('username')
        self.stdout.write("\nAvailable Recruiter Accounts:")
        for r in recruiters:
            is_demo = " (Sample Demo Account)" if r.username in DEMO_RECRUITERS else " (Custom Recruiter)"
            comp = r.company.name if hasattr(r, 'company') else "No company"
            self.stdout.write(f"  - {r.username:<15} [Email: {r.email}] [Company: {comp}]{is_demo}")

    def get_and_validate_target_user(self, username):
        # Case-insensitive matching for user convenience
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            available = list(User.objects.filter(profile__role='RECRUITER').values_list('username', flat=True))
            raise CommandError(
                f"User '{username}' does not exist in the database.\n"
                f"Available recruiter accounts: {', '.join(available) if available else 'None'}"
            )

        # Verify role is RECRUITER
        if not hasattr(user, 'profile') or user.profile.role != 'RECRUITER':
            role = user.profile.role if hasattr(user, 'profile') else 'Unknown'
            raise CommandError(
                f"User '{user.username}' has role '{role}'. "
                "Only accounts with role 'RECRUITER' can own and manage jobs."
            )

        return user

    def resolve_jobs(self, options):
        qs = Job.objects.all().select_related('recruiter')

        # Filter by specific job IDs if requested
        if options.get('job_ids'):
            qs = qs.filter(id__in=options['job_ids'])
            return qs

        # Filter by specific source recruiter
        if options.get('from_recruiter'):
            from_username = options['from_recruiter']
            qs = qs.filter(recruiter__username__iexact=from_username)
            return qs

        # By default, transfer jobs belonging to the standard demo recruiters
        if not options.get('include_all'):
            qs = qs.filter(recruiter__username__in=DEMO_RECRUITERS)

        return qs

    def sync_target_company(self, target_user, custom_name=None, is_dry_run=False):
        """
        Ensures the target recruiter has an active, realistic Company profile
        so their recruiter dashboard displays professional branding.
        """
        # Determine best company details
        default_name = custom_name or "TechCorp Solutions"
        default_location = "Bangalore, India"
        default_website = "https://techcorp.example.com"
        default_description = "A leading provider of innovative enterprise solutions and digital platforms."

        if hasattr(target_user, 'company'):
            company = target_user.company
            # Update placeholder if necessary
            if custom_name:
                if not is_dry_run:
                    company.name = custom_name
                    company.save()
                return f"Updated existing company name to '{custom_name}'"
            elif company.name in ['Your Company Name', '', None]:
                if not is_dry_run:
                    company.name = default_name
                    company.location = default_location
                    company.website = default_website
                    company.description = default_description
                    company.save()
                return f"Populated company profile with '{default_name}'"
            return f"Retained existing company '{company.name}'"
        else:
            if not is_dry_run:
                Company.objects.create(
                    owner=target_user,
                    name=default_name,
                    location=default_location,
                    website=default_website,
                    description=default_description
                )
            return f"Created new company profile '{default_name}'"

    def print_summary(self, target_user, records, company_status, is_dry_run):
        action = "WOULD TRANSFER" if is_dry_run else "SUCCESSFULLY TRANSFERRED"
        self.stdout.write(self.style.SUCCESS(f"\n=================================================="))
        self.stdout.write(self.style.SUCCESS(f" {action} DEMO JOBS"))
        self.stdout.write(self.style.SUCCESS(f"=================================================="))
        self.stdout.write(f"Target Recruiter: {self.style.SUCCESS(target_user.username)} ({target_user.email})")
        self.stdout.write(f"Company Status  : {company_status}")
        self.stdout.write(f"Jobs Count      : {len(records)}")
        
        total_apps = sum(r['applications'] for r in records)
        self.stdout.write(f"Applicants Kept : {total_apps} (all resumes and candidate statuses preserved)\n")

        header = f"{'ID':<4} | {'Title':<26} | {'Company':<18} | {'From':<14} | {'Apps':<6} | {'Status'}"
        self.stdout.write(header)
        self.stdout.write("-" * len(header))
        for r in records:
            status = "Active" if r['is_active'] else "Inactive"
            comp = r['company_name'] or "-"
            self.stdout.write(f"{r['id']:<4} | {r['title'][:26]:<26} | {comp[:18]:<18} | {r['from']:<14} | {r['applications']:<6} | {status}")

        if not is_dry_run:
            self.stdout.write(self.style.SUCCESS("\nAll selected jobs and candidate applications are now managed by:"))
            self.stdout.write(f"  Username : {target_user.username}")
            self.stdout.write(f"  Dashboard: http://127.0.0.1:8000/accounts/recruiter/dashboard/\n")
