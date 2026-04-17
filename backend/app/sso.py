"""
CodeLens AI - SSO/SAML/OIDC Support Module
Enterprise Single Sign-On support for SAML 2.0 and OpenID Connect.
"""
import os
import hashlib
import secrets
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Literal
from dataclasses import dataclass
from fastapi import HTTPException


# ─── IdP Configuration ──────────────────────────────────────────

@dataclass
class SAMLIdPConfig:
    """SAML Identity Provider configuration"""
    entity_id: str
    sso_url: str
    slo_url: Optional[str]
    x509_cert: str
    label: str = "SSO"
    enabled: bool = True


@dataclass
class OIDCConfig:
    """OpenID Connect Provider configuration"""
    issuer: str
    client_id: str
    client_secret: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    label: str = "OIDC"
    enabled: bool = True


# Environment-based IdP config loader
def load_idp_configs() -> tuple[list[SAMLIdPConfig], list[OIDCConfig]]:
    """
    Load IdP configurations from environment variables.
    
    SAML config via CODELENS_SAML_* vars (comma-separated for multiple)
    OIDC config via CODELENS_OIDC_* vars
    """
    saml_configs = []
    oidc_configs = []

    # Load SAML configs
    saml_entity_ids = os.getenv("CODELENS_SAML_ENTITY_IDS", "")
    if saml_entity_ids:
        for i, entity_id in enumerate(saml_entity_ids.split(",")):
            entity_id = entity_id.strip()
            if not entity_id:
                continue
            prefix = f"CODELENS_SAML_{i+1}_"
            config = SAMLIdPConfig(
                entity_id=entity_id,
                sso_url=os.getenv(f"{prefix}SSO_URL", ""),
                slo_url=os.getenv(f"{prefix}SLO_URL"),
                x509_cert=os.getenv(f"{prefix}X509_CERT", ""),
                label=os.getenv(f"{prefix}LABEL", f"SSO {i+1}"),
                enabled=os.getenv(f"{prefix}ENABLED", "true").lower() == "true",
            )
            if config.sso_url:
                saml_configs.append(config)

    # Load OIDC configs
    oidc_issuers = os.getenv("CODELENS_OIDC_ISSUERS", "")
    if oidc_issuers:
        for i, issuer in enumerate(oidc_issuers.split(",")):
            issuer = issuer.strip()
            if not issuer:
                continue
            prefix = f"CODELENS_OIDC_{i+1}_"
            config = OIDCConfig(
                issuer=issuer,
                client_id=os.getenv(f"{prefix}CLIENT_ID", ""),
                client_secret=os.getenv(f"{prefix}CLIENT_SECRET", ""),
                authorization_endpoint=os.getenv(f"{prefix}AUTH_ENDPOINT", ""),
                token_endpoint=os.getenv(f"{prefix}TOKEN_ENDPOINT", ""),
                userinfo_endpoint=os.getenv(f"{prefix}USERINFO_ENDPOINT", ""),
                jwks_uri=os.getenv(f"{prefix}JWKS_URI", ""),
                label=os.getenv(f"{prefix}LABEL", f"OIDC {i+1}"),
                enabled=os.getenv(f"{prefix}ENABLED", "true").lower() == "true",
            )
            if config.client_id and config.authorization_endpoint:
                oidc_configs.append(config)

    return saml_configs, oidc_configs


# ─── SSO Provider Registry ─────────────────────────────────────

class SSOProviderRegistry:
    """
    Central registry for SSO providers (SAML + OIDC).
    Provides login URLs and token exchange for enterprise SSO.
    """

    def __init__(self):
        self.saml_providers: list[SAMLIdPConfig] = []
        self.oidc_providers: list[OIDCConfig] = []
        self._state_store: dict[str, dict] = {}  # in-memory state storage
        self._nonce_store: dict[str, datetime] = {}
        self._load_configs()

    def _load_configs(self):
        self.saml_providers, self.oidc_providers = load_idp_configs()

    def reload(self):
        """Reload IdP configurations from environment"""
        self._load_configs()

    def list_providers(self) -> list[dict]:
        """List all configured SSO providers"""
        providers = []
        for p in self.saml_providers:
            providers.append({
                "type": "saml",
                "id": hashlib.md5(p.entity_id.encode()).hexdigest()[:8],
                "label": p.label,
                "entity_id": p.entity_id,
                "enabled": p.enabled,
            })
        for p in self.oidc_providers:
            providers.append({
                "type": "oidc",
                "id": hashlib.md5(p.issuer.encode()).hexdigest()[:8],
                "label": p.label,
                "issuer": p.issuer,
                "enabled": p.enabled,
            })
        return providers

    # ─── SAML Methods ─────────────────────────────────────────────

    def get_saml_login_url(self, provider_id: str, redirect_uri: str) -> dict:
        """
        Generate SAML AuthnRequest and return redirect URL.
        Returns {url, request_id, state} for SP-initiated SSO.
        """
        for p in self.saml_providers:
            pid = hashlib.md5(p.entity_id.encode()).hexdigest()[:8]
            if pid == provider_id and p.enabled:
                request_id = f"_{secrets.token_hex(16)}"
                issue_instant = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

                # Build simplified SAML AuthnRequest
                # In production, use python3-saml or similar library
                params = {
                    "SAMLRequest": self._build_saml_authn_request(request_id, issue_instant, redirect_uri, p),
                    "RelayState": redirect_uri,
                }
                login_url = f"{p.sso_url}?{urllib.parse.urlencode(params)}"

                # Store state
                self._state_store[request_id] = {
                    "provider": provider_id,
                    "relay_state": redirect_uri,
                    "created_at": datetime.utcnow().isoformat(),
                    "type": "saml",
                }

                return {
                    "redirect_url": login_url,
                    "request_id": request_id,
                    "provider_label": p.label,
                }

        raise HTTPException(status_code=404, detail="SSO provider not found")

    def _build_saml_authn_request(self, request_id: str, issue_instant: str, callback: str, config: SAMLIdPConfig) -> str:
        """Build a simplified SAML AuthnRequest (deflated, base64 encoded)"""
        import base64
        import zlib

        sp_entity_id = os.getenv("CODELENS_SP_ENTITY_ID", "https://codelens.ai")
        request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:AuthnRequest
    xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    ID="{request_id}"
    Version="2.0"
    IssueInstant="{issue_instant}"
    AssertionConsumerServiceURL="{callback}"
    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
    <saml:Issuer>{sp_entity_id}</saml:Issuer>
    <samlp:NameIDPolicy Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress" AllowCreate="true"/>
</samlp:AuthnRequest>"""

        compressed = zlib.compress(request.encode())[2:-4]  # deflate
        return base64.b64encode(compressed).decode()

    def handle_saml_response(self, saml_response: str, relay_state: str) -> dict:
        """
        Process SAML Response and return user info.
        
        In production, validate signature against IdP certificate,
        check timestamps, audience, recipient, etc.
        This simplified version extracts basic user info.
        """
        import base64
        import xml.etree.ElementTree as ET

        try:
            decoded = base64.b64decode(saml_response).decode("utf-8")
            root = ET.fromstring(decoded)

            # Parse SAML assertion
            ns = {
                "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
                "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
            }

            # Extract user attributes
            name_id_elem = root.find(".//saml:NameID", ns)
            name_id = name_id_elem.text if name_id_elem is not None else None

            attributes = {}
            for attr in root.findall(".//saml:Attribute", ns):
                attr_name = attr.get("Name", "")
                attr_value = attr.find("saml:AttributeValue", ns)
                if attr_value is not None:
                    attributes[attr_name] = attr_value.text

            email = attributes.get("email") or attributes.get(
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
            ) or name_id

            return {
                "provider": "saml",
                "email": email,
                "name": attributes.get("displayName") or attributes.get(
                    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
                ),
                "external_id": name_id,
                "attributes": attributes,
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid SAML response: {e}")

    # ─── OIDC Methods ─────────────────────────────────────────────

    def get_oidc_login_url(self, provider_id: str, redirect_uri: str) -> dict:
        """Generate OIDC authorization URL with PKCE"""
        for p in self.oidc_providers:
            pid = hashlib.md5(p.issuer.encode()).hexdigest()[:8]
            if pid == provider_id and p.enabled:
                state = secrets.token_hex(16)
                nonce = secrets.token_hex(16)
                code_verifier = secrets.token_urlsafe(64)
                code_challenge = self._pkce_challenge(code_verifier)

                self._state_store[state] = {
                    "provider": provider_id,
                    "nonce": nonce,
                    "relay_state": redirect_uri,
                    "code_verifier": code_verifier,
                    "created_at": datetime.utcnow().isoformat(),
                    "type": "oidc",
                }

                params = {
                    "client_id": p.client_id,
                    "response_type": "code",
                    "redirect_uri": redirect_uri,
                    "scope": "openid email profile",
                    "state": state,
                    "nonce": nonce,
                    "code_challenge": code_challenge,
                    "code_challenge_method": "S256",
                }
                login_url = f"{p.authorization_endpoint}?{urllib.parse.urlencode(params)}"

                return {
                    "redirect_url": login_url,
                    "state": state,
                    "provider_label": p.label,
                }

        raise HTTPException(status_code=404, detail="OIDC provider not found")

    def _pkce_challenge(self, verifier: str) -> str:
        """Generate PKCE code challenge from verifier"""
        import hashlib
        import base64
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")

    async def exchange_oidc_code(self, provider_id: str, code: str, state: str, redirect_uri: str) -> dict:
        """Exchange OIDC authorization code for tokens"""
        import httpx

        # Validate state
        stored = self._state_store.get(state)
        if not stored or stored.get("type") != "oidc":
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        # Find provider
        provider = None
        for p in self.oidc_providers:
            pid = hashlib.md5(p.issuer.encode()).hexdigest()[:8]
            if pid == provider_id:
                provider = p
                break

        if not provider:
            raise HTTPException(status_code=404, detail="OIDC provider not found")

        code_verifier = stored["code_verifier"]

        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                provider.token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "client_id": provider.client_id,
                    "client_secret": provider.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "code_verifier": code_verifier,
                },
            )

        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_resp.text}")

        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        id_token = tokens.get("id_token")

        # Fetch userinfo
        async with httpx.AsyncClient() as client:
            user_resp = await client.get(
                provider.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
            )

        userinfo = user_resp.json() if user_resp.status_code == 200 else {}

        # Clean up state
        del self._state_store[state]

        return {
            "provider": "oidc",
            "email": userinfo.get("email"),
            "name": userinfo.get("name"),
            "sub": userinfo.get("sub"),
            "access_token": access_token,
            "id_token": id_token,
        }


# ─── SSO User Provisioning ───────────────────────────────────────

def provision_sso_user(provider: str, email: str, name: Optional[str] = None, external_id: Optional[str] = None) -> dict:
    """
    Provision or retrieve a user from SSO login.
    Creates a local account if one doesn't exist for the SSO identity.
    """
    from .auth import get_db, create_access_token

    if not email:
        raise HTTPException(status_code=400, detail="Email not available from SSO provider")

    conn = get_db()
    cursor = conn.cursor()

    # Check for existing user
    cursor.execute("SELECT id, email, name, created_at FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if user:
        conn.close()
        token_data = create_access_token(user["id"], user["email"])
        return {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "created_at": user["created_at"],
            },
            **token_data,
        }

    # Create new user from SSO identity
    now = datetime.utcnow().isoformat()
    # Generate random password (SSO-only user)
    random_password = secrets.token_hex(32)

    cursor.execute(
        "INSERT INTO users (email, password_hash, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (email, hashlib.sha256(random_password.encode()).hexdigest(), name, now, now)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    token_data = create_access_token(user_id, email)

    # Log audit
    try:
        from .audit import log_audit
        log_audit(
            action="sso_provision",
            resource="auth",
            method="POST",
            path="/api/v1/auth/sso/callback",
            user_email=email,
            metadata={"provider": provider, "external_id": external_id},
        )
    except Exception:
        pass

    return {
        "user": {
            "id": user_id,
            "email": email,
            "name": name,
            "created_at": now,
        },
        **token_data,
    }


# Global registry instance
sso_registry = SSOProviderRegistry()
