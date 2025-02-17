"""
Django settings for backend project.
"""
import environ
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

# 환경변수 로드
env = environ.Env()

# 개발 환경에서는 .env 파일을 로드, 서버 환경에서는 무시
if os.path.exists(".env"):  
    environ.Env.read_env()

# 기본 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent

# 환경변수에서 SECRET_KEY 불러오기 (없으면 에러 발생)
SECRET_KEY = env("SECRET_KEY", default=None)
if SECRET_KEY is None:
    raise ImproperlyConfigured("SECRET_KEY environment variable is missing!")

# DEBUG 설정 (환경변수에서 불러오되, 기본값은 False)
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# 허용된 호스트 설정 (환경변수에서 불러오고 기본값은 모두 허용)
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# Installed Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "corsheaders",
    'rest_framework',
    'user_auth',
    'review',
]

# Middleware 설정
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

# CORS 설정
CORS_ALLOW_ALL_ORIGINS = True  # 개발 환경에서만 True (배포 시 특정 도메인만 허용)

# URL 설정
ROOT_URLCONF = 'backend.urls'

# Templates 설정
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# Database 설정 (PostgreSQL 환경변수 기반)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env("DB_NAME"),
        'USER': env("DB_USER"),
        'PASSWORD': env("DB_PASSWORD"),
        'HOST': env("DB_HOST"),
        'PORT': env("DB_PORT"),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static Files 설정
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'user_auth.AlgoReviewUser'
