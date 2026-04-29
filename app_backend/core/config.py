import os


class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agentguard.db")
    CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
    CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL")
    CLERK_ISSUER_URL = os.getenv("CLERK_ISSUER_URL") or os.getenv("CLERK_ISSUER")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    OAUTH_STATE_SECRET = os.getenv("OAUTH_STATE_SECRET")
    GMAIL_CONNECTOR_MODE = os.getenv("GMAIL_CONNECTOR_MODE", "mock")
    WORKSPACE_EMAIL_DOMAIN = os.getenv("WORKSPACE_EMAIL_DOMAIN", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


settings = Settings()
