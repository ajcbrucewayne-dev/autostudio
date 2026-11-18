// One timeline for picture, voice, score and checks (TREATMENT.md). Film seconds.
import { clamp, lerp, seg, ss, monotone, track } from '/core/lib.js';
export const DUR = 54.0;
export const LINES = [
  ['l01', 0.2, ['This town is in the United States,', "but you can't drive there", 'without leaving the United States.']],
  ['l02', 5.8, ['This is Point Roberts, Washington.', 'About 13 square kilometres,', 'and 1,200 people.']],
  ['l03', 12.0, ['In 1846, Britain and America', 'split this region along a straight line:', 'the 49th parallel.']],
  ['l04', 19.2, ["The line didn't care about the coast.", 'It sliced right through this peninsula,', 'and left its tip on the American side.']],
  ['l05', 26.4, ['So to reach the rest of America by land,', 'you drive about 40 km through Canada,', 'and cross the border twice.']],
  ['l06', 33.6, ['Older kids have long taken a school bus through Canada:', 'four border crossings, every school day.']],
  ['l07', 39.8, ['And when the border shut in 2020,', 'the whole town was cut off by land', 'for over a year and a half.']],
  ['l08', 46.0, ['Would you live in an American town where', 'you need a passport to go shopping in America?']],
];
export const HITS = { line0: .35, tip: 3.7, usa: 2.4, name: 6.0, area: 8.6, pop: 10.6, y1846: 12.2, region: 15.6, par49: 17.4, sliced: 21.8, side: 24.8,
  drive: 28.9, cross1: 31.8, cross2: 32.6, bus: 34.2, four: 37.05, y2020: 40.9, cutoff: 43.1, ask: 46.0 };
const C = track([
  [0.0, [-123.06, 48.975, Math.log(15), 52, 0]],
  [5.6, [-123.06, 48.985, Math.log(12.5), 54, 6]],
  [11.8, [-123.06, 48.99, Math.log(8.5), 56, 18]],        // close on the tip
  [15.2, [-122.95, 49.0, Math.log(40), 50, 6]],
  [19.0, [-122.85, 49.02, Math.log(62), 46, 0]],          // the line across the region
  [22.0, [-123.05, 48.995, Math.log(16), 54, -4]],
  [26.2, [-123.05, 48.995, Math.log(18), 52, -10]],       // sliced
  [29.0, [-122.97, 49.04, Math.log(34), 50, -18]],
  [33.4, [-122.90, 49.04, Math.log(38), 50, -26]],        // the drive
  [39.4, [-122.92, 49.04, Math.log(40), 48, -20]],        // the bus
  [41.5, [-123.064, 49.0, Math.log(6.5), 58, -8]],        // the closed crossing
  [45.6, [-123.064, 49.0, Math.log(5.6), 60, -14]],
  [DUR, [-123.0, 49.0, Math.log(30), 46, 0]],             // crane up
]);
export const CAM = t => { const c = C(t); return { lon: c[0], lat: c[1], d: Math.exp(c[2]), tilt: c[3], head: c[4] }; };
// schematic route: Tyee Drive crossing → Tsawwassen → Hwy 17 / 99 → Peace Arch crossing → Blaine
export const ROUTE = [[-123.0636, 48.995], [-123.0636, 49.0021], [-123.065, 49.02], [-123.07, 49.04], [-123.055, 49.06], [-123.02, 49.075], [-122.97, 49.08],
  [-122.92, 49.075], [-122.86, 49.06], [-122.81, 49.04], [-122.78, 49.02], [-122.7566, 49.0020], [-122.75, 48.995], [-122.747, 48.993]];
export const XING = { tyee: [-123.0636, 49.0021], peace: [-122.7566, 49.0020] };
