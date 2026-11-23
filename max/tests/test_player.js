// Teste mlg_player.js hors de Max : fonctions de Max simulées.
const fs = require("fs"), path = require("path"), vm = require("vm");
const core = require(path.join(__dirname, "..", "mlg_core.js"));
const out = [];
const ctx = { outlet: (i, ...a) => out.push([i, ...a]), arrayfromargs: (a) => Array.prototype.slice.call(a),
              LiveAPI: function (cb) { this.cb = cb; }, Math, Date, String, parseInt, autowatch: 0 };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "mlg_player.js"), "utf8"), ctx);
let fails = 0; const check = (c, m) => { if (!c) { console.log("ECHEC", m); fails++; } };

const clipArgs = (c) => { const a = [c.lengthPpq, c.stepPpq, c.stepsPerBar, c.drums ? 1 : 0]; for (const n of c.notes) a.push(n.start, n.length, n.pitch, n.velocity); return a; };
const s = { rhythmMode: 0, steps: 16, division: 3, density: 60, pulses: 5, rotation: 0, swing: 30, root: 0, scale: 1,
            lowNote: 48, highNote: 67, maxJump: 3, lenMin: 50, lenMax: 150, legato: 1, velMin: 80, velMax: 110, accent: 15 };
const clip = core.generate(s, { rhythm: 42, pitch: 9, rhythmMutations: 0, pitchMutations: 0 });
ctx.clip(...clipArgs(clip));
ctx.init(); ctx.onLive(["is_playing", 1]);
// transport qui avance par blocs de ~11 ms à 120 bpm (= 10,6 ticks)
let ticks = 0, ons = 0, sounding = new Map(), maxPoly = 0, poly = 0;
for (let b = 0; b < 1200; ++b) {
  out.length = 0; ctx.tick(ticks); ticks += 10.6;
  for (const m of out) if (m[0] === 0) {
    if (m[2] > 0) { ons++; poly++; maxPoly = Math.max(maxPoly, poly); sounding.set(m[1], (sounding.get(m[1]) || 0) + 1); }
    else { check((sounding.get(m[1]) || 0) > 0, "note-off sans note-on"); sounding.set(m[1], sounding.get(m[1]) - 1); poly--; }
  }
}
const cycles = ticks / 480 / clip.lengthPpq;
console.log("notes jouées", ons, "attendues ~", Math.round(cycles * clip.notes.length), "poly max", maxPoly);
check(Math.abs(ons - cycles * clip.notes.length) <= clip.notes.length, "nombre de notes");
out.length = 0; ctx.onLive(["is_playing", 0]);
check(out.filter(m => m[0] === 0).length === poly, "arrêt coupe tout");
// changement à la mesure suivante
ctx.switchat(1); ctx.onLive(["is_playing", 1]); ticks = 0; out.length = 0;
for (let b = 0; b < 60; ++b) { ctx.tick(ticks); ticks += 10.6; }
const other = core.generate(Object.assign({}, s, { lowNote: 90, highNote: 100 }), { rhythm: 1, pitch: 2, rhythmMutations: 0, pitchMutations: 0 });
ctx.clip(...clipArgs(other));
const tChange = ticks; let firstNew = -1;
for (let b = 0; b < 400; ++b) { out.length = 0; ctx.tick(ticks); for (const m of out) if (m[0] === 0 && m[2] > 0 && m[1] >= 90 && firstNew < 0) firstNew = ticks; ticks += 10.6; }
console.log("nouvelle ligne à partir de", (firstNew / 480).toFixed(2), "noires (demandée à", (tChange / 480).toFixed(2), ")");
check(firstNew / 480 >= 4 - 0.05, "attend la mesure");
console.log(fails ? "ECHECS " + fails : "OK lecteur");
