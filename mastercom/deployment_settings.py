# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mastercom_django',
        'HOST': 'localhost',
        'USER': 'mastercom_django',
        'PASSWORD': 'lsd88Django'
    }
}

ALLOWED_HOSTS = ['my.mastercom.su']

STATIC_ROOT = '/home/m/mastercom/my/public_html/static/'
