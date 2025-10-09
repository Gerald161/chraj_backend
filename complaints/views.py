from .models import Complaint, CaseFile
from rest_framework.views import APIView
from rest_framework.response import Response

class createComplaint(APIView):
    def post(self, request, *args, **kwargs):
        required_fields = [
            "title", "description", "location", "complainant", 
            "complainant_email", "respondent", "respondent_email"
        ]

        errors = {}

        for field in required_fields:
            if not request.data.get(field):
                errors[field] = "This field is required"

        if errors:
            return Response(errors)
        
        # print(Complaint.objects.count() + 1)

        complaint = Complaint()

        complaint.title = request.data.get("title")
        complaint.description = request.data.get("description")
        complaint.location = request.data.get("location")
        complaint.complainant = request.data.get("complainant")
        complaint.complainant_email = request.data.get("complainant_email")
        complaint.respondent = request.data.get("respondent")
        complaint.respondent_email = request.data.get("respondent_email")
        
        case_num = Complaint.objects.count() + 1

        complaint.case_id = f"CASE-{case_num:04d}"
        complaint.complainant_reference_id = f"COMPL-{case_num:04d}"
        complaint.respondent_reference_id = f"RES-{case_num:04d}"

        complaint.save()

        for field_name, files in request.FILES.lists():
            for file in files:
                case_file = CaseFile()

                case_file.document = file

                case_file.complaint = complaint

                case_file.save()

        return Response({
            'status': "saved", 
        })