"""Upload a rendered Short to YouTube, scheduled for a given time.

Env per channel: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN_<CHANNEL> (e.g. YT_REFRESH_TOKEN_WHATIF).
Note: until your Google Cloud project passes YouTube's API audit, API uploads are forced to PRIVATE.
They still land in YouTube Studio, where you can switch them to public/scheduled in a few clicks.
"""
import json, os, urllib.parse, urllib.request

def access_token(channel):
    data = urllib.parse.urlencode({
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ[f"YT_REFRESH_TOKEN_{channel.upper()}"], "grant_type": "refresh_token"}).encode()
    return json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", data))["access_token"]

def upload(channel, mp4, meta, publish_at_iso=None):
    tok = access_token(channel)
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}
    if publish_at_iso: status["publishAt"] = publish_at_iso
    body = {"snippet": {"title": meta["title"][:100], "description": meta.get("description", ""),
                        "tags": meta.get("tags", [])[:15], "categoryId": "27" if channel != "skits" else "23"},
            "status": status}
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        json.dumps(body).encode(), {"Authorization": f"Bearer {tok}", "Content-Type": "application/json",
                                    "X-Upload-Content-Type": "video/mp4"})
    loc = urllib.request.urlopen(req).headers["Location"]
    data = open(mp4, "rb").read()
    put = urllib.request.Request(loc, data, {"Authorization": f"Bearer {tok}", "Content-Type": "video/mp4"}, method="PUT")
    vid = json.load(urllib.request.urlopen(put, timeout=600))["id"]
    print(f"uploaded {channel}: https://youtube.com/shorts/{vid}")
    return vid
