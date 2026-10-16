import os
import json
import base64
import urllib.request
import urllib.parse

TG_TOKEN = os.environ.get("TG_TOKEN", "")
API_BASE = f"https://api.telegram.org/bot{TG_TOKEN}" if TG_TOKEN else ""


def tg_api(method: str, payload: dict):
    """Вызов Telegram Bot API без внешних зависимостей."""
    if not TG_TOKEN:
        print("ERROR: TG_TOKEN is not set")
        return
    url = f"{API_BASE}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"TG {method}: {r.status} {r.read()[:500]}")
    except Exception as e:
        print(f"TG {method} failed: {e}")


def handle_update(update: dict):
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "")

    if not chat_id:
        return

    if text == "/start":
        reply = "Привет! Я бот на Yandex Functions 👋\nПопробуй /ping"
    elif text == "/ping":
        reply = "pong 🏓"
    elif text.startswith("/echo "):
        reply = text[len("/echo "):]
    else:
        reply = f"Ты написал: {text}"

    tg_api("sendMessage", {"chat_id": chat_id, "text": reply})


def handler(event, context):
    """Entrypoint для Yandex Cloud Functions (runtime python312, точка входа index.handler)."""
    # 1. Проверка секрета Telegram (защита от чужих запросов)
    secret = os.environ.get("TG_SECRET", "")
    if secret:
        headers = event.get("headers") or {}
        # Yandex может отдавать заголовки в разном регистре
        got = headers.get("X-Telegram-Bot-Api-Secret-Token") or headers.get(
            "x-telegram-bot-api-secret-token", ""
        )
        if got != secret:
            return {"statusCode": 401, "body": "unauthorized"}

    # 2. Достаём body (Yandex может присылать base64)
    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    if not body:
        return {"statusCode": 200, "body": "ok - no body"}

    try:
        update = json.loads(body)
    except Exception as e:
        print(f"Bad JSON: {e} body={body[:500]}")
        return {"statusCode": 200, "body": "ok - bad json"}

    print(f"Update: {json.dumps(update, ensure_ascii=False)[:2000]}")

    try:
        handle_update(update)
    except Exception as e:
        print(f"handle_update failed: {e}")

    # Важно всегда отвечать 200, иначе Telegram будет ретраить
    return {"statusCode": 200, "body": "ok"}
