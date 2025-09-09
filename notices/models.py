from django.db import models
from detachments.models import Detachment
from users.models import CustomUser
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

# Create your models here.

class Notice(models.Model):
    title = models.CharField(max_length=100)
    content = models.CharField(max_length=5000)
    sender = models.CharField(max_length=100, default="团委实践组")
    detachment = models.ManyToManyField(Detachment, related_name='notices')
    date = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        ordering = ['-date']

class UserNotice(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_notices')
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='recipients')
    confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'notice')  # 防止重复记录