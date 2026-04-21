import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django.setup()

from django.core.management import call_command
call_command('migrate')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()