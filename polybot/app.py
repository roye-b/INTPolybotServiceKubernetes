import flask
from flask import request
import os
import boto3
from bot import ObjectDetectionBot
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = flask.Flask(__name__)


TELEGRAM_APP_URL = os.environ['TELEGRAM_APP_URL']
S3_BUCKET_NAME = os.environ['BUCKET_NAME']
s3_client = boto3.client('s3')

def get_telegram_token_from_aws():
    secret_name = "telegram/bot/token"
    region_name = "eu-north-1"

    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        return secret.strip()
    except ClientError as e:
        logger.error(f"Failed to retrieve Telegram token from Secrets Manager: {e}")
        return None

# Try getting the token from AWS Secrets Manager first
TELEGRAM_TOKEN = get_telegram_token_from_aws()

# Fallback options (optional)
if not TELEGRAM_TOKEN:
    secret_file_path = '/run/secrets/telegram_token'
    if os.path.exists(secret_file_path):
        with open(secret_file_path, 'r') as secret_file:
            TELEGRAM_TOKEN = secret_file.read().strip()
    else:
        TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# Validate token
if not TELEGRAM_TOKEN or ':' not in TELEGRAM_TOKEN:
    logger.warning("Telegram token is not set or invalid. Ensure it's passed via AWS Secrets Manager, file, or environment variable.")
else:
    print(f"Telegram token: {TELEGRAM_TOKEN}")

bot = ObjectDetectionBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL, S3_BUCKET_NAME, s3_client)

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
