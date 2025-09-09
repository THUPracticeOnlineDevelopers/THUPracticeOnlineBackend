from rest_framework import serializers
from .models import Detachment

class DetachmentSerializer(serializers.ModelSerializer):
    detachment_leader = serializers.SerializerMethodField()
    detachment_member = serializers.SerializerMethodField()

    class Meta:
        model = Detachment
        fields = [
            'id',
            'name',
            'start_date',
            'end_date',
            'valid',
            'detachment_leader',
            'detachment_member'
        ]

    def get_detachment_leader(self, obj):
        leaders = obj.get_leaders()
        return list(leaders.values_list('username', flat=True))

    def get_detachment_member(self, obj):
        members = obj.get_members()
        return list(members.values_list('username', flat=True))