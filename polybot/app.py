import flask
from flask import request
import os
import boto3
import json
from bot import ObjectDetectionBot # ודא שהקובץ bot.py קיים והמחלקה ObjectDetectionBot מוגדרת בו
import logging
from botocore.exceptions import ClientError # הוספה לטיפול בשגיאות ספציפי

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s') # פורמט לוג משופר
logger = logging.getLogger(__name__)
app = flask.Flask(__name__)

TELEGRAM_APP_URL = os.environ.get('TELEGRAM_APP_URL')
S3_BUCKET_NAME = os.environ.get('BUCKET_NAME')

# Initialize the S3 client
s3_client = boto3.client('s3')


def get_telegram_token_from_aws():
    secret_name = "telegram/bot/token"  # ודא שזהו שם הסוד הנכון
    region_name = "eu-north-1"          # ודא שזהו האזור הנכון

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        # הנחה שהסוד הוא JSON עם מפתח "TELEGRAM_TOKEN"
        # אם הסוד הוא מחרוזת פשוטה, השתמש ב: return get_secret_value_response['SecretString']
        secret_dict = json.loads(get_secret_value_response['SecretString'])
        token = secret_dict.get("TELEGRAM_TOKEN")
        if not token:
            logger.warning(f"Key 'TELEGRAM_TOKEN' not found in secret '{secret_name}' JSON.")
            return None
        return token
    except ClientError as e:
        logger.warning(f"AWS ClientError retrieving Telegram token from Secrets Manager: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to decode JSON from secret '{secret_name}': {e}")
        return None
    except Exception as e: # תופס כל שגיאה אחרת לא צפויה
        logger.warning(f"Unexpected error retrieving Telegram token from Secrets Manager: {e}")
        return None


# Try to load the Telegram token
TELEGRAM_TOKEN = get_telegram_token_from_aws()

if not TELEGRAM_TOKEN:
    logger.info("Could not retrieve token from AWS Secrets Manager, trying environment variable 'TELEGRAM_TOKEN'.")
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# קריטי: בדוק אם הטוקן נטען לפני שממשיכים
if not TELEGRAM_TOKEN:
    logger.error("CRITICAL: Telegram token is not set or could not be retrieved. Bot cannot start. Exiting.")
    exit(1) # יציאה מהאפליקציה
else:
    # אל תדפיס את הטוקן עצמו!
    logger.info(f"Telegram token loaded successfully. Length: {len(TELEGRAM_TOKEN)}")


# Initialize the bot - רק אחרי שווידאנו שיש טוקן
try:
    bot = ObjectDetectionBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL, S3_BUCKET_NAME, s3_client)
except Exception as e:
    logger.error(f"Failed to initialize ObjectDetectionBot: {e}")
    exit(1)


@app.route('/', methods=['GET'])
def index():
    return 'Ok'


# הגדר את ה-route ל-webhook רק אחרי שיש טוקן
@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    if not req or 'message' not in req:
        logger.warning("Received webhook request without 'message' field or invalid JSON.")
        return 'Bad Request', 400
    # logger.info(f'Received webhook request content: {req}') # יכול להיות מאוד ורבלי, השתמש בזהירות
    logger.info(f"Received message for bot: {req.get('message', {}).get('message_id', 'N/A')}")
    bot.handle_message(req['message'])
    return 'Ok', 200

#
if __name__ == "__main__":
    #  להשתמש בשרת WSGI ברמה של production כמו gunicorn או uWSGI
    # , אם מריצים עם gunicorn: gunicorn -w 4 -b 0.0.0.0:8443 app:app
    logger.info(f"Starting Flask development server on port 8443 for bot webhook...")
    app.run(host='0.0.0.0', port=8443)
