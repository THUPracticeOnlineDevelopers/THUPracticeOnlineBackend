from django.db import models
from users.models import CustomUser

# Create your models here.

class Detachment(models.Model):
    name = models.CharField('实践名称', max_length=100)
    start_date = models.DateField('开始日期')
    end_date = models.DateField('结束日期')
    valid = models.BooleanField(default=True)
    participant = models.ManyToManyField(
        CustomUser,
        through='DetachmentMembership',
        related_name='_detachments'
    )
    research_content = models.CharField(max_length=100, null=True, blank=True, default='')
    member_num = models.IntegerField(null=True, blank=True, default=0)
    province = models.CharField(max_length=100, null=True, blank=True, default='')
    city = models.CharField(max_length=100, null=True, blank=True, default='')
    init = models.BooleanField(default=False)
    class Meta:
        ordering = ['-id']

    def get_leaders(self):
        """ 获取所有队长 """
        return self.participant.filter(
            detachmentmembership__role='leader'
        )
    
    def get_members(self):
        """ 获取所有队员 """
        return self.participant.filter(
            detachmentmembership__role='member'
        )

class DetachmentMembership(models.Model):
    ROLE_CHOICES = [
        ('member', '队员'),
        ('leader', '队长'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    detachment = models.ForeignKey(Detachment, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    class Meta:
        unique_together = [('user', 'detachment')]  # 禁止重复加入同一支队