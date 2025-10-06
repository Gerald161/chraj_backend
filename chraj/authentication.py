from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

class AccountBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, email=None, staff_id=None):
        User = get_user_model()

        try:
            user = User.objects.get(username=username)
            
            if user.check_password(password) is True:
                return user
            
            return None
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=email)

                if user.check_password(password) is True:
                    return user
                
                return None
            except User.DoesNotExist:
                try:
                    user = User.objects.get(staff_id=staff_id)

                    if user.check_password(password) is True:
                        return user
                    
                    return None
                except User.DoesNotExist:
                    return None

    def get_user(self, staff_id):
        User = get_user_model()
        
        try:
            return User.objects.get(pk=staff_id)
        except User.DoesNotExist:
            return None