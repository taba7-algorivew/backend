# Import Base image
FROM python:3.10.12-slim

# 워킹디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 컨테이너 워킹 디렉토리에 프로젝트 COPY
COPY . .

# 정적 파일을 수집할 디렉토리 생성
RUN mkdir -p staticfiles

# 서버 실행 및 마이그레이션
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn --bind 0.0.0.0:8000 backend.wsgi:application --access-logfile - --timeout 60"]
