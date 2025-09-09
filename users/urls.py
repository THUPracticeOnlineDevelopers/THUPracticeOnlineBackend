from django.urls import path
from .views import RegisterView, LoginView, SendEmailView, GetUserView, GetAdminView, GetSuperAdminView, GetAllAdminView, ModifyPermissionView, FeishuBindView, FeishuCallbackView, UserInfoView, GetUserByIdView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('send-email/', SendEmailView.as_view(), name='send-email'),
    path('get-user/', GetUserView.as_view(), name='get-user'),
    path('get-administrator/', GetAdminView.as_view(), name='get-administrator'),
    path('get-super/', GetSuperAdminView.as_view(), name='get-super'),
    path('get-all-administrator/', GetAllAdminView.as_view(), name='get-all-administrator'),
    path('modify-permission/', ModifyPermissionView.as_view(), name='modify-permission'),
    path('feishu-bind/', FeishuBindView.as_view(), name='feishu-bind'),
    path('feishu-callback/', FeishuCallbackView.as_view(), name='feishu-callback'),
    path('user-info/', UserInfoView.as_view(), name='user-info'),
    path('get-user-by-id/', GetUserByIdView.as_view(), name='get-user-by-id'),
]