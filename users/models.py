from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True, default=None)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True, default=None)
    lark_open_id = models.CharField(max_length=64, unique=True, null=True, blank=True, default=None)
    class UserPermissions(models.IntegerChoices) :
        normal_user = 1, '普通用户'
        administrator = 2, '普通管理员'
        super_administrator = 3, '超级管理员'
    
    user_permission = models.IntegerField(choices=UserPermissions, default=UserPermissions.normal_user)

    def __str__(self):
        return self.username
    
    class Meta:
        ordering = ['-id']
    
    @classmethod
    def get_permission_value(cls, label):
        for choice in cls.UserPermissions:
            if choice.label == label:
                return choice.value
        raise ValueError(f"权限名称无效")
