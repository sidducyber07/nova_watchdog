import os
from celery import Celery
from kombu import Queue, Exchange

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery("nova_watchdog", broker=REDIS_URL, backend=REDIS_URL)

# Define queues and exchanges
default_exchange = Exchange("nova", type="direct")
app.conf.task_queues = (
    Queue("monitoring", default_exchange, routing_key="monitoring"),
    Queue("screenshots", default_exchange, routing_key="screenshots"),
    Queue("ai", default_exchange, routing_key="ai"),
    Queue("notifications", default_exchange, routing_key="notifications"),
    Queue("dead_letter", default_exchange, routing_key="dead_letter"),
)

app.conf.task_default_queue = "monitoring"
app.conf.task_default_exchange = "nova"
app.conf.task_default_routing_key = "monitoring"
app.conf.imports = ("app.tasks",)

# Retry and timeouts
app.conf.broker_transport_options = {"visibility_timeout": 3600}
app.conf.task_annotations = {"*": {"rate_limit": "1000/s"}}

class BaseTaskWithDLQ(app.Task):
    autoretry_for = (Exception,)
    max_retries = 3
    retry_backoff = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # When max retries exhausted, forward to dead_letter queue
        try:
            if self.request.retries >= self.max_retries:
                app.send_task("dead_letter_handler", args=[self.name, args, kwargs, str(exc)], queue="dead_letter")
        except Exception:
            pass

app.Task = BaseTaskWithDLQ
