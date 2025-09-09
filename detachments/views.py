from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework import status
from rest_framework.response import Response
from users.models import CustomUser
from .models import Detachment, DetachmentMembership
from .serializers import DetachmentSerializer
from utils.check import check_detachment_leader_input, check_detachment_member_input, check_detachment_leader, check_user_permission
from utils.get import transform_date
from utils.pagination import CustomPagination
from django.shortcuts import get_object_or_404

not_permitted = "用户权限不足"

# Create your views here.
class CreateDetachmentView(APIView) :
    def post(self, request) :
        data = request.data
        name = data.get("name")
        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")
        detachment_leader = data.get("detachment_leader")
        detachment_member = data.get("detachment_member")

        access_token = request.COOKIES.get('access_token')
        if not check_user_permission(access_token) :
            return Response({'error':not_permitted}, status=status.HTTP_400_BAD_REQUEST)


        if not isinstance(name, str) or len(name) >  100 :
            return Response({"error" : "支队名不合法"}, status=status.HTTP_400_BAD_REQUEST)
        
        start_date = transform_date(start_date_str)
        if start_date is None :
            return Response({'error':'开始日期格式不合法'}, status=status.HTTP_400_BAD_REQUEST)

        end_date = transform_date(end_date_str)
        if end_date is None :
            return Response({'error':'结束日期格式不合法'}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(check_detachment_leader_input(detachment_leader), Response) :
            return check_detachment_leader_input(detachment_leader)
        
        if isinstance(check_detachment_member_input(detachment_member), Response) :
            return check_detachment_member_input(detachment_member)
        
        detachment = Detachment.objects.create(
            name = name,
            start_date = start_date,
            end_date = end_date
        )

        for username in detachment_leader :
            user = CustomUser.objects.get(username=username)
            DetachmentMembership.objects.create(
                user = user,
                detachment = detachment,
                role = 'leader'
            )

        for username in detachment_member :
            user = CustomUser.objects.get(username=username)
            DetachmentMembership.objects.create(
                user = user,
                detachment = detachment,
                role = 'member'
            )

        detachment.save()
        return Response({'message':'创建支队成功'}, status=status.HTTP_200_OK)

class ModifyDetachmentView(APIView) :
    def valid_data(self, request):
        data = request.data
        key = data.get("id")
        name = data.get("name")
        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")
        detachment_member = data.get("detachment_member")

        detachment = get_object_or_404(Detachment, id=key)

        access_token = request.COOKIES.get('access_token')
        if not check_user_permission(access_token) and not check_detachment_leader(access_token, key) :
            return Response({"error":"用户无权修改支队信息"}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(name, str) and len(name) >  100 :
            return Response({"error" : "支队名不合法"}, status=status.HTTP_400_BAD_REQUEST)
        
        if isinstance(start_date_str, str) :
            start_date = transform_date(start_date_str)
            if start_date is None :
                return Response({'error':'开始日期格式不合法'}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(end_date_str, str) :
            end_date = transform_date(end_date_str)
            if end_date is None :
                return Response({'error':'结束日期格式不合法'}, status=status.HTTP_400_BAD_REQUEST)

        response = self.check_member(detachment_member)
        if isinstance(response, Response) :
            return response
        return detachment
    
    def check_member(self, detachment_member):
        if not isinstance(detachment_member, list) :
            return Response({'error':'支队员信息不合法'}, status=status.HTTP_400_BAD_REQUEST)

        if len(detachment_member) > 0:
            for i in detachment_member :
                if not isinstance(i, str) or len(i) > 100 :
                    return Response({'error':'输入格式非法'}, status=status.HTTP_400_BAD_REQUEST)
                if not CustomUser.objects.filter(username = i).exists() :
                    return Response({'error':f"用户 {i} 不存在"}, status=status.HTTP_400_BAD_REQUEST)
                
        return None
        
    def post(self, request) :
        data = request.data
        name = data.get("name")
        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")
        detachment_member = data.get("detachment_member")

        detachment = self.valid_data(request)
        if isinstance(detachment, Response):
            return detachment
        start_date = transform_date(start_date_str)
        end_date = transform_date(end_date_str)
        
        if name is not None :
            detachment.name = name
        
        if start_date_str is not None :
            detachment.start_date = start_date

        if end_date_str is not None :
            detachment.end_date = end_date

        if len(detachment_member) > 0 :
            DetachmentMembership.objects.filter(detachment = detachment, role='member').delete()
            for username in detachment_member :
                user = CustomUser.objects.get(username=username)
                DetachmentMembership.objects.create(
                    user = user,
                    detachment = detachment,
                    role = 'member'
                )
        
        detachment.save()

        return Response({'message':'成功修改支队信息'}, status=status.HTTP_200_OK)
    

    
class DeactivateDetachmentView(APIView) :
    def post(self, request) :
        data = request.data
        key = data.get("id")

        try :
            detachment = Detachment.objects.get(id = key)
        except Detachment.DoesNotExist :
            return Response({"error":"支队不存在"}, status=status.HTTP_400_BAD_REQUEST)

        access_token = request.COOKIES.get("access_token")
        if not check_user_permission(access_token) :
            return Response({'error':not_permitted}, status=status.HTTP_400_BAD_REQUEST)

        detachment.valid = False
        detachment.save()
        return Response({'message':'成功停用支队'}, status=status.HTTP_200_OK)
    
class DeleteDetachmentView(APIView):
    def post(self, request):
        data = request.data
        primary_key = data.get('id')

        access_token = request.COOKIES.get('access_token')
        if not check_user_permission(access_token) :
            return Response({'error':not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        
        detachment = Detachment.objects.filter(id=primary_key).first()
        if not detachment:
            return Response({'error': '支队不存在'}, status=status.HTTP_400_BAD_REQUEST)
        detachment.delete()
        return Response({'message': '成功删除支队'}, status=status.HTTP_200_OK)
    
class GetAllDetachmentView(ListAPIView):
    queryset = Detachment.objects.all()
    serializer_class = DetachmentSerializer
    pagination_class = CustomPagination

class GetValidDetachment(ListAPIView):
    queryset = Detachment.objects.filter(valid=True)
    serializer_class = DetachmentSerializer
    pagination_class = CustomPagination