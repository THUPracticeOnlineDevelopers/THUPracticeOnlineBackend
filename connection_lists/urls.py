from django.urls import path
from .views import UploadConnectionListView, QueryConnectionListView, ClearConnectionListView, DownloadConnectionListView
urlpatterns = [
    path('upload/', UploadConnectionListView.as_view(), name='upload-connection-list'),
    path('query/', QueryConnectionListView.as_view(), name='query-connection-list'),
    path('clear/', ClearConnectionListView.as_view(), name='clear-connection-list'),
    path('download/', DownloadConnectionListView.as_view(), name='download-connection-list'),
]