import re
from users.models import CustomUser
from detachments.models import Detachment, DetachmentMembership
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.response import Response
from rest_framework import status
import pandas as pd

def check_input_length(input_str : str, max_length : int, min_length = 0) -> bool :
    "检查字符串的长度，防止攻击"
    if len(input_str) < min_length:
        return False
    if len(input_str) > max_length:
        return False
    return True

def check_email(email : str) -> bool :
    "检查邮箱格式是否合法"
    return check_input_length and (email.endswith("@mails.tsinghua.edu.cn") or email.endswith("@mail.tsinghua.edu.cn") or email.endswith("@tsinghua.edu.cn"))

def check_username(username : str) -> bool:
    "检查用户名是否合法"
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{5,19}$'
    return bool(re.match(pattern, username))

def check_password(password : str) -> bool:
    "检查密码是否合法"
    if len(password) <= 64:
        return True
    return False

def check_phone_number(phone_number : str, allow_none = True) -> bool:
    "检查手机号是否合法"
    if (phone_number is None or len(phone_number) == 0)and allow_none :
        return True
    if (phone_number is None or len(phone_number) == 0)and allow_none :
        return False
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone_number))

def check_student_id(student_id : str, allow_none = True) -> bool:
    "检查学号是否合法"
    if (student_id is None or len(student_id) == 0) and allow_none :
        return True
    if (student_id is None or len(student_id) == 0) and not allow_none :
        return False
    pattern = r'^\d{10}$'
    return bool(re.match(pattern, student_id))

def check_verification_code(code : str) -> bool:
    "检查验证码格式是否合法"
    pattern = r'^\d{6}$'
    return bool(re.match(pattern, code))

def check_detachment_leader_input(detachment : list[str]) :
    " 检查输入的支队长列表是否合法 "
    if not isinstance(detachment, list) or len(detachment) == 0:
        return Response({'error':'支队长信息格式非法'},status=status.HTTP_400_BAD_REQUEST)
    for name in detachment :
        if not isinstance(name, str) or len(name) > 100 :
            return Response({'error':'输入格式非法'}, status=status.HTTP_400_BAD_REQUEST)
        if not CustomUser.objects.filter(username = name).exists() :
            return Response({'error':f"用户 {name} 不存在"}, status=status.HTTP_400_BAD_REQUEST)
    return 1

def check_detachment_member_input(detachment : list[str]) :
    " 检查输入的支队员列表是否合法 "
    if not isinstance(detachment, list):
        return Response({'error':'支队员信息格式非法'},status=status.HTTP_400_BAD_REQUEST)
    for name in detachment :
        if not isinstance(name, str) or len(name) > 100 :
            return Response({'error':'输入格式非法'}, status=status.HTTP_400_BAD_REQUEST)
        if not CustomUser.objects.filter(username = name).exists() :
            return Response({'error':f"用户 {name} 不存在"}, status=status.HTTP_400_BAD_REQUEST)
    return 1

def check_user_permission(access_token : str) -> bool :
    " 检查用户是否权限至少是管理员 "
    try :
        token = AccessToken(access_token)
        user_id = token['user_id']
        user = CustomUser.objects.get(id = user_id)
        if user.user_permission >= CustomUser.UserPermissions.administrator:
            return True
        return False
    except Exception :
        return False
    
def check_detachment_leader(access_token : str, key : int) -> bool :
    " 检查传入的用户是不是对应支队的支队长 "
    try :
        token = AccessToken(access_token)
        user_id = token['user_id']
        user = CustomUser.objects.get(id = user_id)
        detachment = Detachment.objects.get(id = key)
        try :
            membership = DetachmentMembership.objects.get(user=user, detachment=detachment)
            return membership.role == 'leader'
        except DetachmentMembership.DoesNotExist:
            return False
    except Exception :
        return False
    
def check_administrator_from_request(request) -> bool:
    " 根据request检查用户权限是不是至少是普通管理员 "
    access_token = request.COOKIES.get("access_token")
    return check_user_permission(access_token)

def check_user_super_permission(access_token : str) -> bool:
    " 检查用户权限是不是超级管理员 "
    try :
        token = AccessToken(access_token)
        user_id = token['user_id']
        user = CustomUser.objects.get(id = user_id)
        return user.user_permission == CustomUser.UserPermissions.super_administrator
    except Exception :
        return False
    
def check_super_administrator_from_request(request) -> bool | Response :
    " 根据request检查用户权限是不是至少是超级管理员 "
    access_token = request.COOKIES.get("access_token")
    return check_user_super_permission(access_token)

def check_connection_list_excel(df : pd.DataFrame) -> bool | Response :
    "检查传入的表格是否格式正确"
    headers = df.columns.to_list()
    if "支队名称" in headers[0][0] and "支队长" in headers[1][0] and "调研主题" in headers[2][0] and "实践时间" in headers[3][0] and "实践地点" in headers[4][0] and "企业" in headers[5][1] and "政府" in headers[6][1] and "场馆" in headers[7][1]:
        return True
    return Response({"error":"传入的表格格式不正确。要求表格前两行为一二级列名，第一行为支队名称,支队长,调研主题,实践时间,实践地点,实践内容，实践内容下有三列，其二级列名分别是企业、政府机构、场馆"}, status=status.HTTP_400_BAD_REQUEST)

def check_excel(file : str) -> bool :
    if file == '.xlsx' or file == '.xsl' or file == '.xlsm' or file == '.xltx':
        return True
    return False

def check_whether_detachment_leader(user : CustomUser) -> bool :
    "检查传入的用户是不是支队长"
    memberships = DetachmentMembership.objects.filter(user=user)
    for membership in memberships:
        if membership.role == 'leader':
            return True
    return False

def check_reviewer(reviewer, user) -> bool :
    '检查用户是不是指定的审核人'
    return reviewer == user

def check_user_id_list(user_ids) -> bool | Response :
    "检查输入的用户主键列表中的用户是否全部存在"
    for i in user_ids :
        try :
            CustomUser.objects.get(id=i)
        except CustomUser.DoesNotExist:
            return Response({'error' : f"主键为{i}的用户不存在"}, status=status.HTTP_400_BAD_REQUEST)
    return True

def check_username_list(usernames) -> bool | Response :
    "检查输入的用户名列表中的用户是否存在"
    for name in usernames:
        try :
            CustomUser.objects.get(username=name)
        except CustomUser.DoesNotExist:
            return Response({'error' : f"用户{name}不存在"}, status=status.HTTP_400_BAD_REQUEST)
    return True

def check_in_detachment(user : CustomUser, detachment : Detachment) -> bool :
    "返回用户在不在支队中"
    return DetachmentMembership.objects.filter(user=user, detachment=detachment).exists()