from django.urls import path
from .views import CreateDetachmentView, ModifyDetachmentView, DeactivateDetachmentView, DeleteDetachmentView, GetAllDetachmentView, GetValidDetachment

urlpatterns = [
    path('create/', CreateDetachmentView.as_view(), name='create'),
    path('modify/', ModifyDetachmentView.as_view(), name='detachment-modify'),
    path('deactivate/', DeactivateDetachmentView.as_view(), name='deactivate'),
    path('delete/', DeleteDetachmentView.as_view(), name='delete'),
    path('get-all/', GetAllDetachmentView.as_view(), name='get-all'),
    path('get-valid/', GetValidDetachment.as_view(), name='get-valid'),
]