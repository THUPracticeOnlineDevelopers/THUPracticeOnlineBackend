from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from users.models import CustomUser
from .serializers import NoticeSerializer, UserNoticeSerializer
from .models import Notice, UserNotice
from utils.get import get_user_from_request
from django.utils import timezone
from utils.send import send_notice_email
from utils.check import check_administrator_from_request
from utils.pagination import CustomPagination

not_permitted = "用户权限不足"

class SendNoticeView(APIView) :
    def post(self, request):
        # 检查权限
        if not check_administrator_from_request(request):
            return Response({"error":not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = NoticeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # 自动抛出 ValidationError
        notice = serializer.save()
        
        detachment_leaders = [un.user for un in notice.recipients.all()]
        content = notice.content + f'\n\n发自：{notice.sender}'
        title = notice.title

        for leader in detachment_leaders:
            email = leader.email
            send_notice_email(email, content, title)

        return Response({'message':'发送成功'}, status=status.HTTP_200_OK)

class GetNoticeView(ListAPIView):
    serializer_class = UserNoticeSerializer
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user
        self.queryset = UserNotice.objects.filter(user=user).order_by("id")

        return super().list(request, *args, **kwargs)
    
class ConfirmView(APIView):
    def post(self, request):
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user
        data = request.data
        primary_key = data.get('id')
        try:
            user_notice = UserNotice.objects.get(user=user, notice_id=primary_key)
        except UserNotice.DoesNotExist:
            return Response({"error":"未找到对应通知"}, status=status.HTTP_400_BAD_REQUEST)
        if (user_notice.confirmed):
            return Response({"error":"您已确认过该通知"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user_notice.confirmed = True
            user_notice.confirmed_at = timezone.now()
            user_notice.save()
            return Response({"message": "确认成功"}, status=status.HTTP_200_OK)

class QueryView(ListAPIView):
    queryset = Notice.objects.all().order_by("id")
    serializer_class = NoticeSerializer
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        # 执行权限检查
        if not check_administrator_from_request(request):
            return Response({"error": not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        
        # 继续原有处理流程
        return super().list(request, *args, **kwargs)

class QueryConfirmView(APIView):
    def post(self, request):
        # 检查权限
        if not check_administrator_from_request(request):
            return Response({"error":not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data
        primary_key = data.get('id')
        try:
            notice = Notice.objects.get(id=primary_key)
        except Notice.DoesNotExist:
            return Response({"error":"未找到对应通知"}, status=status.HTTP_400_BAD_REQUEST)
        all_user = CustomUser.objects.filter(user_notices__notice=notice).values_list('username', flat=True)
        confirmed_user = CustomUser.objects.filter(user_notices__notice=notice, user_notices__confirmed=True).values_list('username', flat=True)
        return Response({"title": notice.title, "all_user": all_user, "confirmed_user": confirmed_user}, status=status.HTTP_200_OK)