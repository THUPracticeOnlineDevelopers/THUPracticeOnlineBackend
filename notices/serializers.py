from rest_framework import serializers
from .models import Notice, UserNotice
from detachments.models import Detachment

class NoticeSerializer(serializers.ModelSerializer):
    detachment = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Detachment.objects.all(),
        required = False,
        error_messages = {
            "does_not_exist": "指定支队主键不存在",
            "incorrect_type": "支队主键类型错误"
        }
    )

    class Meta:
        model = Notice
        fields = ['id', 'title', 'content', 'sender', 'detachment', 'date']
        read_only_fields = ['date']
        extra_kwargs = {
            'title': {
                'required': True,
                'error_messages': {
                    'required': '标题不能为空',
                    'blank': '标题不能为空',
                    'max_length': '标题不得超过 100 个字符',
                }
            },
            'content': {
                'required': True,
                'error_messages': {
                    'required': '内容不能为空',
                    'blank': '内容不能为空',
                    'max_length': '正文不得超过 5000 个字符',
                }
            },
            'sender': {
                'required': False,
                'allow_blank': True,
                'default': '团委实践组',
                'error_messages': {
                    'max_length': '发送方不得超过 100 个字符',
                }
            }
        }

    
    def create(self, validated_data):
        detachments = validated_data.pop("detachment", [])
        notice = Notice.objects.create(**validated_data)
        notice.detachment.set(detachments)
        for detachment in detachments:
            for leader in detachment.get_leaders():
                UserNotice.objects.get_or_create(user=leader, notice=notice)
        return notice
    
    def validate(self, attrs):
        if 'sender' in attrs and attrs['sender'].strip() == '':
            attrs['sender'] = '团委实践组'  # 设置默认值
        detachment = attrs.get('detachment', [])
        if len(detachment) == 0:
            raise serializers.ValidationError({"error": "请至少选择一个支队"})
        return attrs
    
class UserNoticeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='notice.id')
    title = serializers.CharField(source='notice.title')
    content = serializers.CharField(source='notice.content')
    sender = serializers.CharField(source='notice.sender')

    class Meta:
        model = UserNotice
        fields = ['id', 'title', 'content', 'sender', 'confirmed']