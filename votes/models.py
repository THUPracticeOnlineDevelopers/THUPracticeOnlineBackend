from django.db import models
from users.models import CustomUser

# Create your models here.
class Questionnaire(models.Model):
    title = models.CharField(max_length=100)
    permissions = models.JSONField()  # 存储权限列表，如["超级管理员", "普通管理员"]
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('single', '单选'),
        ('multiple', '多选'),
        ('text', '填空'),
        ('score', '打分'),
    ]
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questions')
    question_idx = models.IntegerField() # 题号
    question_text = models.TextField(max_length=500) # 题目描述
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    options = models.JSONField(null=True, blank=True)  # 选项
    min_score = models.IntegerField(null=True, blank=True)
    max_score = models.IntegerField(null=True, blank=True)
    step = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('questionnaire', 'question_idx')

    def __str__(self):
        return f"{self.question_idx}. {self.question_text}"

class Answer(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'questionnaire', 'question')

    def __str__(self):
        return f"{self.user} - {self.question}"