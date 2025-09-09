from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from .models import Questionnaire, Question, Answer
from .serializers import QuestionnaireSerializer, AnswerSerializer
from users.models import CustomUser
from utils.get import get_user_from_request
from utils.check import check_super_administrator_from_request
from utils.pagination import CustomPagination

not_permitted = "用户权限不足"
vote_miss = "问卷不存在"

class CreateQuestionnaireView(APIView):
    def post(self, request):
        if not check_super_administrator_from_request(request):
            return Response({"error": not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        serializer = QuestionnaireSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "成功创建问卷"}, status=status.HTTP_200_OK)

class UpdateQuestionnaireView(APIView):
    def post(self, request):
        if not check_super_administrator_from_request(request):
            return Response({"error": not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            questionnaire = Questionnaire.objects.get(id=request.data['id'])
        except Questionnaire.DoesNotExist:
            return Response({"error": vote_miss}, status=status.HTTP_400_BAD_REQUEST)

        if questionnaire.is_published:
            return Response({"error": "无法更新已发布的问卷"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = QuestionnaireSerializer(
            instance=questionnaire,
            data=request.data,
            partial=False  # 需要前端传输完整数据
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({"message": "成功更新问卷"}, status=status.HTTP_200_OK)

class GetQuestionnaireListView(ListAPIView):
    serializer_class = QuestionnaireSerializer
    pagination_class = CustomPagination
    queryset = Questionnaire.objects.all().order_by("id")

    def list(self, request, *args, **kwargs):
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user

        return super().list(request, *args, **kwargs)

class PublishQuestionnaireView(APIView):
    def post(self, request):
        try:
            if not check_super_administrator_from_request(request):
                return Response({"error": not_permitted}, status=status.HTTP_400_BAD_REQUEST)
            questionnaire = Questionnaire.objects.get(id=request.data['id'])
            # 如果要发布的问卷已经截止，则重新发布
            if questionnaire.is_closed == True:
                questionnaire.is_closed = False
            questionnaire.is_published = True
            questionnaire.save()
            return Response({"message": "成功发布问卷"}, status=status.HTTP_200_OK)
        except Questionnaire.DoesNotExist:
            return Response({"error": vote_miss}, status=status.HTTP_400_BAD_REQUEST)

class CloseQuestionnaireView(APIView):
    def post(self, request):
        try:
            if not check_super_administrator_from_request(request):
                return Response({"error": not_permitted}, status=status.HTTP_400_BAD_REQUEST)
            questionnaire = Questionnaire.objects.get(id=request.data['id'])
            if questionnaire.is_published == False:
                return Response({"error": "无法截止未发布的问卷"}, status=status.HTTP_400_BAD_REQUEST)
            questionnaire.is_closed = True
            questionnaire.save()
            return Response({"message": "成功截止收集问卷"}, status=status.HTTP_200_OK)
        except Questionnaire.DoesNotExist:
            return Response({"error": vote_miss}, status=status.HTTP_400_BAD_REQUEST)

class SubmitAnswerView(APIView):
    def post(self, request):
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user
        data = request.data
        try:
            questionnaire = Questionnaire.objects.get(id=data['id'])
            if user.get_user_permission_display() not in questionnaire.permissions:
                return Response({"error": not_permitted}, status=status.HTTP_400_BAD_REQUEST)
            if not questionnaire.is_published or questionnaire.is_closed:
                return Response({"error": "问卷未开放提交"}, status=status.HTTP_400_BAD_REQUEST)
            
            for answer in data['answers']:
                question = Question.objects.get(
                    questionnaire=questionnaire,
                    question_idx=answer['question_idx']
                )
                serializer = AnswerSerializer(data=answer, context={'question': question})
                serializer.is_valid(raise_exception=True)
                Answer.objects.update_or_create(
                    user=user,
                    questionnaire=questionnaire,
                    question=question,
                    defaults={'answer': answer['answer']}
                )
            return Response({"message": "成功提交问卷"}, status=status.HTTP_200_OK)
        except Questionnaire.DoesNotExist:
            return Response({"error": vote_miss}, status=status.HTTP_400_BAD_REQUEST)
        except Question.DoesNotExist:
            return Response({"error": "问题不存在"}, status=status.HTTP_400_BAD_REQUEST)

class QuestionnaireResultView(APIView):
    def post(self, request):
        if not check_super_administrator_from_request(request):
            return Response({"error": "无权查看结果"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            questionnaire = Questionnaire.objects.get(id=request.data['id'])
            
            answers = Answer.objects.filter(questionnaire=questionnaire)
            results = {}
            for answer in answers:
                user_id = answer.user.id
                if user_id not in results:
                    results[user_id] = {"user_id": user_id, "answers": []}
                results[user_id]["answers"].append({
                    "question_idx": answer.question.question_idx,
                    "answer": answer.answer
                })
            return Response({"results": list(results.values())}, status=status.HTTP_200_OK)
        except Questionnaire.DoesNotExist:
            return Response({"error": vote_miss}, status=status.HTTP_400_BAD_REQUEST)

class DeleteQuestionnaireView(APIView):
    def post(self, request):
        if not check_super_administrator_from_request(request):
            return Response({"error": not_permitted}, status=status.HTTP_400_BAD_REQUEST)
        try:
            questionnaire_id = request.data.get('id')
            questionnaire = Questionnaire.objects.get(id=questionnaire_id)
            
            questionnaire.delete()
            return Response({"message": "成功删除问卷"}, status=status.HTTP_200_OK)
            
        except Questionnaire.DoesNotExist:
            return Response({"error": vote_miss}, status=status.HTTP_400_BAD_REQUEST)