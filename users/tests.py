from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import CustomUser
from django.core.cache import cache
from utils.test import create_normal_user, create_administrator, create_super_administrator
from urllib.parse import quote, unquote
from unittest.mock import patch

class SendEmailViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('send-email')
        self.test_email = 'zuyz23@mails.tsinghua.edu.cn'

    def test_send_email_success(self):
        """测试成功发送验证码"""
        cache.clear()
        response = self.client.post(self.url, {'email': self.test_email})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(cache.get(f'verification_code:{self.test_email}'))

    def test_send_email_existing_user(self):
        """测试已注册邮箱发送验证码"""
        CustomUser.objects.create_user(username='existing', email=self.test_email, password='test123')
        response = self.client.post(self.url, {'email': self.test_email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_email_rate_limit(self):
        """测试1分钟内重复发送限制"""
        cache.clear()
        # 第一次发送
        self.client.post(self.url, {'email': self.test_email})
        # 立即尝试第二次发送
        response = self.client.post(self.url, {'email': self.test_email})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('register')
        self.test_data = {
            'username': 'testuser',
            'email': 'test@mails.tsinghua.edu.cn',
            'password': 'Testpass123',
            'student_id': '2021010001',
            'phone_number': '13800138000'
        }
        self.least_data = {
            'username' : 'testuser',
            'email' : 'test@mails.tsinghua.edu.cn',
            'password' : 'Testpass123',
        }
        # 预生成验证码
        cache.set(f'verification_code:test@mails.tsinghua.edu.cn', '123456', 600)

    def test_register_success(self):
        """测试成功注册"""
        data = {**self.test_data, 'verification_code': '123456'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(username='testuser').exists())

    def test_register_duplicate_username(self):
        """测试重复用户名注册"""
        CustomUser.objects.create_user(username='testuser', email='existing@mails.tsinghua.edu.cn', password='test1234')
        response = self.client.post(self.url, {**self.test_data, 'verification_code': '123456'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_studentId(self):
        """测试重复学号注册"""
        CustomUser.objects.create_user(username='testuser1', student_id='2021010001', password='test1234')
        response = self.client.post(self.url, {**self.test_data, 'verification_code': '123456'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_phonenumber(self):
        """测试重复手机号注册"""
        CustomUser.objects.create_user(username='testuser2', phone_number='13800138000', password='test1234')
        response = self.client.post(self.url, {**self.test_data, 'verification_code': '123456'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_code(self):
        """测试错误验证码注册"""
        data = {**self.test_data, 'verification_code': '654321'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_wrong_email(self):
        """ 测试邮箱格式不合法 """
        response = self.client.post(self.url, {'email':'test@testuser.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_username(self):
        """ 测试用户名格式不合法 """
        response = self.client.post(self.url, {'email':'testuser@mails.tsinghua.edu.cn', 'username':'123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_password(self):
        " 测试密码格式不合法 "
        wrong_password = ''
        for _ in range(100) :
            wrong_password += 'a'
        response = self.client.post(self.url, {'email':'testuser@mails.tsinghua.edu.cn', 'username':'testuser', 'password':wrong_password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_phone_number(self):
        " 测试是手机号格式不合法 "
        response = self.client.post(self.url, {**self.least_data, 'phone_number':'123456'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_student_id(self):
        " 测试学号格式不合法 "
        response = self.client.post(self.url, {**self.least_data, 'student_id':'123456'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_verification_code(self):
        " 测试验证码格式不合法 "
        response = self.client.post(self.url, {**self.test_data, 'verification_code':'123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class LoginViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('login')
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@mails.tsinghua.edu.cn',
            password='Testpass123',
            student_id='2021010001',
            phone_number='13800138000'
        )

    def test_login_username_success(self):
        """测试用户名登录成功"""
        response = self.client.post(self.url, {'username': 'testuser', 'password': 'Testpass123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_email_success(self):
        """测试邮箱登录成功"""
        response = self.client.post(self.url, {'email': 'test@mails.tsinghua.edu.cn', 'password': 'Testpass123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_phonenumber_success(self):
        """测试手机号登录成功"""
        response = self.client.post(self.url, {'phone_number': '13800138000', 'password': 'Testpass123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_studentId_success(self):
        """测试学号登录成功"""
        response = self.client.post(self.url, {'student_id': '2021010001', 'password': 'Testpass123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_login_invalid_password(self):
        """测试错误密码登录"""
        response = self.client.post(self.url, {'username': 'testuser', 'password': 'wrongpass'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        """测试不存在的用户登录"""
        response = self.client.post(self.url, {'username': 'nonexistent', 'password': 'test1234'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_email(self):
        " 测试邮箱格式非法 "
        response = self.client.post(self.url, {"email":'test@test.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_username(self):
        " 测试用户名格式非法 "
        response = self.client.post(self.url, {'username':'123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_password(self):
        " 测试密码格式非法 "
        response = self.client.post(self.url, {'password':'123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_phone_number(self):
        " 测试手机号格式非法 "
        response = self.client.post(self.url, {"password":"Testpass123", "phone_number":"123456"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_strudent_id(self):
        " 测试学号格式非法 "
        response = self.client.post(self.url, {"password":"Testpass123", "student_id":"123456"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class CustomUserModelTests(TestCase):
    def test_create_user(self):
        """测试用户模型创建"""
        user = CustomUser.objects.create_user(
            username='modeltest',
            email='model@test.com',
            password='test123'
        )
        self.assertEqual(user.email, 'model@test.com')
        self.assertTrue(user.check_password('test123'))

    def test_unique_constraints(self):
        """测试唯一性约束"""
        CustomUser.objects.create_user(username='user1', email='unique@test.com', password='test123')
        with self.assertRaises(Exception):
            CustomUser.objects.create_user(username='user2', email='unique@test.com', password='test123')

class GetUserViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('get-user')
        self.admin = create_super_administrator()
        self.normal_user = create_normal_user('user')
        admin_token = str(RefreshToken.for_user(self.admin).access_token)
        self.client.cookies['access_token'] = admin_token

    def test_get_users_with_admin(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_unauthorized_access(self):
        client = APIClient()
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class GetAdminViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('get-administrator')
        self.admin = create_administrator()
        admin_token = str(RefreshToken.for_user(self.admin).access_token)
        self.client.cookies['access_token'] = admin_token

    def test_get_admins(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_unauthorized_access(self):
        client = APIClient()
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class GetSuperAdminViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('get-super')
        self.super_admin = create_super_administrator()
        admin_token = str(RefreshToken.for_user(self.super_admin).access_token)
        self.client.cookies['access_token'] = admin_token

    def test_get_super_admins(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_unauthorized_access(self):
        client = APIClient()
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class GetAllAdminViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('get-all-administrator')
        self.admin = create_administrator()
        self.super_admin = create_super_administrator()
        admin_token = str(RefreshToken.for_user(self.admin).access_token)
        self.client.cookies['access_token'] = admin_token

    def test_get_all_admins(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['all-admin']), 2)
        usernames = [user['username'] for user in response.data['all-admin']]
        self.assertIn('test_administrator', usernames)
        self.assertIn('test_super_administrator', usernames)

    def test_unauthorized_access(self):
        client = APIClient()
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class ModifyPermissionViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('modify-permission')
        self.super_admin = create_super_administrator()
        self.normal_user = create_normal_user('user')
        super_token = str(RefreshToken.for_user(self.super_admin).access_token)
        self.client.cookies['access_token'] = super_token

    def test_modify_permission_success(self):
        data = {
            'username': 'user',
            'user_permission': '普通管理员'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_user = CustomUser.objects.get(username='user')
        self.assertEqual(updated_user.user_permission, CustomUser.UserPermissions.administrator)

    def test_modify_with_invalid_permission(self):
        data = {
            'username': 'user',
            'user_permission': '错误权限名称'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_access(self):
        data = {
            'username': 'user',
            'user_permission': '普通管理员'
        }
        client = APIClient()
        response = client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_does_not_exist(self):
        data = {
            'username': 'user_not_exist',
            'user_permission': '普通管理员'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class FeishuBindViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('feishu-bind')
        self.user = create_normal_user('user')
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.cookies['access_token'] = token

    @patch('users.views.feishu_authenticated')
    def test_get_auth_url(self, mock_auth):
        mock_auth.return_value = False

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_url', response.data)
        self.assertIn('https://accounts.feishu.cn/open-apis/authen/v1/authorize', response.data['auth_url'])

    @patch('users.views.feishu_authenticated')
    def test_already_bind(self, mock_auth):
        mock_auth.return_value = True

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class FeishuCallbackViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('feishu-callback')
        self.user = create_normal_user('test_user')
        user_token = str(RefreshToken.for_user(self.user).access_token)
        self.client.cookies['access_token'] = user_token
        self.source_url = 'https://localhost:3000/handbook'

    def _build_callback_url(self, code=None, error=None):
        # 构建带来源参数的callback URL
        base_url = reverse('feishu-callback')
        encoded_source = quote(f"{self.source_url}/handbook")
        url = f"{base_url}?from={encoded_source}"
        
        if code:
            url += f"&code={code}"
        if error:
            url += f"&error={error}"
        return url

    @patch('users.views.get_user_info')
    @patch('users.views.get_user_access_token')
    def test_successful_binding(self, mock_get_token, mock_get_info):
        mock_get_token.return_value = ('test_token', 7200, 'refresh_token', 7200)
        mock_get_info.return_value = 'feishu_123'
        
        response = self.client.get(self._build_callback_url(code='test_code'))
        self.assertEqual(response.status_code, 302)
        updated_user = CustomUser.objects.get(username='test_user')
        self.assertEqual(updated_user.lark_open_id, 'feishu_123')

    def test_error_response(self):
        response = self.client.get(self._build_callback_url(error='access_denied'))
        self.assertEqual(response.status_code, 302)
        redirect_url = unquote(response.url)
        self.assertIn('error=飞书授权失败', redirect_url)

    def test_no_code(self):
        response = self.client.get(self._build_callback_url())
        self.assertEqual(response.status_code, 302)
        redirect_url = unquote(response.url)
        self.assertIn('error=缺少授权码(code)', redirect_url)

class GetUserByIdViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('get-user-by-id')
        self.user = create_normal_user('test_user')
    
    def test_get_user_info_success(self):
        response = self.client.post(self.url, {"id": self.user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_does_not_exist(self):
        response = self.client.post(self.url, {"id": 99999})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)