from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class VitaStockAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Usuario"
        self.fields["password"].label = "Contraseña"
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Usuario", "autofocus": True}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Contraseña"}
        )


class VitaStockSignupForm(UserCreationForm):
    email = forms.EmailField(label="Correo electrónico", required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        labels = {
            "username": "Usuario",
            "password1": "Contraseña",
            "password2": "Confirmar contraseña",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "Usuario",
            "email": "Correo electrónico",
            "password1": "Contraseña",
            "password2": "Confirmar contraseña",
        }
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {"class": "form-control", "placeholder": placeholders.get(name, "")}
            )
