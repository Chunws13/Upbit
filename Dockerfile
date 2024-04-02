# 버전 지정
FROM python:3.9

# Time Zone 설정
RUN ln -snf /usr/share/zoneinfo/Asia/Seoul /etc/localtime
RUN echo Asia/Seoul > /etc/timezone

WORKDIR /app

# 필요 소스 복사
COPY . /app

# 패키지 설치
RUN pip install -r requirement.txt

CMD ["python", "main.py"]