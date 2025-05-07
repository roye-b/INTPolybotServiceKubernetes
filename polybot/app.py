import flask
from flask import request
import os
import boto3
from botocore.exceptions import ClientError
from bot import ObjectDetectionBot
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = flask.Flask(__name__)

# Load required environment variables
TELEGRAM_APP_URL = os.environ.get('TELEGRAM_APP_URL')
S3_BUCKET_NAME = os.environ.get('BUCKET_NAME')

# Validate required variables
if not TELEGRAM_APP_URL or not S3_BUCKET_NAME:
    raise ValueError("Missing required environment variables: TELEGRAM_APP_URL or BUCKET_NAME")

# Get Telegram token from AWS Secrets Manager
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
        secret_string = get_secret_value_response['SecretString']
        try:
            # Try to parse as JSON if the secret is a JSON string
            secret_dict = json.loads(secret_string)
            return secret_dict.get("TELEGRAM_TOKEN")
        except json.JSONDecodeError:
            # If not JSON, treat as plain token string
            return secret_string.strip()
    except ClientError as e:
        logger.error(f"Failed to retrieve secret from AWS: {e}")
        raise

# Get the token from AWS
TELEGRAM_TOKEN = get_telegram_token_from_aws()

# Validate token format
if not TELEGRAM_TOKEN or ':' not in TELEGRAM_TOKEN:
    logger.warning("Telegram token is missing or invalid. It must contain a colon.")
    raise ValueError("Missing or invalid TELEGRAM_TOKEN")

print(f"Telegram token: {TELEGRAM_TOKEN}")

# Initialize the S3 client
s3_client = boto3.client('s3')

# Initialize the bot
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
