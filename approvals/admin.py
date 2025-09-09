from django.contrib import admin
from .models import ApprovalModel, ApprovalManageModel

# Register your models here.
admin.site.register(ApprovalModel)
admin.site.register(ApprovalManageModel)