# CodeLens AI - Enterprise Deployment Guide

> **Version 1.0.0** | SOC2 / ISO27001 / HIPAA Ready

---

## Table of Contents

1. [Quick Start (Docker Compose)](#1-quick-start-docker-compose)
2. [Manual Deployment](#2-manual-deployment)
3. [Platform Deployment](#3-platform-deployment)
4. [SSO Configuration](#4-sso-configuration)
5. [Enterprise Features](#5-enterprise-features)
6. [Environment Variables](#6-environment-variables)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Quick Start (Docker Compose)

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Steps

```bash
# Clone the repository
git clone https://github.com/chongjie-ran/ai-code-review-saas.git
cd ai-code-review-saas

# Configure environment
cp .env.example .env
# Edit .env and set JWT_SECRET

# Build and start
docker-compose up -d

# Verify health
curl http://localhost:8090/health
```

**Result:** Backend at `http://localhost:8090`, Frontend at `http://localhost:3000`

### Stop

```bash
docker-compose down        # keep data
docker-compose down -v     # remove data volumes
```

---

## 2. Manual Deployment

### Backend (Python 3.12+)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment
export JWT_SECRET="your-super-secret-key-min-32-chars"
export CODELENS_RATE_LIMIT=100

# Run
python -m uvicorn app.main:app --host 0.0.0.0 --port 8090
```

### Frontend

The frontend is a static SPA. Build and serve with any HTTP server:

```bash
cd frontend
npm install
npm run build

# Serve with nginx
cp -r dist/* /var/www/codelens/
```

Or Python's built-in server (development only):
```bash
cd frontend/dist
python3 -m http.server 3000
```

---

## 3. Platform Deployment

### Render.com

**`render.yaml`** (in repository root):

```yaml
services:
  - type: web
    name: codelens-backend
    env: python
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: JWT_SECRET
        generateValue: true
      - key: PORT
        value: 8090
```

### Railway

```bash
# Connect GitHub repo
railway init
railway add --service backend
railway up
railway variable set JWT_SECRET=your-secret-key
```

### Railway (Frontend)

```bash
railway add --service frontend
railway up --service frontend
```

### Heroku

```bash
# Create Heroku app
heroku create codelens-backend

# Set buildpack for Python
heroku buildpacks:set heroku/python

# Set environment
heroku config:set JWT_SECRET=your-secret-key

# Deploy
git push heroku main
```

---

## 4. SSO Configuration

### SAML 2.0

Configure your SAML Identity Provider and set these environment variables:

```bash
CODELENS_SAML_ENTITY_IDS=https://idp.yourcompany.com/saml
CODELENS_SAML_1_SSO_URL=https://idp.yourcompany.com/saml/sso
CODELENS_SAML_1_X509_CERT=-----BEGIN CERTIFICATE-----\nMIID...\n-----END CERTIFICATE-----
CODELENS_SAML_1_LABEL=Company SSO
```

**Service Provider Entity ID:** `https://your-codelens-domain.com`

**Assertion Consumer Service URL:** `https://your-codelens-domain.com/api/v1/auth/saml/callback`

### OIDC (OpenID Connect)

```bash
CODELENS_OIDC_ISSUERS=https://accounts.google.com
CODELENS_OIDC_1_CLIENT_ID=your-client-id
CODELENS_OIDC_1_CLIENT_SECRET=your-client-secret
CODELENS_OIDC_1_AUTH_ENDPOINT=https://accounts.google.com/o/oauth2/v2/auth
CODELENS_OIDC_1_TOKEN_ENDPOINT=https://oauth2.googleapis.com/token
CODELENS_OIDC_1_USERINFO_ENDPOINT=https://openidconnect.googleapis.com/userinfo
CODELENS_OIDC_1_LABEL=Google Workspace
```

**Authorized Redirect URI:** `https://your-codelens-domain.com/api/v1/auth/oidc/callback`

### Testing SSO

```bash
# List available providers
curl http://localhost:8090/api/v1/auth/sso/providers

# Initiate SAML login
curl "http://localhost:8090/api/v1/auth/saml/login?provider_id=<ID>&redirect_uri=http://localhost:3000"
```

---

## 5. Enterprise Features

### 5.1 Audit Logging

All API operations are logged to `codelens_audit.db`.

```bash
# Query logs via API
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8090/api/v1/audit/logs?limit=50"

# Export as CSV
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8090/api/v1/audit/logs/export?format=csv" \
  -o audit.csv
```

Audit logs include:
- Timestamp, user, action, resource
- HTTP method, path, status code
- Client IP, user agent
- Request duration (ms)

**Retention:** 90 days (configurable via `AUDIT_RETENTION_DAYS`)

### 5.2 Compliance Reports

```bash
# SOC2 Report
curl -H "Authorization: Bearer <token>" \
  http://localhost:8090/api/v1/compliance/soc2 | python -m json.tool

# SOC2 HTML Report
open http://localhost:8090/api/v1/compliance/soc2/html

# ISO 27001 Report
open http://localhost:8090/api/v1/compliance/iso27001/html

# HIPAA Report
open http://localhost:8090/api/v1/compliance/hipaa/html
```

### 5.3 Rate Limiting

| Tier | Requests/min | Scope |
|------|-------------|-------|
| Anonymous | 20 | per IP |
| Free | 100 | per user |
| Pro | 1000 | per user |
| Enterprise | 10000 | per user |
| API (/analyze) | 100 | per user/IP |

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 45
```

### 5.4 AES-256 Encryption

Encrypt sensitive data at rest:

```bash
# Encrypt
curl -X POST -H "Authorization: Bearer <token>" \
  -d '{"plaintext":"my-secret-api-key"}' \
  http://localhost:8090/api/v1/enterprise/encrypt

# Decrypt
curl -X POST -H "Authorization: Bearer <token>" \
  -d '{"encrypted":"<base64-encrypted>"}' \
  http://localhost:8090/api/v1/enterprise/decrypt
```

Generate a 32-byte encryption key:
```python
python3 -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"
```

---

## 6. Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET` | ✅ | - | JWT signing secret (min 32 chars) |
| `WEBHOOK_SECRET` | For webhooks | - | GitHub webhook HMAC secret |
| `CODELENS_RATE_LIMIT` | No | 100 | Default rate limit (req/window) |
| `CODELENS_RATE_WINDOW` | No | 60 | Rate limit window (seconds) |
| `CODELENS_ANONYMOUS_LIMIT` | No | 20 | Anonymous rate limit |
| `CODELENS_AUDIT_RETENTION_DAYS` | No | 90 | Audit log retention |
| `CODELENS_ENCRYPTION_KEY` | No | derived | Base64 AES-256 key |
| `PORT` | No | 8090 | Backend port (Docker) |
| `FRONTEND_PORT` | No | 3000 | Frontend port (Docker) |

### SSO Variables

| Variable | Description |
|----------|-------------|
| `CODELENS_SAML_ENTITY_IDS` | Comma-separated SAML Entity IDs |
| `CODELENS_SAML_N_SSO_URL` | SAML SSO URL for provider N |
| `CODELENS_SAML_N_X509_CERT` | SAML IdP X509 certificate |
| `CODELENS_OIDC_ISSUERS` | Comma-separated OIDC issuers |
| `CODELENS_OIDC_N_CLIENT_ID` | OIDC client ID |
| `CODELENS_OIDC_N_CLIENT_SECRET` | OIDC client secret |
| `CODELENS_OIDC_N_AUTH_ENDPOINT` | OIDC authorization endpoint |
| `CODELENS_OIDC_N_TOKEN_ENDPOINT` | OIDC token endpoint |

---

## 7. Troubleshooting

### Backend won't start

```bash
# Check database
ls -la backend/codelens.db
ls -la backend/codelens_audit.db

# Verify Python version
python3 --version  # needs 3.12+

# Check dependencies
pip install -r backend/requirements.txt
```

### SSO not working

1. Verify IdP certificate is valid and properly formatted (PEM with `\n` for newlines)
2. Check `CODELENS_SAML_ENTITY_IDS` matches IdP entity ID exactly
3. Ensure Assertion Consumer Service URL is whitelisted in IdP

```bash
# Debug SSO config
curl http://localhost:8090/api/v1/auth/sso/providers | python -m json.tool
```

### Rate limit hitting

- Check `X-RateLimit-*` headers in response
- Reduce request frequency or upgrade tier
- Adjust limits in `rate_limiter.py`

### Audit logs missing

- Verify `codelens_audit.db` file exists and is writable
- Check disk space
- Run cleanup manually: `python3 -c "from app.audit import cleanup_old_audit_logs; print(cleanup_old_audit_logs())"`

---

## Security Checklist

- [ ] Set `JWT_SECRET` to a strong random value
- [ ] Enable HTTPS (reverse proxy with TLS termination)
- [ ] Configure firewall rules
- [ ] Set `AUDIT_RETENTION_DAYS` per compliance requirements
- [ ] For HIPAA: ensure database encryption and access controls
- [ ] For SOC2: configure SSO and enable all audit logging
- [ ] Regular security updates: `pip install -r requirements.txt --upgrade`

---

*Generated for CodeLens AI v1.0.0 Enterprise*
