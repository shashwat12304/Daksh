from django.urls import path
from . import views

urlpatterns = [
    path('Daksh/', views.Daksh, name='Daksh'),
    path('Daksh/submitForm', views.submitForm, name='submitForm'),
]