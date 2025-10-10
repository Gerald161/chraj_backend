from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('create-complaint', views.createComplaint.as_view()),
    path('mandate-decision', views.mandateDecision.as_view()),
]