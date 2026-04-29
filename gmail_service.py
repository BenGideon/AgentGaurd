import base64
from email.mime.text import MIMEText
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def get_gmail_service():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


def create_draft(to: str, subject: str, body: str) -> dict:
    service = get_gmail_service()
    return create_draft_with_service(service, to=to, subject=subject, body=body)


def create_draft_with_access_token(access_token: str, to: str, subject: str, body: str) -> dict:
    creds = Credentials(token=access_token, scopes=SCOPES)
    service = build("gmail", "v1", credentials=creds)
    return create_draft_with_service(service, to=to, subject=subject, body=body)


def create_draft_with_service(service, to: str, subject: str, body: str) -> dict:
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    response = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )

    return {
        "draft_id": response.get("id"),
        "response": response,
    }
