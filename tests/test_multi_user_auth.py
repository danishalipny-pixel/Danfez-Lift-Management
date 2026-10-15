import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.auth_token import PasswordResetToken, RevokedToken

client = TestClient(app)

# Generate unique run ID so tests are completely isolated and idempotent
RUN_ID = uuid.uuid4().hex[:6]
USER1_EMAIL = f"sarah_{RUN_ID}@example.com"
USER2_EMAIL = f"kyle_{RUN_ID}@example.com"

def test_multi_user_registration():
    """Verify multiple distinct user accounts can register independently."""
    # User 1
    resp1 = client.post("/api/auth/register", json={
        "email": USER1_EMAIL,
        "password": "SarahSafePass2026!",
        "full_name": "Sarah Connor",
        "phone": "+1 555-0101",
        "role": "technician"
    })
    assert resp1.status_code == 201, resp1.text
    data1 = resp1.json()
    assert data1["email"] == USER1_EMAIL
    assert data1["role"] == "technician"

    # User 2
    resp2 = client.post("/api/auth/register", json={
        "email": USER2_EMAIL,
        "password": "KyleSafePass2026!",
        "full_name": "Kyle Reese",
        "phone": "+1 555-0102",
        "role": "viewer"
    })
    assert resp2.status_code == 201, resp2.text
    data2 = resp2.json()
    assert data2["email"] == USER2_EMAIL
    assert data2["role"] == "viewer"

    # Test Duplicate Registration is Blocked
    dup_resp = client.post("/api/auth/register", json={
        "email": USER1_EMAIL,
        "password": "AnotherPassword2026!",
        "full_name": "Sarah Connor Duplicate"
    })
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"].lower()


def test_public_registration_cannot_escalate_to_admin():
    """Verify public self-service registration blocks unauthorized admin role requests."""
    sneaky_email = f"sneaky_{RUN_ID}@example.com"
    resp = client.post("/api/auth/register", json={
        "email": sneaky_email,
        "password": "AdminAttemptPass2026!",
        "full_name": "Sneaky User",
        "role": "admin"
    })
    assert resp.status_code == 201
    # System must downgrade requested admin role to viewer
    assert resp.json()["role"] == "viewer"


def test_login_and_remember_me():
    """Test login with and without remember_me."""
    # Standard login
    resp_std = client.post("/api/auth/login", json={
        "email": USER1_EMAIL,
        "password": "SarahSafePass2026!",
        "remember_me": False
    })
    assert resp_std.status_code == 200
    data_std = resp_std.json()
    assert "access_token" in data_std

    # Remember-Me login (30 days)
    resp_rem = client.post("/api/auth/login", json={
        "email": USER1_EMAIL,
        "password": "SarahSafePass2026!",
        "remember_me": True
    })
    assert resp_rem.status_code == 200
    data_rem = resp_rem.json()
    assert "access_token" in data_rem


def test_session_revocation_on_logout():
    """Test that logging out revokes the JWT session so it cannot be reused."""
    login_resp = client.post("/api/auth/login", json={
        "email": USER2_EMAIL,
        "password": "KyleSafePass2026!"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Verify token works
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == USER2_EMAIL

    # Call logout
    logout_resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200
    assert "revoked" in logout_resp.json()["message"].lower()

    # Calling /me again with the revoked token must fail with 401
    revoked_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert revoked_resp.status_code == 401
    assert "revoked" in revoked_resp.json()["detail"].lower()


def test_password_recovery_single_use_tokens():
    """Test forgot-password token generation, usage, and single-use enforcement."""
    # 1. Request forgot password
    forgot_resp = client.post("/api/auth/forgot-password", json={
        "email": USER1_EMAIL
    })
    assert forgot_resp.status_code == 200
    data = forgot_resp.json()
    token = data.get("reset_token")
    assert token is not None, "In dev/test environment, reset_token should be returned"

    # 2. Reset password using the valid token
    new_password = "SarahNewStrongPassword2026!"
    reset_resp = client.post("/api/auth/reset-password", json={
        "token": token,
        "new_password": new_password
    })
    assert reset_resp.status_code == 200
    assert "successfully" in reset_resp.json()["message"].lower()

    # 3. Attempting to REUSE the same token must fail
    reuse_resp = client.post("/api/auth/reset-password", json={
        "token": token,
        "new_password": "YetAnotherPassword2026!"
    })
    assert reuse_resp.status_code == 400
    assert "already been used" in reuse_resp.json()["detail"].lower()

    # 4. Old password must now fail
    old_login = client.post("/api/auth/login", json={
        "email": USER1_EMAIL,
        "password": "SarahSafePass2026!"
    })
    assert old_login.status_code == 401

    # 5. New password must succeed
    new_login = client.post("/api/auth/login", json={
        "email": USER1_EMAIL,
        "password": new_password
    })
    assert new_login.status_code == 200


def test_password_recovery_expired_token():
    """Test that an expired password reset token is rejected."""
    # Create an artificially expired token in the database
    db = SessionLocal()
    user = db.query(User).filter(User.email == USER1_EMAIL).first()
    expired_token_str = f"artificially-expired-token-{uuid.uuid4().hex}"
    expired_token = PasswordResetToken(
        user_id=user.id,
        token=expired_token_str,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
        is_used=False
    )
    db.add(expired_token)
    db.commit()
    db.close()

    resp = client.post("/api/auth/reset-password", json={
        "token": expired_token_str,
        "new_password": "NeverAppliedPassword2026!"
    })
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


def test_email_verification_workflow():
    """Test verification token validation and resend endpoints."""
    # Find user token from database
    db = SessionLocal()
    user = db.query(User).filter(User.email == USER2_EMAIL).first()
    verification_token = user.verification_token
    db.close()

    assert verification_token is not None

    # Call verify-email endpoint
    verify_resp = client.get(f"/api/auth/verify-email?token={verification_token}")
    assert verify_resp.status_code == 200
    assert "verified" in verify_resp.json()["message"].lower()

    # Verify status in database
    db = SessionLocal()
    updated_user = db.query(User).filter(User.email == USER2_EMAIL).first()
    assert updated_user.is_verified is True
    db.close()

    # Call verify again -> token was consumed/cleared, so it should report 400 invalid/expired
    reverify_resp = client.get(f"/api/auth/verify-email?token={verification_token}")
    assert reverify_resp.status_code == 400
    assert "invalid or expired" in reverify_resp.json()["detail"].lower()


def test_profile_update():
    """Test updating user profile full_name and telephone."""
    login_resp = client.post("/api/auth/login", json={
        "email": USER2_EMAIL,
        "password": "KyleSafePass2026!"
    })
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]

    update_resp = client.put(
        "/api/auth/profile",
        json={"full_name": "Sergeant Kyle Reese", "phone": "+1 555-9999"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["full_name"] == "Sergeant Kyle Reese"
    assert updated_data["phone"] == "+1 555-9999"

    # Confirm via /me
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.json()["full_name"] == "Sergeant Kyle Reese"


def test_google_oauth_unconfigured_response():
    """Verify unconfigured Google OAuth gracefully returns 501 Not Implemented with instructions."""
    resp = client.post("/api/auth/google", json={"credential": "fake-google-id-token"})
    assert resp.status_code == 501
    assert "google_client_id" in resp.json()["detail"].lower()


def test_auth_html_routes():
    """Verify all auth HTML pages are served correctly."""
    pages = [
        "/login.html",
        "/register.html",
        "/forgot-password.html",
        "/reset-password.html",
        "/verify-email.html",
        "/profile.html"
    ]
    for page in pages:
        resp = client.get(page)
        assert resp.status_code == 200, f"Page {page} failed with {resp.status_code}"
        assert "DANFEZ TECH HOUSE" in resp.text
