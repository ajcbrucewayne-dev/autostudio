---
name: darkhistory
description: Turn a dark-history story into a finished, verified vertical Short in the parchment / living-manuscript style. Use when the user types /darkhistory <topic>, or asks for a Dark History video/episode.
---

# /darkhistory <topic>

Makes one 1080x1920 Short (45–65 s): aged parchment, ink drawings that draw themselves, red ink only for death and
danger, expressive ink characters, narrator `bm_george`. Free and offline (cairo + Kokoro + numpy + ffmpeg).
Library: `engine/parchment.py`. Template episode (copy it): `engine/parch_dancing.py`.

**Stop at the two checkpoints** and wait for the user.

## 1. Research
- If no topic was given, propose 3 lesser-known stories. Search the web for each and say honestly how widely it's
  already covered — prefer lesser-known ones.
- Collect facts from at least 2 sources. Disputed claims (death tolls, legends) must be hedged in narration
  ("it's said", "some accounts"). Keep the source list.

## 2. Script  → CHECKPOINT 1
- **Frame 1 = the most dramatic image, already drawn** (no blank paper), plus on-screen hook text (big red line +
  smaller ink line) that works on mute. No cute or smiling faces in the hook.
- First sentence = the shocking fact (a number, a death, an absurd decision). Never open with a date.
- Then a turn ("And it all started with one woman.") where everything else un-draws and the camera pushes in.
- 9–11 beats; one visual change every ~2 s; a short **Impact** beat near the end (what changed because of it).
- End with a question, and rebuild the frame-1 image so the loop is seamless.
- Show a beat table (beat | narration | drawing | sound) with sources; **wait for approval**.

## 3. Build
- Copy `engine/parch_dancing.py` to `engine/parch_<slug>.py`; replace `BEATS`, `STAMPS`, the plate functions,
  `PLATES`, `cams()`, the `tableau()` hook image and `build_audio()` cues. Change the voice cache name in `main()`.
- Characters: `figure(ink, x, y_feet, h, pose, p, kind="woman"|"man"|"skeleton", alpha, rot, expr, t, var)` with
  `dance_pose(...)` / `STAND` poses and expressions `neutral happy trance tired pain fear dead smug sad think`.
- Scenery and props: `ground, house, cathedral, sun(face=False), moon, mountain, chapel, shoe, wheat, skull, eye,
  drip, tally, note`, plus `ink.stroke / fill / hatch / circle / text / dot` for anything new (draw it in the plate
  function with tapered strokes and hatching, never flat cartoon fills).
- Time everything to words with `Wt(beat, word)` and reveal with `c.P(start, dur)` (draw-on 0→1).
- Red ink (`RED`) only for blood, death, danger and key numbers.

## 4. Stills  → fix until clean
`python3 engine/parch_<slug>.py <scratch>/stills --stills 0 <1–2 times per beat>` (first run makes the voice and
prints beat times). Tile into one contact sheet and look at it: frame 1 full and dramatic, captions not covering
faces, nothing cut off by camera zooms, stamps not colliding with drawings, text cues not late.

## 5. Render + verify
`python3 engine/parch_<slug>.py /home/user/darkhistory_<nn>_<slug>.mp4` (~15–20 min). Extract ~10 frames across
the video, check audio level with `volumedetect`, confirm the first and last frames match for the loop.

## 6. Deliver  → CHECKPOINT 2
Send the mp4 with SendUserFile; give duration, what was checked, a title / description / hashtags and the sources.
Commit locally. Never upload or publish unless the user asks.
