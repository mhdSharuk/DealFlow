import requests
import logging
from core.config import SLACK_WEBHOOK_URL

print(SLACK_WEBHOOK_URL)

def alert_slack(job_id: str, error: str, slack_webhook_url: str = SLACK_WEBHOOK_URL) -> None:
    try:
        logging.info("utils.slack_alert.alert_slack: Sending Slack alert for job_id=%s with error: %s", job_id, error[-200:])
        message = {
            "text": f"Dead Letter Alert for Job ID: {job_id}\nError: {error[-1000:]}"
        }

        requests.post(slack_webhook_url, json=message)
        logging.info("utils.slack_alert.alert_slack: Slack alert sent for job_id=%s", job_id)
    except Exception as exc:
        logging.error("utils.slack_alert.alert_slack: Failed to send Slack alert for job_id=%s: %s", job_id, exc)
