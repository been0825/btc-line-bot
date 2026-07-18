# BTC価格 LINE通知BOT

BTC価格を6時間ごと(0時・6時・12時・18時)に取得し、LINEに通知するBOTです。

※ 旧LINE Notifyは2025年3月31日でサービス終了しているため、
本BOTは後継の **LINE Messaging API (Push Message)** を使用しています。

---

## 1. 事前準備: LINE Developersの設定

1. [LINE Developers Console](https://developers.line.biz/console/) にログイン
2. 「新規プロバイダー作成」→ プロバイダー名を入力
3. 「新規チャネル作成」→ **Messaging API** を選択してチャネルを作成
4. チャネル基本設定タブから以下を確認・発行
   - **チャネルアクセストークン(長期)** → 発行ボタンを押して取得
5. Messaging API設定タブで、あなたの **Bot用QRコード** を読み取り、自分のLINEアカウントで友だち追加する
6. 自分の **userId** を取得する方法(いずれか)
   - Webhookを一時的に有効にし、自分から何かメッセージを送って `events[0].source.userId` をログ出力して確認する
   - または [LINE公式のuserId確認方法](https://developers.line.biz/ja/docs/messaging-api/getting-user-ids/) を参照

## 2. インストール

```bash
cd btc_line_bot
pip install -r requirements.txt
cp .env.example .env
# .env を編集して、チャネルアクセストークンとuserIdを設定
```

## 3. 動作確認

```bash
python3 btc_notify.py
```

正常に動作すると、LINEに以下のようなメッセージが届きます。

```
₿ BTC価格情報 (2026/07/18 06:00)
----------------------
JPY: ¥15,234,567
USD: $102,345.67
24h変動: 📈 +2.35%
```

## 4. GitHub Actionsで6時間ごとに自動実行する

このリポジトリには `.github/workflows/btc-notify.yml` が含まれており、
JSTの 0時・6時・12時・18時 に自動実行されるよう設定済みです。

### 手順

1. このフォルダの中身(`btc_notify.py` / `requirements.txt` / `.github/workflows/btc-notify.yml`)を
   GitHubリポジトリにpushする(`.env` はpushしない。`.gitignore`に追加推奨)
2. リポジトリの **Settings → Secrets and variables → Actions → New repository secret** から
   以下2つを登録する
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `LINE_USER_ID`
3. **Actions** タブを開くと `BTC Price LINE Notify` ワークフローが表示される
   - 右上の **Run workflow** ボタンで手動テスト実行が可能(`workflow_dispatch`設定済み)
4. 以降は自動でJST 0:00 / 6:00 / 12:00 / 18:00 に実行され、LINEに通知が届く

### cronの時刻について(重要)

GitHub Actionsのスケジュールは **UTC基準** です。JSTはUTC+9のため、
JSTの 0/6/12/18時 は UTC の 15(前日)/21(前日)/3/9時 に相当します。
ワークフロー内では次のように設定しています。

```yaml
schedule:
  - cron: "0 3,9,15,21 * * *"
```

### 注意点

- GitHub Actionsの `schedule` トリガーは、リポジトリが一定期間(60日程度)操作されないと
  自動的に無効化されることがあります。定期的にリポジトリを確認してください
- 無料枠(Public repoは無料、Private repoは月2,000分まで無料)の範囲内で収まる想定です
  (1回の実行は数十秒程度)
- 実行時刻は混雑状況により数分〜十数分ずれることがあります(GitHub側の仕様)

### ローカルやサーバーで動かしたい場合

GitHub Actionsではなく自前のマシンで動かす場合は、`crontab -e` で以下のように設定できます。

```cron
0 0,6,12,18 * * * cd /path/to/btc_line_bot && /usr/bin/python3 btc_notify.py >> btc_notify.log 2>&1
```

## 5. カスタマイズ

- 通知先を複数人・グループにしたい場合は `LINE_USER_ID` をグループIDに変更するか、
  `send_line_message` を呼び出すループで複数の宛先に送信してください
- 価格取得元を変えたい場合は `get_btc_price()` 内のAPI呼び出しを変更してください
  (CoinGeckoは無料・APIキー不要ですが、レート制限があります)
- 通知条件を「前回より○%以上変動したときだけ」にしたい場合は、
  前回価格をファイルやDBに保存して比較するロジックを追加してください
