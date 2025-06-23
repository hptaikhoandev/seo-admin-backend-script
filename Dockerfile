FROM python:3.13-alpine
WORKDIR /app
RUN apk update && \
    apk add busybox-extras curl && \
    adduser -D -u 501 appuser
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser . .
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
