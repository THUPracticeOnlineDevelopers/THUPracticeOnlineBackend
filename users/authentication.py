from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework import exceptions, status
from rest_framework.response import Response

class AuthenticationFailedError(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '无效的访问令牌，请重新登录'
    default_code = 'authentication_failed'

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # 优先从 Cookie 获取 Token
        access_token = request.COOKIES.get('access_token')
        if access_token:
            # 验证 Token 有效性
            try :
                validated_token = self.get_validated_token(access_token)
                user = self.get_user(validated_token)
                return (user, validated_token)
            except InvalidToken as e:
                raise AuthenticationFailedError from e
            except exceptions.AuthenticationFailed as e:
                raise AuthenticationFailedError from e
        
        # 如果 Cookie 中没有，回退到 Header 中读取
        return super().authenticate(request)