from django.db import models
from users.models import CustomUser

# Create your models here.
class ApprovalManageModel(models.Model):
    '审核流程管理模型'
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE) # 审核人
    order = models.IntegerField() # 第几个审核

    def __str__(self) -> str:
        return f"第{self.order}位审核人"
    
class ApprovalModel(models.Model):
    "推送审核模型"
    APPROVAL_STATUS = [
        ('review', '审核中'),
        ('reject', '拒绝'),
        ('approve', '通过'),
    ]

    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sender') # 送审人
    sender_name = models.CharField(max_length=100) # 送审人姓名
    link = models.CharField(max_length=200, unique=True) # 秀米链接
    status = models.CharField(max_length=10, choices=APPROVAL_STATUS, default='review') # 审核状态
    message = models.CharField(max_length=1000, blank=True, null=True, default='') # 评语反馈
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviewer') # 当前审核人

    def __str__(self) -> str:
        return f"{self.sender.username}的推送审核"

    def get_status(self):
        """获取中文状态"""
        status_dict = dict(self.APPROVAL_STATUS)
        return status_dict.get(self.status, self.status)