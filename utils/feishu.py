import requests
from django.conf import settings
from urllib.parse import quote
from users.models import CustomUser
from django.core.cache import cache

class FeishuError(Exception):
    """飞书认证专用异常"""

def get_feishu_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {
        "app_id": settings.LARK_CONFIG['APP_ID'],
        "app_secret": settings.LARK_CONFIG['APP_SECRET'],
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get('tenant_access_token')
    raise FeishuError("无法获取tenant access token")

def get_user_access_token(code, request, redirect_url):
    url = 'https://open.feishu.cn/open-apis/authen/v2/oauth/token'
    data = {
        'grant_type': 'authorization_code',
        'client_id': settings.LARK_CONFIG['APP_ID'],
        'client_secret': settings.LARK_CONFIG['APP_SECRET'],
        'code': code,
        'redirect_uri': quote(redirect_url),
    }
    response = requests.post(url=url, data=data).json()
    if response.get('code') == 0:
        return response.get('access_token'), response.get('expires_in'), response.get('refresh_token'), response.get('refresh_token_expires_in')
    raise FeishuError("无法获取user_access_token")

def refresh_user_access_token(refresh_token):
    url = 'https://open.feishu.cn/open-apis/authen/v2/oauth/token'
    data = {
        'grant_type': 'refresh_token',
        'client_id': settings.LARK_CONFIG['APP_ID'],
        'client_secret': settings.LARK_CONFIG['APP_SECRET'],
        'refresh_token': refresh_token,
    }
    response = requests.post(url=url, data=data).json()
    if response.get('code') == 0:
        return response.get('access_token'), response.get('expires_in'), response.get('refresh_token'), response.get('refresh_token_expires_in')
    raise FeishuError("无法刷新user_access_token")

def feishu_authenticated(user : CustomUser):
    if user.lark_open_id is None:
        return False
    user_access_token = cache.get(f'{user.pk}: user_access_token')
    if user_access_token is None:
        refresh_token = cache.get(f'{user.pk}: refresh_token')
        if refresh_token is None:
            return False # user_access_token和refresh_token均过期，需要重新授权
        else:
            try:
                user_access_token, expires_in, refresh_token, refresh_token_expires_in = refresh_user_access_token(refresh_token)
                cache.set(f'{user.pk}: user_access_token', user_access_token, timeout=expires_in)
                cache.set(f'{user.pk}: refresh_token', refresh_token, timeout=refresh_token_expires_in)
                return True
            except FeishuError:
                return False # user_access_token刷新失败
    # user_access_token未过期，尝试使用user_access_token获取用户信息，检查用户是否处于授权状态
    else:
        try:
            openid = get_user_info(user_access_token)
            if openid == user.lark_open_id:
                return True
            else:
                return False
        except FeishuError:
            return False

def get_user_info(user_access_token):
    url = 'https://open.feishu.cn/open-apis/authen/v1/user_info'
    headers = {"Authorization": f"Bearer {user_access_token}"}
    response = requests.get(url=url, headers=headers).json()
    if response.get('code') == 0:
        return response.get('data').get('open_id')
    raise FeishuError("无法获取用户信息")

def get_domain(access_token):
    url = "https://open.feishu.cn/open-apis/tenant/v2/tenant/query"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url=url, headers=headers)

    if response.status_code == 200:
        return response.json().get('data').get('tenant').get('domain')
    raise FeishuError("无法获取租户域名")

def create_feishu_document():
    access_token = get_feishu_access_token()
    url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.post(url=url, headers=headers)
    
    if response.status_code == 200:
        doc = response.json().get('data').get('document')
        doc_id = doc.get('document_id')
        domain = get_domain(access_token)
        url = f"https://{domain}/docx/{doc_id}"
        return doc_id, url
    raise FeishuError("无法创建文档")

def add_coauthor(document_id, open_id):
    access_token = get_feishu_access_token()
    url = f'https://open.feishu.cn/open-apis/drive/v1/permissions/{document_id}/members?type=docx'
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data = {
        "member_type": "openid",
        "member_id": open_id,
        "perm": "edit"
    }

    response = requests.post(url=url, headers=headers, data=data)
    if response.status_code != 200:
        raise FeishuError("无法添加协作者")

def remove_coauthor(document_id, open_id):
    access_token = get_feishu_access_token()
    url = f'https://open.feishu.cn/open-apis/drive/v1/permissions/{document_id}/members/{open_id}?type=docx&member_type=openid'
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.delete(url=url, headers=headers)
    if response.status_code != 200:
        raise FeishuError("无法删除协作者")

# !!! 这个函数目前无法使用，需要飞书组织进行认证后才可以将文档的权限设置为互联网获得链接的人可查看
def set_doc_permission(document_id):
    access_token = get_feishu_access_token()
    url = f'https://open.feishu.cn/open-apis/drive/v2/permissions/{document_id}/public?type=docx'
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data = {
        "link_share_entity":"anyone_readable"
    }

    response = requests.patch(url=url, headers=headers, data=data)
    if response.status_code != 200:
        raise FeishuError("无法修改文档权限")

def delete_feishu_document(document_id):
    access_token = get_feishu_access_token()
    url = f'https://open.feishu.cn/open-apis/drive/v1/files/{document_id}?type=docx'
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.delete(url=url, headers=headers)
    if response.status_code != 200:
        raise FeishuError("无法删除文档")