"""
CodeLens AI - Audit Logging Module
Records all API operations for compliance and security auditing.
"""
import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Literal
from pathlib import Path


# ─── Configuration ───────────────────────────────────────────────

AUDIT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "codelens_audit.db")

# Retention: 90 days default for enterprise compliance
AUDIT_RETENTION_DAYS = int(os.getenv("CODELENS_AUDIT_RETENTION_DAYS", "90"))


# ─── Database Setup ──────────────────────────────────────────────

def get_audit_db() -> sqlite3.Connection:
    """Get audit database connection"""
    conn = sqlite3.connect(AUDIT_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_audit_db():
    """Initialize audit logging database tables"""
    conn = get_audit_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id INTEGER,
            user_email TEXT,
            action TEXT NOT NULL,
            resource TEXT NOT NULL,
            resource_id TEXT,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            status_code INTEGER,
            ip_address TEXT,
            user_agent TEXT,
            request_body TEXT,
            response_body TEXT,
            duration_ms INTEGER,
            team_id INTEGER,
            metadata TEXT
        )
    """)

    # Indexes for common queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id, timestamp)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action, timestamp)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_team ON audit_logs(team_id, timestamp)
    """)

    conn.commit()
    conn.close()


# ─── Audit Log Entry ────────────────────────────────────────────

def log_audit(
    action: str,
    resource: str,
    method: str,
    path: str,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    resource_id: Optional[str] = None,
    status_code: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_body: Optional[str] = None,
    response_body: Optional[str] = None,
    duration_ms: Optional[int] = None,
    team_id: Optional[int] = None,
    metadata: Optional[dict] = None,
):
    """
    Record an audit log entry.
    
    Args:
        action: Action performed (e.g., 'analyze', 'login', 'create_team')
        resource: Resource type (e.g., 'analysis', 'auth', 'team')
        method: HTTP method
        path: Request path
        user_id: Authenticated user ID
        user_email: User email
        resource_id: Specific resource identifier
        status_code: HTTP response status code
        ip_address: Client IP address
        user_agent: Client user agent
        request_body: Sanitized request body
        response_body: Sanitized response body
        duration_ms: Request duration in milliseconds
        team_id: Associated team ID
        metadata: Additional metadata as JSON
    """
    # Sanitize sensitive data
    sanitized_body = _sanitize_body(request_body) if request_body else None

    conn = get_audit_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO audit_logs (
            timestamp, user_id, user_email, action, resource, resource_id,
            method, path, status_code, ip_address, user_agent,
            request_body, response_body, duration_ms, team_id, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        user_id,
        user_email,
        action,
        resource,
        resource_id,
        method,
        path,
        status_code,
        ip_address,
        user_agent,
        sanitized_body,
        None,  # response_body kept null to avoid size issues
        duration_ms,
        team_id,
        json.dumps(metadata) if metadata else None,
    ))

    conn.commit()
    conn.close()


def _sanitize_body(body: str) -> str:
    """Remove sensitive fields from request body"""
    if not body:
        return body
    sensitive_keys = {
        "password", "token", "access_token", "refresh_token",
        "secret", "api_key", "authorization", "x_hub_signature",
        "credit_card", "ssn", "private_key",
    }
    try:
        data = json.loads(body)
        if isinstance(data, dict):
            for key in list(data.keys()):
                if any(sk in key.lower() for sk in sensitive_keys):
                    data[key] = "[REDACTED]"
        return json.dumps(data, ensure_ascii=False)[:4000]
    except (json.JSONDecodeError, TypeError):
        return body[:4000]


# ─── Query Audit Logs ───────────────────────────────────────────

def query_audit_logs(
    user_id: Optional[int] = None,
    team_id: Optional[int] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """
    Query audit logs with filters.
    
    Returns dict with 'logs' list and 'total' count.
    """
    conn = get_audit_db()
    cursor = conn.cursor()

    conditions = []
    params = []

    if user_id is not None:
        conditions.append("user_id = ?")
        params.append(user_id)

    if team_id is not None:
        conditions.append("team_id = ?")
        params.append(team_id)

    if action:
        conditions.append("action = ?")
        params.append(action)

    if resource:
        conditions.append("resource = ?")
        params.append(resource)

    if start_date:
        conditions.append("timestamp >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("timestamp <= ?")
        params.append(end_date)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Count total
    cursor.execute(f"SELECT COUNT(*) as cnt FROM audit_logs WHERE {where_clause}", params)
    total = cursor.fetchone()["cnt"]

    # Fetch logs
    cursor.execute(f"""
        SELECT * FROM audit_logs
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """, params + [limit, offset])

    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {"logs": logs, "total": total, "limit": limit, "offset": offset}


def export_audit_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    format: Literal["json", "csv"] = "json",
) -> str:
    """
    Export audit logs as JSON or CSV string.
    """
    conn = get_audit_db()
    cursor = conn.cursor()

    conditions = []
    params = []

    if start_date:
        conditions.append("timestamp >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("timestamp <= ?")
        params.append(end_date)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    cursor.execute(f"""
        SELECT * FROM audit_logs
        WHERE {where_clause}
        ORDER BY timestamp DESC
    """, params)

    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if format == "csv":
        if not logs:
            return "timestamp,user_email,action,resource,method,path,status_code,ip_address\n"
        headers = list(logs[0].keys())
        lines = [",".join(headers)]
        for log in logs:
            lines.append(",".join(str(log.get(h, "")) for h in headers))
        return "\n".join(lines)

    # JSON
    return json.dumps({"audit_logs": logs, "exported_at": datetime.utcnow().isoformat()}, ensure_ascii=False, indent=2)


# ─── Middleware ─────────────────────────────────────────────────

class AuditMiddleware:
    """
    Starlette middleware to automatically log all API requests.
    """

    def __init__(self, app, excluded_paths: Optional[set] = None):
        self.app = app
        self.excluded_paths = excluded_paths or {"/health", "/docs", "/openapi.json", "/redoc"}

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in self.excluded_paths:
            await self.app(scope, receive, send)
            return

        # Skip non-API paths
        if not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        import time
        start_time = time.perf_counter()

        # Extract client info
        client_ip = None
        user_agent = None
        headers = dict(scope.get("headers", []))
        for k, v in headers.items():
            if k == b"x-forwarded-for":
                client_ip = v.decode().split(",")[0].strip()
            elif k == b"user-agent":
                user_agent = v.decode()

        client_ip = client_ip or scope.get("client", [None])[0]

        # Extract user from JWT (if present)
        user_id = None
        user_email = None
        authorization = headers.get(b"authorization", b"").decode()
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            try:
                from .auth import decode_token
                payload = decode_token(token)
                user_id = int(payload.get("sub", 0)) or None
                user_email = payload.get("email")
            except Exception:
                pass

        # Read request body
        request_body = None
        if scope.get("method") in ("POST", "PUT", "PATCH"):
            body = await self._get_body(receive)
            request_body = body

        # Process request
        status_code = 500
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        await self.app(scope, receive, send_wrapper)

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Determine action/resource from path
        action, resource, resource_id = _parse_path_for_audit(path)

        log_audit(
            action=action,
            resource=resource,
            method=scope.get("method", "UNKNOWN"),
            path=path,
            user_id=user_id,
            user_email=user_email,
            resource_id=resource_id,
            status_code=status_code,
            ip_address=client_ip,
            user_agent=user_agent,
            request_body=request_body,
            duration_ms=duration_ms,
        )

    async def _get_body(self, receive) -> Optional[str]:
        """Read request body"""
        body = b""
        while True:
            message = await receive()
            if message["type"] == "http.request":
                body += message.get("body", b"")
            if not message.get("more_body"):
                break
        try:
            return body.decode("utf-8", errors="replace")
        except Exception:
            return None


def _parse_path_for_audit(path: str) -> tuple:
    """Parse API path to extract action, resource, and resource_id"""
    parts = path.strip("/").split("/")

    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "v1":
        resource_parts = parts[2:]
        resource = resource_parts[0] if resource_parts else "unknown"
        resource_id = resource_parts[1] if len(resource_parts) > 1 else None
        action = f"{resource}.{'.'.join(resource_parts[1:])}" if len(resource_parts) > 1 else resource
        return action, resource, resource_id

    return "unknown", "unknown", None


# ─── Cleanup ────────────────────────────────────────────────────

def cleanup_old_audit_logs():
    """Remove audit logs older than retention period"""
    conn = get_audit_db()
    cursor = conn.cursor()
    cutoff = (datetime.utcnow() - timedelta(days=AUDIT_RETENTION_DAYS)).isoformat()
    cursor.execute("DELETE FROM audit_logs WHERE timestamp < ?", (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


# Initialize on module load
init_audit_db()
