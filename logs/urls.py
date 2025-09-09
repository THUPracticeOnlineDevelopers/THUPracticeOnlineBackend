from django.urls import path
from .views import InitLogView, WriteLogView, QueryLogView
urlpatterns = [
    path('init/', InitLogView.as_view(), name='init-log'),
    path('write/', WriteLogView.as_view(), name='write-log'),
    path('query/', QueryLogView.as_view(), name='query-log'),
]