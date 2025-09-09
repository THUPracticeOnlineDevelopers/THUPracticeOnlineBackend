from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from detachments.models import Detachment
from django.shortcuts import get_object_or_404
from utils.get import get_illegal_response, get_user_from_request, transform_date
from utils.check import check_in_detachment, check_administrator_from_request
from .models import LogModel
from utils.pagination import CustomPagination
from .serializers import DetachmentWithLogsSerializer
import datetime

def modify_or_create(detachment : Detachment, content : str, date = None):
    if date is None :
        date = datetime.date.today() 
    try :
        log = LogModel.objects.get(detachment=detachment, date=date)
        log.content = content
        log.save()
        return log
    except LogModel.DoesNotExist:
        log = LogModel.objects.create(
                detachment=detachment,
                content=content,
                date = date
            )
        return log
# Create your views here.
class InitLogView(APIView):
    def post(self, request):
        data = request.data
        detachment_id = data.get('id')
        research = data.get('research')
        number = data.get('number')
        province = data.get('province')
        city = data.get('city')

        user = get_user_from_request(request)
        if isinstance(user, Response) :
            return user

        detachment = get_object_or_404(Detachment, id=detachment_id)

        if not check_in_detachment(user, detachment) :
            return Response({'error':'您不在本支队中，无权操作'}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(research, str) or len(research) > 100 :
            return get_illegal_response("主要调研内容")
        if not isinstance(number, int) or number > 50 :
            return get_illegal_response("支队人数")
        if not isinstance(province, str) or len(province) > 20 :
            return get_illegal_response("实践省份")
        if not isinstance(city, str) or len(city) > 100 :
            return get_illegal_response("实践城市")
        
        detachment.research_content = research
        detachment.member_num = number
        detachment.province = province
        detachment.city = city
        detachment.init = True

        detachment.save()

        return Response({"message":"初始化成功"}, status=status.HTTP_200_OK)


class WriteLogView(APIView):
    def post(self, request):
        data = request.data
        detachment_id = data.get('id')
        date = data.get('date')
        content = data.get('content')

        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user

        detachment = get_object_or_404(Detachment, id=detachment_id)

        if not check_in_detachment(user, detachment) :
            return Response({'error':'您不在本支队中，无权操作'}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(date, str) :
            date = transform_date(date)
        if not isinstance(content, str) or len(content) > 200 :
            return get_illegal_response("日报内容")
        
        if not detachment.init :
            return Response({'error':'请先初始化'}, status=status.HTTP_400_BAD_REQUEST)

        modify_or_create(detachment, content, date) 
        return Response({'message':'填写成功'}, status=status.HTTP_200_OK)


class QueryLogView(ListAPIView) :
    pagination_class = CustomPagination
    serializer_class = DetachmentWithLogsSerializer

    def get(self, request, *args, **kwargs):
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user
        if check_administrator_from_request(request):
            self.queryset = Detachment.objects.prefetch_related('logs_for_detachment').filter(valid=True).order_by('-id')
        else :
            self.queryset = user._detachments.all()
        return super().get(request, *args, **kwargs)