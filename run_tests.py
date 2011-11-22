
# from http://www.travisswicegood.com/2010/01/17/django-virtualenv-pip-and-fabric/

import os

from django.conf import settings
from django.core.management import call_command

import registration_email_only

def main():
    # Dynamically configure the Django settings with the minimum necessary to
    # get Django running tests
    settings.configure(
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.admin',
            'django.contrib.sessions',
            'registration',
            'registration_email_only',
        ),
        SECRET_KEY = 'shhh secret',
        # Django replaces this, but it still wants it. *shrugs*
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': '/tmp/django_test.db',
            }
        },
        MEDIA_ROOT = '/tmp/django_test_media/',
        ROOT_URLCONF = '',
        DEBUG = True,
		TEMPLATE_DEBUG = True,
		TEMPLATE_DIRS = [
		    os.path.join(os.path.dirname(registration_email_only.__file__), 'tests/templates')
		],
    ) 
    
    #call_command('syncdb')
    
    # Fire off the tests
    call_command('test', 'registration_email_only')
    

if __name__ == '__main__':
    main()

