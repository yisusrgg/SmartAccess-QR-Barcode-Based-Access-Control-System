from django.urls import path
from .views import ValidarQRView

urlpatterns = [
    path('validar/', ValidarQRView.as_view()),
]