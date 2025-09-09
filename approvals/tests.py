# tests.py
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import ApprovalManageModel, ApprovalModel
from users.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken

class BaseTestCase(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.client = APIClient()
        self.super_admin = CustomUser.objects.create_user(
            username='superadmin',
            password='password',
            email = 'testemail1',
            user_permission=CustomUser.UserPermissions.super_administrator
        )
        self.admin = CustomUser.objects.create_user(
            username='admin',
            password='password',
            email = 'testemail2',
            user_permission=CustomUser.UserPermissions.administrator
        )
        self.user1 = CustomUser.objects.create_user(
            username='user1',
            password='password',
            email = 'testemail3',
            student_id='1001'
        )
        self.user2 = CustomUser.objects.create_user(
            username='user2',
            password='password',
            email = 'testemail4',
            student_id='1002'
        )
        self.valid_token = str(RefreshToken.for_user(self.super_admin).access_token)
        self.token = str(RefreshToken.for_user(self.admin).access_token)
        self.client.cookies['access_token'] = self.valid_token
        
        # 设置审核流程
        ApprovalManageModel.objects.create(reviewer=self.admin, order=1)
        ApprovalManageModel.objects.create(reviewer=self.super_admin, order=2)

class SendApprovalViewTests(BaseTestCase):
    def test_send_approval_success(self):
        url = reverse('send')
        data = {
            'sender_name': 'Test User',
            'link': 'https://example.com'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ApprovalModel.objects.count(), 1)

class QueryApprovalViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        # 创建测试审核数据
        ApprovalModel.objects.create(
            sender=self.admin,
            sender_name='Admin',
            link='https://example.com/1',
            reviewer=self.admin
        )
        ApprovalModel.objects.create(
            sender=self.super_admin,
            sender_name='Super Admin',
            link='https://example.com/2',
            reviewer=self.super_admin
        )

    def test_query_approvals(self):
        url = reverse('approval-query')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

class ApprovalWorkflowTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.approval = ApprovalModel.objects.create(
            sender=self.admin,
            sender_name='Admin',
            link='https://example.com',
            reviewer=self.admin
        )

    def test_pass_down_approval(self):
        self.client.cookies['access_token'] = self.token
        url = reverse('pass-down')
        data = {'id': self.approval.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.approval.refresh_from_db()
        self.assertEqual(self.approval.reviewer, self.super_admin)

    def test_reject_approval(self):
        self.client.cookies['access_token'] = self.token
        url = reverse('reject')
        data = {'id': self.approval.id, 'message': '需要修改'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.approval.refresh_from_db()
        self.assertEqual(self.approval.status, 'reject')

    def test_final_approve(self):
        # 先将审核人设置为最后一个审核人
        self.approval.reviewer = self.super_admin
        self.approval.save()
        self.client.cookies['access_token'] = self.valid_token
        
        url = reverse('approve')
        data = {'id': self.approval.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.approval.refresh_from_db()
        self.assertEqual(self.approval.status, 'approve')

class ManageApprovalViewTests(BaseTestCase):
    def test_manage_approval_flow(self):
        self.client.cookies['access_token'] = self.valid_token
        url = reverse('manage')
        data = {
            'user-id': [self.admin.id, self.super_admin.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ApprovalManageModel.objects.count(), 2)

    def test_manage_approval_with_usernames(self):
        self.client.cookies['access_token'] = self.valid_token
        url = reverse('manage')
        data = {
            'username': ['admin', 'superadmin']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ApprovalManageModel.objects.count(), 2)

class ModifyApprovalViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.approval = ApprovalModel.objects.create(
            sender=self.admin,
            sender_name='Admin',
            link='https://old-link.com',
            reviewer=self.admin
        )

    def test_modify_approval_success(self):
        self.client.cookies['access_token'] = self.token
        url = reverse('approval-modify')
        data = {
            'id': self.approval.id,
            'link': 'https://new-link.com'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.approval.refresh_from_db()
        self.assertEqual(self.approval.link, 'https://new-link.com')
        self.assertEqual(self.approval.status, 'review')

class QueryStatusViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        ApprovalModel.objects.create(
            sender=self.admin,
            sender_name='Admin',
            link='https://example.com',
            reviewer=self.admin
        )

    def test_query_status(self):
        self.client.cookies['access_token'] = self.token
        url = reverse('query-status')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

class ModelMethodTests(BaseTestCase):
    def test_approval_status_display(self):
        approval = ApprovalModel.objects.create(
            sender=self.admin,
            sender_name='Admin',
            link='https://example.com',
            reviewer=self.admin,
            status='approve'
        )
        self.assertEqual(approval.get_status(), '通过')

    def test_user_permission_label(self):
        self.assertEqual(
            CustomUser.get_permission_value('超级管理员'),
            CustomUser.UserPermissions.super_administrator
        )

class PermissionCheckTests(BaseTestCase):
    def test_check_reviewer(self):
        from utils.check import check_reviewer
        self.assertTrue(check_reviewer(self.admin, self.admin))
        self.assertFalse(check_reviewer(self.admin, self.user1))