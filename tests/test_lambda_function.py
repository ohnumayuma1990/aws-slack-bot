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

# DynamoDBのモック
mock_table = MagicMock()
with patch('boto3.resource') as mock_resource:
    mock_resource.return_value.Table.return_value = mock_table
    from lambda_function import lambda_handler

class TestLambdaFunction(unittest.TestCase):

    def setUp(self):
        self.signing_secret = 'test-secret'
        os.environ['SLACK_BOT_TOKEN'] = 'fake-token'
        os.environ['SLACK_SIGNING_SECRET'] = self.signing_secret
        os.environ['DYNAMODB_TABLE'] = 'TestTable'
        mock_table.reset_mock()

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

    @patch('lambda_function.send_slack_message')
    def test_app_mention(self, mock_send_message):
        """app_mentionイベントでクイズ投稿とDynamoDB保存が行われるかテスト"""
        mock_send_message.return_value = {'ok': True, 'ts': '1234567890.123456'}

        timestamp = str(int(time.time()))
        body_dict = {
            'type': 'event_callback',
            'event': {
                'type': 'app_mention',
                'channel': 'C12345',
                'text': '<@U12345> クイズ出して'
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

        mock_send_message.assert_called_once_with('C12345', '【クイズ】日本の首都はどこ？')
        mock_table.put_item.assert_called_once()
        args, kwargs = mock_table.put_item.call_args
        self.assertEqual(kwargs['Item']['message_ts'], '1234567890.123456')
        self.assertEqual(kwargs['Item']['correct_reaction'], 'tokyo')

    @patch('lambda_function.send_dm')
    def test_reaction_added_correct(self, mock_send_dm):
        """正しいリアクションでDM送信が行われるかテスト"""
        mock_table.get_item.return_value = {'Item': {'correct_reaction': 'tokyo'}}

        timestamp = str(int(time.time()))
        body_dict = {
            'type': 'event_callback',
            'event': {
                'type': 'reaction_added',
                'user': 'U12345',
                'reaction': 'tokyo',
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

        mock_table.get_item.assert_called_once_with(Key={'message_ts': '1234567890.123456'})
        mock_send_dm.assert_called_once_with('U12345', '正解です！おめでとうございます！ (Message TS: 1234567890.123456)')

    @patch('lambda_function.send_dm')
    def test_reaction_added_wrong(self, mock_send_dm):
        """誤ったリアクションでDM送信が行われないかテスト"""
        mock_table.get_item.return_value = {'Item': {'correct_reaction': 'tokyo'}}

        timestamp = str(int(time.time()))
        body_dict = {
            'type': 'event_callback',
            'event': {
                'type': 'reaction_added',
                'user': 'U12345',
                'reaction': 'osaka',
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

        mock_send_dm.assert_not_called()

if __name__ == '__main__':
    unittest.main()
