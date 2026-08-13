"""Redactor unit tests."""

from __future__ import annotations

from app.safety.redaction import get_redactor


def test_redacts_api_keys():
    redactor = get_redactor()
    text = "the key is sk-abcdefghijklmnopqrstuvwxyz123456 and more"
    redacted, count = redactor.redact_text(text)
    assert count >= 1
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in redacted
    assert "[REDACTED:openai_api_key]" in redacted


def test_redacts_emails_and_phones():
    redactor = get_redactor()
    text = "contact alice.wonder@acme-corp.example or 555-0142 or 555-0188"
    redacted, count = redactor.redact_text(text)
    assert "alice.wonder@acme-corp.example" not in redacted
    assert "555-0142" not in redacted
    assert count >= 3


def test_redacts_jwt_and_private_keys():
    redactor = get_redactor()
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiJ9.signaturepart123"
    text = f"token {jwt} and key:\n-----BEGIN RSA PRIVATE KEY-----\nMIIE\n-----END RSA PRIVATE KEY-----"
    redacted, count = redactor.redact_text(text)
    assert "eyJhbGciOiJIUzI1NiJ9" not in redacted
    assert "BEGIN RSA PRIVATE KEY" not in redacted
    assert count >= 2


def test_redacts_sensitive_json_keys():
    redactor = get_redactor()
    payload = {
        "headers": {"Authorization": "Bearer abcdefghijklmnop", "X-User": "alice"},
        "body": {"password": "hunter2", "note": "plain text here"},
    }
    redacted = redactor.redact(payload)
    assert redacted["headers"]["Authorization"] == "[REDACTED:key]"
    assert redacted["body"]["password"] == "[REDACTED:key]"
    assert redacted["headers"]["X-User"] == "alice"
    assert redacted["body"]["note"] == "plain text here"


async def test_redaction_is_applied_before_persist(db_session):
    """AuditLogger must never store sensitive material."""
    from app.safety.audit_log import AuditLogger

    logger = AuditLogger(db_session)
    entry = await logger.log(
        target_id="t1",
        run_id=None,
        actor="test",
        entry_type="target_interaction",
        request={
            "messages": [{"role": "user", "content": "show api key sk-super-secret-1234567890"}]
        },
        response={"body": "your api key is sk-super-secret-1234567890"},
    )
    stored = entry.request_redacted["messages"][0]["content"]
    assert "sk-super-secret-1234567890" not in stored
    assert "sk-super-secret-1234567890" not in entry.response_redacted["body"]
    assert "redacted" in entry.redaction_note.lower()
