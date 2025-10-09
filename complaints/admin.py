from django.contrib import admin
from .models import Complaint, CaseFile

# Register your models here.
admin.site.register(Complaint)
admin.site.register(CaseFile)