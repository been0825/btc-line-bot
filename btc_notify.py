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
from zoneinfo import ZoneInfo
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


def get_crypto_prices() -> dict:
    """CoinGeckoからBTC・HYPEの現在価格(USD)と24h変動率を取得する"""
    params = {
        "ids": "bitcoin,hyperliquid",
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    res = requests.get(COINGECKO_URL, params=params, timeout=10)
    res.raise_for_status()
    return res.json()


def _format_coin_block(label: str, icon: str, coin_data: dict) -> str:
    usd = coin_data.get("usd")
    change_24h = coin_data.get("usd_24h_change", 0.0)
    arrow = "📈" if change_24h >= 0 else "📉"

    return (
        f"{icon} {label}\n"
        f"USD: ${usd:,.2f}\n"
        f"24h変動: {arrow} {change_24h:+.2f}%"
    )


def build_message(prices: dict) -> str:
    now = datetime.datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y/%m/%d %H:%M")

    btc_block = _format_coin_block("BTC", "₿", prices["bitcoin"])
    hype_block = _format_coin_block("HYPE", "🟢", prices["hyperliquid"])

　　 message = (
        f"📊 仮想通貨価格\n"
        f"{now}\n"
        f"---------\n"
        f"{btc_block}\n"
        f"---------\n"
        f"{hype_block}"
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
        prices = get_crypto_prices()
    except requests.RequestException as e:
        print(f"価格の取得に失敗しました: {e}")
        sys.exit(1)

    message = build_message(prices)
    print(message)
    send_line_message(message)


if __name__ == "__main__":
    main()
