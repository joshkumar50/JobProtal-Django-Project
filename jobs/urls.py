from django.urls import path
from . import views

urlpatterns = [
    path('', views.JobListView.as_view(), name='job_list'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('create/', views.JobCreateView.as_view(), name='job_create'),
    path('<int:pk>/update/', views.JobUpdateView.as_view(), name='job_update'),
    path('<int:pk>/delete/', views.JobDeleteView.as_view(), name='job_delete'),
    path('<int:pk>/toggle/', views.JobToggleActiveView.as_view(), name='job_toggle'),
    path('<int:pk>/apply/', views.apply_to_job, name='apply_to_job'),
    path('<int:pk>/applicants/', views.JobApplicantsView.as_view(), name='job_applicants'),
    path('application/<int:pk>/status/<str:status>/', views.ChangeApplicationStatusView.as_view(), name='change_application_status'),
    path('<int:pk>/save/', views.ToggleSavedJobView.as_view(), name='toggle_saved_job'),
    path('saved/', views.SavedJobListView.as_view(), name='saved_jobs'),
    path('company/', views.CompanyUpdateView.as_view(), name='company_update'),
    path('company/<int:pk>/', views.CompanyDetailView.as_view(), name='company_detail'),
]
