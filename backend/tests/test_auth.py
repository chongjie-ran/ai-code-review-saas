"""
CodeLens AI - Auth Tests
Tests for password hashing (bcrypt), JWT tokens
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)


class TestPasswordHashing:
    """TD-01: bcrypt password hashing tests"""

    @pytest.mark.asyncio
    async def test_hash_password_returns_string(self):
        """hash_password should return a string hash"""
        result = await hash_password("testpassword123")
        assert isinstance(result, str)
        assert result != "testpassword123"
        assert len(result) > 20

    @pytest.mark.asyncio
    async def test_hash_password_different_each_time(self):
        """Same password should produce different hashes (salt)"""
        password = "samepassword"
        hash1 = await hash_password(password)
        hash2 = await hash_password(password)
        assert hash1 != hash2, "bcrypt should produce unique salts per hash"

    @pytest.mark.asyncio
    async def test_verify_password_correct(self):
        """verify_password should return True for correct password"""
        password = "MySecureP@ssw0rd!"
        hashed = await hash_password(password)
        result = await verify_password(password, hashed)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_password_incorrect(self):
        """verify_password should return False for wrong password"""
        password = "CorrectPassword"
        wrong = "WrongPassword"
        hashed = await hash_password(password)
        result = await verify_password(wrong, hashed)
        assert result is False

    @pytest.mark.asyncio
    async def test_hash_password_special_chars(self):
        """Passwords with special characters should hash correctly"""
        password = 'P@$$w0rd!#$%^&*()_+-=[]{}|;:\'",./<>?'
        hashed = await hash_password(password)
        result = await verify_password(password, hashed)
        assert result is True


class TestJWT:
    """TD-03: JWT token tests"""

    def test_create_access_token(self):
        """create_access_token should return a JWT string"""
        token = create_access_token(user_id=1, email="test@example.com")
        assert isinstance(token, str)
        assert len(token) > 20
        assert token.count(".") == 2  # JWT has 3 parts

    def test_decode_token(self):
        """decode_token should decode a valid token"""
        token = create_access_token(user_id=42, email="user@example.com")
        decoded = decode_token(token)
        # JWT library may return sub as string or int
        assert str(decoded["sub"]) == "42"
        assert decoded["email"] == "user@example.com"

    def test_decode_token_invalid(self):
        """decode_token should raise for invalid token"""
        with pytest.raises(Exception):
            decode_token("invalid.token.here")

    def test_token_contains_expiration(self):
        """Token should contain expiration claim"""
        token = create_access_token(user_id=1, email="user@example.com")
        decoded = decode_token(token)
        assert "exp" in decoded


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
