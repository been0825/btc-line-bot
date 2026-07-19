#!/usr/bin/env python3
"""
BTC価格アラートBot(5分毎チェック・前回比1%以上の変動でLINE通知)

1. 前回価格を last_price.json から読み込む
2. CoinGeckoから現在のBTC価格を取得
3. 前回価格との変化率を計算し、±1%以上なら上昇/下落それぞれの文言でLINE通知
4. 現在価格を last_price.json に上書き保存(次回比較用)
"""

import os
import sys
import json
import datetime
from zoneinfo import ZoneInfo
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
PRICE_FILE = "last_price.json"
THRESHOLD_PERCENT = 1.0  # この%以上変動したら通知

CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")


def get_btc_price() -> dict:
    params = {
        "ids": "bitcoin",
        "vs_currencies": "jpy,usd",
    }
    res = requests.get(COINGECKO_URL, params=params, timeout=10)
    res.raise_for_status()
    return res.json()["bitcoin"]


def load_last_price() -> dict | None:
    if not os.path.exists(PRICE_FILE):
        return None
    try:
        with open(PRICE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "usd" in data:
            return data
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def save_current_price(price_data: dict) -> None:
    now = datetime.datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
    record = {
        "usd": price_data["usd"],
        "jpy": price_data["jpy"],
        "timestamp": now,
    }
    with open(PRICE_FILE, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


def build_alert_message(last_price: dict, current_price: dict, change_pct: float) -> str:
    now = datetime.datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y/%m/%d %H:%M")

    if change_pct >= 0:
        header = "🚨📈 BTC価格 急騰アラート"
        trend_line = f"5分前より +{change_pct:.2f}% 上昇しました！"
    else:
        header = "🚨📉 BTC価格 急落アラート"
        trend_line = f"5分前より {change_pct:.2f}% 下落しました！"

    message = (
        f"{header}\n"
        f"{now}\n"
        f"----------------------\n"
        f"{trend_line}\n"
        f"前回: ¥{last_price['jpy']:,.0f} (${last_price['usd']:,.2f})\n"
        f"現在: ¥{current_price['jpy']:,.0f} (${current_price['usd']:,.2f})"
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
    print("LINE通知を送信しました。")


def main():
    try:
        current_price = get_btc_price()
    except requests.RequestException as e:
        print(f"BTC価格の取得に失敗しました: {e}")
        sys.exit(1)

    last_price = load_last_price()

    if last_price is None:
        # 初回実行(比較対象がないので通知はせず、今回価格を保存するだけ)
        print("初回実行のため、比較対象がありません。価格を保存します。")
        save_current_price(current_price)
        return

    change_pct = (current_price["usd"] - last_price["usd"]) / last_price["usd"] * 100
    print(f"変化率: {change_pct:+.2f}%")

    if abs(change_pct) >= THRESHOLD_PERCENT:
        message = build_alert_message(last_price, current_price, change_pct)
        print(message)
        send_line_message(message)
    else:
        print("閾値未満のため通知なし。")

    save_current_price(current_price)


if __name__ == "__main__":
    main()
