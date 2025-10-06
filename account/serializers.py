from rest_framework import serializers
from .models import Account


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        # fields = ["email", "password", "username"]
        fields = ["email", "password"]


class ChangePasswordSerializer(serializers.Serializer):
    model = Account
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)