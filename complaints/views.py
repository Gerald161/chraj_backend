from .models import Complaint
from rest_framework.views import APIView
from rest_framework.response import Response

class createComplaint(APIView):
    def post(self, request, *args, **kwargs):
        return Response({
        'status': "works", 
        })