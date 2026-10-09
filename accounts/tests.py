from django.test import TestCase
from django.contrib.auth.models import User
from .models import Profile

class AccountsTestCase(TestCase):
    def setUp(self):
        self.candidate = User.objects.create_user(username='candidate1', password='password123', email='c@example.com')
        self.candidate.profile.role = 'CANDIDATE'
        self.candidate.profile.save()
        
        self.recruiter = User.objects.create_user(username='recruiter1', password='password123', email='r@example.com')
        self.recruiter.profile.role = 'RECRUITER'
        self.recruiter.profile.save()

    def test_profile_creation(self):
        self.assertEqual(Profile.objects.count(), 2)
        self.assertEqual(self.candidate.profile.role, 'CANDIDATE')

    def test_signup_view(self):
        response = self.client.get('/accounts/register/')
        self.assertEqual(response.status_code, 200)
        
        # Test candidate signup
        post_data = {
            'username': 'newcandidate',
            'email': 'new@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'role': 'CANDIDATE'
        }
        response = self.client.post('/accounts/register/', data=post_data)
        self.assertRedirects(response, '/accounts/dashboard/', fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(username='newcandidate').exists())

    def test_login_logout(self):
        # Test Login with username
        response = self.client.post('/accounts/login/', data={'username': 'candidate1', 'password': 'password123'})
        self.assertRedirects(response, '/accounts/dashboard/', fetch_redirect_response=False)

        # Test Login with email
        self.client.logout()
        response = self.client.post('/accounts/login/', data={'username': 'c@example.com', 'password': 'password123'})
        self.assertRedirects(response, '/accounts/dashboard/', fetch_redirect_response=False)
        
        # Test Logout
        response = self.client.post('/accounts/logout/')
        self.assertRedirects(response, '/')

    def test_dashboard_redirects(self):
        self.client.login(username='candidate1', password='password123')
        response = self.client.get('/accounts/dashboard/')
        self.assertRedirects(response, '/accounts/dashboard/candidate/', fetch_redirect_response=False)
        
        self.client.logout()
        
        self.client.login(username='recruiter1', password='password123')
        response = self.client.get('/accounts/dashboard/')
        self.assertRedirects(response, '/accounts/recruiter/dashboard/', fetch_redirect_response=False)

    def test_role_based_access(self):
        self.client.login(username='candidate1', password='password123')
        # Candidate tries to access recruiter dashboard
        response = self.client.get('/accounts/recruiter/dashboard/')
        # Custom decorators redirect to login if fail
        self.assertEqual(response.status_code, 302)
        
        self.client.logout()
        
        self.client.login(username='recruiter1', password='password123')
        # Recruiter tries to access candidate dashboard
        response = self.client.get('/accounts/dashboard/candidate/')
        self.assertEqual(response.status_code, 302)
