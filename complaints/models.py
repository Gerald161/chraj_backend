from django.db import models
from django.conf import settings

# Create your models here.
class Complaint(models.Model):
    title = models.CharField(max_length=300)
    description = models.CharField(max_length=300)
    location = models.CharField(max_length=300)
    complainant = models.CharField(max_length=300)
    complainant_email = models.CharField(max_length=300)
    respondent = models.CharField(max_length=300)
    respondent_email = models.CharField(max_length=300)
    time_filed = models.DateTimeField(auto_now_add=True) #system auto added
    case_id = models.CharField(max_length=300, unique=True) #auto added
    complainant_reference_id = models.CharField(max_length=300, unique=True, null=True) #auto added
    respondent_reference_id = models.CharField(max_length=300, unique=True, null=True) #auto added
    investigation_notes = models.CharField(max_length=300, null=True) #later added
    case_officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True) #later added
    case_status = models.CharField(max_length=300, default="initial")
    isWithinMandate = models.BooleanField(null=True) #later added


    def __str__(self):
        return str(self.case_id)



class CaseFile(models.Model):
    STEP_CHOICES = [
        ("initial", "initial"), ("investigation", "investigation"), 
        ("hearing", "hearing")
    ]

    document = models.FileField()
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE)
    step = models.CharField(default="initial", choices=STEP_CHOICES)


    def __str__(self):
        return str(self.complaint)
    

    def delete(self, *args, **kwargs):
        self.document.delete()
        super().delete(*args, **kwargs)



class RequestedDocument(models.Model):    
    STEP_CHOICES = [
        ("investigation", "investigation"), 
        ("hearing", "hearing")
    ]

    name = models.CharField(max_length=300)
    step_requested = models.CharField(default="investigation", choices=STEP_CHOICES)
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE)


    def __str__(self):
        return str(self.name)