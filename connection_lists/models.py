from django.db import models

# Create your models here.
class ConnectionListModel(models.Model):
    "外联清单"
    detachment_name = models.CharField(max_length=100, unique=True) # 支队名
    leader = models.CharField(max_length=100) # 支队长 
    theme = models.CharField(max_length=100) # 实践主题
    duration = models.CharField(max_length=100) # 实践时间
    location = models.CharField(max_length=100) # 实践地点
    enterprise = models.CharField(max_length=1000) # 参访企业
    government = models.CharField(max_length=1000) # 政府机构   
    venue = models.CharField(max_length=1000) # 场馆

    def __str__(self) -> str:
        return self.detachment_name

class FileModel(models.Model):
    "文件模型"
    file = models.FileField(upload_to='uploads/')
    upload_at = models.DateTimeField(auto_now_add=True)
    mime_type = models.CharField(max_length=100, default='')
    filename = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.filename