"""Run this ON YOUR OWN COMPUTER once per YouTube channel to get its refresh token.

  pip install google-auth-oauthlib
  python get_youtube_token.py client_secret.json

A browser opens -> pick the Google account -> choose the CHANNEL (brand account) -> Allow.
Copy the printed refresh token into GitHub Secrets as YT_REFRESH_TOKEN_WHATIF / _SKITS / _DARKHISTORY.
"""
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], ["https://www.googleapis.com/auth/youtube.upload"])
creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
print("\nREFRESH TOKEN:\n" + creds.refresh_token)
