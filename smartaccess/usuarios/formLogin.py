from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate

class MiFormularioLogin(AuthenticationForm):
    tipo = forms.ChoiceField(choices=[('0', 'ALUMNO'), ('1', 'DOCENTE')])

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        tipo = self.cleaned_data.get('tipo')

        if username and password:
            self.user_cache = authenticate(
                self.request, 
                username=username, 
                password=password, 
                tipo=tipo
            )
            
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data