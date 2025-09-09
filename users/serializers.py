from rest_framework import serializers
from .models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    user_permission = serializers.CharField(source='get_user_permission_display')
    class Meta:
        model = CustomUser
        fields = [
            'id', 
            'username', 
            'email', 
            'password', 
            'student_id', 
            'phone_number', 
            'user_permission'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

class UsernameSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'username',
        ]