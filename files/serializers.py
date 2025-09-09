from rest_framework import serializers
from .models import LetterFileModel, LetterPairModel
from users.serializers import CustomUserSerializer

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterFileModel
        fields = [
            'id',
            'filename',
        ]

class LetterSerializer(serializers.ModelSerializer):
    sender = CustomUserSerializer(read_only=True)

    class Meta:
        model = LetterFileModel
        fields = [
            'id',
            'filename',
            'sender',
        ]

class LetterPairSerializer(serializers.ModelSerializer):
    letter = TemplateSerializer(read_only=True)
    reply = TemplateSerializer(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = LetterPairModel
        fields = [
            'letter',
            'status',
            'reply',
        ]

    def get_status(self, obj):
        "获取中文状态"
        return obj.get_status()