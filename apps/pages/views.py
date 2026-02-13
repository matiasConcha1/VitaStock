from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import VitaStockAuthenticationForm, VitaStockSignupForm


def index(request):
    """Redirige según autenticación: panel o pantalla de login."""
    if request.user.is_authenticated:
        return redirect("/panel/")
    return redirect(settings.LOGIN_URL)


class VitaStockLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = VitaStockAuthenticationForm
    redirect_authenticated_user = True
    next_page = settings.LOGIN_REDIRECT_URL

    def form_valid(self, form):
        response = super().form_valid(form)
        remember = self.request.POST.get("remember")
        self.request.session.set_expiry(60 * 60 * 24 * 14 if remember else 0)
        return response


class VitaStockRegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = VitaStockSignupForm
    success_url = reverse_lazy("panel")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "¡Cuenta creada! Bienvenido a VitaStock.")
        return super().form_valid(form)
