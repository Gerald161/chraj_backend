from django.contrib import admin
from .models import Complaint, CaseFile, RequestedDocument, Appointment, AppointmentDocument, Term, Notification

# Register your models here.
admin.site.register(Complaint)
admin.site.register(CaseFile)
admin.site.register(RequestedDocument)
admin.site.register(Appointment)
admin.site.register(AppointmentDocument)
admin.site.register(Term)
admin.site.register(Notification)