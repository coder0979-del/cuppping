import os
import sys
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# 🔒 المفتاح السري
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-u0+0hbe4-mrj3c0i9@#jw#4f4)$9#f=oe0&*-c&f2hr*ji-*y7')

# 🛠️ وضع التطوير
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# 🌐 النطاقات المسموحة
ALLOWED_HOSTS = ['*']
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# 📧 إعدادات البريد الإلكتروني
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'coder0979@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'gtfk eypu kcye hvuo')
DEFAULT_FROM_EMAIL = 'مركز الحجامة <coder0979@gmail.com>'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cuupping',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'alrayed.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cuupping.context_processors.cuupping_permissions',
            ],
        },
    },
]

WSGI_APPLICATION = 'alrayed.wsgi.application'


# 🗄️ إعداد قاعدة بيانات PostgreSQL
# 🗄️ إعداد قاعدة البيانات - معالجة آمنة لـ DATABASE_URL
db_url = os.environ.get('DATABASE_URL', '').strip()

# إذا كان المتغير غير موجود أو يحتوي على قيمة مشوهة مثل '://'
if not db_url or db_url == '://' or not db_url.startswith(('postgres://', 'postgresql://', 'sqlite://')):
    db_url = 'postgres://postgres:123456@localhost:5432/alrayed_db'

DATABASES = {
    'default': dj_database_url.parse(
        db_url,
        conn_max_age=600,
        ssl_require=not DEBUG
    )
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Dubai'
USE_I18N = True
USE_TZ = True

# 📁 الملفات الساكنة والميديا
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'