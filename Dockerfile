# Sử dụng base image Python 3.9-alpine
FROM python:3.9-alpine

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép file yêu cầu (các dependency)
COPY requirements.txt .

# Cài đặt các dependency cần thiết
RUN python3 -m venv venv
RUN python3 -m pip install --upgrade pip
RUN source venv/bin/activate
RUN pip3 install --default-timeout=100 -r requirements.txt

# Sao chép toàn bộ mã nguồn vào thư mục làm việc
COPY . .

# Thêm user appuser để chạy container với quyền không phải root
RUN adduser -D -u 501 appuser && \
    chown -R appuser:appuser /app

# Sử dụng user không phải root để chạy container
USER appuser

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 7200 --reload"]
