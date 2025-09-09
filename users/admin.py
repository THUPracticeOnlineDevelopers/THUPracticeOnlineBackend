from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # 控制列表页显示字段
    list_display = ('username', 'email', 'student_id', 'phone_number', 'user_permission')
    
    # 控制编辑页表单字段分组
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('email', 'student_id', 'phone_number', 'user_permission')}),
    )
    
    # 添加用户时的必填字段
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)