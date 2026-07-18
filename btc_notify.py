#!/usr/bin/env python3
"""
BTC価格取得 → LINE通知BOT

6時間おき(0:00 / 6:00 / 12:00 / 18:00)にcron等から実行される想定のスクリプト。
1. CoinGecko の無料APIからBTC価格(JPY/USD)を取得
2. LINE Messaging API の Push Message で通知を送信

必要な環境変数 (.env または OS の環境変数):
    LINE_CHANNEL_ACCESS_TOKEN : LINE Developersで発行したチャネルアクセストークン(長期)
    LINE_USER_ID              : 通知を送りたい相手(自分)のuserId

使い方:
    python3 btc_notify.py
"""

import os
import sys
import datetime
import requests

# .env を使いたい場合は python-dotenv を読み込む(なければ無視)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"

CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")


def get_btc_price() -> dict:
    """CoinGeckoからBTCの現在価格(JPY, USD)と24h変動率を取得する"""
    params = {
        "ids": "bitcoin",
        "vs_currencies": "jpy,usd",
        "include_24hr_change": "true",
    }
    res = requests.get(COINGECKO_URL, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()
    return data["bitcoin"]


def build_message(price_data: dict) -> str:
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    jpy = price_data.get("jpy")
    usd = price_data.get("usd")
    change_24h = price_data.get("usd_24h_change", 0.0)

    arrow = "📈" if change_24h >= 0 else "📉"

    message = (
        f"₿ BTC価格情報 ({now})\n"
        f"----------------------\n"
        f"JPY: ¥{jpy:,.0f}\n"
        f"USD: ${usd:,.2f}\n"
        f"24h変動: {arrow} {change_24h:+.2f}%"
    )
    return message


def send_line_message(message: str) -> None:
    if not CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("エラー: LINE_CHANNEL_ACCESS_TOKEN または LINE_USER_ID が設定されていません。")
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}],
    }

    res = requests.post(LINE_PUSH_URL, headers=headers, json=payload, timeout=10)

    if res.status_code != 200:
        print(f"LINE通知に失敗しました: {res.status_code} {res.text}")
        sys.exit(1)
    else:
        print("LINE通知を送信しました。")


def main():
    try:
        price_data = get_btc_price()
    except requests.RequestException as e:
        print(f"BTC価格の取得に失敗しました: {e}")
        sys.exit(1)

    message = build_message(price_data)
    print(message)
    send_line_message(message)


if __name__ == "__main__":
    main()
