"""
CodeLens AI - Webhook Handler
External CI/CD system webhook integration
"""
import hashlib
import hmac
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Webhook event handler for external CI/CD systems"""

    def __init__(self, secret: Optional[str] = None):
        self.secret = secret

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature (HMAC)"""
        if not self.secret:
            logger.warning("Webhook secret not configured, skipping signature verification")
            return True
        if not signature:
            return False
        expected = hmac.new(
            self.secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    def parse_github_event(self, event_type: str, payload: dict) -> dict:
        """Parse GitHub webhook event"""
        if event_type == "pull_request":
            return self._parse_pull_request(payload)
        elif event_type == "push":
            return self._parse_push(payload)
        elif event_type == "workflow_run":
            return self._parse_workflow_run(payload)
        return {"type": event_type, "raw": payload}

    def _parse_pull_request(self, payload: dict) -> dict:
        """Parse GitHub PR event"""
        pr = payload.get("pull_request", {})
        action = payload.get("action", "")
        return {
            "type": "pull_request",
            "action": action,
            "pr_number": pr.get("number"),
            "pr_title": pr.get("title"),
            "pr_body": pr.get("body"),
            "head_sha": pr.get("head", {}).get("sha"),
            "base_branch": pr.get("base", {}).get("ref"),
            "head_branch": pr.get("head", {}).get("ref"),
            "author": pr.get("user", {}).get("login"),
            "url": pr.get("html_url"),
            "is_draft": pr.get("draft", False),
        }

    def _parse_push(self, payload: dict) -> dict:
        """Parse GitHub push event"""
        return {
            "type": "push",
            "ref": payload.get("ref"),
            "before": payload.get("before"),
            "after": payload.get("after"),
            "commits_count": len(payload.get("commits", [])),
            "pusher": payload.get("pusher", {}).get("name"),
            "repository": payload.get("repository", {}).get("full_name"),
        }

    def _parse_workflow_run(self, payload: dict) -> dict:
        """Parse GitHub workflow_run event"""
        wr = payload.get("workflow_run", {})
        return {
            "type": "workflow_run",
            "run_id": wr.get("id"),
            "run_name": wr.get("name"),
            "conclusion": wr.get("conclusion"),
            "status": wr.get("status"),
            "head_sha": wr.get("head_sha"),
            "event": wr.get("event"),
        }


# Global webhook handler (secret loaded from env)
webhook_handler = WebhookHandler()
