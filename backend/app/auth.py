"""
CodeLens AI - Authentication Module
JWT-based user authentication
"""
import os
import sqlite3
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

# ─── Configuration ───────────────────────────────────────────────

# TD-03: JWT_SECRET must be set - no fallback to random value
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable must be set")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# TD-01: Password hashing with bcrypt (replaces insecure SHA256)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── Database Setup ──────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "codelens.db")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_auth_db():
    """Initialize authentication database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Teams table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
    """)
    
    # Team members table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            invited_at TEXT NOT NULL,
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(team_id, user_id)
        )
    """)
    
    conn.commit()
    conn.close()

# ─── Pydantic Models ─────────────────────────────────────────────

class UserRegister(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TeamCreate(BaseModel):
    name: str

class TeamInvite(BaseModel):
    email: str
    role: str = "member"  # owner, admin, member

class TeamMemberResponse(BaseModel):
    user_id: int
    email: str
    name: Optional[str]
    role: str
    invited_at: str

class TeamResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: str
    members: list[TeamMemberResponse] = []

# ─── Password Utilities ─────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash"""
    return pwd_context.verify(password, hashed)

# ─── JWT Utilities ──────────────────────────────────────────────

def create_access_token(user_id: int, email: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ─── Security Scheme ────────────────────────────────────────────

security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    """
    Dependency to get current authenticated user from JWT token.
    For optional auth, use get_optional_user instead.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_token(token)
    user_id = int(payload.get("sub"))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return dict(user)

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Optional[dict]:
    """Optional authentication - returns None if not authenticated"""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

# ─── Auth Endpoints ─────────────────────────────────────────────

def register_user(email: str, password: str, name: Optional[str] = None) -> dict:
    """Register a new user"""
    # Validate email format
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Validate password strength
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    now = datetime.utcnow().isoformat()
    password_hash = hash_password(password)
    
    cursor.execute(
        "INSERT INTO users (email, password_hash, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (email, password_hash, name, now, now)
    )
    conn.commit()
    
    user_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": user_id,
        "email": email,
        "name": name,
        "created_at": now,
    }

def login_user(email: str, password: str) -> dict:
    """Authenticate user and return token"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, email, password_hash, name, created_at FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(user["id"], user["email"])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "created_at": user["created_at"],
        }
    }

# ─── Team Management ────────────────────────────────────────────

def create_team(name: str, owner_id: int) -> dict:
    """Create a new team"""
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    
    # Create team
    cursor.execute(
        "INSERT INTO teams (name, owner_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (name, owner_id, now, now)
    )
    team_id = cursor.lastrowid
    
    # Add owner as admin member
    cursor.execute(
        "INSERT INTO team_members (team_id, user_id, role, invited_at) VALUES (?, ?, ?, ?)",
        (team_id, owner_id, "owner", now)
    )
    
    conn.commit()
    conn.close()
    
    return {
        "id": team_id,
        "name": name,
        "owner_id": owner_id,
        "created_at": now,
        "members": [{
            "user_id": owner_id,
            "role": "owner",
            "invited_at": now,
        }]
    }

def get_user_teams(user_id: int) -> list[dict]:
    """Get all teams a user belongs to"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.id, t.name as team_name, t.owner_id, t.created_at,
               tm.user_id, tm.role,
               u.email, u.name as user_name
        FROM teams t
        JOIN team_members tm ON t.id = tm.team_id
        JOIN users u ON tm.user_id = u.id
        WHERE tm.user_id = ?
        ORDER BY t.created_at DESC
    """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Group by team
    teams = {}
    for row in rows:
        team_id = row["id"]
        if team_id not in teams:
            teams[team_id] = {
                "id": team_id,
                "name": row["team_name"],
                "owner_id": row["owner_id"],
                "created_at": row["created_at"],
                "members": []
            }
        teams[team_id]["members"].append({
            "user_id": row["user_id"],
            "email": row["email"],
            "name": row["user_name"],
            "role": row["role"],
        })
    
    return list(teams.values())

def get_team(team_id: int, user_id: int) -> dict:
    """Get team details (only for members)"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check membership
    cursor.execute(
        "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
        (team_id, user_id)
    )
    membership = cursor.fetchone()
    if not membership:
        conn.close()
        raise HTTPException(status_code=403, detail="Not a team member")
    
    # Get team
    cursor.execute("SELECT id, name, owner_id, created_at FROM teams WHERE id = ?", (team_id,))
    team = cursor.fetchone()
    if not team:
        conn.close()
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get members
    cursor.execute("""
        SELECT tm.user_id, tm.role, tm.invited_at, u.email, u.name
        FROM team_members tm
        JOIN users u ON tm.user_id = u.id
        WHERE tm.team_id = ?
    """, (team_id,))
    
    members = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "id": team["id"],
        "name": team["name"],
        "owner_id": team["owner_id"],
        "created_at": team["created_at"],
        "members": members,
    }

def invite_to_team(team_id: int, inviter_id: int, email: str, role: str) -> dict:
    """Invite a user to team"""
    if role not in ["admin", "member"]:
        raise HTTPException(status_code=400, detail="Role must be admin or member")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check inviter is owner or admin
    cursor.execute(
        "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
        (team_id, inviter_id)
    )
    inviter = cursor.fetchone()
    if not inviter or inviter["role"] not in ["owner", "admin"]:
        conn.close()
        raise HTTPException(status_code=403, detail="Only owner or admin can invite")
    
    # Find user by email
    cursor.execute("SELECT id, email, name FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    user_id = user["id"]
    
    # Check if already member
    cursor.execute(
        "SELECT id FROM team_members WHERE team_id = ? AND user_id = ?",
        (team_id, user_id)
    )
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="User is already a team member")
    
    # Add member
    now = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO team_members (team_id, user_id, role, invited_at) VALUES (?, ?, ?, ?)",
        (team_id, user_id, role, now)
    )
    conn.commit()
    conn.close()
    
    return {
        "user_id": user_id,
        "email": email,
        "role": role,
        "invited_at": now,
    }

def remove_from_team(team_id: int, remover_id: int, target_user_id: int) -> bool:
    """Remove a user from team"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check remover is owner or admin
    cursor.execute(
        "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
        (team_id, remover_id)
    )
    remover = cursor.fetchone()
    if not remover or remover["role"] not in ["owner", "admin"]:
        conn.close()
        raise HTTPException(status_code=403, detail="Only owner or admin can remove members")
    
    # Cannot remove owner
    cursor.execute("SELECT owner_id FROM teams WHERE id = ?", (team_id,))
    team = cursor.fetchone()
    if team and team["owner_id"] == target_user_id:
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot remove team owner")
    
    # Remove member
    cursor.execute(
        "DELETE FROM team_members WHERE team_id = ? AND user_id = ?",
        (team_id, target_user_id)
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0

# Initialize database on module load
init_auth_db()
