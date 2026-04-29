from typing import Any


SENSITIVE_KEY_PARTS = ["authorization", "api_key", "token", "secret", "password"]
SECRET_REFERENCE_KEYS = {"secret_name", "username_secret", "password_secret", "allowed_secrets"}


def redact_sensitive_data(data: Any) -> Any:
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            key_text = str(key).lower()
            if key_text in SECRET_REFERENCE_KEYS:
                redacted[key] = redact_sensitive_data(value)
            elif any(part in key_text for part in SENSITIVE_KEY_PARTS):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_sensitive_data(value)
        return redacted
    if isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    return data
