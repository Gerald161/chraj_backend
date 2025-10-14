from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('create-complaint', views.createComplaint.as_view()),
    path('mandate-decision', views.mandateDecision.as_view()),
    path('investigation-findings/<slug:slug>', views.investigationFindings.as_view()),
    path('upload-investigation-files/<slug:slug>', views.uploadInvestigationFiles.as_view()),
    path('hearing/<slug:slug>', views.hearing.as_view()),
    path('mediation/<slug:slug>', views.mediation.as_view()),
    path('decision/<slug:slug>', views.decision.as_view()),
    path('get-all-appointments', views.allAppointments.as_view()),
    path('get-all-notifications', views.allNotifications.as_view()),
    path('get-appointment/<slug:slug>', views.appointment.as_view()),
    path('confirm_attendace/<slug:slug>', views.confirmAttendance.as_view()),
    path('reschedule-appointment/<slug:slug>', views.rescheduleAppointment.as_view()),
    path('reschedule-request-notification/<slug:slug>', views.rescheduleRequestNotification.as_view()),
]