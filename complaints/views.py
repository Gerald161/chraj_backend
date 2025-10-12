from .models import Complaint, CaseFile, RequestedDocument, Appointment, AppointmentDocument
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

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
    

class mandateDecision(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        required_fields = [
            "case_id", "mandate_decision",
        ]

        errors = {}

        for field in required_fields:
            if not request.data.get(field):
                errors[field] = "This field is required"

        if errors:
            return Response(errors)
        
        case_id = request.data.get("case_id")

        mandate_decision = request.data.get("mandate_decision")

        complaint = Complaint.objects.filter(case_id__iexact=case_id).first()

        if complaint:
            complaint.isWithinMandate = eval(mandate_decision)

            complaint.case_officer = request.user

            complaint.case_status = "investigation"

            complaint.save()

            return Response({
                'status': "Saved", 
            })
        else:
            return Response({
                'case_id': "No such record", 
            })        


class investigationFindings(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        slug = self.kwargs['slug']

        investigation_notes = request.data.get("investigation_notes")
        
        if not investigation_notes:
            return Response({
                'investigation_notes': "Please include your investigation notes", 
            })
        
        complaint = Complaint.objects.filter(case_id__iexact=slug).first()

        if complaint:
            complaint.investigation_notes = investigation_notes

            complaint.case_status = "hearing"

            complaint.save()

            for key, value in request.data.items():
                if key == "investigation_notes":
                    continue

                if RequestedDocument.objects.filter(complaint=complaint).filter(name=value).filter(step_requested="investigation").first():
                    continue

                requestedDocument = RequestedDocument()

                requestedDocument.name = value

                requestedDocument.complaint = complaint

                requestedDocument.save()
            
            return Response({
                'status': "Investigation step complete", 
            })
        else:
            return Response({
            'complaint': "Case not found", 
        })    



class hearing(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        slug = self.kwargs['slug']

        required_fields = [
            "date", "time", "venue", "purpose", "attendee"
        ]

        errors = {}

        for field in required_fields:
            if not request.data.get(field):
                errors[field] = "This field is required"

        if errors:
            return Response(errors)

        complaint = Complaint.objects.filter(case_id__iexact=slug).first()

        if complaint:
            appointment = Appointment()

            appointment.date = request.data.get("date")

            appointment.time = request.data.get("time")

            appointment.type = "hearing"

            appointment.venue = request.data.get("venue")

            appointment.purpose = request.data.get("purpose")

            appointment.attendee = request.data.get("attendee")

            appointment.complaint = complaint

            appointment.save()

            for key, value in request.data.items():
                if key in required_fields:
                    continue

                appointmentDocument = AppointmentDocument()

                appointmentDocument.appointment = appointment

                appointmentDocument.name = value

                appointmentDocument.save()

            complaint.case_status = "mediation"

            complaint.save()

            return Response({
                'status': "Saved", 
            })
        else:
            return Response({
                'complaint': "Case not found", 
            })
        

class mediation(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        slug = self.kwargs['slug']

        required_fields = [
            "date", "time", "venue", "purpose"
        ]

        errors = {}

        for field in required_fields:
            if not request.data.get(field):
                errors[field] = "This field is required"


        if errors:
            return Response(errors)


        complaint = Complaint.objects.filter(case_id__iexact=slug).first()

        if complaint:
            appointment = Appointment()

            appointment.date = request.data.get("date")

            appointment.time = request.data.get("time")

            appointment.venue = request.data.get("venue")

            appointment.purpose = request.data.get("purpose")

            appointment.complaint = complaint

            appointment.save()

            complaint.case_status = "decision"

            complaint.save()

            return Response({
                'status': "Saved", 
            })
        else:
            return Response({
                'complaint': "Case not found", 
            })