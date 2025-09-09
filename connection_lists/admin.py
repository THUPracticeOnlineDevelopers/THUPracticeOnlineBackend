from django.contrib import admin
from .models import ConnectionListModel, FileModel

# Register your models here.
admin.site.register(ConnectionListModel)
admin.site.register(FileModel)