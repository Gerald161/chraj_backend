from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('create-complaint', views.createComplaint.as_view()),
    path('mandate-decision', views.mandateDecision.as_view()),
    path('investigation-findings/<slug:slug>', views.investigationFindings.as_view()),
    path('hearing/<slug:slug>', views.hearing.as_view()),
    path('mediation/<slug:slug>', views.mediation.as_view()),
    path('decision/<slug:slug>', views.decision.as_view()),
]