from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from .models import LetterFileModel, LetterPairModel
from .serializers import TemplateSerializer, LetterSerializer, LetterPairSerializer
import os
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from utils.get import get_user_from_request
from utils.check import check_administrator_from_request
from utils.pagination import CustomPagination
import base64
from datetime import datetime

MIME_TYPES = {
    # '.txt' : 'text/plain; charset=utf-8',
    '.pdf' : 'application/pdf',
    # '.xsl' : 'application/vnd.ms-excel',
    # '.xlsx' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    # '.xlsm' : 'application/vnd.ms-excel.sheet.macroEnabled.12',
    # '.xltx' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
    '.doc' : 'application/msword',
    '.docx' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}

def base_file_upload(request, template = False, reply = True) :
    " 文件上传基础函数 "
    file = request.FILES.get('file')
    if file is None :
        return Response({'error':'文件不存在'}, status=status.HTTP_400_BAD_REQUEST)
    file_extension = os.path.splitext(file.name)[1].lower()
    
    mime_type = MIME_TYPES.get(file_extension, None)
    if mime_type is None:
        return Response({'error':'文件格式不支持'}, status=status.HTTP_400_BAD_REQUEST)

    user = get_user_from_request(request) 
    if isinstance(user, Response) :
        return user
    
    basename = os.path.basename(file.name)
    name = basename.split(".")[0]
    date = datetime.now().strftime("%Y-%m-%d")
    filename = name + "_from_" + user.username + "_upload_at_" + date

    letter = LetterFileModel.objects.create(
        file=file,
        mime_type=mime_type,
        sender=user,
        template = template,
        whether_reply = reply,
        filename = filename
    )

    return letter


class UploadTemplateView(APIView):
    "管理员上传公函模板"
    def post(self, request):
        if not check_administrator_from_request(request):
            return Response({"error":"权限不足"}, status=status.HTTP_400_BAD_REQUEST) 

        letter = base_file_upload(request, template=True)

        if isinstance(letter, Response) :
            return letter

        return Response({"message":"上传成功"}, status=status.HTTP_200_OK)


class UploadLetterView(APIView):
    " 支队长上传填写好的公函 "
    def post(self, request):
        letter = base_file_upload(request, reply=False)

        if isinstance(letter, Response):
            return letter

        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user

        LetterPairModel.objects.create(
            letter = letter,
            owner = user
        )
        return Response({'message':'上传成功'}, status=status.HTTP_200_OK)


class GetTemplateView(ListAPIView):
    "查询所有的模板"
    pagination_class = CustomPagination
    serializer_class = TemplateSerializer
    queryset = LetterFileModel.objects.filter(template=True).order_by("id")


class DeleteTemplateView(APIView):
    "删除模板"
    def post(self, request):
        letter_id = request.data.get('id')

        if letter_id is None :
            return Response({"error":"请传入公函模板主键"}, status=status.HTTP_400_BAD_REQUEST)

        if not check_administrator_from_request(request):
            return Response({"error":"权限不足"}, status=status.HTTP_400_BAD_REQUEST)

        letter = get_object_or_404(LetterFileModel, id=letter_id) 
        letter.delete()
        return Response({"message":"删除成功"}, status=status.HTTP_200_OK)


class DownloadView(APIView):
    "下载视图"
    def post(self, request):
        letter_id = request.data.get('id')

        if letter_id is None :
            return Response({"error":"请传入公函模板主键"}, status=status.HTTP_400_BAD_REQUEST)

        letter = get_object_or_404(LetterFileModel, id=letter_id)
        file = letter.file
        filename = letter.filename
        # 对文件名进行 UTF-8 编码，然后进行 Base64 编码
        encoded_filename = base64.b64encode(filename.encode('utf-8')).decode('utf-8')
        response = FileResponse(file.open(), content_type=letter.mime_type, filename=filename, as_attachment=True)
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
        return response

class QueryLetterView(ListAPIView):
    pagination_class = CustomPagination
    serializer_class = LetterSerializer
    queryset = LetterFileModel.objects.filter(template=False, whether_reply=False).order_by("id")

class UploadCompletedLetterView(APIView):
    def post(self, request, *args, **kwargs):
        letter_id = kwargs.get('id')
        letter = get_object_or_404(LetterFileModel, id=letter_id)

        if not check_administrator_from_request(request):
            return Response({"error":"权限不足"}, status=status.HTTP_400_BAD_REQUEST)
        
        reply = base_file_upload(request)
        if isinstance(reply, Response):
            return reply

        letter_pair = get_object_or_404(LetterPairModel, letter=letter)
        letter_pair.reply = reply
        letter_pair.status = 'finish'
        letter_pair.save()

        letter.whether_reply = True
        letter.save()

        return Response({'message':'上传成功'}, status=status.HTTP_200_OK)
    
class QueryStatusView(ListAPIView):
    pagination_class = CustomPagination
    serializer_class = LetterPairSerializer

    def get(self, request, *args, **kwargs):
        user = get_user_from_request(request)
        if isinstance(user, Response):
            return user
        self.queryset = LetterPairModel.objects.filter(owner = user).order_by("id")
        return super().get(request, *args, **kwargs)