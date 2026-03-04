# Slack 答え合わせBot

このプロジェクトは、Slackで特定のリアクション（スタンプ）が押された際に、自動でユーザーにDM（ダイレクトメッセージ）を送信するAWS Lambdaベースのボットです。AWSの無料枠内で構築可能です。

## 機能
- `white_check_mark` (✅) スタンプが押されたことを検知
- スタンプを押したユーザーに対して、自動で正解通知のDMを送信

## 構成
- **AWS Lambda**: Pythonによるメインロジックの実装
- **Amazon API Gateway**: SlackからのWebHookを受け取るエンドポイント
- **Slack API (Events API)**: リアクションイベントの通知

## セットアップ手順

### 1. Slackアプリの設定
詳細な手順は [slack_setup.md](slack_setup.md) を参照してください。
- 必要な権限: `reactions:read`, `chat:write`, `users:read`
- イベント購読: `reaction_added`

### 2. AWS環境の構築
詳細な手順は [aws_setup.md](aws_setup.md) を参照してください。
- Lambda関数の作成（コードは `src/lambda_function.py` を使用）
- 環境変数 `SLACK_BOT_TOKEN` および `SLACK_SIGNING_SECRET` の設定
- API Gateway の作成とSlackへの登録

## 開発とテスト

### ディレクトリ構成
- `src/`: Lambda関数のソースコード
- `tests/`: ローカルテスト用のスクリプト

### テストの実行
```bash
python3 -m unittest tests/test_lambda_function.py
```

## 注意事項
- 本プロジェクトはAWSの無料枠を想定していますが、リクエスト数が多い場合は料金が発生する可能性があります。
- AWS Billingで請求アラートを設定することを強く推奨します。
