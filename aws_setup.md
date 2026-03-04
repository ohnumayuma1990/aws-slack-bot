# AWS環境の構築手順

AWSの無料枠の範囲内でボットを運用するための設定手順です。

1. **Lambda関数の作成**
   - AWSコンソールで Lambda サービスを開きます。
   - 「関数の作成」をクリックし、「一から作成」を選択します。
     - 関数名: `slack-answer-bot`
     - ランタイム: `Python 3.12` (または最新)
   - 「関数の作成」をクリックします。
   - `src/lambda_function.py` のコードをコードエディタに貼り付けて「Deploy」をクリックします。

2. **環境変数の設定**
   - 「設定」タブの「環境変数」を選択し、「編集」をクリックします。
   - 以下の変数を追加して保存します：
     - キー: `SLACK_BOT_TOKEN`
     - 値: Slackアプリ設定で取得した `xoxb-...` のトークン
     - キー: `SLACK_SIGNING_SECRET`
     - 値: Slackアプリ設定の Basic Information で取得した `Signing Secret`

3. **API Gateway の設定**
   - Lambda関数の「関数の概要」セクションで「トリガーを追加」をクリックします。
   - トリガーの設定で「API Gateway」を選択します。
     - API: `新しいAPIを作成する`
     - APIタイプ: `HTTP API`
     - セキュリティ: `オープン` (Slackからのアクセスを許可するため)
   - 「追加」をクリックします。
   - 生成された 「API エンドポイント」 のURLをコピーします。

4. **Slack アプリへの登録**
   - Slack APIの設定画面（Event Subscriptions）に戻ります。
   - 「Request URL」にコピーしたAPIエンドポイントURLを貼り付けます。
   - 「Verified」と表示されることを確認します。

5. **(推奨) 請求アラートの設定**
   - AWS Billing サービスで「請求アラート」を有効にし、無料枠を超えそうになった際に通知が届くように設定します。
