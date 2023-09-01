from pathlib import Path

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': Path(__file__).resolve().parent.parent / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mastercom_djtest',
        'HOST': 'vh340.timeweb.ru',
        'USER': 'mastercom_djtest',
        'PASSWORD': 'lsd88Test'
    }
}

ALLOWED_HOSTS = ['127.0.0.1']
STATICFILES_DIRS = [Path(__file__).resolve().parent.parent / 'assets']
pass