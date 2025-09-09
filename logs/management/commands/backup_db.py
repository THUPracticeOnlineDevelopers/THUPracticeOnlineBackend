from django.core.management.base import BaseCommand
import os
import subprocess
from datetime import datetime, timedelta
import glob

class Command(BaseCommand):
    help = 'Backup MySQL database and clean old backups'

    def handle(self, *args, **options):
        # 获取 Django 的数据库配置
        from THUPracticeOnline_backend import settings
        db_config = settings.DATABASES['default']

        # 数据库配置
        db_name = db_config['NAME']
        db_user = db_config['USER']
        db_password = db_config['PASSWORD']
        db_host = db_config['HOST']
        db_port = db_config['PORT']

        # 备份目录
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # 当前时间戳
        timestamp = datetime.now().strftime('%Y%m%d')
        backup_file = os.path.join(backup_dir, f'{db_name}_{timestamp}.sql')

        # 执行 mysqldump 命令进行备份
        dump_cmd = [
            'mysqldump',
            f'--host={db_host}',
            f'--port={db_port}',
            f'--user={db_user}',
            f'--password={db_password}',
            db_name,
            f'--result-file={backup_file}'
        ]
        subprocess.run(dump_cmd, check=True)

        # 保留过去七天的备份，删除旧备份
        days_to_keep = 7
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_timestamp = cutoff_date.strftime('%Y%m%d')

        # 查找并删除超过七天的备份文件
        for old_backup in glob.glob(os.path.join(backup_dir, f'{db_name}_*.sql')):
            filename = os.path.basename(old_backup)
            file_timestamp = filename.split('_')[1].split('.')[0]
            if file_timestamp < cutoff_timestamp:
                os.remove(old_backup)
                self.stdout.write(self.style.SUCCESS(f'Deleted old backup: {old_backup}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully backed up database to {backup_file}'))