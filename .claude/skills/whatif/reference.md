# Cartoon engine API (`engine/cartoon.py`)

Canvas 1080x1920, 30 fps, cairo. Episodes do `from cartoon import *`.

## Episode module
| name | meaning |
|---|---|
| `NAME` | folder for the voice cache (`out/cartoon/<NAME>`) |
| `TITLE, DESCRIPTION, TAGS` | written to `<video>.json` |
| `VOICE, SPEED` | Kokoro voice, e.g. `"am_michael", 1.05` |
| `HOOK = ("LINE 1", "LINE 2")` | on-screen hook text during the first beat (line 2 is big yellow) |
| `BEATS = [(beat, text, pause_after_s)]` | narration; timings come from the generated voice |
| `SCENES = [(beat, fn)]` | scene `fn(c, s)` is drawn from that beat's start until the next scene; first scene starts at frame 0 |
| `cams(Wt, B)` | optional `{beat: [(t, cx, cy, zoom), ...]}` — eased camera keys (centre point + zoom) |
| `sfx(Wt, B, put)` | optional `put(clip, t, gain)` sound cues |
| `CAPTION_Y` | optional caption height (default `H*0.72`) |

Every cut gets an automatic punch-in and whoosh. Captions (word-by-word, current word yellow) are automatic.

## Inside a scene: `s`
- `s.t` absolute time, `s.t0` scene start, `s.lt` time since scene start
- `s.W(beat, word, end=False)` → time the first word starting with `word` is spoken in `beat` (raises if not found)
- `s.P(start, dur=0.4)` → 0..1 progress (clamped); feed into `ease`, `ease_out`, `ease_back` (overshoot pop), `lerp`, `mix`

## Drawing helpers (all take the cairo context `c` first)
| helper | notes |
|---|---|
| `bg_space(c, t)`, `bg_sky(c, t)`, `bg_color(c, col)` | full-screen backgrounds (space has twinkling stars; sky has drifting clouds) |
| `earth(c, cx, cy, r, spin, bulge=0..1, bulge_ang, tilt, axis=True)` | spinning cartoon Earth, optional tidal bulge / tilted axis |
| `moon(c, cx, cy, r, face=None/"happy"/"shock"/"sad"/"sleep", t, alpha, crack=0..1)` | |
| `sun(c, cx, cy, r, t, face=...)`, `planet(c, cx, cy, r, col, ring_col, bands=[cols])` | |
| `leo(c, x, y, scale, pose, face, t, look=(dx,dy), wave=False)` | (x, y) = feet. Poses: idle point_up point_left point_right shock cheer think shrug cover. Faces: happy shock curious scared sad wow smirk worried |
| `crab(c, x, y, s, t, mood, walk)`, `coral(c, x, y, s, t, col, glow)`, `snowflake`, `cloud`, `star` | |
| `wave_band(c, y, t, col, amp, ...)` | animated sea surface filled down to `bottom` |
| `text(c, s, x, y, size, col, outline, alpha)`, `pop_text(c, s, x, y, size, p, col)` | bold outlined Inter |
| `label(c, s, x, y, size, bg, fg, p)` | pill label that pops in |
| `arrow(c, p0, p1, p, col)`, `ring(c, x, y, r, col, w, alpha)`, `dashed_circle`, `burst(c, x, y, lt, ...)` | |
| `counter(c, x, y, a, b, p, size, fmt, prefix, suffix)` | animated number |
| `circle(c, x, y, r, col)`, `path(c, pts)`, `blob(cx, cy, r, seed)`, `rrect`, `fs(c, col, ow)` | build custom shapes: `c.new_path(); path(c, pts); fs(c, col, 8)` |

Colours: `OUT` (outline), `WHITE YEL RED BLUE GREEN DKGREEN SAND PINK ORANGE GREY SKY PURPLE CYAN`, `rgb("#hex")`.

## Sounds
`sfx_pop(f)`, `sfx_whoosh(seed)`, `sfx_boom(f, dur)`, `sfx_ding(f)`, `sfx_shatter()`, `sfx_tick()`. Music bed and voice ducking are automatic.

## Style rules
Flat bright fills, dark `OUT` outlines (ow 6–10), one cel-shadow per round object, no thin lines or tiny text
(min ~40 px), at most 2–3 things moving at once, and the subject of each sentence must be on screen while it's spoken.
