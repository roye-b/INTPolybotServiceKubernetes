
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip

COPY . /app

EXPOSE 8443

ENV TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
ENV TELEGRAM_APP_URL=${TELEGRAM_APP_URL}
ENV BUCKET_NAME=${BUCKET_NAME}
ENV AWS_ACCESS_KEY=${AWS_ACCESS_KEY}
ENV AWS_SECRET_KEY=${AWS_SECRET_KEY}

CMD ["python", "app.py"]]