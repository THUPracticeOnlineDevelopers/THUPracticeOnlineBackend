from django.urls import path
from .views import SendNoticeView, GetNoticeView, ConfirmView, QueryView, QueryConfirmView

urlpatterns = [
    path('send-notice/', SendNoticeView.as_view(), name='send-notice'),
    path('get-notice/', GetNoticeView.as_view(), name='get-notice'),
    path('confirm/', ConfirmView.as_view(), name='confirm'),
    path('query/', QueryView.as_view(), name='notice-query'),
    path('query-confirm/', QueryConfirmView.as_view(), name='query-confirm'),
]