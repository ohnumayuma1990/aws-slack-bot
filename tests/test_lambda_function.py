import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys
import hmac
import hashlib
import time

# srcディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from lambda_function import lambda_handler

class TestLambdaFunction(unittest.TestCase):

    def setUp(self):
        self.signing_secret = 'test-secret'
        os.environ['SLACK_BOT_TOKEN'] = 'fake-token'
        os.environ['SLACK_SIGNING_SECRET'] = self.signing_secret

    def generate_signature(self, timestamp, body):
        sig_basestring = f"v0:{timestamp}:{body}"
        signature = 'v0=' + hmac.new(
            self.signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def test_url_verification(self):
        """Slackの認証チャレンジに対応するかテスト"""
        timestamp = str(int(time.time()))
        body_dict = {
            'type': 'url_verification',
            'challenge': 'test_challenge'
        }
        body = json.dumps(body_dict)
        signature = self.generate_signature(timestamp, body)

        event = {
            'headers': {
                'x-slack-signature': signature,
                'x-slack-request-timestamp': timestamp
            },
            'body': body
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        res_body = json.loads(response['body'])
        self.assertEqual(res_body['challenge'], 'test_challenge')

    @patch('lambda_function.send_dm')
    def test_reaction_added(self, mock_send_dm):
        """reaction_addedイベントでDM送信関数が呼ばれるかテスト"""
        timestamp = str(int(time.time()))
        body_dict = {
            'type': 'event_callback',
            'event': {
                'type': 'reaction_added',
                'user': 'U12345',
                'reaction': 'white_check_mark',
                'item': {
                    'channel': 'C12345',
                    'ts': '1234567890.123456'
                }
            }
        }
        body = json.dumps(body_dict)
        signature = self.generate_signature(timestamp, body)

        event = {
            'headers': {
                'x-slack-signature': signature,
                'x-slack-request-timestamp': timestamp
            },
            'body': body
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        mock_send_dm.assert_called_once_with('U12345', '正解です！おめでとうございます！ (Message TS: 1234567890.123456)')

    def test_invalid_signature(self):
        """不正な署名の場合に401エラーを返すかテスト"""
        timestamp = str(int(time.time()))
        body = json.dumps({'type': 'url_verification'})
        signature = 'v0=invalid'

        event = {
            'headers': {
                'x-slack-signature': signature,
                'x-slack-request-timestamp': timestamp
            },
            'body': body
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 401)

if __name__ == '__main__':
    unittest.main()
