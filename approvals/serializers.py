from rest_framework import serializers
from .models import ApprovalModel, ApprovalManageModel
from users.serializers import UsernameSerializer, CustomUserSerializer

class ApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalModel
        fields = [
            'id',
            'sender',
            'sender_name',
            'link',
            'status',
            'message',
            'reviewer',
        ]
        extra_kwargs = {
            'sender_name' : {
                'required' : True,
                'error_messages' : {
                    'required' : '送审人不能为空',
                    'max_length' : '送审人姓名不能超过100字',
                } 
            },
            'link' : {
                'required' : True,
                'error_messages' : {
                    'required' : '链接不能为空',
                    'max_length' : '链接不能超过200字符',
                }
            },
        }

    def validate(self, attrs):
        return super().validate(attrs)
    
    def create(self, validated_data):
        return ApprovalModel.objects.create(**validated_data)
    
class ReviewApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalModel
        fields = [
            'id',
            'sender_name',
            'link',
        ]

class QueryStatusSerializer(serializers.ModelSerializer):
    reviewer = UsernameSerializer(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalModel
        fields = [
            'id',
            'sender_name',
            'link',
            'status',
            'message',
            'reviewer',
        ]

    def get_status(self, obj):
        "获取中文状态"
        return obj.get_status()
    
class ReviewerSerializer(serializers.ModelSerializer):
    reviewer = CustomUserSerializer(read_only=True)

    class Meta:
        model = ApprovalManageModel
        fields = [
            'order',
            'reviewer',
        ]