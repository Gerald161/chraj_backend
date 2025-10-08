from django.db import models
from django.conf import settings

# Create your models here.
class Complaint(models.Model):
    title = models.CharField(max_length=300)
    description = models.CharField(max_length=300)
    slug = models.SlugField(null=True) #auto added
    case_id = models.CharField(max_length=300) #auto added
    location = models.CharField(max_length=300)
    complainant = models.CharField(max_length=300)
    complainant_email = models.CharField(max_length=300)
    respondent = models.CharField(max_length=300)
    respondent_email = models.CharField(max_length=300)
    time_filed = models.DateTimeField(auto_now_add=True) #auto added
    case_officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True) #auto added
    isWithinMandate = models.BooleanField(null=True)


    def __str__(self):
        return str(self.slug)



class CaseDocuments(models.Model):
    document = models.FileField()
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE)

    def delete(self, *args, **kwargs):
        self.document.delete()
        super().delete(*args, **kwargs)
    