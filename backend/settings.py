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

# [Prod] 환경 변수 로드 함수
def read_secret(secret_name, default=None):
    path = f"/run/secrets/{secret_name}"
    try:
        with open(path, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return default

# 서버 환경에 따라 로드하는 방법이 다름
def get_env_var(var_name, secret_name=None, default=None):
    # 1️⃣ .bashrc나 실행 환경 변수에서 로드
    value = os.getenv(var_name)
    if value:
        return value
    
    # 2️⃣ Docker 시크릿에서 로드 (secret_name이 제공된 경우)
    if secret_name:
        value = read_secret(secret_name)
        if value:
            return value
    
    # 3️⃣ 기본값 반환 또는 오류 발생
    if default is not None:
        return default
    raise ImproperlyConfigured(f"{var_name} is not set and no default provided!")

# 기본 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent

# Django 필수 환경 변수 불러오기
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
SECRET_KEY = get_env_var("SECRET_KEY", secret_name="secret_key")
DEBUG = get_env_var("DEBUG", secret_name="debug_mode", default="False").lower() == "true"
ALLOWED_HOSTS = get_env_var("ALLOWED_HOSTS", default="*").split(",")
OPENAI_API_KEY = get_env_var("OPENAI_API_KEY", secret_name="open_api_key")
GENAI_API_KEY = get_env_var("GENAI_API_KEY", secret_name="genai_api_key")

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

# Database 설정
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env_var("DB_NAME", secret_name="db_name"),
        'USER': get_env_var("DB_USER", secret_name="db_user"),
        'PASSWORD': get_env_var("DB_PASSWORD", secret_name="db_password"),
        'HOST': get_env_var("DB_HOST", secret_name="db_host"),
        'PORT': get_env_var("DB_PORT", secret_name="db_port"),
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
