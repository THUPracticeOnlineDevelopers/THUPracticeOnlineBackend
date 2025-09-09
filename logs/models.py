from django.db import models
import datetime
from detachments.models import Detachment

# Create your models here.
class LogModel(models.Model):
    date = models.DateField(auto_now=False, auto_created=False, default=datetime.date.today)
    detachment = models.ForeignKey(Detachment, on_delete=models.CASCADE, related_name='logs_for_detachment')
    content = models.CharField(max_length=200)

    def __str__(self) -> str:
        return f"{self.detachment.name}{self.date}的实践日志"