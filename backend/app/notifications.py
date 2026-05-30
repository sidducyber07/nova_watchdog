import httpx
import asyncio
from typing import Any
import json
from aiosmtplib import SMTP


def _load_cfg(config: Any) -> dict:
    if isinstance(config, str):
        try:
            return json.loads(config)
        except Exception:
            return {}
    return config or {}


async def send_telegram(config: Any, message: str) -> bool:
    cfg = _load_cfg(config)
    bot_token = cfg.get("bot_token")
    chat_id = cfg.get("chat_id")
    if not bot_token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, json={"chat_id": chat_id, "text": message})
        return r.status_code == 200


async def send_discord(config: Any, message: str) -> bool:
    cfg = _load_cfg(config)
    url = cfg.get("webhook_url")
    if not url:
        return False
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, json={"content": message})
        return r.status_code in (200, 204)


async def send_webhook(config: Any, payload: dict) -> bool:
    cfg = _load_cfg(config)
    url = cfg.get("url") or cfg.get("webhook_url")
    if not url:
        return False
    headers = cfg.get("headers") or {}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, json=payload, headers=headers)
        return 200 <= r.status_code < 300


async def send_slack(config: Any, message: str) -> bool:
    cfg = _load_cfg(config)
    url = cfg.get("webhook_url")
    if not url:
        return False
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, json={"text": message})
        return r.status_code in (200, 204)


async def send_email(config: Any, subject: str, body: str) -> bool:
    cfg = _load_cfg(config)
    host = cfg.get("host")
    port = int(cfg.get("port", 587))
    username = cfg.get("username")
    password = cfg.get("password")
    sender = cfg.get("sender") or username
    recipient = cfg.get("recipient")
    if not (host and username and password and recipient):
        return False
    message = f"From: {sender}\r\nTo: {recipient}\r\nSubject: {subject}\r\n\r\n{body}"
    try:
        smtp = SMTP(hostname=host, port=port, start_tls=True)
        await smtp.connect()
        await smtp.login(username, password)
        await smtp.sendmail(sender, [recipient], message)
        await smtp.quit()
        return True
    except Exception:
        return False
