from rest_framework.views import exception_handler
from rest_framework import serializers
from users.authentication import AuthenticationFailedError

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response:
        field = next(iter(response.data))
        if isinstance(response.data[field], list):
            error = response.data[field][0]
        else:
            error = response.data[field]
        response.data = {"error": error}

    if isinstance(exc, AuthenticationFailedError):
        response.data = {'error':exc.detail}
        response.set_cookie(key='xiajiba_cookie', value='1145141919810', secure=True, httponly=True, samesite='None')
        response.delete_cookie('access_token', samesite='None')
        response.delete_cookie('refresh_token', samesite='None')
    
    if isinstance(exc, serializers.ValidationError):
        # 提取第一个错误信息
        errors = response.data['error']
        if 'non_field_errors' in errors:
            error_msg = errors['non_field_errors'][0]
            response.data = {'error': error_msg}

    return response