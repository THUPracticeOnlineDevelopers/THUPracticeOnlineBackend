from django.urls import path
from .views import GetLinkView, CreateHandbookView, AddCoauthorView, DeleteHandbookView, ModifyTitleView

urlpatterns = [
    path('get-link/', GetLinkView.as_view(), name='get-link'),
    path('create/', CreateHandbookView.as_view(), name='create-handbook'),
    path('add-coauthor/', AddCoauthorView.as_view(), name='add-coauthor'),
    path('delete-handbook/', DeleteHandbookView.as_view(), name='delete-handbook'),
    path('modify-title/', ModifyTitleView.as_view(), name='modify-title'),
]