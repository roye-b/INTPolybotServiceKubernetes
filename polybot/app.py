import flask
from flask import request
import os
import boto3
import json
import logging
from bot import ObjectDetectionBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = flask.Flask(__name__)

TELEGRAM_APP_URL = os.environ['TELEGRAM_APP_URL']
S3_BUCKET_NAME = os.environ['BUCKET_NAME']
TELEGRAM_TOKEN = None

# Try to get the token from a mounted file (e.g., Kubernetes secret volume)
secret_file_path = '/run/secrets/telegram_token'
if os.path.exists(secret_file_path):
    with open(secret_file_path, 'r') as secret_file:
        TELEGRAM_TOKEN = secret_file.read().strip()
        logger.info("Telegram token loaded from file.")
# Try to get from environment variable
elif os.environ.get('TELEGRAM_TOKEN'):
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    logger.info("Telegram token loaded from environment variable.")
# Try to load from AWS Secrets Manager
else:
    try:
        secret_name = "telegram/bot/token"
        region_name = "us-north-1"

        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=region_name)

        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        TELEGRAM_TOKEN = json.loads(secret)['TELEGRAM_TOKEN']
        logger.info("Telegram token loaded from AWS Secrets Manager.")
    except Exception as e:
        logger.error(f"Failed to load token from AWS Secrets Manager: {e}")

if not TELEGRAM_TOKEN:
    logger.warning("Telegram token is not set. Ensure it's passed via file, env var, or AWS Secrets Manager.")

print(f"Telegram token: {TELEGRAM_TOKEN}")

# Initialize the bot
bot = ObjectDetectionBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL, S3_BUCKET_NAME, boto3.client('s3'))

@app.route('/', methods=['GET'])
def index():
    return 'Ok'

@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    logger.info(f'Received webhook request: {req}')
    bot.handle_message(req['message'])
    return 'Ok'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8443)
