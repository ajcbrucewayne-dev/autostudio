# AutoStudio: 3 animated Shorts channels on autopilot ($0)

Channels: `whatif` (space/science What Ifs), `skits` (Blob Life comedy), `darkhistory` (Dark Pages).
Every day GitHub Actions writes scripts (Gemini free tier), voices them (Kokoro offline TTS), animates them,
and uploads them to YouTube scheduled for the next day (2 per channel = 6/day by default; change the repo variable VIDEOS_PER_CHANNEL).

- Render one script by hand: `python engine/render.py scripts/whatif/001_moon_vanished.json`
- Put hand-written scripts in `scripts/<channel>/queue/`. They are used before AI-written ones.
- Rendered MP4s are attached to each Actions run as "videos" for Instagram Reels / TikTok.
