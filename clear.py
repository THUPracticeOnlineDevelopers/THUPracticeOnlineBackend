import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'THUPracticeOnline_backend.settings')
django.setup()

from files.models import LetterPairModel, LetterFileModel

LetterPairModel.objects.all().delete()
LetterFileModel.objects.all().delete()