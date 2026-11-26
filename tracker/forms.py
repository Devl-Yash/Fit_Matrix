from django import forms
from django.contrib.auth.models import User
from .models import Profile, FoodLog

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match")

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['age', 'weight', 'height', 'goal']

class FoodUploadForm(forms.Form):
    image = forms.ImageField()

from django import forms
from .models import Profile


class ProfileForm(forms.ModelForm):

    class Meta:

        model = Profile

        fields = [
            "age",
            "gender",
            "weight",
            "height",
            "goal",
            "water_goal"
        ]