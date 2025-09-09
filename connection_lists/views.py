from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.http import FileResponse
from utils.check import check_administrator_from_request, check_excel
import pandas as pd
from utils.check import check_connection_list_excel
from utils.get import get_detachment_name, get_leader, get_theme, get_duration, get_location, get_enterprise, get_government, get_venue
from .serializers import ConnectionListSerializer
from .models import ConnectionListModel, FileModel
from utils.pagination import CustomPagination
import os
import base64

MIME_TYPES = {
    '.xsl' : 'application/vnd.ms-excel',
    '.xlsx' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xlsm' : 'application/vnd.ms-excel.sheet.macroEnabled.12',
    '.xltx' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
}

class UploadConnectionListView(APIView):
    def post(self, request):
        if not check_administrator_from_request(request):
            return Response({"error":"用户权限不足"}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES.get('file')
        if file is None :
            return Response({'error':'文件不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        file_extension = os.path.splitext(file.name)[1].lower()
        if not check_excel(file_extension):
            return Response({'error':'传入的文件不是Excel表格'}, status=status.HTTP_400_BAD_REQUEST) 

        df = pd.read_excel(file, header=[0,1])
        res = check_connection_list_excel(df)
        if isinstance(res, Response):
            return res

        # 删除原来的表格并创建
        FileModel.objects.all().delete()
        ConnectionListModel.objects.all().delete()
        FileModel.objects.create(
            file=file,
            mime_type = MIME_TYPES[file_extension],
            filename = os.path.basename(file.name),
        )

        headers = df.columns.to_list()
        for _, row in df.iterrows():
            data = {
                'detachment_name' : get_detachment_name(row, headers),
                'leader' : get_leader(row, headers),
                'theme' : get_theme(row, headers),
                'duration' : get_duration(row, headers),
                'location' : get_location(row, headers),
                'enterprise' : get_enterprise(row, headers),
                'government' : get_government(row, headers),
                'venue' : get_venue(row, headers),
            } 
            serializer = ConnectionListSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response({'message':'上传成功'}, status=status.HTTP_200_OK)
    
class QueryConnectionListView(ListAPIView):
    queryset = ConnectionListModel.objects.all().order_by("id")
    serializer_class = ConnectionListSerializer
    pagination_class = CustomPagination

class ClearConnectionListView(APIView):
    "清空外联清单"
    def post(self, request):
        if not check_administrator_from_request(request):
            return Response({"error":"权限不足"}, status=status.HTTP_400_BAD_REQUEST)
        
        ConnectionListModel.objects.all().delete()
        FileModel.objects.all().delete()

        return Response({'message':'清空成功'}, status=status.HTTP_200_OK)

class DownloadConnectionListView(APIView):
    "下载外联清单"
    def post(self, request):
        if FileModel.objects.count() == 0:
            return Response({'error':'没有文件可供下载'}, status=status.HTTP_400_BAD_REQUEST)
        
        for excel in FileModel.objects.all():
            file = excel.file
            filename = excel.filename
            # 对文件名进行 UTF-8 编码，然后进行 Base64 编码
            encoded_filename = base64.b64encode(filename.encode('utf-8')).decode('utf-8')
            response = FileResponse(file.open(), content_type=excel.mime_type, filename=filename, as_attachment=True)
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
            break

        return response