# tests.py
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework import status
from .models import LetterFileModel, LetterPairModel
from .serializers import LetterPairSerializer
from users.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken

class ModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            student_id='123456'
        )
        self.admin = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            user_permission=CustomUser.UserPermissions.administrator
        )

    def test_letter_pair_status(self):
        letter_file = LetterFileModel.objects.create(
            filename='test.docx',
            sender=self.user,
            mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        pair = LetterPairModel.objects.create(
            letter=letter_file,
            owner=self.user
        )
        self.assertEqual(pair.get_status(), '盖章中')
        pair.status = 'finish'
        pair.save()
        self.assertEqual(pair.get_status(), '已盖章')

class ViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.factory = APIRequestFactory()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            student_id='123456'
        )
        self.admin = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            user_permission=CustomUser.UserPermissions.administrator
        )
        
        # 测试文件
        self.test_file = SimpleUploadedFile(
            "test.docx", 
            b"file_content", 
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        self.user_token =  str(RefreshToken.for_user(self.user).access_token) 
        self.admin_token = str(RefreshToken.for_user(self.admin).access_token)
        self.client.cookies['access_token'] = self.user_token

    def test_upload_template_permission_denied(self):
        response = self.client.post(reverse('upload-template'), {'file': self.test_file})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_upload_template_success(self):
        self.client.cookies['access_token'] = self.admin_token
        response = self.client.post(reverse('upload-template'), {'file': self.test_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LetterFileModel.objects.count(), 1)

    def test_upload_letter_success(self):
        response = self.client.post(reverse('upload-letter'), {'file': self.test_file})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LetterPairModel.objects.count(), 1)

    def test_download_file(self):
        letter = LetterFileModel.objects.create(
            filename='test.docx',
            file=self.test_file,
            sender=self.user,
            mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response = self.client.post(reverse('download'), {'id': letter.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    def test_query_status_pagination(self):
        # 创建测试数据
        for i in range(15):
            letter = LetterFileModel.objects.create(
                filename=f'letter_{i}.docx',
                sender=self.user,
                mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            LetterPairModel.objects.create(letter=letter, owner=self.user)
        
        response = self.client.get(reverse('query-letter-status'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # 假设分页大小为10

class SerializerTests(TestCase):
    def test_letter_pair_serialization(self):
        user = CustomUser.objects.create_user(username='test', email='test@example.com')
        letter = LetterFileModel.objects.create(
            filename='test.docx',
            sender=user,
            mime_type='application/msword'
        )
        pair = LetterPairModel.objects.create(
            letter=letter,
            owner=user,
            status='finish'
        )
        serializer = LetterPairSerializer(pair)
        self.assertEqual(serializer.data['status'], '已盖章')
        self.assertEqual(serializer.data['letter']['filename'], 'test.docx')

class PermissionTests(TestCase):
    def test_admin_permission_check(self):
        admin = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            user_permission=CustomUser.UserPermissions.administrator
        )
        normal_user = CustomUser.objects.create_user(
            username='user',
            email='user@example.com',
        )
        
        # 测试删除模板权限
        client = APIClient()
        self.user_token =  str(RefreshToken.for_user(normal_user).access_token) 
        self.admin_token = str(RefreshToken.for_user(admin).access_token)
        # 普通用户尝试删除
        client.cookies['access_token'] = self.user_token 
        response = client.post(reverse('delete-template'), {'id': 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 管理员删除
        client.cookies['access_token'] = self.admin_token
        response = client.post(reverse('delete-template'), {'id': 1})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class FileValidationTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            user_permission=CustomUser.UserPermissions.administrator
        )
        self.invalid_file = SimpleUploadedFile(
            "test.txt", 
            b"file_content", 
            content_type="text/plain"
        )
        self.admin_token = str(RefreshToken.for_user(self.admin).access_token)

    def test_invalid_file_upload(self):
        self.client.cookies['access_token'] = self.admin_token
        response = self.client.post(reverse('upload-template'), {'file': self.invalid_file})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)