from django.db import models

# Create your models here.
class Handbook(models.Model):
    document_id = models.CharField(max_length=255, unique=True)
    url = models.URLField()
    title = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)