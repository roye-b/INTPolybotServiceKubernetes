import flask
from flask import request
import os
import boto3
import json
from bot import ObjectDetectionBot
import logging

# === Logging configuration ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Flask app ===
app = flask.Flask(__name__)

# === Load from environment ===
TELEGRAM_APP_URL = os.environ.get('TELEGRAM_APP_URL')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

# === Initialize S3 client ===
s3_client = boto3.client('s3')

def get_telegram_token_from_aws():
    """Fetch TELEGRAM_TOKEN from AWS Secrets Manager"""
    secret_name = "telegram/bot/token"
    region_name = "eu-north-1"

    try:
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=region_name)

        response = client.get_secret_value(SecretId=secret_name)
        secret_dict = json.loads(response['SecretString'])

        return secret_dict.get("TELEGRAM_TOKEN")
    except Exception as e:
        logger.warning(f"Failed to retrieve token from AWS Secrets Manager: {e}")
        return None

# === Get Telegram Token ===
TELEGRAM_TOKEN = get_telegram_token_from_aws() or os.environ.get("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_TOKEN is missing. Please configure via AWS Secrets Manager or env variable.")
    raise ValueError("Telegram token not provided.")

logger.info(f"✅ Telegram token loaded successfully.")

# === Initialize the bot ===
bot = ObjectDetectionBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL, S3_BUCKET_NAME, s3_client)

# === Routes ===
@app.route('/', methods=['GET'])
def index():
    return 'Ok'

@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    try:
        req = request.get_json()
        logger.info(f"📩 Received Telegram update: {req}")
        if "message" in req:
            bot.handle_message(req["message"])
    except Exception as e:
        logger.exception(f"Error processing update: {e}")
    return 'Ok'

# === Main ===
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8443)

