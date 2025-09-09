# tests.py
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Questionnaire, Question, Answer
from users.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken
from utils.test import create_normal_user, create_super_administrator
from django.urls import reverse

# 公共基础测试类
class BaseQuestionnaireTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.super_admin = create_super_administrator()
        cls.normal_user = create_normal_user('user')

class CreateQuestionnaireViewTests(BaseQuestionnaireTest):
    def setUp(self):
        self.client = APIClient()
        self.valid_data = {
            "title": "员工满意度调查",
            "permissions": ["普通用户"],
            "questions": [
                {
                    "question_idx": 1,
                    "question_text": "您对薪资是否满意？",
                    "question_type": "single",
                    "options": ["满意", "一般", "不满意"]
                }
            ]
        }
        self.url = reverse('create-questionaire')

    def test_admin_can_create(self):
        """测试管理员创建问卷成功"""
        self.client.cookies['access_token'] = str(RefreshToken.for_user(self.super_admin).access_token)
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Questionnaire.objects.count(), 1)

    def test_normal_user_create_fail(self):
        """测试普通用户创建失败"""
        self.client.cookies['access_token'] = str(RefreshToken.for_user(self.normal_user).access_token)
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class SubmitAnswerViewTests(BaseQuestionnaireTest):
    def setUp(self):
        self.client = APIClient()
        # 创建测试问卷
        self.questionnaire = Questionnaire.objects.create(
            title="测试问卷",
            permissions=["普通用户"],
            is_published=True
        )
        Question.objects.create(
            questionnaire=self.questionnaire,
            question_idx=1,
            question_text="单选题",
            question_type="single",
            options=["A", "B"]
        )
        Question.objects.create(
            questionnaire=self.questionnaire,
            question_idx=2,
            question_text="填空题",
            question_type="text"
        )
        self.url = reverse('submit-questionaire')

    def test_valid_submission(self):
        """测试有效答案提交"""
        self.client.cookies['access_token'] = str(RefreshToken.for_user(self.normal_user).access_token)
        data = {
            "id": self.questionnaire.id,
            "answers": [
                {"question_idx": 1, "answer": "A"},
                {"question_idx": 2, "answer": "自由文本"}
            ]
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Answer.objects.count(), 2)

    def test_invalid_type_submission(self):
        """测试无效答案类型提交"""
        self.client.cookies['access_token'] = str(RefreshToken.for_user(self.normal_user).access_token)
        data = {
            "id": self.questionnaire.id,
            "answers": [
                {"question_idx": 1, "answer": ["A", "B"]}  # 单选不能提交数组
            ]
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class GetQuestionnaireListViewTests(BaseQuestionnaireTest):
    def setUp(self):
        self.client = APIClient()
        # 创建不同权限的问卷
        Questionnaire.objects.create(
            title="管理员问卷",
            permissions=["超级管理员"],
            is_published=True
        )
        Questionnaire.objects.create(
            title="用户问卷",
            permissions=["普通用户"],
            is_published=True
        )
        self.url = reverse('get-questionaire')

    def test_get_all_questionaire(self):
        """测试获取所有问卷"""
        self.client.cookies['access_token'] = str(RefreshToken.for_user(self.normal_user).access_token)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data["results"]), 2)

class UpdateQuestionnaireViewTests(BaseQuestionnaireTest):
    def setUp(self):
        self.client = APIClient()
        self.client.cookies['access_token'] = str(RefreshToken.for_user(self.super_admin).access_token)
        self.questionnaire = Questionnaire.objects.create(
            title="原始问卷",
            permissions=["普通用户"]
        )
        self.update_data = {
            "id": self.questionnaire.id,
            "title": "更新后的问卷",
            "permissions": ["普通用户"],
            "questions": [
                {
                    "question_idx": 1,
                    "question_text": "新问题",
                    "question_type": "single",
                    "options": ["是", "否"]
                }
            ]
        }
        self.url = reverse('update-questionaire')

    def test_valid_update(self):
        """测试有效更新"""
        response = self.client.post(self.url, self.update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.questionnaire.refresh_from_db()
        self.assertEqual(self.questionnaire.title, "更新后的问卷")

class DeleteQuestionnaireViewTests(BaseQuestionnaireTest):
    def setUp(self):
        self.client = APIClient()
        self.client.cookies['access_token'] = str(RefreshToken.for_user(self.super_admin).access_token)
        self.questionnaire = Questionnaire.objects.create(title="待删除问卷", permissions=["超级管理员"])
        self.url = reverse('delete-questionaire')

    def test_successful_deletion(self):
        """测试成功删除"""
        response = self.client.post(self.url, {"id": self.questionnaire.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Questionnaire.objects.count(), 0)

class QuestionnaireResultViewTests(BaseQuestionnaireTest):
    def setUp(self):
        self.client = APIClient()
        self.client.cookies['access_token'] = str(RefreshToken.for_user(self.super_admin).access_token)
        self.questionnaire = Questionnaire.objects.create(title="结果问卷", permissions=["超级管理员"], is_published=True)
        self.question = Question.objects.create(
            questionnaire=self.questionnaire,
            question_idx=1,
            question_text="测试问题",
            question_type="single",
            options=["A", "B"]
        )
        Answer.objects.create(
            user=self.normal_user,
            questionnaire=self.questionnaire,
            question=self.question,
            answer="A"
        )
        self.url = reverse('questionaire-result')

    def test_result_retrieval(self):
        """测试结果获取"""
        data = {"id": self.questionnaire.id}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)