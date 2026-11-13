---
name: whatif
description: Turn a "What if...?" topic into a finished, verified vertical Short for the What If channel (bright cartoon style with Leo). Use when the user types /whatif <topic>, or asks to make a What If video/episode.
---

# /whatif <topic>

Makes one finished 1080x1920 Short (30–60 s) in the channel's **bright cartoon style** (style A) with the narrator
`am_michael` and the mascot **Leo**, using only free, offline tools (cairo + Kokoro TTS + numpy audio + ffmpeg).
Engine: `engine/cartoon.py`. API reference: `reference.md` in this folder. Template episode: `engine/episodes/whatif_moon.py`.

Work through the steps in order. **Stop at the two checkpoints** and wait for the user.

## 1. Vet the idea
- If no topic was given, propose 3 from `scripts/whatif/queue` (or new ones) and let the user pick.
- Channel rule for the first episodes: **only ideas that have never been made as a notable video.** Search the web
  (e.g. `"what if <idea>" video`, `<idea> youtube`) and report honestly what exists. Never claim "never made" without searching.
- Collect 3–5 **verifiable facts** with sources. Every number in the script must come from a source; soften anything
  uncertain ("could", "about", "it's said"). Keep the source list for step 6.

## 2. Write the script  → CHECKPOINT 1
Hook rules (learned the hard way):
- **Frame 1 must already show the most dramatic image** — never a blank or calm screen. Something is breaking,
  exploding, flooding or about to happen in the first second.
- **First sentence = the shocking consequence**, not a date or setup. Max ~8 words before the payoff.
- Add on-screen `HOOK` text (2 short lines) so it works on mute.
- A new visual event every 1.5–2 s; 5–7 beats; total 30–60 s.
- End with a question that invites comments, and ideally a last frame that loops back into frame 1.
Write the beats as a table: beat name | narration | what's on screen | sound. Show it with the fact sources and
**wait for approval** before animating.

## 3. Build the episode
- Copy `engine/episodes/whatif_moon.py` to `engine/episodes/<slug>.py` and rewrite it: `NAME`, `TITLE`,
  `DESCRIPTION`, `TAGS`, `HOOK`, `BEATS`, one draw function per scene, `SCENES`, `cams()`, `sfx()`.
- Draw with the helpers in `reference.md` (earth, moon, sun, planet, leo, crab, coral, wave_band, label, arrow,
  pop_text, counter, burst, ring...). If the topic needs a new object (volcano, honey, cloud city...), write a small
  draw function **in the episode file** in the same style: flat fills, `OUT` outlines (ow≈8–10), a cel-shadow,
  bright palette. Put it in `engine/cartoon.py` only if other episodes will reuse it.
- Time everything to narration with `s.W(beat, word)` and `s.P(start, dur)` — never hard-coded seconds.
- Leo appears in most scenes with a fitting face (`happy, shock, curious, scared, sad, wow, smirk, worried`) and pose
  (`idle, point_up, point_left, point_right, shock, cheer, think, shrug, cover`). Keep him in the bottom ~25 %
  (feet at y≈2060–2080, scale 0.7–0.8) so the caption (y≈1382) never covers his face.
- Keep main subjects between y≈250 and y≈1300; captions sit at y≈1382.

## 4. Check stills  → fix until clean
```bash
python3 engine/cartoon.py engine/episodes/<slug>.py <scratch>/stills --stills 0 1.5 <one or two times per beat>
```
The first run also generates the voice and prints the beat start times. Tile the PNGs into one contact sheet, **look
at it**, and fix before rendering: blank/weak frame 1, captions covering faces or subjects, things cut off by the
camera, text overlapping, objects drawn in the wrong order, word cues firing late.

## 5. Render + verify
```bash
python3 engine/cartoon.py engine/episodes/<slug>.py /home/user/whatif_<nn>_<slug>.mp4
```
About 1–3 minutes of rendering per 10 s of video on 4 CPUs. Then extract ~10 frames with ffmpeg across the whole video,
look at them, and check audio with `ffmpeg -af volumedetect` (max_volume should be about -1 to -6 dB). Confirm
frame 1 shows the hook.

## 6. Deliver  → CHECKPOINT 2
Send the mp4 to the user with SendUserFile. In the message give: duration, what you checked, a ready-to-paste
title / description / 5–8 hashtags (also written to `<output>.json`), and the fact sources. Commit the episode file
locally. Never upload or publish anywhere unless the user asks.
