# Job Portal

*Developed by Team **Nexbit***

A complete, modern, and professional Job Portal web application built with Django. This project fulfills the "Intermediate Level" requirements where companies can post jobs and candidates can search and apply, featuring two distinct user roles.

## 🚀 Objective & Overview
The objective of this project is to provide a platform where **Companies post jobs** and **Candidates search and apply**. It is designed with a professional UI/UX and built to industry standards, featuring role-based access control, secure authentication, job CRUD operations, and application workflows with PDF resume support.

## 🛠️ Technologies Used
- **Backend**: Python, Django
- **Database**: SQLite (SQL)
- **Frontend**: HTML5, CSS (Tailwind CSS for styling, Alpine.js for interactivity)
- **File Management**: Django FileSystemStorage (Resumes/PDFs), Pillow (Image processing)

## ✨ Core Features Built
- **Two Roles**: Custom User profiles distinguishing between `Recruiter` and `Candidate` roles.
- **Job Management**: Recruiters can post, edit, and delete jobs.
- **Search Functionality**: Candidates can search for jobs by **skill** and **location** (implemented using Django ORM's `Q` objects).
- **Resume Upload**: Candidates apply to jobs with a resume upload restricted to **PDF** formats (handled via `FileField`).
- **Applicant Tracking**: Recruiters can view applicants for their jobs and change application statuses (Applied, Shortlisted, Rejected).

## 🔒 Implementation Highlights ("What to do first")
1. **Extended User Model**: Created a `Profile` model (extending Django's User) to store the user `role` (`id, user_id, role`).
2. **Role-Based Access**: Restricted pages by role using custom decorators (e.g., Candidates cannot access Recruiter dashboards).
3. **Advanced Search**: Built search functionality using `Q` objects in the Django ORM to filter by title/skills and location simultaneously.
4. **File Uploads**: Handled PDF resume uploads securely using Django's `FileField`.
5. **Status Workflow**: Added a status update mechanism for applications with choices: `Applied`, `Shortlisted`, and `Rejected`.

## 🌟 Bonus Features Implemented
- **Email Notifications**: Automatic email notifications are sent (via the console backend) when an application status changes.
- **Saved Jobs**: Candidates can bookmark/save jobs and view them in a dedicated dashboard.
- **Company Profiles**: Recruiters can manage public company profiles with logos, providing candidates an aggregated view of all active company jobs.
- **Automated Seed Script**: A custom management command (`seed_data`) to quickly populate realistic sample data into the database.

## 🗄️ Database Tables (SQL Schema)
The database structure adheres to the project specifications:
- **Profile**: `(id, user_id, role)` - Extends User to define roles.
- **Job**: `(id, recruiter_id, title, skills, location, salary, posted_on)` - Stores job postings linked to the recruiter.
- **Application**: `(id, job_id, candidate_id, resume, status)` - Links candidates to jobs, tracking resume files and current status.
*(Additional tables include Company profiles and SavedJobs to support bonus features).*

## ⚙️ Setup & Execution Instructions

1. **Clone the repository and enter the directory**:
   ```bash
   git clone <repository_url>
   cd JobPortal
   ```

2. **Create a virtual environment and activate it**:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables**:
   Copy `.env.example` to `.env` and configure your settings.
   ```bash
   cp .env.example .env
   ```

5. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Seed Realistic Sample Data & Demo Credentials**:
   ```bash
   python manage.py seed_data
   ```
   To assign all demo jobs to your recruiter account for presentations:
   ```bash
   python manage.py assign_demo_jobs Recruiter
   ```

7. **Demo Login Credentials**:
   | Role | Username / Email | Password | Access / Features |
   | :--- | :--- | :--- | :--- |
   | **Recruiter** | `recruiter@gmail.com` *(or `Recruiter`)* | `recruiter@gmail.com` | Manages 5 jobs, company profile, review & shortlist candidates |
   | **Candidate** | `candidate@gmail.com` *(or `Candidate`)* | `candidate@gmail.com` | Explores jobs, applies with PDF resume, bookmarks saved jobs |

8. **Run the Development Server**:
   ```bash
   python manage.py runserver
   ```
   Open `http://localhost:8000` in your browser.

## 🧪 Testing
The project includes a comprehensive suite of automated tests verifying models, views, custom permissions, and `Q` object search functionality.

```bash
python manage.py test
```

## 📸 Deliverables Checklist
- [x] Working source code
- [x] SQL database file (`db.sqlite3`)
- [x] Short README (This file)
- [ ] 5-6 Screenshots (See list below to capture)

### Screenshots to Capture:
1. **Home Page**: Showcasing the landing page and recent jobs.
2. **Job Search**: Showcasing the search results filtering by skill and location.
3. **Job Detail & Apply Modal**: Highlighting job information and the PDF resume upload form.
4. **Candidate Dashboard**: Showing application history with status badges and saved jobs.
5. **Recruiter Dashboard**: Highlighting job stats and the job management table.
6. **Applicant Management View**: The recruiter's UI to view applicants and update statuses (Applied, Shortlisted, Rejected).
