from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from utils.check import check_administrator_from_request
from utils.get import get_user_from_request
from utils.feishu import create_feishu_document, add_coauthor, delete_feishu_document
from .models import Handbook
from .serializers import HandbookSerializer
from utils.feishu import FeishuError, feishu_authenticated

not_permitted = "用户权限不足"
handbook_miss = "文档不存在"
# Create your views here.

class GetLinkView(APIView):
    def get(self, request):
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user
        handbook = Handbook.objects.all()
        serializer = HandbookSerializer(handbook, many=True)
        return Response({"handbook": serializer.data}, status=status.HTTP_200_OK)

class CreateHandbookView(APIView):
    def post(self, request):
        # 检查权限
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user
        if user.user_permission == 1:
            return Response({"error":not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        if not feishu_authenticated(user):
            return Response({"error": "请先授权飞书"}, status=status.HTTP_400_BAD_REQUEST)
        if Handbook.objects.exists():
            return Response({"error":"已经存在支队长手册"}, status=status.HTTP_400_BAD_REQUEST)
        title = request.data.get('title')
        if title is not None and len(title) > 100:
            return Response({"error":"标题不得多于100个字符"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            document_id, url = create_feishu_document()
            Handbook.objects.create(document_id=document_id, url=url, title=title)
            add_coauthor(document_id, user.lark_open_id)
            return Response({"url": url}, status=status.HTTP_200_OK)
        except FeishuError as e:
            return Response({"error":str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AddCoauthorView(APIView):
    def post(self, request):
        # 检查权限
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user
        if user.user_permission == 1:
            return Response({"error":not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        if not user.lark_open_id:
            return Response({"error": "请先授权飞书"}, status=status.HTTP_400_BAD_REQUEST)
        url = request.data.get('url')
        try:
            handbook = Handbook.objects.get(url=url)
            add_coauthor(handbook.document_id, user.lark_open_id)
            return Response({"message": "您已成为文档协作者"}, status=status.HTTP_200_OK)
        except Handbook.DoesNotExist:
            return Response({"error":handbook_miss}, status=status.HTTP_400_BAD_REQUEST)
        except FeishuError as e:
             return Response({"error":str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DeleteHandbookView(APIView):
    def post(self, request):
        if not check_administrator_from_request(request):
            return Response({"error":not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        url = request.data.get('url')
        try:
            handbook = Handbook.objects.get(url=url)
            delete_feishu_document(handbook.document_id)
            handbook.delete()
            return Response({"message": "成功删除文档"}, status=status.HTTP_200_OK)
        except Handbook.DoesNotExist:
            return Response({"error":handbook_miss}, status=status.HTTP_400_BAD_REQUEST)
        except FeishuError as e:
             return Response({"error":str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ModifyTitleView(APIView):
    def post(self, request):
        if not check_administrator_from_request(request):
            return Response({"error":not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        url = request.data.get('url')
        title = request.data.get('title')
        try:
            handbook = Handbook.objects.get(url=url)
            handbook.title = title
            handbook.save()
            return Response({"message": "成功修改标题"}, status=status.HTTP_200_OK)
        except Handbook.DoesNotExist:
            return Response({"error":handbook_miss}, status=status.HTTP_400_BAD_REQUEST)