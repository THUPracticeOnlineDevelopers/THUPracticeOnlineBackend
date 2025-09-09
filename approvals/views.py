from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from utils.check import check_reviewer, check_super_administrator_from_request, check_user_id_list, check_username_list
from utils.get import get_user_from_request
from .serializers import ApprovalSerializer, ReviewApprovalSerializer, QueryStatusSerializer, ReviewerSerializer
from utils.pagination import CustomPagination
from .models import ApprovalModel, ApprovalManageModel
from users.models import CustomUser
from utils.send import send_email

class SendApprovalView(APIView):
    "送审视图"
    def post(self, request):
        data = request.data.copy()
        user = get_user_from_request(request)

        if isinstance(user, Response):
            return user
        
        # 创建审核
        data['sender'] = user.id
        try :
            reviewer = ApprovalManageModel.objects.get(order=1).reviewer
            data['reviewer'] = reviewer.id
        except ApprovalManageModel.DoesNotExist:
            return Response({'error':'审核人未定义，请联系管理员'}, status=status.HTTP_400_BAD_REQUEST) 

        send_email(
            subject="您有新的待审核的推送",
            content="您有新的待审核的推送，请登录https://THUPracticeOnline-frontend-THUPracticeOnline.app.spring25a.secoder.net查看",
            receipient_list=[reviewer.email]
        )        

        serializer = ApprovalSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message':'送审成功'}, status=status.HTTP_200_OK)

class QueryApprovalView(ListAPIView):
    '管理员查询待审核的推送视图'
    serializer_class = ReviewApprovalSerializer
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user
        self.queryset = ApprovalModel.objects.filter(reviewer=user, status='review').order_by("id")
        return super().get(request, *args, **kwargs)

class PassDownApprovalView(APIView):
    "审核通过，向下传递视图"
    def post(self, request):
        approval_id = request.data.get('id')

        approval = ApprovalModel.objects.get(id=approval_id)
        now_reviewer = approval.reviewer
        order = ApprovalManageModel.objects.get(reviewer=now_reviewer).order
        
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user

        # 检查当前用户是不是对应的审核人
        if not check_reviewer(now_reviewer, user):
            return Response({'error':'您无权操作本篇推送'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查当前推送状态是否正确
        if approval.status == 'approve' :
            return Response({'error':'当前推送审核已通过，无法操作'}, status=status.HTTP_400_BAD_REQUEST)

        try :
            next_reviewer = ApprovalManageModel.objects.get(order=order+1).reviewer
        except ApprovalManageModel.DoesNotExist:
            return Response({'error':'您已是最后一个审核人，无法传递给下一个审核人'}, status=status.HTTP_400_BAD_REQUEST)

        send_email(
            subject="您有新的待审核的推送",
            content="您有新的待审核的推送，请登录https://THUPracticeOnline-frontend-THUPracticeOnline.app.spring25a.secoder.net查看",
            receipient_list=[next_reviewer.email]
        )        

        approval.reviewer = next_reviewer
        approval.message = ''
        approval.save()
        return Response({'message':'操作成功'}, status=status.HTTP_200_OK)

class RejectApprovalView(APIView):
    "审核不通过，打回修改"
    def post(self, request):
        data = request.data
        approval_id = data.get('id')
        message = data.get('message')

        approval = ApprovalModel.objects.get(id=approval_id)
        now_reviewer = approval.reviewer

        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user

        # 检查当前用户是不是对应的审核人
        if not check_reviewer(now_reviewer, user):
            return Response({'error':'您无权操作本篇推送'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查当前推送状态是否正确
        if approval.status == 'approve' :
            return Response({'error':'当前推送审核已通过，无法操作'}, status=status.HTTP_400_BAD_REQUEST)

        send_email(
            subject="您的推送已被拒绝",
            content=f"您的推送 : {approval.link} 已被拒绝，请登录https://THUPracticeOnline-frontend-THUPracticeOnline.app.spring25a.secoder.net查看具体情况",
            receipient_list=[approval.sender.email]
        )

        approval.status = 'reject'
        approval.message = message

        approval.save()

        return Response({'message':'操作成功'}, status=status.HTTP_200_OK)

class ApproveApprovalView(APIView):
    "审核最终通过，允许发表"
    def post(self, request):
        approval_id = request.data.get('id')
        user = get_user_from_request(request)

        if isinstance(user, Response):
            return user

        try :
            approval = ApprovalModel.objects.get(id=approval_id)
        except ApprovalModel.DoesNotExist:
            return Response({"error":f"id={approval_id}的推送审核不存在"}, status=status.HTTP_400_BAD_REQUEST)

        final_reviewer = ApprovalManageModel.objects.all().order_by("-order")[0].reviewer
        # 检查当前用户是不是最终审核员
        if not check_reviewer(final_reviewer, user) :
            return Response({'error':'无权操作'}, status=status.HTTP_400_BAD_REQUEST)

        send_email(
            subject="您的推送审核已通过",
            content=f"您的推送 - {approval.link} - 审核已通过！",
            receipient_list=[approval.sender.email]
        )

        approval.status = 'approve'
        approval.message = ''
        approval.save()

        return Response({'message':'操作成功'}, status=status.HTTP_200_OK)

class QueryStatusView(ListAPIView):
    pagination_class = CustomPagination
    serializer_class = QueryStatusSerializer
    
    def get(self, request, *args, **kwargs):
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user
        self.queryset = ApprovalModel.objects.filter(sender=user).order_by("id")
        return super().get(request, *args, **kwargs)

class ModifyApprovalView(APIView):
    def post(self, request):
        data = request.data
        approval_id = data.get('id')
        link = data.get('link')

        user = get_user_from_request(request)
        if isinstance(user, Response) :
            return user

        # 输入检查
        try :
            approval = ApprovalModel.objects.get(id=approval_id)
        except ApprovalModel.DoesNotExist:
            return Response({'error':'推送审核不存在'}, status=status.HTTP_400_BAD_REQUEST)

        if user != approval.sender :
            return Response({'error':'权限不足'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(link, str) or len(link) > 100 :
            return Response({'error':'传入链接不合法'}, status=status.HTTP_400_BAD_REQUEST)

        send_email(
            subject="被驳回的推送审核已更新，请重新审核",
            content="被驳回的推送审核已更新，请登录https://THUPracticeOnline-frontend-THUPracticeOnline.app.spring25a.secoder.net 重新审核",
            receipient_list=[approval.reviewer.email]
        )        

        approval.link = link
        approval.status = 'review'
        approval.save()

        return Response({'message':'修改成功'}, status=status.HTTP_200_OK)
    
class ManageApprovalView(APIView):
    def post(self, request):
        data = request.data
        user_ids = data.get('user-id')
        usernames = data.get('username')

        if not check_super_administrator_from_request(request):
            return Response({'error':'用户权限不足'}, status=status.HTTP_400_BAD_REQUEST) 

        if user_ids is None and usernames is None:
            return Response({'error':'用户主键、用户名至少提供一个'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user_ids is None :
            return self.create_from_id(user_ids)
        
        if not usernames is None :
            return self.create_from_name(usernames)

    def create_from_id(self, user_ids):
        response = check_user_id_list(user_ids)
        if isinstance(response, Response) :
            return response
        
        ApprovalManageModel.objects.all().delete()

        for order, user_id in enumerate(user_ids) :
            user = CustomUser.objects.get(id = user_id)
            ApprovalManageModel.objects.create(reviewer=user, order=order+1) 
        
        first = CustomUser.objects.get(id = user_ids[0])

        approvals = ApprovalModel.objects.all()
        for approval in approvals :
            if approval.status == 'approve' :
                continue
            approval.reviewer = first
            approval.save()

        return Response({'message':'创建成功'}, status=status.HTTP_200_OK)
    
    def create_from_name(self, usernames):
        response = check_username_list(usernames)
        if isinstance(response, Response) :
            return response
        
        ApprovalManageModel.objects.all().delete()

        for order, name in enumerate(usernames) :
            user = CustomUser.objects.get(username = name)
            ApprovalManageModel.objects.create(reviewer=user, order=order+1)
        
        first = CustomUser.objects.get(username = usernames[0])

        approvals = ApprovalModel.objects.all()
        for approval in approvals :
            if approval.status == 'approve' :
                continue
            approval.reviewer = first
            approval.save()

        return Response({'message':'创建成功'}, status=status.HTTP_200_OK)

class QueryReviewerView(ListAPIView):
    pagination_class = CustomPagination
    queryset = ApprovalManageModel.objects.all().order_by('order')
    serializer_class = ReviewerSerializer