# Slackアプリの設定手順

1. **Slackアプリの作成**
   - [Slack API](https://api.slack.com/apps) にアクセスし、「Create New App」をクリックします。
   - 「From scratch」を選択し、アプリ名（例：答え合わせBot）とワークスペースを選択して「Create App」をクリックします。

2. **権限（Scopes）の設定**
   - 左サイドバーの「OAuth & Permissions」を選択します。
   - 「Scopes」セクションの「Bot Token Scopes」に以下の権限を追加します：
     - `reactions:read` (スタンプの検知)
     - `chat:write` (DMの送信)
     - `users:read` (ユーザー情報の確認)

3. **アプリのインストール**
   - 同じページのトップにある「Install to Workspace」をクリックして、ワークスペースにアプリをインストールします。
   - 完了後、表示される `Bot User OAuth Token` (xoxb-...) を控えておきます。これは後でAWS Lambdaの環境変数に使用します。

4. **Signing Secret の取得**
   - 左サイドバーの「Basic Information」を選択します。
   - 「App Credentials」セクションにある `Signing Secret` を表示して控えておきます。これも後でAWS Lambdaの環境変数に使用します。

5. **イベント購読（Event Subscriptions）の設定**
   - 左サイドバーの「Event Subscriptions」を選択し、「Enable Events」をオンにします。
   - 「Request URL」に後ほど作成する API Gateway のエンドポイントURLを入力します。
   - 「Subscribe to bot events」で `reaction_added` を追加します。
   - 「Save Changes」をクリックします。
