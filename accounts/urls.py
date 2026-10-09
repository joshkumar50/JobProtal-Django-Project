from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recruiter/dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('dashboard/candidate/', views.candidate_dashboard, name='candidate_dashboard'),
    path('profile/update/', views.profile_update, name='profile_update'),
]
