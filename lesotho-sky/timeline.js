// One timeline for picture, voice, score and checks (TREATMENT.md). Film seconds.
import { clamp, lerp, seg, ss, monotone, track } from '/core/lib.js';
export const DUR = 55.0;
export const LINES = [
  ['l01', 0.25, ["This country's lowest point is higher", "than Britain's highest mountain."]],
  ['l02', 4.55, ["And it's completely surrounded", 'by another country.']],
  ['l03', 7.75, ['This is Lesotho,', 'a kingdom of mountains inside South Africa.']],
  ['l04', 12.25, ['Watch what happens if the sea starts to rise.']],
  ['l05', 15.55, ['At 1,000 metres,', 'almost half of South Africa is underwater.']],
  ['l06', 20.2, ['At 1,400, about four-fifths is gone,', "and Lesotho still hasn't got wet."]],
  ['l07', 25.75, ['No country on Earth has a higher lowest point.', 'And its peak tops 3,400 metres.']],
  ['l08', 32.3, ['So why is it a separate country?', 'In 1868, its king asked Britain', 'for protection from the Boers.']],
  ['l09', 39.3, ['That kept his mountain kingdom apart.', 'In 1966 it became independent,', 'surrounded on every side.']],
  ['l10', 46.9, ['They call it the Kingdom in the Sky.']],
  ['l11', 49.5, ['Would you live in a country with no lowlands at all?']],
];
export const HITS = { ben: 2.6, drain: 4.7, border: 6.0, lesotho: 8.3, rise: 14.3, k1000: 15.95, half: 17.8, k1400: 20.45, fifths: 22.0,
  wet: 24.9, low: 26.4, peak: 29.4, peakN: 30.0, drain2: 32.4, y1868: 34.8, y1966: 41.8, around: 45.0, rise2: 46.6, title: 47.2, ask: 49.5 };
// sea level in metres
const lv = monotone([[0, 0], [HITS.rise, 0], [HITS.k1000, 1000], [HITS.k1400 - .6, 1000],
  [HITS.k1400, 1400], [HITS.drain2, 1400], [HITS.drain2 + 1.3, 0], [HITS.rise2, 0], [HITS.rise2 + 2.6, 1400], [DUR, 1400]]);
export const LEVEL = t => Math.max(0, lv(t));
// measured share of South Africa below each level (data/measure.json)
const share = monotone([[0, 0], [200, 5.5], [500, 14.6], [1000, 42.9], [1200, 60.9], [1345, 74.1], [1400, 79.1], [1500, 86.6]]);
export const SHARE = h => share(h);
// camera [lon, lat, ln d, tilt, head]
const C = track([
  [0.0, [28.25, -29.65, Math.log(64), 44, 0]],
  [4.4, [28.25, -29.65, Math.log(58), 46, 4]],          // hook: slow push on the kingdom
  [7.6, [27.8, -29.8, Math.log(120), 44, 2]],           // pull back: South Africa on every side
  [11.6, [27.0, -30.0, Math.log(210), 42, 0]],
  [14.2, [25.6, -29.8, Math.log(300), 40, 0]],          // the region
  [19.9, [25.8, -29.9, Math.log(320), 42, -3]],
  [22.4, [26.6, -29.9, Math.log(270), 44, -5]],
  [24.9, [27.9, -29.8, Math.log(120), 50, -8]],         // push to the dry kingdom
  [26.4, [27.45, -30.25, Math.log(42), 62, -20]],       // dive to the lowest point
  [28.6, [27.7, -30.1, Math.log(48), 64, -40]],
  [30.6, [29.1, -29.55, Math.log(46), 62, -70]],        // low track to the summit
  [32.2, [29.2, -29.5, Math.log(52), 60, -78]],
  [34.0, [28.2, -29.55, Math.log(95), 46, -30]],        // history: near-locked over the country
  [44.0, [28.1, -29.6, Math.log(88), 44, -10]],
  [46.4, [28.1, -29.6, Math.log(100), 44, 0]],
  [DUR, [27.4, -29.8, Math.log(190), 40, 0]],           // crane up and back
]);
export const CAM = t => { const c = C(t); return { lon: c[0], lat: c[1], d: Math.exp(c[2]), tilt: c[3], head: c[4] }; };
