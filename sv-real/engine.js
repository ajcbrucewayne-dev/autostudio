// Realistic 3D map engine (the China / Lesotho look): Sentinel-2 imagery on AWS terrain, a wide region + a detail box,
// baked sun shadows, distance haze into a sky gradient, an animated sea with glints and surf, glowing ribbons, bloom + DOF.
// Assets come from geo3d/prep.py. Copy this file next to a film's index.html (pages can't import from ../).
import * as THREE from 'three';
import { makePost } from './post.js';
import { clamp } from '/core/lib.js';
const D2R = Math.PI / 180;

export async function makeWorld(o) {
  const Wd = innerWidth, Ht = innerHeight, Q = new URLSearchParams(location.search), SS = +(Q.get('ss') || 1.5);
  const J = u => fetch(u).then(r => r.json()), B = u => fetch(u).then(r => r.arrayBuffer());
  const meta = await J('assets/meta.json');
  const [rRaw, dRaw] = await Promise.all([B('assets/mesh_r.bin'), B('assets/mesh_d.bin')]);
  const HRb = new Float32Array(rRaw), HDb = new Float32Array(dRaw);
  const [RW, RH] = meta.mesh_r, [DW, DH] = meta.mesh_d, [r0, r1, r2, r3] = meta.R, [d0, d1, d2, d3] = meta.D, EX = o.ex ?? meta.ex;
  const LON0 = o.lon0 ?? (d0 + d1) / 2, LAT0 = o.lat0 ?? (d2 + d3) / 2, KX = 111.32 * Math.cos(meta.lat0 * D2R), KZ = 111.32;   // 1 unit = 1 km
  const xz = (lon, lat) => [(lon - LON0) * KX, -(lat - LAT0) * KZ];
  const ll = (x, z) => [LON0 + x / KX, LAT0 - z / KZ];
  function bil(buf, w, h, gx, gz) { const x0 = clamp(Math.floor(gx), 0, w - 2), z0 = clamp(Math.floor(gz), 0, h - 2), fx = clamp(gx - x0), fz = clamp(gz - z0);
    return (buf[z0 * w + x0] * (1 - fx) + buf[z0 * w + x0 + 1] * fx) * (1 - fz) + (buf[(z0 + 1) * w + x0] * (1 - fx) + buf[(z0 + 1) * w + x0 + 1] * fx) * fz; }
  const hAt = (lon, lat) => lon > d0 && lon < d1 && lat > d2 && lat < d3 ? bil(HDb, DW, DH, (lon - d0) / (d1 - d0) * (DW - 1), (d3 - lat) / (d3 - d2) * (DH - 1))
    : bil(HRb, RW, RH, (lon - r0) / (r1 - r0) * (RW - 1), (r3 - lat) / (r3 - r2) * (RH - 1));
  const yOf = h => Math.max(h, 0) / 1000 * EX;
  const geo = (lon, lat, lift = 0) => { const [X, Z] = xz(lon, lat); return new THREE.Vector3(X, yOf(hAt(lon, lat)) + lift, Z); };

  const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1); renderer.setSize(Wd, Ht); renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = o.exposure ?? 1.5;
  document.body.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  const SKYC = o.sky ?? ['#0b1a2c', '#27486a', '#7d9bb4', '#b9c6cf'];
  { const c = document.createElement('canvas'); c.width = 4; c.height = 512; const q = c.getContext('2d'); const gr = q.createLinearGradient(0, 0, 0, 512);
    gr.addColorStop(0, SKYC[0]); gr.addColorStop(.5, SKYC[1]); gr.addColorStop(.82, SKYC[2]); gr.addColorStop(1, SKYC[3]); q.fillStyle = gr; q.fillRect(0, 0, 4, 512);
    const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; scene.background = tx; }
  const hx = c => { const v = new THREE.Color(c); return `vec3(${v.r.toFixed(3)},${v.g.toFixed(3)},${v.b.toFixed(3)})`; };   // Color() is already linear
  const camera = new THREE.PerspectiveCamera(o.fov ?? 38, Wd / Ht, .01, 3000);
  const tl = new THREE.TextureLoader(), load = u => new Promise((r, e) => tl.load(u, r, undefined, e));
  const names = ['albedo_r.jpg', 'albedo_d.jpg', 'normal_r.png', 'normal_d.png', 'height_r.png', 'height_d.png', 'shadow_r.png', 'shadow_d.png', meta.island_centre ? 'mask_d.png' : 'shadow_d.png'];
  const [albR, albD, nrmR, nrmD, hR, hD, shR, shD, mD] = await Promise.all(names.map(n => load('assets/' + n)));
  for (const t of [albR, albD]) t.colorSpace = THREE.SRGBColorSpace;
  for (const t of [albR, albD, nrmR, nrmD, shR, shD, mD]) { t.anisotropy = 8; }
  for (const t of [hR, hD]) { t.minFilter = t.magFilter = THREE.NearestFilter; t.generateMipmaps = false; }
  const [saz, sel] = meta.sun, SUNV = new THREE.Vector3(Math.sin(saz * D2R) * Math.cos(sel * D2R), Math.sin(sel * D2R), -Math.cos(saz * D2R) * Math.cos(sel * D2R)).normalize();
  const G = { time: { value: 0 }, camP: { value: new THREE.Vector3() }, fogD: { value: 60 }, resY: { value: Ht * SS }, sunV: { value: SUNV }, glow: { value: 0 }, glowCol: { value: new THREE.Color(o.glowCol ?? 0xff4a3a) },
    lvl: { value: 0 }, wet: { value: o.wet ?? 1 }, sunCol: { value: new THREE.Color(o.sunCol ?? 0xffe2b8) }, ambCol: { value: new THREE.Color(o.ambCol ?? 0x7d93b0) }, sunK: { value: o.sunK ?? 3.4 }, ambK: { value: o.ambK ?? .8 } };
  const SKY = `vec3 skyAt(float v){ vec3 a = ${hx(SKYC[0])}, b = ${hx(SKYC[1])}, c = ${hx(SKYC[2])}, d = ${hx(SKYC[3])};
      return v < .5 ? mix(a, b, v / .5) : v < .82 ? mix(b, c, (v - .5) / .32) : mix(c, d, (v - .82) / .18); }
    vec3 hazeC(){ return ${hx(o.haze ?? SKYC[3])}; }`;
  const NOISE = `float hh(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
    float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3. - 2. * f); return mix(mix(hh(i), hh(i + vec2(1, 0)), u.x), mix(hh(i + vec2(0, 1)), hh(i + vec2(1, 1)), u.x), u.y); }`;
  const mx = .08 * (r1 - r0), mz = .08 * (r3 - r2);
  const EDGE = `float edgeF(vec2 ll){ return 1. - smoothstep(${r2.toFixed(4)}, ${(r2 + mz).toFixed(4)}, ll.y) + smoothstep(${(r3 - mz).toFixed(4)}, ${r3.toFixed(4)}, ll.y)
      + 1. - smoothstep(${r0.toFixed(4)}, ${(r0 + mx).toFixed(4)}, ll.x) + smoothstep(${(r1 - mx).toFixed(4)}, ${r1.toFixed(4)}, ll.x); }`;
  function terMat(det) {
    return new THREE.ShaderMaterial({
      uniforms: { tAlb: { value: det ? albD : albR }, tNrm: { value: det ? nrmD : nrmR }, tSh: { value: det ? shD : shR }, tMask: { value: mD }, tAlbR: { value: albR }, tNrmR: { value: nrmR }, tShR: { value: shR },
        box: { value: new THREE.Vector4(...(det ? [d0, d2, d1, d3] : [r0, r2, r1, r3])) }, rbox: { value: new THREE.Vector4(r0, r2, r1, r3) }, det: { value: det ? 1 : 0 }, dbg: { value: +(Q.get('dbg') || 0) }, hasMask: { value: meta.island_centre && det ? 1 : 0 }, ...G },
      vertexShader: `attribute vec2 aLL; varying vec2 vLL; varying vec3 vW; void main(){ vLL = aLL; vec4 w = modelMatrix * vec4(position, 1.); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`,
      fragmentShader: `varying vec2 vLL; varying vec3 vW; uniform sampler2D tAlb, tNrm, tSh, tMask, tAlbR, tNrmR, tShR; uniform vec4 box, rbox; uniform float dbg, det, hasMask, glow, fogD, resY, sunK, ambK;
        uniform vec3 camP, sunV, glowCol, sunCol, ambCol; ${SKY} ${EDGE}
        void main(){
          if (det < .5 && vLL.x > ${(d0 + .002).toFixed(4)} && vLL.x < ${(d1 - .002).toFixed(4)} && vLL.y > ${(d2 + .002).toFixed(4)} && vLL.y < ${(d3 - .002).toFixed(4)}) discard;
          vec2 uv = (vLL - box.xy) / (box.zw - box.xy), ur = (vLL - rbox.xy) / (rbox.zw - rbox.xy);
          vec3 alb = texture2D(tAlb, uv).rgb; alb = pow(alb, vec3(2.2)); vec3 n = normalize(texture2D(tNrm, uv).rgb * 2. - 1.); float sh = texture2D(tSh, uv).r;
          if (det > .5) { float eb = min(min(uv.x, 1. - uv.x), min(uv.y, 1. - uv.y)); float fe = smoothstep(.0, .06, eb);
            alb = mix(pow(texture2D(tAlbR, ur).rgb, vec3(2.2)), alb, fe); n = normalize(mix(texture2D(tNrmR, ur).rgb * 2. - 1., n, fe)); sh = mix(texture2D(tShR, ur).r, sh, fe); }
          float lam = max(dot(n, sunV), 0.) * mix(.18, 1., sh);
          vec3 col = alb * (sunCol * lam * sunK + ambCol * (.55 + .45 * n.y) * ambK);
          if (hasMask > .5) { float m = texture2D(tMask, uv).r; float fw = fwidth(m) * 3.5 + 1e-4; float line = 1. - smoothstep(0., fw, abs(m - .5));
            col = mix(col, glowCol * 2.2, clamp(glow * line, 0., 1.) * .85); col += glowCol * glow * line * .8; }
          float dist = length(vW - camP); col = mix(col, hazeC() * .8, (1. - exp(-pow(dist / fogD, 1.6))) * .55);
          col = mix(col, skyAt(1. - gl_FragCoord.y / resY), clamp(edgeF(vLL), 0., 1.));
          if (dbg > .5 && dbg < 1.5) col = det > .5 ? vec3(1., 0., 1.) : vec3(0., 1., 0.); if (dbg > 1.5 && dbg < 2.5) col = alb; if (dbg > 2.5) col = vec3(lam);
          gl_FragColor = vec4(col, 1.); }` });
  }
  function terrain(buf, w, h, box, mat, lower = 0) {
    const pos = new Float32Array(w * h * 3), lla = new Float32Array(w * h * 2), idx = [];
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) { const lon = box[0] + i / (w - 1) * (box[1] - box[0]), lat = box[3] - j / (h - 1) * (box[3] - box[2]), k = j * w + i, [X, Z] = xz(lon, lat);
      pos.set([X, yOf(buf[k]) - lower, Z], k * 3); lla.set([lon, lat], k * 2); }
    for (let j = 0; j < h - 1; j++) for (let i = 0; i < w - 1; i++) { const a = j * w + i; idx.push(a, a + w, a + 1, a + 1, a + w, a + w + 1); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('aLL', new THREE.BufferAttribute(lla, 2)); g.setIndex(idx);
    const m = new THREE.Mesh(g, mat); m.frustumCulled = false; scene.add(m); return m;
  }
  terrain(HRb, RW, RH, meta.R, terMat(false), .003);
  terrain(HDb, DW, DH, meta.D, terMat(true));

  // the sea: a translucent layer over the imagery (keeps reefs visible), sun glints, swell and surf at the shore
  const water = (() => {
    const g = new THREE.PlaneGeometry((r1 - r0) * KX, (r3 - r2) * KZ, 1, 1); g.rotateX(-Math.PI / 2); const [cx, cz] = xz((r0 + r1) / 2, (r2 + r3) / 2);
    const m = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, uniforms: { tHR: { value: hR }, tHD: { value: hD }, ...G },
      vertexShader: `varying vec3 vW; void main(){ vec4 w = modelMatrix * vec4(position, 1.); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`,
      fragmentShader: `varying vec3 vW; uniform sampler2D tHR, tHD; uniform float lvl, fogD, resY, time, wet; uniform vec3 camP, sunV, sunCol; ${SKY} ${NOISE} ${EDGE}
        float near0(float d){ return exp(-d / 9.); }
        float H(sampler2D t, vec2 uv){ vec3 c = texture2D(t, uv).rgb; return (c.r * 255. * 256. + c.g * 255.) - 12000.; }
        void main(){
          vec2 ll = vec2(${LON0.toFixed(5)} + vW.x / ${KX.toFixed(6)}, ${LAT0.toFixed(5)} - vW.z / ${KZ.toFixed(6)}); float h;
          h = H(tHR, (ll - vec2(${r0.toFixed(4)}, ${r2.toFixed(4)})) / vec2(${(r1 - r0).toFixed(5)}, ${(r3 - r2).toFixed(5)}));
          if (ll.x > ${d0.toFixed(4)} && ll.x < ${d1.toFixed(4)} && ll.y > ${d2.toFixed(4)} && ll.y < ${d3.toFixed(4)}) { float hd = H(tHD, (ll - vec2(${d0.toFixed(4)}, ${d2.toFixed(4)})) / vec2(${(d1 - d0).toFixed(5)}, ${(d3 - d2).toFixed(5)})); h = hd > .5 ? hd : min(hd, h); }
          float dep = lvl - h; if (dep < 0.) discard;
          vec2 wp = ll * vec2(${(KX * 2.5).toFixed(2)}, ${(KZ * 2.5).toFixed(2)}); float t2 = time * .5; float dist = length(vW - camP);
          vec3 wn = normalize(vec3((vn(wp + t2) - vn(wp - vec2(.5) - t2)) * .28, 1., (vn(wp.yx * 1.3 + t2) - vn(wp.yx * 1.3 - t2)) * .28));
          vec3 vd = normalize(camP - vW), hv = normalize(vd + sunV);
          float k = clamp(dep / 80., 0., 1.); wn = normalize(mix(vec3(0, 1, 0), wn, near0(dist)));
          vec3 col = mix(${hx(o.seaShallow ?? '#2f7c86')}, ${hx(o.seaDeep ?? '#0b3a55')}, k) * (.92 + .16 * vn(wp * .3 + t2 * .2));
          float fres = pow(1. - max(dot(vd, vec3(0, 1, 0)), 0.), 4.); col = mix(col, skyAt(.75) * .9, fres * .6);
          float near = exp(-dist / 5.); col += sunCol * pow(max(dot(wn, hv), 0.), 80.) * 2.2 * near;
          float foam = smoothstep(.5, .8, vn(ll * ${(KX * 400).toFixed(1)} + vec2(time * .7, 0.))) * exp(-pow(max(dep, 0.) / 3.5, 2.)) * wet * exp(-dist / 12.);
          float a = mix(.15, 1., smoothstep(3., 45., dep));
          col = mix(col, vec3(.9), foam * .55); a = max(a, foam * .6);
          col = mix(col, hazeC() * .8, (1. - exp(-pow(dist / fogD, 1.6))) * .75);
          float e = clamp(edgeF(ll), 0., 1.); col = mix(col, skyAt(1. - gl_FragCoord.y / resY), e); a = mix(a, 1., e);
          gl_FragColor = vec4(col, a); }` });
    const w = new THREE.Mesh(g, m); w.position.set(cx, .01, cz); w.renderOrder = 1; w.frustumCulled = false; scene.add(w); if (Q.has('nowater')) w.visible = false; return w;
  })();

  // glowing ribbons (screen-space width floor so thin lines stay visible from far away)
  const PIXK = 2 * Math.tan(camera.fov / 2 * D2R) / Ht;
  const RIB_V = `attribute float aSide; attribute vec3 aNorm; attribute float aAlong; uniform float wW, pxW, pixK; varying float vSide, vAlong;
    void main(){ vec4 wp = modelMatrix * vec4(position, 1.); float pw = length(cameraPosition - wp.xyz) * pixK;
      float hw = max(wW * .5, pxW * .5 * pw); wp.xyz += aNorm * aSide * hw; vSide = aSide; vAlong = aAlong; gl_Position = projectionMatrix * viewMatrix * wp; }`;
  const RIB_F = `varying float vSide, vAlong; uniform vec3 col; uniform float k, inten, rev, soft, head, headAmt, dash, duty, base, phase;
    void main(){ float g = exp(-vSide * vSide * k); float vis = 1. - smoothstep(rev - soft, rev, vAlong); if (vis <= 0.) discard;
      float a = base; if (dash > 0.) a *= step(fract((vAlong + phase) / dash), duty); a += headAmt * exp(-pow((vAlong - head) / soft, 2.));
      gl_FragColor = vec4(col * g * a * inten * vis, 1.); }`;
  function ribbon(pts, q = {}) {
    const n = pts.length, pos = new Float32Array(n * 6), side = new Float32Array(n * 2), nrm = new Float32Array(n * 6), al = new Float32Array(n * 2), idx = []; let L = 0;
    for (let i = 0; i < n; i++) {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)], t = new THREE.Vector3().subVectors(b, a);
      const nv = q.vertical ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(-t.z, 0, t.x).normalize(); if (i) L += pts[i].distanceTo(pts[i - 1]);
      for (let s = 0; s < 2; s++) { const k = 2 * i + s; pos.set([pts[i].x, pts[i].y, pts[i].z], k * 3); side[k] = s ? -1 : 1; nrm.set([nv.x, nv.y, nv.z], k * 3); al[k] = L; }
      if (i) { const k = 2 * i; idx.push(k - 2, k - 1, k, k - 1, k + 1, k); }
    }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('aSide', new THREE.BufferAttribute(side, 1));
    g.setAttribute('aNorm', new THREE.BufferAttribute(nrm, 3)); g.setAttribute('aAlong', new THREE.BufferAttribute(al, 1)); g.setIndex(idx);
    const u = { col: { value: new THREE.Color(q.col ?? 0xffa63d) }, k: { value: q.k ?? 3 }, inten: { value: 0 }, wW: { value: q.wW ?? 0 }, pxW: { value: q.pxW ?? 2 }, pixK: { value: PIXK },
      rev: { value: 1e9 }, soft: { value: q.soft ?? .05 }, head: { value: -1e6 }, headAmt: { value: 0 }, dash: { value: q.dash ?? 0 }, duty: { value: q.duty ?? .55 }, base: { value: q.base ?? 1 }, phase: { value: 0 } };
    const m = new THREE.Mesh(g, new THREE.ShaderMaterial({ uniforms: u, vertexShader: RIB_V, fragmentShader: RIB_F, side: THREE.DoubleSide, transparent: true,
      depthWrite: false, depthTest: q.depthTest ?? true, blending: THREE.AdditiveBlending, toneMapped: false }));
    m.renderOrder = q.order ?? 3; m.frustumCulled = false; scene.add(m); m.u = u; m.L = L;
    m.reveal = (p, inten = 1, headAmt = 0) => { u.rev.value = L * p + 1e-4; u.inten.value = inten; u.head.value = L * p; u.headAmt.value = headAmt; };
    return m;
  }
  const densify = (lls, step) => { const out = []; for (let i = 0; i < lls.length - 1; i++) { const [a, b] = lls[i], [c, d] = lls[i + 1]; const n = Math.max(1, Math.ceil(Math.hypot(c - a, d - b) / step));
    for (let k = 0; k < n; k++) out.push([a + (c - a) * k / n, b + (d - b) * k / n]); } out.push(lls[lls.length - 1]); return out; };
  // a ribbon that drapes over the terrain (or floats at a fixed height)
  const path = (lls, q = {}) => ribbon(densify(lls, q.step ?? .002).map(([lo, la]) => q.y != null ? (() => { const [X, Z] = xz(lo, la); return new THREE.Vector3(X, q.y, Z); })() : geo(lo, la, q.lift ?? .01)), q);
  const circle = (lon, lat, rkm, q = {}) => { const pts = []; for (let i = 0; i <= 160; i++) { const a = i / 160 * Math.PI * 2; pts.push([lon + Math.cos(a) * rkm / KX, lat + Math.sin(a) * rkm / KZ]); } return path(pts, { step: 1, ...q }); };

  const { composer, dof, bloom } = makePost(renderer, scene, camera, Wd, Ht, { ssaa: SS, ao: false });
  bloom.strength = o.bloom ?? .55; bloom.radius = .45; bloom.threshold = 1.05;
  // camera: target lon/lat, distance d (km), tilt from vertical, heading (deg, 0 = looking north)
  function setCam(c) {
    const [X, Z] = xz(c.lon, c.lat), Y = (c.ty ?? yOf(hAt(c.lon, c.lat)) * .6), th = c.tilt * D2R, hd = c.head * D2R;
    const off = new THREE.Vector3(-Math.sin(hd) * Math.sin(th), Math.cos(th), Math.cos(hd) * Math.sin(th)).multiplyScalar(c.d);
    camera.near = Math.max(.003, c.d * .04); camera.far = c.d * 40 + 300; camera.updateProjectionMatrix();
    camera.position.set(X + off.x, Y + off.y, Z + off.z); camera.up.set(0, 1, 0); camera.lookAt(X, Y, Z); camera.updateMatrixWorld();
    G.camP.value.copy(camera.position); G.fogD.value = Math.max(o.fogMin ?? 8, c.d * (o.fogK ?? 2.6));
    if (c.dof) { dof.focus = c.d; dof.aper = c.dof / c.d; dof.maxCoc = 12; } else dof.maxCoc = 0;
  }
  const proj = (lon, lat, lift = .05, y = null) => { const p = geo(lon, lat, lift); if (y != null) p.y = y; const v = p.project(camera); return [(v.x + 1) / 2 * Wd, (1 - v.y) / 2 * Ht, v.z < 1 && Math.abs(v.x) < 1.2 && Math.abs(v.y) < 1.2]; };
  const projV = p => { const v = p.clone().project(camera); return [(v.x + 1) / 2 * Wd, (1 - v.y) / 2 * Ht, v.z < 1]; };
  return { THREE, scene, camera, renderer, composer, G, meta, xz, ll, hAt, yOf, geo, ribbon, path, circle, densify, setCam, proj, projV, water, KX, KZ, Wd, Ht, SS };
}

// ---------- shared overlay helpers (China-style typography) ----------
export function makeOverlay(Wd, Ht) {
  const ov = document.createElement('canvas'); ov.width = Wd; ov.height = Ht; document.body.appendChild(ov); const g = ov.getContext('2d'); let TX = [];
  function txt(id, s, x, y, o = {}) {
    const a = o.a ?? 1; if (a <= .01 || !s) return;
    g.save(); g.globalAlpha = a; g.font = `${o.w ?? 600} ${o.size ?? 34}px Barlow`; g.letterSpacing = (o.track ?? 0) + 'px'; g.textAlign = o.align ?? 'center';
    if (o.shadow !== false) { g.shadowColor = 'rgba(0,0,0,.65)'; g.shadowBlur = o.blur ?? 14; }
    g.fillStyle = o.col ?? '#f6eee0'; g.fillText(s, x, y); const w = g.measureText(s).width; g.restore();
    const x0 = o.align === 'left' ? x : o.align === 'right' ? x - w : x - w / 2;
    if (a > .95) TX.push({ id, text: s, x0, y0: y - (o.size ?? 34), x1: x0 + w, y1: y + 6, ...(o.pass ? { pass: true } : {}) });
  }
  function dot(x, y, r, col, a = 1, ring = 0) { if (a <= .01) return; g.save(); g.globalAlpha = a; g.fillStyle = col; g.shadowColor = col; g.shadowBlur = 18; g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
    if (ring > 0) { g.globalAlpha = a * (1 - ring); g.strokeStyle = col; g.lineWidth = 3; g.beginPath(); g.arc(x, y, r + ring * 70, 0, Math.PI * 2); g.stroke(); } g.restore(); }
  function leader(x0, y0, x1, y1, col, a) { if (a <= .01) return; g.save(); g.globalAlpha = a; g.strokeStyle = col; g.lineWidth = 2; g.shadowColor = 'rgba(0,0,0,.5)'; g.shadowBlur = 6; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); g.restore(); }
  function pin(id, name, x, y, a, col = '#f6eee0', size = 40, h = 90, sub = null, subCol = '#ffc36b') {
    if (a <= .01) return; dot(x, y, 8, col, a); leader(x, y - 12, x, y - h, col, a); txt(id, name, x, y - h - 14, { size, w: 600, track: 6, a, col });
    if (sub) txt(id + 's', sub, x, y - h - 14 - size - 4, { size: size * .7, w: 500, track: 6, a, col: subCol }); }
  function subtitles(CUES, t, accent = '#ffa63d') {
    const c = CUES.find(c => t >= c.t0 - .05 && t < c.t1 + .3); if (!c) return;
    const seg = (x, a, b) => clamp((x - a) / (b - a)); const a = Math.min(seg(t, c.t0 - .05, c.t0 + .1), 1 - seg(t, c.t1 + .15, c.t1 + .3)), x = 64, size = 44;
    g.save(); g.font = `600 ${size}px Barlow`; const words = c.text.split(' '), lines = ['']; for (const w of words) { const tr = (lines.at(-1) + ' ' + w).trim(); if (g.measureText(tr).width > Wd - 150 && lines.at(-1)) lines.push(w); else lines[lines.length - 1] = tr; } g.restore();
    const y = Ht - 220 - (lines.length - 1) * 54;
    g.save(); const gr = g.createLinearGradient(0, Ht - 420, 0, Ht); gr.addColorStop(0, 'rgba(5,8,12,0)'); gr.addColorStop(1, 'rgba(5,8,12,.62)');
    g.fillStyle = gr; g.globalAlpha = a; g.fillRect(0, Ht - 420, Wd, 420); g.fillStyle = accent; g.fillRect(x - 22, y - size + 4, 5, size + 8 + (lines.length - 1) * 54); g.restore();
    lines.forEach((l, i) => txt('sub' + i, l, x, y + i * 54, { size, w: 600, align: 'left', a, col: '#f4efe6', blur: 8 }));
  }
  return { g, txt, dot, leader, pin, subtitles, clear() { TX = []; g.clearRect(0, 0, Wd, Ht); }, get TX() { return TX; } };
}
