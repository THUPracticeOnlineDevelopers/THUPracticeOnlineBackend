from django.core.mail import send_mail
from THUPracticeOnline_backend import settings

def send_verification_email(email, verification_code):
    subject = 'THUPracticeOnline网站注册验证码'
    message = f'您的验证码是：{verification_code}，验证码将在10分钟后过期'
    from_email = settings.DEFAULT_FROM_EMAIL  # 从配置中获取发件人
    recipient_list = [email]
    
    send_mail(
        subject,
        message,
        from_email,
        recipient_list,
        fail_silently=False,
    )


def send_notice_email(email : str, content : str, title : str) :
    subject = f"THUPracticeOnline - 发布新公告 : {title}"
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, content, from_email, [email], fail_silently=False)


def send_email(subject : str, content : str, receipient_list : list) :
    "使用默认邮箱发送邮件"
    subject = f"THUPracticeonline - {subject}"
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, content, from_email, receipient_list, fail_silently=False)