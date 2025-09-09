from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from detachments.models import Detachment
import datetime

class Command(BaseCommand):
    help = 'Sends a daily email at 8 PM.'

    def handle(self, *args, **options):
        today = datetime.date.today()
        subject = f'THUPracticeOnline - 提醒您填写实践日报'
        message_body = '请您记得填写今日的实践日报。'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [] # 修改为您的目标邮箱
        
        detachments = Detachment.objects.filter(valid=True)
        for detachment in detachments :
            if detachment.start_date <= today and today <= detachment.end_date :
                leaders = detachment.get_leaders()
                for leader in leaders :
                    recipient_list.append(leader.email)

        try:
            send_mail(
                subject,
                message_body,
                from_email,
                recipient_list,
                fail_silently=False, # 如果为 True，发送失败时不抛出异常
            )
            self.stdout.write(self.style.SUCCESS(f'成功发送每日邮件至: {", ".join(recipient_list)}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'发送邮件时发生错误: {e}'))