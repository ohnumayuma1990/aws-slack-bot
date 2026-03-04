import json
import os
import urllib.request
import logging
import hmac
import hashlib
import time

# ログの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_slack_bot_token():
    return os.environ.get('SLACK_BOT_TOKEN')

def get_slack_signing_secret():
    return os.environ.get('SLACK_SIGNING_SECRET')

def verify_slack_signature(event):
    """
    Slackからのリクエスト署名を検証する
    """
    signing_secret = get_slack_signing_secret()
    if not signing_secret:
        logger.error("SLACK_SIGNING_SECRET is not set")
        return False

    headers = event.get('headers', {})
    signature = headers.get('x-slack-signature')
    timestamp = headers.get('x-slack-request-timestamp')

    if not signature or not timestamp:
        logger.error("Missing Slack signature or timestamp")
        return False

    # タイムスタンプの検証（5分以上前のリクエストは拒否）
    if abs(time.time() - int(timestamp)) > 60 * 5:
        logger.error("Request timestamp is too old")
        return False

    body = event.get('body', '')
    sig_basestring = f"v0:{timestamp}:{body}"

    computed_signature = 'v0=' + hmac.new(
        signing_secret.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    if hmac.compare_digest(computed_signature, signature):
        return True
    else:
        logger.error("Invalid Slack signature")
        return False

def lambda_handler(event, context):
    """
    Slackからのイベントを処理するLambda関数
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # 署名の検証
    if not verify_slack_signature(event):
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Invalid signature'})
        }

    body = json.loads(event.get('body', '{}'))

    # Slackからの認証チャレンジ（url_verification）への対応
    if body.get('type') == 'url_verification':
        return {
            'statusCode': 200,
            'body': json.dumps({'challenge': body.get('challenge')})
        }

    # イベントの処理
    slack_event = body.get('event', {})

    # reaction_added イベントの処理
    if slack_event.get('type') == 'reaction_added':
        reaction = slack_event.get('reaction')
        user_id = slack_event.get('user')
        item = slack_event.get('item', {})
        ts = item.get('ts')

        # 特定のリアクション（例：white_check_mark）に反応
        if reaction == 'white_check_mark':
            send_dm(user_id, f"正解です！おめでとうございます！ (Message TS: {ts})")

    return {
        'statusCode': 200,
        'body': json.dumps({'ok': True})
    }

def send_dm(user_id, text):
    """
    対象ユーザーにDMを送信する
    """
    url = "https://slack.com/api/chat.postMessage"

    data = {
        "channel": user_id,
        "text": text
    }

    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Authorization": f"Bearer {get_slack_bot_token()}"
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as res:
            response_body = res.read().decode("utf-8")
            logger.info(f"Slack API response: {response_body}")
    except Exception as e:
        logger.error(f"Error sending DM: {e}")
