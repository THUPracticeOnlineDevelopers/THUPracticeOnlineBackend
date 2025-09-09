from rest_framework import serializers
from .models import Questionnaire, Question

invalid_answer = "问卷提交格式非法"

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['question_idx', 'question_text', 'question_type', 'options', 
                 'min_score', 'max_score', 'step']
        extra_kwargs = {
            'question_text': {
                'required': True,
                'allow_blank': False,
                'error_messages': {
                    'required': '题目描述不能为空',
                    'blank': '题目描述不能为空',
                    'max_length': '题目描述不得超过 500 个字符',
                }
            },
            'question_type': {
                'required': True,
                'allow_blank': False,
                'error_messages': {
                    'required': '请选择题目类型',
                    'blank': '请选择题目类型',
                }
            },
            'options': {
                'required': False,
                'allow_null': True
            },
            'min_score': {
                'required': False, 
                'allow_null': True
            },
            'max_score': {
                'required': False, 
                'allow_null': True
            },
            'step': {
                'required': False, 
                'allow_null': True
            },
        }

    def validate(self, data):
        q_type = data.get('question_type')
        if q_type in ['single', 'multiple']:
            if 'options' not in data or not isinstance(data['options'], list) or len(data['options']) == 0:
                raise serializers.ValidationError("选择题必须提供有效的选项列表")
        elif q_type == 'score':
            for field in ['min_score', 'max_score', 'step']:
                if data.get(field) is None:
                    raise serializers.ValidationError(f"打题必须提供{field}")
            if data['min_score'] >= data['max_score']:
                raise serializers.ValidationError("最低分必须小于最高分")
        elif q_type != 'text':
            raise serializers.ValidationError("无效的问题类型")
        return data

class QuestionnaireSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(
        many=True, 
        required=True, 
        error_messages={
            'required': '问题列表不能为空',
        }
    )
    permissions = serializers.ListField(
        child=serializers.CharField(), 
        required=True,
        allow_empty=False,
        error_messages={
            'required': '权限列表不能为空',
            'empty': '权限列表不能为空',
        }
    )

    class Meta:
        model = Questionnaire
        fields = ['id', 'title', 'permissions', 'questions', 'is_published', 'is_closed']
        extra_kwargs = {
            'title': {
                'required': True,
                'allow_blank': False,
                'error_messages': {
                    'required': '标题不能为空',
                    'blank': '标题不能为空',
                    'max_length': '标题不得超过 100 个字符',
                }
            }
        }
    
    def validate_questions(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("问题列表不能为空")
        return value

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        questionnaire = Questionnaire.objects.create(**validated_data)
        for q_data in questions_data:
            Question.objects.create(questionnaire=questionnaire, **q_data)
        return questionnaire
    
    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions')
        
        # 更新问卷基本信息
        instance.title = validated_data.get('title', instance.title)
        instance.permissions = validated_data.get('permissions', instance.permissions)
        instance.save()

        # 处理问题更新（先删除旧问题再创建新问题）
        instance.questions.all().delete()
        for q_data in questions_data:
            Question.objects.create(questionnaire=instance, **q_data)
        
        return instance

class AnswerSerializer(serializers.Serializer):
    question_idx = serializers.IntegerField(required=True)
    answer = serializers.JSONField(required=True)

    def validate(self, attrs):
        question = self.context.get('question')
        if not question:
            raise serializers.ValidationError("未找到对应问题")

        answer = attrs['answer']
        q_type = question.question_type

        # 根据问题类型验证答案
        if q_type == 'single':
            self._single_validate(question, answer)
            
        elif q_type == 'multiple':
            self._multiple_validate(question, answer)
            
        elif q_type == 'score':
            self._score_validate(question, answer)
            
        elif q_type == 'text':
            self._text_validate(question, answer)
            
        return attrs

    def _check_step(self, score, question):
        """验证步长，允许浮点数精度误差"""
        normalized = (score - question.min_score) / question.step
        return abs(normalized - round(normalized)) < 1e-6
    
    def _single_validate(self, question, answer):
        if not isinstance(answer, str) or answer not in question.options:
            raise serializers.ValidationError(invalid_answer)
    
    def _multiple_validate(self, question, answer):
        if not isinstance(answer, list) or any(opt not in question.options for opt in answer):
                raise serializers.ValidationError(invalid_answer)
    
    def _score_validate(self, question, answer):
        try:
            score = float(answer)
            if (score < question.min_score or 
                score > question.max_score or 
                not self._check_step(score, question)):
                raise ValueError
        except (TypeError, ValueError):
            raise serializers.ValidationError(invalid_answer)
    
    def _text_validate(self, question, answer):
        if not isinstance(answer, str):
                raise serializers.ValidationError(invalid_answer)