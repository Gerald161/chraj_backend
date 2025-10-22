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

            all_requested_docs = []    

            requested_docs = RequestedDocument.objects.filter(complaint=complaint)

            for requested_doc in requested_docs:
                all_requested_docs.append(requested_doc.name)

            all_hearing_appointments = []

            hearing_appointments = Appointment.objects.filter(complaint=complaint).filter(type="hearing")

            for appointment in hearing_appointments:
                all_complainant_appointment_documents = []

                all_respondent_appointment_documents = []

                if appointment.attendee == "complainant":
                    appointmentDocuments = AppointmentDocument.objects.filter(
                        appointment=appointment,
                        appointment__attendee="complainant"
                    )

                    for appointmentDocument in appointmentDocuments:
                        all_complainant_appointment_documents.append(appointmentDocument.name)

                if appointment.attendee == "respondent":
                    appointmentDocuments = AppointmentDocument.objects.filter(
                        appointment=appointment,
                        appointment__attendee="respondent"
                    )

                    for appointmentDocument in appointmentDocuments:
                        all_respondent_appointment_documents.append(appointmentDocument.name)

                all_hearing_appointments.append({
                    "id": appointment.id,
                    "date": appointment.date,
                    "time": appointment.time,
                    "venue": appointment.venue,
                    "attendees": [appointment.attendee],
                    "purpose": appointment.purpose,
                    "itemsForRespondent": all_complainant_appointment_documents,
                    "itemsForComplainant": all_respondent_appointment_documents,
                    "respondent_attending": appointment.respondent_attending,
                    "complainant_attending": appointment.complainant_attending,
                })

            mediation_appointment = Appointment.objects.filter(complaint=complaint).filter(attendee="both").first()

            mediation_data = {
                "date": "",
                "time": "",
                "venue": "",
                "purpose": "",
                "respondent_attending": "",
                "complainant_attending": ""
            }

            if mediation_appointment:
                mediation_data = {
                    "date": mediation_appointment.date,
                    "time": mediation_appointment.time,
                    "venue": mediation_appointment.venue,
                    "purpose": mediation_appointment.purpose,
                    "respondent_attending": mediation_appointment.respondent_attending,
                    "complainant_attending": mediation_appointment.complainant_attending
                }

            all_terms = []

            terms = Term.objects.filter(complaint=complaint)

            for term in terms:
                all_terms.append(term.term_detail)

            all_complaints.append({
                "id": complaint.case_id, 
                "title": complaint.title,
                "description": complaint.description,
                "dateSubmitted": complaint.time_filed.date(),
                "complainant": complaint.complainant,
                "investigation_notes": complaint.investigation_notes,
                "respondent": complaint.respondent,
                "documents": all_case_files,
                "status": complaint.case_status,
                "docRequests": all_requested_docs,
                "hearings": all_hearing_appointments,
                "mediation": mediation_data,
                "terms": all_terms,
                "resolved_positively": complaint.resolved_positively,
                "final_notes": complaint.final_officer_notes
            })

        return Response({
            'all_complaints': all_complaints, 
        })
    

class fileComplaintCase(APIView):
    def get(self, request, *args, **kwargs):
        slug = self.kwargs['slug']

        if slug.lower().startswith('c'):
            complaint = Complaint.objects.filter(complainant_reference_id__iexact=slug).first()

        if slug.lower().startswith('r'):
            complaint = Complaint.objects.filter(respondent_reference_id__iexact=slug).first()

        if not slug.lower().startswith(('c', 'r')):
            return Response({
                'error': "Case not found", 
            })

        if complaint:
            case_files = CaseFile.objects.filter(complaint=complaint)

            all_case_files = []

            for case_file in case_files:
                all_case_files.append(case_file.document.name)

            requestedDocuments = RequestedDocument.objects.filter(complaint=complaint)

            all_requestedDocuments = []

            for requestedDocument in requestedDocuments:
                all_requestedDocuments.append(requestedDocument.name)

            all_terms = []

            terms = Term.objects.filter(complaint=complaint)

            for term in terms:
                all_terms.append(term.term_detail)


            your_hearing_appointment = {
                "id": "",
                "date": "",
                "time": "",
                "venue": ""
            }

            requested_reschedule = {
                "date": "",
                "time": ""
            }

            if slug.lower().startswith('c'):
                hearing_appointment = Appointment.objects.filter(complaint=complaint).filter(type="hearing").filter(attendee="complainant").first()

                rescheduled_date = Notification.objects.filter(appointment=hearing_appointment).filter(requester="complainant").first()

                if rescheduled_date:
                    requested_reschedule = {
                        "date": rescheduled_date.date,
                        "time": rescheduled_date.time
                    }

                view_type = "complainant"

            if slug.lower().startswith('r'):
                hearing_appointment = Appointment.objects.filter(complaint=complaint).filter(type="hearing").filter(attendee="respondent").first()

                rescheduled_date = Notification.objects.filter(appointment=hearing_appointment).filter(requester="respondent").first()

                if rescheduled_date:
                    requested_reschedule = {
                        "date": rescheduled_date.date,
                        "time": rescheduled_date.time
                    }

                view_type = "respondent"

            if hearing_appointment:
                your_hearing_appointment = {
                    "id": hearing_appointment.id,
                    "date": hearing_appointment.date,
                    "time": hearing_appointment.time,
                    "venue": hearing_appointment.venue,
                    "respondent_attending": hearing_appointment.respondent_attending,
                    "complainant_attending": hearing_appointment.complainant_attending,
                    "requested_reschedule": requested_reschedule
                }

                hearing_appointment_documents = []

                if slug.lower().startswith('c'):
                    appointmentDocuments = AppointmentDocument.objects.filter(
                        appointment=hearing_appointment,
                        appointment__attendee="complainant"
                    )

                    for appointmentDocument in appointmentDocuments:
                        hearing_appointment_documents.append(appointmentDocument.name)

                if slug.lower().startswith('r'):
                    appointmentDocuments = AppointmentDocument.objects.filter(
                        appointment=hearing_appointment,
                        appointment__attendee="respondent"
                    )

                    for appointmentDocument in appointmentDocuments:
                        hearing_appointment_documents.append(appointmentDocument.name)

            return Response({
                'complaint': {
                    "id": complaint.case_id, 
                    "case_officer": complaint.case_officer.full_name,
                    "status": complaint.case_status,
                    "title": complaint.title,
                    "description": complaint.description,
                    "dateSubmitted": complaint.time_filed.date(),
                    "complainant": complaint.complainant,
                    "respondent": complaint.respondent,
                    "case_files": all_case_files,
                    "requested_documents": all_requestedDocuments,
                    "hearing_appointment_documents": hearing_appointment_documents,
                    "terms": all_terms,
                    "your_hearing_appointment": your_hearing_appointment,
                    "view_type": view_type,
                    "mandate_decision": complaint.isWithinMandate
                }, 
            })
        else:
            return Response({
            'error': "Case not found", 
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


class advanceStep(APIView):
      permission_classes = [IsAuthenticated]

      def post(self, request, *args, **kwargs):
        slug = self.kwargs['slug']

        complaint = Complaint.objects.filter(case_id__iexact=slug).first()

        if complaint:
            status = request.data.get("status")

            if status:
                complaint.case_status = status

                complaint.save()

                return Response({
                    'status': "saved", 
                })
            else:
                return Response({
                    'status': "add status field", 
                })
        else:
            return Response({
            'complaint': "Case not found", 
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

            for key, value in request.data.items():
                if key == "investigation_notes":
                    continue

                if RequestedDocument.objects.filter(complaint=complaint).filter(name=value).first():
                    continue

                requestedDocument = RequestedDocument()

                requestedDocument.name = value

                requestedDocument.complaint = complaint

                requestedDocument.save()
            
            return Response({
                'status': "complete", 
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
                    'status': "uploaded", 
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

            appointment.case_officer = request.user

            appointment.save()

            for key, value in request.data.items():
                if key in required_fields:
                    continue

                appointmentDocument = AppointmentDocument()

                appointmentDocument.appointment = appointment

                appointmentDocument.name = value

                appointmentDocument.save()

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

            appointment.case_officer = request.user

            appointment.save()

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
                'status': "saved",
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
                "respondent": appointment.complaint.respondent,
                "status": appointment.complaint.case_status,
                "complainant_attending": appointment.complainant_attending,
                "respondent_attending": appointment.respondent_attending,
                "attendee": appointment.attendee
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
                    "respondent": appointment.complaint.respondent,
                    "complainant_attending": appointment.complainant_attending,
                    "respondent_attending": appointment.respondent_attending,
                    "attendee": appointment.attendee
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
                    'status': "saved",
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
                'status': "saved",
            })
        else:
            return Response({
                'appointment_id': "Appointment not found",
            })
        


class rescheduleRequestNotification(APIView):
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
                'status': "saved",
            })
        else:
            return Response({
                'appointment_id': "Appointment not found",
            })