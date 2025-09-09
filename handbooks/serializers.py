from rest_framework import serializers
from .models import Handbook

class HandbookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Handbook
        fields = '__all__'