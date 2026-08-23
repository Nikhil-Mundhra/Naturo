"""Create a Google Ads OAuth refresh token for a desktop application."""

from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = ["https://www.googleapis.com/auth/adwords"]
CLIENT_SECRET_FILE = Path(__file__).with_name("client_secret.json")


def main() -> None:
    if not CLIENT_SECRET_FILE.exists():
        raise SystemExit(
            f"Missing {CLIENT_SECRET_FILE.name}. Download the desktop OAuth JSON "
            "and save it next to this script."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
    credentials = flow.run_local_server(port=0, prompt="consent")
    print("\nAdd this value to GOOGLE_ADS_REFRESH_TOKEN in .env:\n")
    print(credentials.refresh_token)


if __name__ == "__main__":
    main()