from django.contrib.auth import authenticate
from .models import Account
from rest_framework.views import APIView
from rest_framework import status, generics
from .serializers import AccountSerializer, ChangePasswordSerializer
import re
from django.contrib.auth.hashers import make_password
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_bytes, smart_str, force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.core.mail import send_mail
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token


def generate_unique_username(full_name):
    User = get_user_model()
    
    # Clean and split the full name
    full_name = full_name
    parts = full_name.split()
    
    if not parts:
        # Handle empty name case
        base = "user"
    elif len(parts) == 1:
        # Single name (e.g., "Madonna")
        base = parts[0].lower()
    else:
        # Multiple parts - treat first as first name, rest as last name
        first_name = parts[0].lower()
        last_name = ''.join(parts[1:]).lower()
        
        # Create base username variations
        username_variants = [
            f"{first_name}{last_name}",
            f"{first_name}.{last_name}",
            f"{first_name}_{last_name}",
            f"{first_name[0]}{last_name}",
            full_name.replace(' ', '').lower(),
            full_name.replace(' ', '.').lower(),
        ]
        
        # Try each variant
        for username in username_variants:
            if not User.objects.filter(username=username).exists():
                return username
        
        base = username_variants[0]
    
    # If all variants are taken (or single name), append numbers
    counter = 1
    
    while True:
        new_username = f"{base}{counter}"
        if not User.objects.filter(username=new_username).exists():
            return new_username
        counter += 1


class signup(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AccountSerializer(data=request.data)

        if serializer.is_valid():
            full_name = request.data.get("full_name")
            staff_id = request.data.get("staff_id")

            if not full_name and not staff_id:
                return Response({
                    'full_name': "This field is required", 
                    "staff_id": "This field is required"
                    })
            elif not full_name:
                return Response({
                    'full_name': "This field is required", 
                    })
            elif not staff_id:
                return Response({
                    "staff_id": "This field is required"
                    })
            else:
                User = get_user_model()

                if User.objects.filter(staff_id=staff_id.lower().strip()).exists():
                    return Response({
                        "staff_id": "Please enter a unique staff ID"
                    })

                username = generate_unique_username(full_name=full_name)

                serializer.validated_data["password"] = make_password(serializer.validated_data.get("password"))

                account = serializer.save(
                    username=username,
                    full_name=full_name,
                    staff_id=staff_id.lower().strip()
                )

                token, _ = Token.objects.get_or_create(user=account)

                return Response({'status': "complete", "name": username, "token": token.key})
        return Response(serializer.errors)


class loginView(APIView):
    def post(self, request, *args, **kwargs):
        password = request.data.get("password")
        staff_id = request.data.get("staff_id")

        if not password and not staff_id:
            return Response({
                "staff_id": "Please enter your Staff ID",
                "password": "Please enter password"
            })
        elif not password:
            return Response({"password": "Please enter password"})
        elif not staff_id:
            return Response({"staff_id": "Please enter staff ID"})
        else:
            if Account.objects.filter(staff_id=staff_id.lower().strip()).count() == 0:
                return Response({'staff_id': 'No such staff ID'})
            else:
                user = authenticate(staff_id=staff_id.lower().strip(), password=password)

                if not user:
                    return Response({'password': 'Password is incorrect'})
                else:
                    User = get_user_model()

                    user_account = User.objects.get(username=user.username)

                    token, _ = Token.objects.get_or_create(user=user_account)

                    return Response({'status': 'complete', "username": user.username, "token": token.key})  

class loginTokenView(APIView):
    def get(self, request, *args, **kwargs):
        User = get_user_model()

        username = request.GET.get("username").lower().strip()

        if User.objects.filter(username=username).exists():
            user_account = User.objects.get(username=username)
            token, _ = Token.objects.get_or_create(user=user_account)
            return Response({'token': token.key})
        else:
            return Response({"error": "No such user found"})


class logoutView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            request.user.auth_token.delete()
            return Response({'status': 'logged out'})
        except:
            return Response({'status': 'user not logged in'})
        

class deleteAccount(APIView):
    def delete(self, request):
        account = Account.objects.get(id=request.user.id)

        account.delete()

        return Response({'status': 'deleted'})
    

class RequestPasswordResetEmail(APIView):
    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response({'email': 'Please specify your email'})

        User = get_user_model()

        if User.objects.filter(email=email.lower().strip()).exists():
            user = User.objects.get(email=email)
            
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))

            token = PasswordResetTokenGenerator().make_token(user)

            send_mail(
                "Reset email",
                f"http://127.0.0.1:8000/account/password-reset/{uidb64}/{token}/",
                "",
                [email],
                fail_silently=False,
            )

            return Response({'status': 'We have sent you a link to reset your password'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No email associated with any account'})
        

class PasswordTokenCheckAPI(APIView):
    def get(self, request, uidb64, token):
        try:
            User = get_user_model()
            
            id = urlsafe_base64_decode(uidb64)

            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({'error': 'Token not valid'})

            return Response({'status': 'valid', "uid": uidb64, "token": token})
        
        except:
            return Response({'error': 'UID not valid'})
        
    
    def put(self, request, uidb64, token):
        try:
            User = get_user_model()

            password = request.data.get("password")

            if not password:
                return Response({'password': 'Please enter your new password'})

            id = force_str(urlsafe_base64_decode(uidb64))

            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({'error': 'Token no longer valid'})
                
            user.set_password(password)

            user.save()

            return Response({'status': "Password has successfully been reset"})
        
        except:
            return Response({'error': 'Token not valid'})


class changePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer

    model = Account

    permission_classes = (IsAuthenticated,)

    def get_object(self):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"error": "Wrong password"}, status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()

            return Response({'status': 'Password successfully reset'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)