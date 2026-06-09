import requests
from worker.celery_app import slack_webhook_url

def alert_slack(job_id: str, error: str, slack_webhook_url: str = slack_webhook_url) -> None:
    message = {
        "text": f"Dead Letter Alert for Job ID: {job_id}\nError: {error[-1000:]}"
    }

    requests.post(slack_webhook_url, json=message)
