"""Enqueue a run_monitor Celery task via API trigger endpoint.

Usage:
  python enqueue_run.py <monitor_id>

Requires API_URL env var (default http://localhost:8000)
"""
import os
import sys
import httpx

API_URL = os.getenv('API_URL', 'http://localhost:8000')

async def main(monitor_id):
    async with httpx.AsyncClient() as client:
        r = await client.post(f'{API_URL}/monitors/{monitor_id}/run')
        print('enqueue status', r.status_code, r.text)

if __name__ == '__main__':
    import asyncio
    if len(sys.argv) < 2:
        print('Usage: python enqueue_run.py <monitor_id>')
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
