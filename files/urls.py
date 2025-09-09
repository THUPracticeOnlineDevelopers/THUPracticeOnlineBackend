from django.urls import path
from .views import UploadCompletedLetterView, UploadTemplateView, UploadLetterView, DownloadView, GetTemplateView, DeleteTemplateView, QueryLetterView, QueryStatusView

urlpatterns = [
    path('upload-template/', UploadTemplateView.as_view(), name='upload-template'),
    path('download/', DownloadView.as_view(), name='download'),
    path('get-template/', GetTemplateView.as_view(), name='get-template'),
    path('delete-template/', DeleteTemplateView.as_view(), name='delete-template'),
    path('upload-letter/', UploadLetterView.as_view(), name='upload-letter'),
    path('upload-completed-letter/<int:id>/', UploadCompletedLetterView.as_view(), name='upload-completed-letter'),
    path('query-letter/', QueryLetterView.as_view(), name='query-letter'),
    path('query-status/', QueryStatusView.as_view(), name='query-letter-status'),
]