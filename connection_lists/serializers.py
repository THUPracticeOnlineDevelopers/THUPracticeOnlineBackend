from rest_framework import serializers
from .models import ConnectionListModel

class ConnectionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectionListModel
        fields = ['id', 'detachment_name', 'leader',
                   'theme','duration', 'location',
                    'enterprise', 'government', 'venue']
        extra_kwargs = {
            'detachment_name' : {
                'required' : True,
                'error_messages' : {
                    'required' : '支队名不能为空',
                    'max_length' : '支队名不能超过100个字符',
                },
            },

            'leader' : {
                'required' : True,
                'error_messages' : {
                    'required' : '支队长不能为空',
                    'max_length' : '支队名不能超过100个字符',
                },
            },

            'theme' : {
                'required' : True,
                'error_messages' : {
                    'required' : '主题不能为空',
                    'max_length' : '主题不能超过100个字符',
                },
            },

            'duration' : {
                'required' : True,
                'error_messages' : {
                    'required' : '时间不能为空',
                    'max_length' : '时间不能超过100个字符',
                },
            },

            'location' : {
                'required' : True,
                'error_messages' : {
                    'required' : '实践地不能为空',
                    'max_length' : '实践地不能超过100个字符',
                },
            },

            'enterprise' : {
                'required' : True,
                'error_messages' : {
                    'required' : '企业不能为空',
                    'max_length' : '企业不能超过1000个字符',
                },
            },

            'government' : {
                'required' : True,
                'error_messages' : {
                    'required' : '政府机构不能为空',
                    'max_length' : '企业不能超过1000个字符',
                },
            },

            'venue' : {
                'required' : True,
                'error_messages' : {
                    'required' : '场馆不能为空',
                    'max_length' : '场馆不能超过1000个字符',
                },
            },
        }

    def create(self, validated_data):
        return ConnectionListModel.objects.create(**validated_data)

    def validate(self, attrs):
        return attrs