# using slim to keep the image smaller
FROM python:3.11-slim

# flush logs immediately and don't write .pyc files inside the image
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# copy requirements first so docker doesnt reinstall packages every time i change app.py
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# don't run as root
RUN useradd --create-home --shell /bin/bash app
USER app

EXPOSE 5000

CMD ["python", "app.py"]
