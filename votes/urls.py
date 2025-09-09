from django.urls import path
from .views import CreateQuestionnaireView, UpdateQuestionnaireView, GetQuestionnaireListView, PublishQuestionnaireView, CloseQuestionnaireView, SubmitAnswerView, QuestionnaireResultView, DeleteQuestionnaireView

urlpatterns = [
    path('create/', CreateQuestionnaireView.as_view(), name='create-questionaire'),
    path('update/', UpdateQuestionnaireView.as_view(), name='update-questionaire'),
    path('get/', GetQuestionnaireListView.as_view(), name='get-questionaire'),
    path('publish/', PublishQuestionnaireView.as_view(), name='publish-questionaire'),
    path('close/', CloseQuestionnaireView.as_view(), name='close-questionaire'),
    path('submit/', SubmitAnswerView.as_view(), name='submit-questionaire'),
    path('result/', QuestionnaireResultView.as_view(), name='questionaire-result'),
    path('delete/', DeleteQuestionnaireView.as_view(), name='delete-questionaire'),
]