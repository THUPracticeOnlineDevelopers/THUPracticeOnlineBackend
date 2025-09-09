from django.test import TestCase
from utils.test import create_detachment, create_normal_user, create_super_administrator, create_notice
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

class SendNoticeViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('send-notice')
        self.admin = create_super_administrator()
        self.leader = create_normal_user('leader')
        self.member = create_normal_user('member')
        self.super_admin_token = str(RefreshToken.for_user(self.admin).access_token)
        self.normal_user_token = str(RefreshToken.for_user(self.leader).access_token)
        self.client.cookies['access_token'] = self.super_admin_token
        self.detachment = create_detachment(['leader'], ['member'])
        self.test_data = {
            'title': 'test notice',
            'content': 'notice',
            'detachment': [self.detachment.pk]
        }

    def test_send_notice_success(self):
        """测试成功发送通知"""
        response = self.client.post(self.url, self.test_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permission_denied(self):
        """测试权限不足"""
        self.client.cookies['access_token'] = self.normal_user_token
        response = self.client.post(self.url, self.test_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_title(self):
        """测试通知标题为空"""
        test_data = self.test_data.copy()
        test_data['title'] = ""
        response = self.client.post(self.url, test_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_content(self):
        """测试通知内容为空"""
        test_data = self.test_data.copy()
        test_data['content'] = ""
        response = self.client.post(self.url, test_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_detachment(self):
        """测试通知支队为空"""
        test_data = self.test_data.copy()
        test_data['detachment'] = []
        response = self.client.post(self.url, test_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class GetNoticeViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('get-notice')
        self.leader = create_normal_user('leader')
        self.member = create_normal_user('member')
        self.token = str(RefreshToken.for_user(self.leader).access_token)
        self.client.cookies['access_token'] = self.token
        self.detachment = create_detachment(['leader'], ['member'])
        self.notice = create_notice(detachments=[self.detachment])
    
    def test_get_notice_success(self):
        """测试成功获取通知"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_notice_unauthenticated(self):
        """测试用户未登录"""
        del self.client.cookies['access_token']
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class ConfirmViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('confirm')
        self.leader = create_normal_user('leader')
        self.member = create_normal_user('member')
        self.token = str(RefreshToken.for_user(self.leader).access_token)
        self.client.cookies['access_token'] = self.token
        self.detachment = create_detachment(['leader'], ['member'])
        self.notice = create_notice(detachments=[self.detachment])
        self.test_data = {
            'id': self.notice.pk
        }

    def test_confirm_success(self):
        """测试正常确认通知"""
        response = self.client.post(self.url, self.test_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_confirm_unauthenticated(self):
        """测试用户未登录"""
        del self.client.cookies['access_token']
        response = self.client.post(self.url, self.test_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_notice_does_not_exist(self):
        """测试通知不存在"""
        test_data = self.test_data.copy()
        test_data['id'] = self.notice.pk + 1
        response = self.client.post(self.url, test_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_confirm(self):
        """测试通知重复确认"""
        response = self.client.post(self.url, self.test_data)
        response = self.client.post(self.url, self.test_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class QueryViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('notice-query')
        self.admin = create_super_administrator()
        self.leader = create_normal_user('leader')
        self.member = create_normal_user('member')
        self.token = str(RefreshToken.for_user(self.admin).access_token)
        self.client.cookies['access_token'] = self.token
        self.detachment = create_detachment(['leader'], ['member'])
        for i in range(10):
            create_notice(
                detachments = [self.detachment],
                title = f'notice title{i}',
                content = f'notice {i}'
            )

    def test_query_success(self):
        """测试成功查询所有通知"""
        response = self.client.get(f'{self.url}?page=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_permission_denied(self):
        """测试权限不足"""
        self.client.cookies['access_token'] = str(RefreshToken.for_user(self.leader).access_token)
        response = self.client.get(f'{self.url}?page=1')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class QueryConfirmViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('query-confirm')
        self.admin = create_super_administrator()
        self.leader = create_normal_user('leader')
        self.member = create_normal_user('member')
        self.token = str(RefreshToken.for_user(self.leader).access_token)
        self.client.cookies['access_token'] = self.token
        self.detachment = create_detachment(['leader'], ['member'])
        self.notice = create_notice(detachments=[self.detachment])
        self.test_data = {
            'id': self.notice.pk
        }

    def test_query_confirm_success(self):
        """测试成功查询确认情况"""
        self.client.post(reverse('confirm'), self.test_data)
        self.client.cookies['access_token'] = str(RefreshToken.for_user(self.admin).access_token)
        response = self.client.post(self.url, self.test_data)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['all_user']), 1)
        self.assertEqual(len(response.data['confirmed_user']), 1)

    def test_permission_denied(self):
        """测试权限不足"""
        response = self.client.post(self.url, self.test_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_notice_does_not_exist(self):
        """测试通知不存在"""
        self.client.cookies['access_token'] = str(RefreshToken.for_user(self.admin).access_token)
        test_data = self.test_data.copy()
        test_data['id'] = self.notice.pk + 1
        response = self.client.post(self.url, test_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)