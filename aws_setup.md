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
     - キー: `DYNAMODB_TABLE`
     - 値: `SlackQuizTable`

3. **DynamoDB テーブルの作成**
   - AWSコンソールで DynamoDB サービスを開きます。
   - 「テーブルの作成」をクリックします。
     - テーブル名: `SlackQuizTable`
     - パーティションキー: `message_ts` (文字列)
   - 「TTL (Time to Live)」を有効化（オプション）:
     - 属性名: `ttl`
   - 「テーブルの作成」をクリックします。

4. **Lambda への権限付与**
   - Lambda関数の「設定」タブの「アクセス権限」を選択します。
   - 実行ロールのリンクをクリックして IAM コンソールを開きます。
   - 「許可を追加」→「ポリシーをアタッチ」を選択し、`AmazonDynamoDBFullAccess` (または必要な権限に絞ったカスタムポリシー) を追加します。

5. **API Gateway の設定**
   - Lambda関数の「関数の概要」セクションで「トリガーを追加」をクリックします。
   - トリガーの設定で「API Gateway」を選択します。
     - API: `新しいAPIを作成する`
     - APIタイプ: `HTTP API`
     - セキュリティ: `オープン` (Slackからのアクセスを許可するため)
   - 「追加」をクリックします。
   - 生成された 「API エンドポイント」 のURLをコピーします。

6. **Slack アプリへの登録**
   - Slack APIの設定画面（Event Subscriptions）に戻ります。
   - 「Request URL」にコピーしたAPIエンドポイントURLを貼り付けます。
   - 「Verified」と表示されることを確認します。

7. **(推奨) 請求アラートの設定**
   - AWS Billing サービスで「請求アラート」を有効にし、無料枠を超えそうになった際に通知が届くように設定します。
