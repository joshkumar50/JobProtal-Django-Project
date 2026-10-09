from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def recruiter_required(function=None, redirect_field_name=None, login_url=None):
    """
    Decorator for views that checks that the user is logged in and is a RECRUITER,
    redirects to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and hasattr(u, 'profile') and u.profile.role == 'RECRUITER',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def candidate_required(function=None, redirect_field_name=None, login_url=None):
    """
    Decorator for views that checks that the user is logged in and is a CANDIDATE,
    redirects to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and hasattr(u, 'profile') and u.profile.role == 'CANDIDATE',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
