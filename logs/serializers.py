from rest_framework import serializers
from detachments.models import Detachment
from .models import LogModel

class DetachmentLogSerializer(serializers.ModelSerializer):
    class Meta :
        model = Detachment
        fields = [
            'id',
            'name',
            'research_content',
            'member_num',
            'province',
            'city',
            'start_date',
            'end_date',
            'valid',
        ]


class LogSerializer(serializers.ModelSerializer) :
    class Meta :
        model = LogModel
        fields = [
            'date',
            'content',
        ]

class DetachmentWithLogsSerializer(serializers.ModelSerializer):
    """
    Main serializer to structure the output as requested.
    It serializes a Detachment and includes its related logs.
    """
    detachment = DetachmentLogSerializer(source='*') # Pass the whole detachment instance to SimpleDetachmentSerializer
    logs = serializers.SerializerMethodField()

    class Meta:
        model = Detachment # The primary model this serializer is based on for the list view
        fields = ['detachment', 'logs']

    def get_logs(self, obj):
        """
        Retrieves and serializes logs for the given detachment instance.
        Orders logs by date descending as per example.
        """
        # obj is an instance of Detachment
        # Access related logs using the reverse accessor (default: logmodel_set, or our custom 'logs_for_detachment')
        logs_queryset = obj.logs_for_detachment.all().order_by('-date') 
        return LogSerializer(logs_queryset, many=True).data