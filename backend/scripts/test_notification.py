"""Send a test notification to a configured integration.

Usage: set DATABASE_URL env var and pass integration id or type.
"""
import os
import asyncio
import asyncpg
import json
from backend.app.notifications import send_webhook, send_telegram, send_discord, send_slack, send_email

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://nova:nova@localhost:5432/nova_watchdog')

async def run(integration_id=None, integ_type=None):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        if integration_id:
            row = await conn.fetchrow('SELECT id, type, config FROM integrations WHERE id = $1', integration_id)
        elif integ_type:
            row = await conn.fetchrow('SELECT id, type, config FROM integrations WHERE type = $1 LIMIT 1', integ_type)
        else:
            row = await conn.fetchrow('SELECT id, type, config FROM integrations LIMIT 1')
        if not row:
            print('No integration found')
            return
        integ_id, t, cfg = row['id'], row['type'], row['config']
        print('Testing integration', integ_id, t)
        if t == 'webhook':
            ok = await send_webhook(cfg, {'test': 'hello'})
        elif t == 'telegram':
            ok = await send_telegram(cfg, 'Test message from Nova Watchdog')
        elif t == 'discord':
            ok = await send_discord(cfg, 'Test message from Nova Watchdog')
        elif t == 'slack':
            ok = await send_slack(cfg, 'Test message from Nova Watchdog')
        elif t == 'email':
            ok = await send_email(cfg, 'Test Nova Watchdog', 'This is a test')
        else:
            print('Unknown type', t)
            ok = False
        print('Result:', ok)
    finally:
        await conn.close()

if __name__ == '__main__':
    import sys
    integration_id = None
    integ_type = None
    if len(sys.argv) > 1:
        integration_id = sys.argv[1]
    asyncio.run(run(integration_id, integ_type))
