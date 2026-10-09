from django import forms
from django.contrib.auth.models import User
from .models import Profile

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input-field'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input-field'}))
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'input-field'}))

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'input-field'}),
            'email': forms.EmailInput(attrs={'class': 'input-field'}),
        }

    def clean_password_confirm(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password_confirm']:
            raise forms.ValidationError("Passwords do not match.")
        return cd['password_confirm']

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input-field'}),
            'last_name': forms.TextInput(attrs={'class': 'input-field'}),
            'email': forms.EmailInput(attrs={'class': 'input-field'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    RECRUITER_ONLY_FIELDS = [
        'company_name', 'company_website',
        'company_location', 'company_description',
    ]

    class Meta:
        model = Profile
        fields = ['phone', 'bio', 'avatar', 'resume', 'company_name', 'company_website', 'company_location', 'company_description']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'input-field'}),
            'bio': forms.Textarea(attrs={'class': 'input-field', 'rows': 4}),
            'avatar': forms.FileInput(attrs={'class': 'mt-1 block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer'}),
            'resume': forms.FileInput(attrs={'class': 'mt-1 block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer'}),
            'company_name': forms.TextInput(attrs={'class': 'input-field'}),
            'company_website': forms.URLInput(attrs={'class': 'input-field'}),
            'company_location': forms.TextInput(attrs={'class': 'input-field'}),
            'company_description': forms.Textarea(attrs={'class': 'input-field', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        profile = kwargs.get('instance') or getattr(self, 'instance', None)
        if profile and profile.role != 'RECRUITER':
            for f in self.RECRUITER_ONLY_FIELDS:
                self.fields.pop(f, None)
