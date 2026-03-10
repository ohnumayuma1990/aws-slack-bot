import json
import os
import urllib.request
import logging
import hmac
import hashlib
import time
import boto3
from boto3.dynamodb.conditions import Key

# ログの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'SlackQuizTable')
table = dynamodb.Table(TABLE_NAME)

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

    slack_event = body.get('event', {})
    event_type = slack_event.get('type')

    # app_mention イベントの処理（クイズの出題）
    if event_type == 'app_mention':
        handle_app_mention(slack_event)

    # reaction_added イベントの処理（答え合わせ）
    elif event_type == 'reaction_added':
        handle_reaction_added(slack_event)

    return {
        'statusCode': 200,
        'body': json.dumps({'ok': True})
    }

def handle_app_mention(slack_event):
    """
    メンションされた際にクイズを出題する
    """
    channel = slack_event.get('channel')

    # クイズの内容（本来はDynamoDBや外部APIから取得するのが望ましいが、簡易化のため固定）
    quiz_text = "【クイズ】日本の首都はどこ？"
    correct_reaction = "tokyo" # 実際にはスタンプ名

    # Slackに投稿
    response = send_slack_message(channel, quiz_text)

    if response and response.get('ok'):
        ts = response.get('ts')
        # DynamoDBに保存
        save_quiz_answer(ts, correct_reaction)

def handle_reaction_added(slack_event):
    """
    リアクションが追加された際に正解判定を行う
    """
    reaction = slack_event.get('reaction')
    user_id = slack_event.get('user')
    item = slack_event.get('item', {})
    ts = item.get('ts')

    # DynamoDBから正解を取得
    correct_reaction = get_quiz_answer(ts)

    if correct_reaction and reaction == correct_reaction:
        send_dm(user_id, f"正解です！おめでとうございます！ (Message TS: {ts})")

def save_quiz_answer(ts, reaction):
    """
    クイズのTSと正解をDynamoDBに保存
    """
    try:
        table.put_item(Item={
            'message_ts': ts,
            'correct_reaction': reaction,
            'ttl': int(time.time()) + 86400 # 24時間で自動削除
        })
    except Exception as e:
        logger.error(f"Error saving to DynamoDB: {e}")

def get_quiz_answer(ts):
    """
    DynamoDBからクイズの正解を取得
    """
    try:
        response = table.get_item(Key={'message_ts': ts})
        return response.get('Item', {}).get('correct_reaction')
    except Exception as e:
        logger.error(f"Error getting from DynamoDB: {e}")
        return None

def send_slack_message(channel, text):
    """
    チャンネルにメッセージを送信する
    """
    url = "https://slack.com/api/chat.postMessage"
    data = {"channel": channel, "text": text}
    return call_slack_api(url, data)

def send_dm(user_id, text):
    """
    対象ユーザーにDMを送信する
    """
    url = "https://slack.com/api/chat.postMessage"
    data = {"channel": user_id, "text": text}
    return call_slack_api(url, data)

def call_slack_api(url, data):
    """
    Slack APIを呼び出す共通関数
    """
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
            return json.loads(response_body)
    except Exception as e:
        logger.error(f"Error calling Slack API: {e}")
        return None
