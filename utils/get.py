from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.response import Response
from users.models import CustomUser
from rest_framework import status
from datetime import datetime

def get_user_from_request(request):
    access_token = request.COOKIES.get('access_token')
    if not access_token:
        return Response({"error": "用户未登录"}, status=status.HTTP_400_BAD_REQUEST)
    token = AccessToken(access_token)
    user_id = token['user_id']
    return CustomUser.objects.get(id = user_id)

def transform_date(date : str) :
    try :
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        return date_obj
    except ValueError :
        return None

def get_detachment_name(df, headers):
    return df[headers[0][0]][headers[0][1]]

def get_leader(df, headers):
    return df[headers[1][0]][headers[1][1]]

def get_theme(df, headers):
    return df[headers[2][0]][headers[2][1]]

def get_duration(df, headers):
    return df[headers[3][0]][headers[3][1]]

def get_location(df, headers):
    return df[headers[4][0]][headers[4][1]]

def get_enterprise(df, headers):
    return df[headers[5][0]][headers[5][1]]

def get_government(df, headers):
    return df[headers[6][0]][headers[6][1]]

def get_venue(df, headers):
    return df[headers[7][0]][headers[7][1]]

def get_illegal_response(target : str) -> Response :
    return Response({'error':f"{target}格式不合法"}, status=status.HTTP_400_BAD_REQUEST)