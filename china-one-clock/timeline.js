// One timeline for picture, voice, score and checks (TREATMENT.md). Times in film seconds.
import { clamp, lerp, seg, ss, eio, monotone, track } from '/core/lib.js';

export const DUR = 43.0;
export const BPM = 96, BEAT = 60 / BPM;            // grid starts at GRID0
export const GRID0 = 3.9;

// narration: line id, start; text as spoken is in lines.json, subtitles here (digits)
export const LINES = [
  ['l01', 0.30, ['China should have 5 time zones.']],
  ['l02', 2.55, ['It uses one.']],
  ['l03', 4.40, ["It's more than 5,000 km wide,", 'and the sun takes 4 hours to cross it.']],
  ['l04', 10.10, ['Until 1949, China really had five.']],
  ['l05', 13.90, ['Then the whole country was put on Beijing time.']],
  ['l06', 17.80, ['On a winter morning,', 'the sun rises over Shanghai before seven.']],
  ['l07', 22.00, ['Then it keeps going west, for hours,']],
  ['l08', 24.60, ['until it finally reaches Kashgar,', 'after 10 a.m.']],
  ['l09', 29.40, ['So many people there quietly keep their own clock,', 'two hours behind.']],
  ['l10', 34.60, ['One country. One clock.']],
  ['l11', 37.10, ['Would you wait until ten for the sunrise?']],
];
export const HITS = {
  one: 3.27,            // "It uses ONE"
  ruler: 4.6, fourH: 7.9,
  zones39: 10.4, beijing: 15.55,
  rewind: 17.0, shanghai: 20.1, kashgar: 26.0, ten: 26.9,
  clocks: 30.6, end1: 34.6, endCard: 39.9,
};
export const SHOTS = [
  { id: 'hook', t0: 0, t1: 3.9 }, { id: 'width', t0: 3.9, t1: 10.0 }, { id: 'history', t0: 10.0, t1: 17.0 },
  { id: 'sweep', t0: 17.0, t1: 28.0 }, { id: 'kashgar', t0: 28.0, t1: 34.4 }, { id: 'end', t0: 34.4, t1: DUR },
];

// ---- the story clock (Beijing time, hours) ----
const clockKeys = monotone([
  [0, 10.5], [16.9, 10.5],                         // shots 1–3: a late winter morning, the far west still at dawn
  [17.7, 6.30],                                    // the rewind
  [HITS.shanghai, 6.80],                           // 06:48 sunrise over Shanghai
  [22.5, 7.90], [24.6, 9.05], [HITS.ten, 10.20],   // accelerates west, brakes into Kashgar 10:12
  [34.4, 10.42], [DUR, 10.70],
]);
export const CLOCK = t => clockKeys(t);

// ---- sunrise geometry, shared with the page (21 Dec) ----
export function sunriseLon(lat, utcH, dec, eqt) {
  const ph = lat * Math.PI / 180, c = (Math.sin(-0.833 * Math.PI / 180) - Math.sin(ph) * Math.sin(dec)) / (Math.cos(ph) * Math.cos(dec));
  const H = -Math.acos(clamp(c, -1, 1)) * 180 / Math.PI;
  return ((H + 180) * 4 - eqt - utcH * 60) / 4;
}

// ---- camera: [t, [lon, lat, ln(d), tilt, head, aperture]] ----
const camKeys = track([
  [0.0, [104.5, 33.0, Math.log(100), 38, 0, 0]],
  [3.9, [104.5, 33.2, Math.log(90), 40, 0, 0]],      // hook: slow push
  [6.5, [104.0, 32.5, Math.log(104), 42, -3, 0]],
  [10.0, [105.0, 33.0, Math.log(100), 42, -6, 0]],   // width: pull back + slow orbit
  [13.5, [107.0, 34.0, Math.log(92), 40, -4, 0]],
  [16.9, [109.0, 34.0, Math.log(88), 40, -2, 0]],    // history: creep toward Beijing
]);
const endKeys = track([
  [28.0, [77.0, 39.3, Math.log(17), 60, -62, 0]],
  [34.4, [76.4, 39.4, Math.log(12.5), 58, -72, 0]],   // crane down on Kashgar
  [39.0, [96.0, 36.5, Math.log(80), 52, -20, 0]],
  [DUR, [104.5, 33.5, Math.log(98), 40, 0, 0]],       // crane up and back: all of China
]);
export function CAM(t, sun) {
  let c;
  if (t < 16.9) c = camKeys(t);
  else if (t < 28.0) {
    // the sweep: target rides just ahead (west) of the real dawn line at a drifting latitude
    const lat = lerp(31.5, 39.3, ss(seg(t, 18.5, 26.6)));
    const dawn = sunriseLon(lat, CLOCK(t) - 8, sun.dec, sun.eqt);
    const lon = Math.min(121.0, dawn + .6);
    const into = ss(seg(t, 16.9, 18.4));                  // fly from the history framing into the low track
    const lowD = lerp(24, 30, Math.sin(Math.PI * seg(t, 18.4, 26.6))), brake = ss(seg(t, 26.2, 28.0));
    const a = camKeys(16.9), b = [lon, lat, Math.log(lerp(lowD, 17, brake)), lerp(62, 60, brake), lerp(-8, -62, brake), 0];
    c = a.map((v, i) => lerp(v, b[i], into));
    if (t >= 26.6) { const e = endKeys(28.0); c = c.map((v, i) => lerp(v, e[i], ss(seg(t, 26.6, 28.0)))); }
  } else c = endKeys(t);
  return { lon: c[0], lat: c[1], d: Math.exp(c[2]), tilt: c[3], head: c[4], ap: c[5] };
}

// cities lit by the dawn (computed sunrise, Beijing time, 21 Dec: FACTS.md)
export const CITIES = [
  { name: 'SHANGHAI', lon: 121.47, lat: 31.23 }, { name: 'BEIJING', lon: 116.40, lat: 39.90 }, { name: 'CHENGDU', lon: 104.07, lat: 30.66 },
  { name: 'LHASA', lon: 91.17, lat: 29.65 }, { name: 'URUMQI', lon: 87.62, lat: 43.83 }, { name: 'KASHGAR', lon: 75.99, lat: 39.47 },
];
