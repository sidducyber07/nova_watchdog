"""Create a monitor via API: registers a user, logs in, and posts a monitor.

Usage: set API_URL env var (default http://localhost:8000)
"""
import os
import httpx

API_URL = os.getenv('API_URL', 'http://localhost:8000')
EMAIL = os.getenv('TEST_EMAIL', 'apiuser@example.com')
PASSWORD = os.getenv('TEST_PASSWORD', 'password')

async def main():
    async with httpx.AsyncClient() as client:
        # register (ignore error if exists)
        try:
            r = await client.post(f'{API_URL}/auth/register', json={'email': EMAIL, 'password': PASSWORD, 'full_name': 'API Test'})
            print('register', r.status_code)
        except Exception as e:
            print('register error', e)
        # login
        r = await client.post(f'{API_URL}/auth/login', json={'email': EMAIL, 'password': PASSWORD})
        if r.status_code != 200:
            print('login failed', r.text)
            return
        token = r.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}
        # create monitor
        payload = {'name': 'Health check - example.com', 'url': 'https://example.com', 'frequency_seconds': 300}
        r = await client.post(f'{API_URL}/monitors/', headers=headers, json=payload)
        print('create monitor', r.status_code, r.text)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
