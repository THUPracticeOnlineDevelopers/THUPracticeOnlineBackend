# tests.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
import pandas as pd
import base64
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ConnectionListModel, FileModel
from .serializers import ConnectionListSerializer
from users.models import CustomUser


class ConnectionListModelTest(TestCase):
    def test_create_connection(self):
        connection = ConnectionListModel.objects.create(
            detachment_name='测试支队',
            leader='支队长',
            theme='测试主题',
            duration='2023-07',
            location='测试地点',
            enterprise='测试企业',
            government='测试政府',
            venue='测试场馆'
        )
        self.assertEqual(str(connection), '测试支队')
        self.assertEqual(connection.enterprise, '测试企业')

class FileModelTest(TestCase):
    def test_create_file(self):
        file = SimpleUploadedFile("test.txt", b"file_content")
        file_model = FileModel.objects.create(
            file=file,
            mime_type='text/plain',
            filename='test.txt'
        )
        self.assertEqual(str(file_model), 'test.txt')

class ConnectionListSerializerTest(TestCase):
    def test_serializer_validation(self):
        data = {
            'detachment_name': '支队名称',
            'leader': '支队长',
            'theme': '主题',
            'duration': '时间',
            'location': '地点',
            'enterprise': '企业',
            'government': '政府',
            'venue': '场馆'
        }
        serializer = ConnectionListSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_missing_field(self):
        invalid_data = {
            'leader': '支队长',
            # 缺少 detachment_name
        }
        serializer = ConnectionListSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('detachment_name', serializer.errors)

class ViewTests(APITestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            user_permission=CustomUser.UserPermissions.administrator
        )
        self.normal_user = CustomUser.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass'
        )
        self.client = APIClient()
        self.user_token = str(RefreshToken.for_user(self.normal_user).access_token)
        self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)
        self.client.cookies['access_token'] = self.admin_token

    def generate_test_excel(self):
        # 构造多级列索引
        multi_columns = pd.MultiIndex.from_tuples([
            ('支队名称', ''),
            ('支队长', ''),
            ('调研主题', ''),
            ('实践时间', ''),
            ('实践地点', ''),
            ('实践内容', '企业'),
            ('实践内容', '政府机构'),
            ('实践内容', '场馆')
        ])

        # 创建示例数据
        data = {
            ('支队名称', ''): ['探珍寻奇——西安市博物馆调研支队', '“清”年爱劳动_计算机系_赴云南永胜启迪扶志教育实践支队', '“家国计”品牌计划实践支队'],
            ('支队长', ''): ['王誉凯', '李子沐', '张书宁'],
            ('调研主题', ''): ['西安市博物馆发展现状与对策', '永胜县教育扶志活动初探', '基层政务信息化建设发展现状和问题'],
            ('实践时间', ''): ['2021年7月11日-7月23日', '2021年7月30日-8月3日', '2021年7月4日-9月14日'],
            ('实践地点', ''): ['陕西西安', '云南省永胜县', '线上（辽宁沈阳）、线下（青海海西、青海西宁、北京昌平、北京海淀）'],
            ('实践内容', '企业'): [
                '清华大学艺术博物馆、西安博物院、秦始皇陵博物院、西安交通大学西迁博物馆、大唐西市博物馆、西安曲江艺术博物馆、西安斑点城市文化创意有限公司',
                '无',
                '华为、商汤、昆仑数智、木瓜移动'
            ],
            ('实践内容', '政府机构'): [
                '西安市文物局、西安市教育局',
                '永胜县教育体育局、永胜县民族中学、永胜县第一中学',
                '中石油昆仑数智、青海冷湖石油基地、青海原子城纪念馆、青海湟中一中'
            ],
            ('实践内容', '场馆'): [
                '西安博物院、大唐西市博物馆、秦始皇陵博物院、西安交通大学西迁博物馆、西安曲江艺术博物馆',
                '无',
                '青海大学'
            ]
        }

        # 创建 DataFrame
        df = pd.DataFrame(data)
        excel_file = BytesIO()
        df.to_excel(excel_file, columns=multi_columns)
        excel_file.seek(0)
        return excel_file

    def test_upload_connection_list_no_permission(self):
        self.client.cookies['access_token'] = self.user_token
        url = reverse('upload-connection-list')
        response = self.client.post(url, {'file': ''}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], '用户权限不足')


    def test_query_connection_list(self):
        ConnectionListModel.objects.create(
            detachment_name='测试支队',
            leader='支队长',
            theme='主题',
            duration='时间',
            location='地点',
            enterprise='企业',
            government='政府',
            venue='场馆'
        )
        url = reverse('query-connection-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_clear_connection_list(self):
        ConnectionListModel.objects.create(
            detachment_name='测试支队',
            leader='支队长',
            theme='主题',
            duration='时间',
            location='地点',
            enterprise='企业',
            government='政府',
            venue='场馆'
        )
        url = reverse('clear-connection-list')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ConnectionListModel.objects.count(), 0)


    def test_download_no_file(self):
        url = reverse('download-connection-list')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], '没有文件可供下载')