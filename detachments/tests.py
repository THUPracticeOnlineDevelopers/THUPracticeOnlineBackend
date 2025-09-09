from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import CustomUser
from .models import Detachment, DetachmentMembership
from rest_framework_simplejwt.tokens import RefreshToken
from utils.test import create_detachment, create_normal_user, create_super_administrator

class CreateDetachmentViewTests(TestCase):
    def setUp(self):
        " 测试设置 "
        self.client = APIClient()
        self.url = reverse('create')
        self.super_administrator = create_super_administrator()
        self.usernames = ['leader_1', 'leader_2', 'member_1', 'member_2']
        create_normal_user(self.usernames)
        self.access_token = str(RefreshToken.for_user(self.super_administrator).access_token)
        self.client.cookies['access_token'] = self.access_token
        self.test_data = {
            'name' : 'test_detachment',
            'start_date' : '2000-01-01',
            'end_date' : '2000-01-02',
            'detachment_leader' : ['leader_1', 'leader_2'],
            'detachment_member' : ['member_1', 'member_2'],
        }

    def test_detachment_create(self):
        " 测试成功创建支队 "
        response = self.client.post(self.url, self.test_data, format='json')
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_wrong_permission(self):
        " 测试用户权限不足 "
        client = APIClient()
        user = CustomUser.objects.get(username='member_1')
        token = str(RefreshToken.for_user(user).access_token)
        client.cookies['access_token'] = token
        response = client.post(self.url, self.test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_name(self):
        " 测试支队名不合法 "
        response = self.client.post(self.url, {'name':1, 'start_date':'2000-01-01'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_start_date(self):
        " 测试开始日期不合法 "
        response = self.client.post(self.url, {'name':'test_detachment', 'start_date':'wrong_date'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_end_date(self):
        " 测试结束日期不合法 "
        response = self.client.post(self.url, {"name":"test_detachment", 'start_date':'2000-01-01', 'end_date':'wrong_date'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_detachment_leaders(self):
        " 测试支队长格式 "
        test_data = {
            'name' : 'test_detachment',
            'start_date' : '2000-01-01',
            'end_date' : '2000-01-02',
        }
        response = self.client.post(self.url, {**test_data, 'detachment_leader':"123"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_detachment_leaders_name(self):
        " 测试支队长格式 "
        test_data = {
            'name' : 'test_detachment',
            'start_date' : '2000-01-01',
            'end_date' : '2000-01-02',
        }
        response = self.client.post(self.url, {**test_data, 'detachment_leader':[1,2,3]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_detachment_leader(self):
        " 测试支队长格式 "
        test_data = {
            'name' : 'test_detachment',
            'start_date' : '2000-01-01',
            'end_date' : '2000-01-02',
        }
        response = self.client.post(self.url, {**test_data, 'detachment_leader':['Mr. Nobody']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_detachment_member(self):
        " 测试支队员格式 "
        test_data = {
            'name' : 'test_detachment',
            'start_date' : '2000-01-01',
            'end_date' : '2000-01-02',
            'detachment_leader' : ['leader_1'],
        }
        response = self.client.post(self.url, {**test_data, 'detachment_member':"123"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_detachment_members_name(self):
        " 测试支队员格式 "
        test_data = {
            'name' : 'test_detachment',
            'start_date' : '2000-01-01',
            'end_date' : '2000-01-02',
            'detachment_leader' : ['leader_1'],
        }
        response = self.client.post(self.url, {**test_data, 'detachment_member':[1,2,3]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_detachment_member(self):
        " 测试支队员格式 "
        test_data = {
            'name' : 'test_detachment',
            'start_date' : '2000-01-01',
            'end_date' : '2000-01-02',
            'detachment_leader' : ['leader_1'],
        }
        response = self.client.post(self.url, {**test_data, 'detachment_member':['Mr. Nobody']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class ModifyDetachmentViewTests(TestCase):
    def setUp(self) -> None:
        " 测试设置 "
        self.client = APIClient()
        self.url = reverse('detachment-modify')
        self.super_administrator = create_super_administrator()
        self.usernames = ['leader_1', 'leader_2', 'member_1', 'member_2']
        create_normal_user(self.usernames)
        self.detachment = create_detachment(['leader_1', 'leader_2'], ['member_1', 'member_2'])
        self.access_token = str(RefreshToken.for_user(self.super_administrator).access_token)
        self.client.cookies['access_token'] = self.access_token
        self.test_data = {
            'id' : self.detachment.id,
            'name' : 'test_detachment',
            'start_date' : '2000-01-01',
            'end_date' : '2000-01-02',
            'detachment_member' : ['member_1'],
        }

    def test_modify_detachment(self):
        " 测试修改支队信息 "
        response = self.client.post(self.url, self.test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_not_existed_detachment(self):
        " 测试支队不存在 "
        response = self.client.post(self.url, {'id':10086}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_wrong_permission(self):
        " 测试用户权限不足 "
        client = APIClient()
        user = CustomUser.objects.get(username='member_1')
        token = str(RefreshToken.for_user(user).access_token)
        client.cookies['access_token'] = token
        response = client.post(self.url, self.test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_name(self):
        " 测试名字不合法 "
        long_name = ''
        for _ in range(200):
            long_name += 'a'
        response = self.client.post(self.url, {'id':self.detachment.id, 'name':long_name})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_start_date(self):
        " 测试开始日期不合法 "
        response = self.client.post(self.url, {'id':self.detachment.id, 'name':'change', 'start_date':'wrong_date'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_end_date(self):
        " 测试结束日期不合法 "
        response = self.client.post(self.url, {'id':self.detachment.id, 'end_date':'wrong_date'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_wrong_detachment_member(self):
        " 测试支队员格式 "
        test_data = {
            'id' : self.detachment.id,
            'name' : 'test_detachment',
            'start_date' : '2000-01-01',
            'end_date' : '2000-01-02',
        }
        response = self.client.post(self.url, {**test_data, 'detachment_member':'wrong'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_detachment_members_name(self):
        " 测试支队员格式 "
        test_data = {
            'id' : self.detachment.id,
            'name' : 'test_detachment',
            'start_date' : '2000-01-01',
            'end_date' : '2000-01-02',
        }
        response = self.client.post(self.url, {**test_data, 'detachment_member':[1,2,3]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_detachment_member(self):
        " 测试支队员格式 "
        test_data = {
            'id' : self.detachment.id,
            'name' : 'test_detachment',
            'start_date' : '2000-01-01',
            'end_date' : '2000-01-02',
        }
        response = self.client.post(self.url, {**test_data, 'detachment_member':['Mr. Nobody']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class DeactivateDetachmentViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('deactivate')
        self.admin = create_super_administrator()
        self.detachment = create_detachment([], [])
        self.valid_token = str(RefreshToken.for_user(self.admin).access_token)
        
    def test_successful_deactivation(self):
        """测试管理员成功停用支队"""
        self.client.cookies['access_token'] = self.valid_token
        response = self.client.post(self.url, {'id': self.detachment.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Detachment.objects.get(id=self.detachment.id).valid)

    def test_deactivate_nonexistent_detachment(self):
        """测试停用不存在的支队"""
        self.client.cookies['access_token'] = self.valid_token
        response = self.client.post(self.url, {'id': 9999})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_deactivation(self):
        """测试普通用户无权停用"""
        user = create_normal_user('test_user')
        token = str(RefreshToken.for_user(user).access_token)
        self.client.cookies['access_token'] = token
        response = self.client.post(self.url, {'id': self.detachment.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class DeleteDetachmentViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('delete')
        self.admin = create_super_administrator()
        self.detachment = create_detachment([], [])
        self.valid_token = str(RefreshToken.for_user(self.admin).access_token)

    def test_successful_deletion(self):
        """测试管理员成功删除支队"""
        self.client.cookies['access_token'] = self.valid_token
        response = self.client.post(self.url, {'id': self.detachment.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Detachment.objects.filter(id=self.detachment.id).exists())

    def test_delete_nonexistent_detachment(self):
        """测试删除不存在的支队"""
        self.client.cookies['access_token'] = self.valid_token
        response = self.client.post(self.url, {'id': 9999})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_deletion(self):
        """测试普通用户无权删除"""
        user = create_normal_user('test_user')
        token = str(RefreshToken.for_user(user).access_token)
        self.client.cookies['access_token'] = token
        response = self.client.post(self.url, {'id': self.detachment.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class GetDetachmentViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.get_all_url = reverse('get-all')
        self.get_valid_url = reverse('get-valid')
        self.detachment1 = create_detachment([], [])
        self.detachment2 = create_detachment([], [])
        self.detachment2.valid = False
        self.detachment2.save()

    def test_get_all_detachments(self):
        """测试获取所有支队"""
        response = self.client.get(self.get_all_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_valid_detachments(self):
        """测试获取有效支队"""
        response = self.client.get(self.get_valid_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.detachment1.id)

    def test_pagination(self):
        """测试分页功能"""
        # 创建足够多的支队测试分页
        for i in range(15):
            create_detachment([], [])
        response = self.client.get(self.get_all_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # 默认分页大小
        self.assertIsNotNone(response.data['next'])