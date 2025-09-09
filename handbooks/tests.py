from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from .models import Handbook
from unittest.mock import patch
from users.models import CustomUser
from utils.test import create_normal_user, create_super_administrator
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

not_permitted = "用户权限不足"
handbook_miss = "文档不存在"

class GetLinkViewTest(APITestCase):
    def setUp(self):
        self.user = create_normal_user('test_user')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('get-link')
        self.access_token = str(RefreshToken.for_user(self.user).access_token)
        self.client.cookies['access_token'] = self.access_token

    def test_get_empty_handbooks(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["handbook"]), 0)

    def test_get_handbooks_success(self):
        Handbook.objects.create(document_id="doc1", url="http://example.com", title="Test")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["handbook"]), 1)

class CreateHandbookViewTest(APITestCase):
    def setUp(self):
        self.admin = create_super_administrator()
        self.user = create_normal_user('user')
        self.access_token = str(RefreshToken.for_user(self.admin).access_token)
        self.client.cookies['access_token'] = self.access_token
        self.url = reverse('create-handbook')

    @patch('handbooks.views.add_coauthor')
    @patch('handbooks.views.create_feishu_document')
    @patch('handbooks.views.feishu_authenticated')
    def test_create_success(self, mock_authenticated, mock_create, mock_add):
        mock_authenticated.return_value = True
        mock_create.return_value = ("doc123", "http://feishu.com")
        mock_add.return_value = None
        response = self.client.post(self.url, {'title': 'Test Handbook'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Handbook.objects.filter(title='Test Handbook').exists())

    def test_permission_denied(self):
        self.client.cookies['access_token'] = str(RefreshToken.for_user(self.user).access_token)
        response = self.client.post(self.url, {'title': 'Test'})
        self.assertEqual(response.data["error"], not_permitted)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('handbooks.views.feishu_authenticated')
    def test_missing_lark_auth(self, mock_authenticated):
        mock_authenticated.return_value = False
        response = self.client.post(self.url, {'title': 'Test'})
        self.assertEqual(response.data["error"], "请先授权飞书")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('handbooks.views.feishu_authenticated')
    def test_duplicate_handbook(self, mock_authenticated):
        mock_authenticated.return_value = True
        Handbook.objects.create(document_id="doc1", url="http://example.com", title="Existing")
        response = self.client.post(self.url, {'title': 'Test'})
        self.assertEqual(response.data["error"], "已经存在支队长手册")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class AddCoauthorViewTest(APITestCase):
    def setUp(self):
        self.user = create_super_administrator()
        self.access_token = str(RefreshToken.for_user(self.user).access_token)
        self.client.cookies['access_token'] = self.access_token
        self.handbook = Handbook.objects.create(document_id="doc1", url="http://example.com", title="Test")
        self.url = reverse('add-coauthor')

    @patch('handbooks.views.add_coauthor')
    def test_add_coauthor_success(self, mock_add):
        response = self.client.post(self.url, {'url': 'http://example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_add.assert_called_once_with("doc1", "super_admin_lark_id")

    @patch('handbooks.views.add_coauthor')
    def test_handbook_not_found(self, mock_add):
        response = self.client.post(self.url, {'url': 'http://invalid.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class DeleteHandbookViewTest(APITestCase):
    def setUp(self):
        self.admin = create_super_administrator()
        self.user = create_normal_user('user')
        self.access_token = str(RefreshToken.for_user(self.admin).access_token)
        self.client.cookies['access_token'] = self.access_token
        self.handbook = Handbook.objects.create(document_id="doc1", url="http://example.com", title="Test")
        self.url = reverse('delete-handbook')

    @patch('handbooks.views.delete_feishu_document')
    def test_admin_delete_success(self, mock_delete):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.url, {'url': 'http://example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Handbook.objects.exists())
        mock_delete.assert_called_once_with("doc1")

    def test_non_admin_delete(self):
        self.client.cookies['access_token'] = str(RefreshToken.for_user(self.user).access_token)
        response = self.client.post(self.url, {'url': 'http://example.com'})
        self.assertEqual(response.data["error"], not_permitted)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class ModifyTitleViewTest(APITestCase):
    def setUp(self):
        self.admin = create_super_administrator()
        self.access_token = str(RefreshToken.for_user(self.admin).access_token)
        self.client.cookies['access_token'] = self.access_token
        self.handbook = Handbook.objects.create(document_id="doc1", url="http://example.com", title="Old Title")
        self.url = reverse('modify-title')

    def test_modify_success(self):
        response = self.client.post(self.url, {
            'url': 'http://example.com',
            'title': 'New Title'
        })
        self.handbook.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.handbook.title, 'New Title')

    def test_modify_non_existent(self):
        response = self.client.post(self.url, {
            'url': 'http://invalid.com',
            'title': 'New Title'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)