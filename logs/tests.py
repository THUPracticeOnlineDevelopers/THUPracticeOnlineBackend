from django.urls import reverse
from rest_framework.test import APITestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from detachments.models import Detachment, DetachmentMembership
from .models import LogModel
import datetime
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class InitLogViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass',
            email='test@example.com'
        )
        self.detachment = Detachment.objects.create(
            name='Test Detachment',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=7)
        )
        DetachmentMembership.objects.create(
            user=self.user,
            detachment=self.detachment,
            role='member'
        )
        self.user_token = str(RefreshToken.for_user(self.user).access_token)
        self.client.cookies['access_token'] = self.user_token

    def test_successful_initialization(self):
        url = reverse('init-log')
        data = {
            'id': self.detachment.id,
            'research': 'Test Research',
            'number': 10,
            'province': 'Test Province',
            'city': 'Test City'
        }
        response = self.client.post(url, data, format='json')
        self.detachment.refresh_from_db()
        
        self.assertEqual(response.status_code, 200)
        
        self.assertTrue(self.detachment.init)
        self.assertEqual(self.detachment.research_content, 'Test Research')

    def test_user_not_in_detachment(self):
        new_user = User.objects.create_user(username='newuser', password='testpass')
        token = str(RefreshToken.for_user(new_user).access_token)
        self.client.cookies['access_token'] = token
        
        url = reverse('init-log')
        data = {'id': self.detachment.id}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_invalid_parameters(self):
        url = reverse('init-log')
        invalid_data = [
            {'research': 123},  # 非字符串类型
            {'number': 200},    # 超过50
            {'province': 'A'*101}, # 超长字符串
        ]
        
        for data in invalid_data:
            data['id'] = self.detachment.id
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 400)


class WriteLogViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass',
            email='test@example.com'
        )
        self.detachment = Detachment.objects.create(
            name='Test Detachment',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=7),
            init = True
        )
        DetachmentMembership.objects.create(
            user=self.user,
            detachment=self.detachment,
            role='member'
        )
        self.user_token = str(RefreshToken.for_user(self.user).access_token)
        self.client.cookies['access_token'] = self.user_token

    def test_create_new_log(self):
        url = reverse('write-log')
        data = {
            'id': self.detachment.id,
            'content': 'Test log content',
            'date': '2023-01-01'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(LogModel.objects.exists())

    def test_update_existing_log(self):
        # 先创建日志
        url = reverse('write-log')
        LogModel.objects.create(
            detachment=self.detachment,
            date='2023-01-01',
            content='Original content'
        )
        
        data = {
            'id': self.detachment.id,
            'date': '2023-01-01',
            'content': 'Updated content'
        }
        response = self.client.post(url, data)
        
        log = LogModel.objects.get()
        self.assertEqual(log.content, 'Updated content')
        self.assertEqual(response.status_code, 200)

    def test_uninitialized_detachment(self):
        url = reverse('write-log')
        self.detachment.init = False
        self.detachment.save()
        
        data = {
            'id': self.detachment.id,
            'date': '2023-01-01',
            'content': 'Updated content'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)


class QueryLogViewTests(APITestCase):
    def setUp(self):
        # 创建测试数据
        self.admin = User.objects.create_user(
            username='admin',
            password = '1234567',
            email = 'admin@test.com',
            user_permission=User.UserPermissions.super_administrator
        )
        self.normal_user = User.objects.create_user(
            username = 'user',
            password = '12345678',
            email = 'user@test.com',
        )
        
        # 创建多个支队和日志
        for i in range(15):
            detachment = Detachment.objects.create(
                name = f"detachment_{i}",
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + datetime.timedelta(days=7)
            )
            LogModel.objects.create(
                detachment=detachment,
                content=f'Log_{i}',
                date=timezone.now().date()
            )

    def test_admin_access(self):
        self.user_token = str(RefreshToken.for_user(self.admin).access_token)
        self.client.cookies['access_token'] = self.user_token
        url = reverse('query-log')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 10)  # 分页测试

    def test_normal_user_access(self):
        # 将用户加入部分支队
        for detachment in Detachment.objects.all()[:5]:
            DetachmentMembership.objects.create(user=self.normal_user, detachment=detachment, role='member')
        
        self.user_token = str(RefreshToken.for_user(self.normal_user).access_token)
        self.client.cookies['access_token'] = self.user_token
        url = reverse('query-log')
        response = self.client.get(url)
        
        self.assertEqual(len(response.data['results']), 5)

    def test_serializer_output(self):
        self.user_token = str(RefreshToken.for_user(self.admin).access_token)
        self.client.cookies['access_token'] = self.user_token
        url = reverse('query-log')
        response = self.client.get(url)
        
        first_result = response.data['results'][0]
        self.assertIn('detachment', first_result)
        self.assertIn('logs', first_result)
        self.assertEqual(len(first_result['logs']), 1)