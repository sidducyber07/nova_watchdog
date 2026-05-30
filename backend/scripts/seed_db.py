"""Seed the Postgres database with sample users, monitors, integrations, and AI rules.

Run inside the api container or a local venv where DATABASE_URL is set.
"""
import os
import asyncio
import asyncpg
import json
from uuid import uuid4

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://nova:nova@localhost:5432/nova_watchdog')

SAMPLE_USER_ID = str(uuid4())

async def run():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # create user
        await conn.execute('''
        INSERT INTO users(id, email, hashed_password, full_name, is_active, is_admin, created_at)
        VALUES($1,$2,$3,$4,true,false,now())
        ON CONFLICT (email) DO NOTHING
        ''', SAMPLE_USER_ID, 'test@example.com', 'not-a-real-hash', 'Test User')

        # sample monitors
        monitor1 = str(uuid4())
        monitor2 = str(uuid4())
        await conn.execute('''
        INSERT INTO monitors(id, user_id, name, url, mode, selector, frequency_seconds, config, created_at)
        VALUES($1,$2,$3,$4,$5,$6,$7,$8,now())
        ON CONFLICT (id) DO NOTHING
        ''', monitor1, SAMPLE_USER_ID, 'Example.com homepage', 'https://example.com', 'rendered', None, 300, json.dumps({}))

        await conn.execute('''
        INSERT INTO monitors(id, user_id, name, url, mode, selector, frequency_seconds, config, created_at)
        VALUES($1,$2,$3,$4,$5,$6,$7,$8,now())
        ON CONFLICT (id) DO NOTHING
        ''', monitor2, SAMPLE_USER_ID, 'Example.org page', 'https://example.org', 'rendered', None, 600, json.dumps({}))

        # sample integrations: webhook and telegram (placeholders)
        integ1 = str(uuid4())
        integ2 = str(uuid4())
        await conn.execute('''
        INSERT INTO integrations(id, user_id, type, name, config, is_active, created_at)
        VALUES($1,$2,$3,$4,$5,true,now())
        ON CONFLICT (id) DO NOTHING
        ''', integ1, SAMPLE_USER_ID, 'webhook', 'Test Webhook', json.dumps({'url': 'http://requestbin.net/r/your-bin'}))

        await conn.execute('''
        INSERT INTO integrations(id, user_id, type, name, config, is_active, created_at)
        VALUES($1,$2,$3,$4,$5,true,now())
        ON CONFLICT (id) DO NOTHING
        ''', integ2, SAMPLE_USER_ID, 'telegram', 'TG Bot (test)', json.dumps({'bot_token': 'BOT_TOKEN', 'chat_id': 'CHAT_ID'}))

        print('Seeded sample user, monitors, and integrations.')
        print('Sample user email: test@example.com (password not set)')
        print('Sample monitor ids: ', monitor1, monitor2)
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(run())
