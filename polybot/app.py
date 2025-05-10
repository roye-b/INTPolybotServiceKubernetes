import flask
from flask import request
import os
import boto3
import json
from bot import ObjectDetectionBot
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = flask.Flask(__name__)

TELEGRAM_APP_URL = os.environ.get('TELEGRAM_APP_URL')
S3_BUCKET_NAME = os.environ.get('BUCKET_NAME')

# Initialize the S3 client
s3_client = boto3.client('s3')


def get_telegram_token_from_aws():
    secret_name = "telegram/bot/token"
    region_name = "eu-north-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret_dict = json.loads(get_secret_value_response['SecretString'])
        return secret_dict.get("TELEGRAM_TOKEN")
    except Exception as e:
        logger.warning(f"Failed to retrieve Telegram token from Secrets Manager: {e}")
        return None


# Try to load the Telegram token from AWS Secrets Manager, fall back to env variable if needed
TELEGRAM_TOKEN = get_telegram_token_from_aws() or os.environ.get('TELEGRAM_TOKEN')

# Log a warning if the token is missing
if not TELEGRAM_TOKEN:
    logger.warning("Telegram token is not set. Ensure it's passed via AWS Secrets Manager or environment variables.")

print(f"Telegram token: {TELEGRAM_TOKEN}")

# Initialize the bot
bot = ObjectDetectionBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL, S3_BUCKET_NAME, s3_client)


@app.route('/', methods=['GET'])
def index():
    return 'Ok'


@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    logger.info(f'Received webhook request: {req}')  # Log the received request
    bot.handle_message(req['message'])
    return 'Ok'


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8443)
