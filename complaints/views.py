from .models import Complaint, CaseFile, RequestedDocument, Appointment, AppointmentDocument, Term, Notification
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail

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


        send_mail(
            f"Complaint filed against you at CHRAJ",
            f"Visit the link http://localhost:3000/check-complaint/ with the ref ID '{complaint.respondent_reference_id}' to view details about the case",
            "",
            [complaint.respondent_email],
            fail_silently=False,
        )

        return Response({
            'status': "saved", 
            "complainant_ref_id": complaint.complainant_reference_id
        })
    

class unassignedCases(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        complaints = Complaint.objects.filter(case_officer=None)

        all_complaints = []

        for complaint in complaints:
            case_files = CaseFile.objects.filter(complaint=complaint)

            all_case_files = []

            for case_file in case_files:
                all_case_files.append(case_file.document.name)

            all_complaints.append({
                "id": complaint.case_id, 
                "title": complaint.title,
                "description": complaint.description,
                "dateSubmitted": complaint.time_filed.date(),
                "complainant": complaint.complainant,
                "respondent": complaint.respondent,
                "documents": all_case_files
            })

        return Response({
            'all_complaints': all_complaints, 
        })
    

class myCases(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        complaints = Complaint.objects.filter(case_officer=request.user).filter(isWithinMandate=True)

        all_complaints = []

        for complaint in complaints:
            case_files = CaseFile.objects.filter(complaint=complaint)

            all_case_files = []

            for case_file in case_files:
                all_case_files.append(case_file.document.name)

            all_complaints.append({
                "id": complaint.case_id, 
                "title": complaint.title,
                "description": complaint.description,
                "dateSubmitted": complaint.time_filed.date(),
                "complainant": complaint.complainant,
                "respondent": complaint.respondent,
                "documents": all_case_files,
                "status": complaint.case_status
            })

        return Response({
            'all_complaints': all_complaints, 
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


class uploadInvestigationFiles(APIView):
    def post(self, request, *args, **kwargs):
        slug = self.kwargs['slug']
        
        complaint = Complaint.objects.filter(case_id__iexact=slug).first()

        if complaint:
            if request.FILES:
                for field_name, files in request.FILES.lists():
                    for file in files:
                        case_file = CaseFile()

                        case_file.document = file

                        case_file.complaint = complaint

                        case_file.name = field_name

                        case_file.step = "investigation"

                        case_file.save()
                
                return Response({
                    'status': "Files Uploaded", 
                })
            else:
                return Response({
                    'files': "Please upload at least one file", 
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
        


class decision(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        slug = self.kwargs['slug']

        required_fields = [
            "final_officer_notes", "resolved_positively"
        ]

        errors = {}

        for field in required_fields:
            if not request.data.get(field):
                errors[field] = "This field is required"

        if errors:
            return Response(errors)

        complaint = Complaint.objects.filter(case_id__iexact=slug).first()

        if complaint:
            complaint.final_officer_notes = request.data.get("final_officer_notes")

            complaint.case_status = "resolved"

            complaint.resolved_positively = eval(request.data.get("resolved_positively"))

            complaint.save()

            for key, value in request.data.items():
                if key in required_fields:
                    continue

                term = Term()

                term.term_detail = value

                term.complaint = complaint

                term.save()

            return Response({
                'status': "Saved",
                "case": "resolved" 
            })
        else:
            return Response({
                'complaint': "Case not found", 
            })
        

class allAppointments(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        appointments = Appointment.objects.filter(case_officer=request.user)
        
        all_appointments = []

        for appointment in appointments:
            all_appointments.append({
                "appointment_id": appointment.id, 
                "type": appointment.type,
                "purpose": appointment.purpose,
                "date": appointment.date,
                "time": appointment.time,
                "venue": appointment.venue,
                "case_id": appointment.complaint.case_id,
                "complainant": appointment.complaint.complainant,
                "respondent": appointment.complaint.respondent
            })

        return Response({
            "appointments": all_appointments
        })
    

class appointment(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        slug = self.kwargs['slug']

        appointment = Appointment.objects.filter(id=slug).first()

        if appointment:
            return Response({
                "appointment": {
                    "type": appointment.type,
                    "purpose": appointment.purpose,
                    "date": appointment.date,
                    "time": appointment.time,
                    "venue": appointment.venue,
                    "case_id": appointment.complaint.case_id,
                    "complainant": appointment.complaint.complainant,
                    "respondent": appointment.complaint.respondent
                }
            })
        else:
            return Response({
                "appointment": "No appointment found"
            })
    

class allNotifications(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(case_officer=request.user)
        
        all_notifications = []

        for notification in notifications:
            all_notifications.append({
                "requester": notification.requester,
                "date": notification.date,
                "time": notification.time,
                "is_read": notification.is_read,
                "appointment_id": notification.appointment.id
            })

        return Response({
            "notifications": all_notifications
        })    


class confirmAttendance(APIView):
    def post(self, request, *args, **kwargs):
        slug = self.kwargs['slug']

        attendee = request.data.get("attendee")

        if attendee:
            appointment = Appointment.objects.filter(id=slug).first()

            if appointment:
                if attendee == "respondent":
                    appointment.respondent_attending = True

                if attendee == "complainant":
                    appointment.complainant_attending = True

                appointment.save()
            
                return Response({
                    'status': "Saved",
                })
            else:
                return Response({
                    'appointment_id': "Appointment not found",
                })
        else:
            return Response({
                'attendee': "Please add field",
            })


class rescheduleAppointment(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        slug = self.kwargs['slug']

        required_fields = [
            "date", "time"
        ]

        errors = {}

        for field in required_fields:
            if not request.data.get(field):
                errors[field] = "This field is required"

        if errors:
            return Response(errors)
        

        appointment = Appointment.objects.filter(id=slug).first()

        if appointment:
            appointment.date = request.data.get("date")
            appointment.time = request.data.get("time")
            appointment.save()

            return Response({
                'status': "Saved",
            })
        else:
            return Response({
                'appointment_id': "Appointment not found",
            })
        


class rescheduleRequestNotification(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        slug = self.kwargs['slug']

        required_fields = [
            "date", "time", "requester"
        ]

        errors = {}

        for field in required_fields:
            if not request.data.get(field):
                errors[field] = "This field is required"

        if errors:
            return Response(errors)
        

        appointment = Appointment.objects.filter(id=slug).first()

        if appointment:
            notification = Notification.objects.filter(appointment=appointment).first()

            if notification:
                notification.date = request.data.get("date")
                notification.time = request.data.get("time")
                notification.save()
            else:
                notification = Notification()
                notification.date = request.data.get("date")
                notification.time = request.data.get("time")
                notification.appointment = appointment
                notification.requester = request.data.get("requester")
                notification.case_officer = appointment.case_officer
                
                notification.save()

            return Response({
                'status': "Saved",
            })
        else:
            return Response({
                'appointment_id': "Appointment not found",
            })