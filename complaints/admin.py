from django.contrib import admin
from .models import Complaint, CaseFile, RequestedDocument

# Register your models here.
admin.site.register(Complaint)
admin.site.register(CaseFile)
admin.site.register(RequestedDocument)