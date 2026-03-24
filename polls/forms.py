from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ExtendedUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, label="İsim", required=True)
    last_name = forms.CharField(max_length=100, label="Soyisim", required=True)
    email = forms.EmailField(label="E-posta", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')