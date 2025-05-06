import flask
from flask import request
import os
import boto3
from bot import ObjectDetectionBot
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = flask.Flask(__name__)


TELEGRAM_APP_URL = os.environ['TELEGRAM_APP_URL']
S3_BUCKET_NAME = os.environ['BUCKET_NAME']
TELEGRAM_TOKEN= os.environ['TELEGRAM_TOKEN']
# Initialize the S3 client
s3_client = boto3.client('s3')
secret_file_path = '/run/secrets/telegram_token'
if os.path.exists(secret_file_path):
    with open(secret_file_path, 'r') as secret_file:
        TELEGRAM_TOKEN = secret_file.read().strip()
else:
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# Log a warning if the token is missing
if not TELEGRAM_TOKEN:
    logger.warning("Telegram token is not set. Ensure it's passed via secrets or environment variables.")

print(f"Telegram token: {TELEGRAM_TOKEN}")


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
#
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8443)