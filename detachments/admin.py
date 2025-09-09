from django.contrib import admin
from .models import Detachment, DetachmentMembership

# Register your models here.
admin.site.register(Detachment)
admin.site.register(DetachmentMembership)