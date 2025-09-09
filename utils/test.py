from users.models import CustomUser
from detachments.models import Detachment, DetachmentMembership
from notices.models import Notice, UserNotice

def create_super_administrator():
    " 创建一个超级管理员 "
    return CustomUser.objects.create(
        username = 'test_super_administrator',
        email = 'test@mails.tsinghua.edu.cn',
        password = 'Testpass123',
        student_id = '2021010001',
        phone_number = '13800138000',
        user_permission = CustomUser.UserPermissions.super_administrator,
        lark_open_id = "super_admin_lark_id",
    ) 

def create_administrator():
    " 创建普通管理员 "
    return CustomUser.objects.create(
        username = 'test_administrator',
        email = 'test1@mails.tsinghua.edu.cn',
        password = '12345678',
        student_id = '2021010002',
        phone_number = '13800138001',
        user_permission = CustomUser.UserPermissions.administrator,
        lark_open_id = "admin_lark_id",
    ) 

def create_normal_user(name : str|list):
    " 创建普通用户 "
    if isinstance(name, str):
        return CustomUser.objects.create(username = name, email = f"{name}@test.com", lark_open_id = f"{name} lark_id")
    elif isinstance(name, list):
        users = []
        for username in name:
            users.append(CustomUser.objects.create(username = username, email = f"{username}@test.com", lark_open_id = f"{username} lark_id"))
        return users

def create_detachment(leaders, members) :
    " 创建支队 "
    detachment = Detachment.objects.create(
        name = "test_detachment",
        start_date = "2025-04-14",
        end_date = "2025-04-15",
    )
    for username in leaders:
        user = CustomUser.objects.get(username=username)
        DetachmentMembership.objects.create(
            user = user,
            detachment = detachment,
            role = 'leader'
        )
    for username in members:
        user = CustomUser.objects.get(username=username)
        DetachmentMembership.objects.create(
            user = user,
            detachment = detachment,
            role = 'member'
        )
    detachment.save()
    return detachment

def create_notice(detachments, title='test notice', content='notice', sender='团委实践组'):
    notice = Notice.objects.create(
        title = title,
        content = content,
        sender = sender
    )
    notice.detachment.set(detachments)
    for detachment in detachments:
        for leader in detachment.get_leaders():
            UserNotice.objects.get_or_create(user=leader, notice=notice)
    return notice