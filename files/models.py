from django.db import models
from users.models import CustomUser

# Create your models here.
class LetterFileModel(models.Model):
    ' 公函文件模型 '
    file = models.FileField(upload_to='uploads/') # 文件
    upload_at = models.DateTimeField(auto_now_add=True) # 上传时间
    mime_type = models.CharField(max_length=100, default='') # 文件类型，详见MIME的定义
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE) # 发送人
    template = models.BooleanField(default=False) # 是否是模板
    filename = models.CharField(max_length=100) # 文件名
    whether_reply = models.BooleanField(default=True) # 本身是否是回复或是否有回复        

    def __str__(self) -> str:
        return self.file.name

class LetterPairModel(models.Model):
    ' 记录待审批公函与审批完成的公函的关系模型 '
    LETTER_STATUS = [
        ('review', '盖章中'),
        ('finish', '已盖章'),
    ]

    letter = models.ForeignKey(LetterFileModel, on_delete=models.CASCADE, related_name='letter', unique=True)
    reply = models.ForeignKey(LetterFileModel, on_delete=models.CASCADE, blank=True, null=True, default=None, related_name='reply')
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=LETTER_STATUS, default='review')

    def __str__(self) -> str:
        return self.letter.filename
    
    def get_status(self):
        """获取中文状态"""
        status_dict = dict(self.LETTER_STATUS)
        return status_dict.get(self.status, self.status)