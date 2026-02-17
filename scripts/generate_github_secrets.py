"""
Helper script to generate properly formatted GitHub Secrets for YouTube upload.

Usage:
    python scripts/generate_github_secrets.py

This script reads config/youtube_token.json and config/client_secrets.json,
validates them, and prints the base64-encoded values to store in GitHub Secrets.

GitHub Secret names required:
  YOUTUBE_TOKEN           <- content of config/youtube_token.json (raw JSON or base64)
  YOUTUBE_CLIENT_SECRETS  <- content of config/client_secrets.json (raw JSON or base64)
"""

import json
import base64
from pathlib import Path


def validate_and_encode(file_path: str, required_fields: list) -> tuple[bool, str]:
    path = Path(file_path)
    if not path.exists():
        print(f"  ERROR: File not found: {file_path}")
        return False, ""

    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  ERROR: Invalid JSON in {file_path}: {e}")
        return False, ""

    missing = [k for k in required_fields if not data.get(k)]
    if missing:
        print(f"  WARNING: Missing fields in {file_path}: {missing}")

    # Re-serialize to compact single-line JSON (safest for secrets)
    compact_json = json.dumps(data, separators=(",", ":"))
    b64_value = base64.b64encode(compact_json.encode("utf-8")).decode("ascii")
    return True, b64_value


def main():
    print("=" * 60)
    print("GitHub Secrets Generator for YouTube Upload")
    print("=" * 60)

    print("\n[1] YOUTUBE_TOKEN (config/youtube_token.json)")
    ok, b64 = validate_and_encode(
        "config/youtube_token.json",
        ["token", "refresh_token", "token_uri", "client_id", "client_secret"]
    )
    if ok:
        print("  Status: VALID")
        print(f"\n  Store this as YOUTUBE_TOKEN in GitHub Secrets:\n")
        print(f"  {b64}\n")
    else:
        print("  Fix the token file first (run: python -m src.youtube.auth --auth)")

    print("\n[2] YOUTUBE_CLIENT_SECRETS (config/client_secrets.json)")
    ok2, b64_2 = validate_and_encode(
        "config/client_secrets.json",
        ["installed", "web"]  # one of these should exist
    )
    # client_secrets has nested structure, just check it loaded
    path = Path("config/client_secrets.json")
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            compact_json = json.dumps(data, separators=(",", ":"))
            b64_2 = base64.b64encode(compact_json.encode("utf-8")).decode("ascii")
            print("  Status: VALID")
            print(f"\n  Store this as YOUTUBE_CLIENT_SECRETS in GitHub Secrets:\n")
            print(f"  {b64_2}\n")
        except json.JSONDecodeError as e:
            print(f"  ERROR: Invalid JSON: {e}")
    else:
        print("  ERROR: File not found. Download from Google Cloud Console.")

    print("=" * 60)
    print("Steps to update GitHub Secrets:")
    print("  1. Go to your repo -> Settings -> Secrets and variables -> Actions")
    print("  2. Update YOUTUBE_TOKEN with the base64 value above")
    print("  3. Update YOUTUBE_CLIENT_SECRETS with the base64 value above")
    print("  4. Re-run the GitHub Actions workflow")
    print("=" * 60)


if __name__ == "__main__":
    main()
