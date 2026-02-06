"""
YouTube Authentication - OAuth2 authentication for YouTube API
"""

import os
import json
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from src.utils.logger import get_logger

logger = get_logger(__name__)


class YouTubeAuth:
    """
    Handles OAuth2 authentication for YouTube Data API v3.

    Setup Instructions:
    1. Go to Google Cloud Console: https://console.cloud.google.com/
    2. Create a new project (or select existing)
    3. Enable "YouTube Data API v3"
    4. Go to Credentials -> Create Credentials -> OAuth 2.0 Client ID
    5. Select "Desktop application"
    6. Download the JSON file
    7. Save it as "config/client_secrets.json"
    """

    # Scopes required for uploading
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.force-ssl"
    ]

    def __init__(
        self,
        client_secrets_file: str = "config/client_secrets.json",
        token_file: str = "config/youtube_token.json"
    ):
        """
        Initialize YouTube authentication.

        Args:
            client_secrets_file: Path to OAuth2 client secrets JSON
            token_file: Path to store/load OAuth2 tokens
        """
        self.client_secrets_file = client_secrets_file
        self.token_file = token_file
        self.credentials: Optional[Credentials] = None
        self.youtube = None

        logger.info("YouTubeAuth initialized")

    def authenticate(self) -> bool:
        """
        Authenticate with YouTube API.
        Will prompt for browser authentication if no valid token exists.

        Returns:
            True if authentication successful
        """
        try:
            self.credentials = self._load_credentials()

            if self.credentials and self.credentials.valid:
                logger.info("Using existing valid credentials")
                return self._build_service()

            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                logger.info("Refreshing expired credentials")
                self.credentials.refresh(Request())
                self._save_credentials()
                return self._build_service()

            # Need new authentication
            logger.info("Starting new OAuth2 authentication flow")
            return self._new_authentication()

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def _load_credentials(self) -> Optional[Credentials]:
        """Load credentials from token file"""
        token_path = Path(self.token_file)

        if token_path.exists():
            try:
                with open(token_path, "r") as f:
                    token_data = json.load(f)

                return Credentials(
                    token=token_data.get("token"),
                    refresh_token=token_data.get("refresh_token"),
                    token_uri=token_data.get("token_uri"),
                    client_id=token_data.get("client_id"),
                    client_secret=token_data.get("client_secret"),
                    scopes=token_data.get("scopes")
                )
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")

        return None

    def _save_credentials(self) -> None:
        """Save credentials to token file"""
        token_path = Path(self.token_file)
        token_path.parent.mkdir(parents=True, exist_ok=True)

        token_data = {
            "token": self.credentials.token,
            "refresh_token": self.credentials.refresh_token,
            "token_uri": self.credentials.token_uri,
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
            "scopes": self.credentials.scopes
        }

        with open(token_path, "w") as f:
            json.dump(token_data, f, indent=2)

        logger.info(f"Credentials saved to: {token_path}")

    def _new_authentication(self) -> bool:
        """Run new OAuth2 authentication flow"""
        secrets_path = Path(self.client_secrets_file)

        if not secrets_path.exists():
            logger.error(
                f"Client secrets file not found: {self.client_secrets_file}\n"
                "Please follow the setup instructions:\n"
                "1. Go to Google Cloud Console\n"
                "2. Create OAuth2 credentials\n"
                "3. Download and save as 'config/client_secrets.json'"
            )
            return False

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(secrets_path),
                scopes=self.SCOPES
            )

            # Run local server for OAuth callback
            self.credentials = flow.run_local_server(
                port=8080,
                prompt="consent",
                authorization_prompt_message="Please visit this URL to authorize: {url}",
                success_message="Authentication successful! You can close this window."
            )

            self._save_credentials()
            return self._build_service()

        except Exception as e:
            logger.error(f"OAuth flow failed: {e}")
            return False

    def _build_service(self) -> bool:
        """Build YouTube API service"""
        try:
            self.youtube = build(
                "youtube",
                "v3",
                credentials=self.credentials
            )
            logger.info("YouTube API service built successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to build YouTube service: {e}")
            return False

    def get_service(self):
        """
        Get authenticated YouTube service.

        Returns:
            YouTube API service object or None
        """
        if not self.youtube:
            self.authenticate()
        return self.youtube

    def get_channel_info(self) -> dict:
        """
        Get authenticated user's channel information.

        Returns:
            Channel information dict
        """
        if not self.youtube:
            if not self.authenticate():
                return {}

        try:
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics",
                mine=True
            )
            response = request.execute()

            if response.get("items"):
                channel = response["items"][0]
                return {
                    "id": channel["id"],
                    "title": channel["snippet"]["title"],
                    "description": channel["snippet"].get("description", ""),
                    "subscribers": channel["statistics"].get("subscriberCount", 0),
                    "videos": channel["statistics"].get("videoCount", 0)
                }

        except Exception as e:
            logger.error(f"Failed to get channel info: {e}")

        return {}

    def is_authenticated(self) -> bool:
        """Check if currently authenticated"""
        return self.credentials is not None and self.credentials.valid

    def revoke(self) -> bool:
        """Revoke current credentials"""
        try:
            if self.credentials:
                # Revoke token
                import requests
                requests.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": self.credentials.token},
                    headers={"content-type": "application/x-www-form-urlencoded"}
                )

            # Delete token file
            token_path = Path(self.token_file)
            if token_path.exists():
                token_path.unlink()

            self.credentials = None
            self.youtube = None

            logger.info("Credentials revoked")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke credentials: {e}")
            return False


# CLI interface for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YouTube Auth CLI")
    parser.add_argument("--auth", action="store_true", help="Authenticate with YouTube")
    parser.add_argument("--info", action="store_true", help="Get channel info")
    parser.add_argument("--revoke", action="store_true", help="Revoke credentials")

    args = parser.parse_args()

    auth = YouTubeAuth()

    if args.auth:
        print("\n=== YouTube Authentication ===\n")
        if auth.authenticate():
            print("Authentication successful!")
            info = auth.get_channel_info()
            if info:
                print(f"\nChannel: {info['title']}")
                print(f"Subscribers: {info['subscribers']}")
                print(f"Videos: {info['videos']}")
        else:
            print("Authentication failed!")

    elif args.info:
        if auth.authenticate():
            info = auth.get_channel_info()
            if info:
                print(f"\nChannel: {info['title']}")
                print(f"ID: {info['id']}")
                print(f"Subscribers: {info['subscribers']}")
                print(f"Videos: {info['videos']}")
            else:
                print("Failed to get channel info")

    elif args.revoke:
        if auth.revoke():
            print("Credentials revoked successfully")
        else:
            print("Failed to revoke credentials")

    else:
        parser.print_help()
