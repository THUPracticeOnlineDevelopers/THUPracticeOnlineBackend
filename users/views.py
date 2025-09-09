from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import CustomUserSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.utils import timezone
from django.shortcuts import redirect
from urllib.parse import quote, unquote
from utils.get import get_user_from_request
from utils.check import check_email, check_password, check_username, check_phone_number, check_student_id, check_verification_code, check_administrator_from_request
from utils.send import send_verification_email
from utils.pagination import CustomPagination
from django.conf import settings
from django.urls import reverse
from urllib.parse import urlencode
from utils.feishu import get_user_access_token, get_user_info, remove_coauthor, feishu_authenticated
from handbooks.models import Handbook
import secrets

email_wrong = "邮箱格式不合法"
not_permitted = "用户权限不足"
user_does_not_exist = "用户不存在"

def generate_verification_code():
    return str(secrets.randbelow(900000) + 100000)

def get_verification_code(email):
    return cache.get(f'verification_code:{email}')

class RegisterView(APIView):
    def post(self, request):

        # 获取用户提交的数据
        data = request.data
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        student_id = data.get('student_id')
        phone_number = data.get('phone_number')
        user_code = data.get('verification_code')

        # 邮箱、用户名、密码、手机号、学号格式检查
        if not check_email(email):
            return Response({'error': email_wrong}, status=status.HTTP_400_BAD_REQUEST) 

        if not check_username(username):
            return Response({'error': '用户名格式不合法。'}, status=status.HTTP_400_BAD_REQUEST)

        if not check_password(password):
            return Response({'error': '密码格式不合法。'}, status=status.HTTP_400_BAD_REQUEST)

        if not check_phone_number(phone_number):
            return Response({'error': '手机号格式不合法。'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not check_student_id(student_id):
            return Response({'error': '学号格式不合法。'}, status=status.HTTP_400_BAD_REQUEST)

        if not check_verification_code(user_code):
            return Response({'error': '验证码格式不合法。'}, status=status.HTTP_400_BAD_REQUEST)

        # 用户名、学号、手机号唯一性检查
        if CustomUser.objects.filter(username=username).exists():
            return Response({'error': '用户名已存在。'}, status=status.HTTP_400_BAD_REQUEST)

        if student_id and CustomUser.objects.filter(student_id=student_id).exists():
            return Response({'error': '学号已被使用'}, status=status.HTTP_400_BAD_REQUEST)

        if phone_number and CustomUser.objects.filter(phone_number=phone_number).exists():
            return Response({'error': '手机号已被使用'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查验证码是否正确
        stored_code = get_verification_code(email)
        if stored_code and stored_code == user_code:
            # 验证成功
            user = CustomUser.objects.create_user(username=username, email=email, password=password, student_id=student_id, phone_number=phone_number, is_active=True)
            user.save()
        else:
            return Response({'error': '验证码无效或已过期。'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': '注册成功。'}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    def post(self, request):
        data = request.data
        username = data.get('username')
        email = data.get('email')
        student_id = data.get('student_id')
        phone_number = data.get('phone_number')
        password = data.get('password')

        # 邮箱、用户名、密码、手机号、学号格式检查
        if email != None and not check_email(email):
            return Response({'error': email_wrong}, status=status.HTTP_400_BAD_REQUEST) 

        if username != None and not check_username(username):
            return Response({'error': '用户名格式不合法。'}, status=status.HTTP_400_BAD_REQUEST)

        if not check_password(password):
            return Response({'error': '密码格式不合法。'}, status=status.HTTP_400_BAD_REQUEST)

        if not check_phone_number(phone_number):
            return Response({'error': '手机号格式不合法。'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not check_student_id(student_id):
            return Response({'error': '学号格式不合法。'}, status=status.HTTP_400_BAD_REQUEST)

        if not any([username, email, student_id, phone_number]):
            return Response({"error": "必须提供用户名、邮箱、学号或手机号之一"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = None
            if username:
                user = CustomUser.objects.get(username=username)
            elif email:
                user = CustomUser.objects.get(email=email)
            elif student_id:
                user = CustomUser.objects.get(student_id=student_id)
            elif phone_number:
                user = CustomUser.objects.get(phone_number=phone_number)

            if not user or not user.check_password(password):
                return Response({"error": "登录凭据无效"}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken.for_user(user)
            access_token = str(token.access_token)
            refresh_token = str(token)
            serializer = CustomUserSerializer(user)
            response = Response({"message":"登录成功", "user_info": serializer.data}, status=status.HTTP_200_OK)

            response.set_cookie(key='access_token', value=access_token, max_age=60 * 60 * 24, secure=True, httponly=True, samesite='Lax')
            response.set_cookie(key="refresh_token", value=refresh_token, max_age=60 * 60 * 24, secure=True, httponly=True, samesite='Lax')
            return response

        except ObjectDoesNotExist:
            return Response({"error": user_does_not_exist}, status=status.HTTP_400_BAD_REQUEST)

class SendEmailView(APIView):
    def post(self, request):
        data = request.data
        email = data.get('email')

        # 邮箱格式检查
        if not check_email(email):
            return Response({'error': email_wrong}, status=status.HTTP_400_BAD_REQUEST) 

        # 检查邮箱是否已被注册
        if CustomUser.objects.filter(email=email).exists():
            return Response({'error': '邮箱已被注册。'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查1分钟内是否已发送过
        last_sent_time = cache.get(f'last_sent_time:{email}')
        if last_sent_time and (timezone.now() - last_sent_time).total_seconds() < 60:
            return Response({'error': '请等待1分钟后再重新发送验证码'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        verification_code = generate_verification_code()
        # 更新缓存（记录验证码和最近一次的发送时间）
        cache.set(f'verification_code:{email}', verification_code, timeout=600)
        cache.set(f'last_sent_time:{email}', timezone.now(), timeout=60)

        # 发送邮件
        try:
            send_verification_email(email, verification_code)
        except Exception:
            cache.delete(f'verification_code:{email}')
            cache.delete(f'last_sent_time:{email}')
            return Response({'error': '邮件发送失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({'message': '验证码已发送到您的邮箱，请查收。'}, status=status.HTTP_201_CREATED)

class GetUserView(ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        # 执行权限检查
        if not check_administrator_from_request(request):
            return Response({"error": not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        
        # 继续原有处理流程
        return super().list(request, *args, **kwargs)

class GetAdminView(ListAPIView):
    queryset = CustomUser.objects.filter(user_permission=CustomUser.UserPermissions.administrator)
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        # 执行权限检查
        if not check_administrator_from_request(request):
            return Response({"error": not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        
        # 继续原有处理流程
        return super().list(request, *args, **kwargs)

class GetSuperAdminView(ListAPIView):
    queryset = CustomUser.objects.filter(user_permission=CustomUser.UserPermissions.super_administrator)
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        # 执行权限检查
        if not check_administrator_from_request(request):
            return Response({"error": not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        
        # 继续原有处理流程
        return super().list(request, *args, **kwargs)

class GetAllAdminView(APIView):
    def get(self, request):
        # 执行权限检查
        if not check_administrator_from_request(request):
            return Response({"error": not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        admin = CustomUser.objects.filter(user_permission__gte=CustomUser.UserPermissions.administrator)
        serializer = CustomUserSerializer(admin, many=True)
        return Response({"all-admin": serializer.data}, status=status.HTTP_200_OK)

class ModifyPermissionView(APIView):
    def post(self, request):
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user
        if user.user_permission != CustomUser.UserPermissions.super_administrator:
            return Response({"error": not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data
        username = data.get('username')
        try:
            target_user = CustomUser.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response({"error": user_does_not_exist}, status=status.HTTP_400_BAD_REQUEST)
        try:
            permission = CustomUser.get_permission_value(data.get('user_permission'))
        except ValueError:
            return Response({"error": "权限名称错误"}, status=status.HTTP_400_BAD_REQUEST)
        if target_user.user_permission >= CustomUser.UserPermissions.administrator and permission == CustomUser.UserPermissions.normal_user and Handbook.objects.exists() and target_user.lark_open_id is not None:
            try:
                handbook = Handbook.objects.first()
                remove_coauthor(handbook.document_id, target_user.lark_open_id)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        target_user.user_permission = permission
        target_user.save()
        return Response({"message": "成功修改权限"}, status=status.HTTP_200_OK)

class FeishuBindView(APIView):
    def get(self, request):
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user
        if feishu_authenticated(user):
            return Response({"error": "您已绑定飞书"}, status=status.HTTP_400_BAD_REQUEST)
        source_url = request.META.get('HTTP_REFERER', '').rstrip('/')
        callback_url = request.build_absolute_uri(reverse('feishu-callback'))
        if source_url:
            redirect_uri = f"{callback_url}?from={source_url}/handbook"
        else:
            redirect_uri = callback_url
        params = {
            'client_id': settings.LARK_CONFIG['APP_ID'],
            'redirect_uri': redirect_uri,
            'scope': 'contact:user.employee_id:readonly offline_access'
        }
        url = f'https://accounts.feishu.cn/open-apis/authen/v1/authorize?{urlencode(params)}'
        return Response({'auth_url': url}, status=status.HTTP_200_OK)

class FeishuCallbackView(APIView):
    def get(self, request):
        encoded_source_url = request.GET.get('from')
        redirect_url = unquote(encoded_source_url)
        callback_url = request.build_absolute_uri(reverse('feishu-callback'))
        redirect_uri = f"{callback_url}?from={redirect_url}"
        error = request.GET.get('error')
        if error:
            redirect_url = f'{redirect_url}?error={quote("飞书授权失败")}'
            return redirect(redirect_url)
        code = request.GET.get('code')
        if not code:
            redirect_url = f'{redirect_url}?error={quote("缺少授权码(code)")}'
            return redirect(redirect_url)
        user = get_user_from_request(request)
        if isinstance(user, Response):
            redirect_url = f'{redirect_url}?error={quote("用户未登录")}'
            return redirect(redirect_url)
        try:
            user_access_token, expires_in, refresh_token, refresh_token_expires_in = get_user_access_token(code, request, redirect_uri)
            cache.set(f'{user.pk}: user_access_token', user_access_token, timeout=expires_in)
            cache.set(f'{user.pk}: refresh_token', refresh_token, timeout=refresh_token_expires_in)
            open_id = get_user_info(user_access_token)
            try:
                existing_user = CustomUser.objects.get(lark_open_id=open_id)
                if existing_user != user:
                    redirect_url = f'{redirect_url}?error={quote("当前飞书账号已经被其他用户绑定")}'
                    return redirect(redirect_url)
            except ObjectDoesNotExist:
                pass
            user.lark_open_id = open_id
            user.save()
            redirect_url = f'{redirect_url}?message={quote("飞书授权成功")}'
            return redirect(redirect_url)
        except Exception as e:
            redirect_url = f'{redirect_url}?error={quote(str(e))}'
            return redirect(redirect_url)

class UserInfoView(APIView):
    def get(self, request):
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user
        serializer = CustomUserSerializer(user)
        return Response({"message": "用户已登录", "user-info": serializer.data}, status=status.HTTP_200_OK)

class GetUserByIdView(APIView):
    def post(self, request):
        userid = request.data.get('id')
        try:
            user = CustomUser.objects.get(id=userid)
            serializer = CustomUserSerializer(user)
            return Response({"user_info": serializer.data}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": user_does_not_exist}, status=status.HTTP_400_BAD_REQUEST)