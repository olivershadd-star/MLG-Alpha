const path = require("path");
const core = require(path.join(__dirname, "..", "mlg_core.js"));
const R = path.join(__dirname, "..", "..", "Resources") + "/";
let fails = 0;
const check = (c, m) => { if (!c) { console.log("ECHEC:", m); fails++; } };
const msgs = [];
const dev = new core.Device((sel, ...a) => msgs.push([sel, a]));
dev.rebuild();
check(msgs.some(m => m[0] === "clip"), "clip potards");
const clipMsg = msgs.filter(m => m[0] === "clip").pop()[1];
console.log("clip potards:", clipMsg.slice(0, 12).join(" "), "...", (clipMsg.length - 4) / 4, "notes");
const t0 = Date.now();
dev.load(R + "mlg_library.txt.gz", R + "mlg_dictionary.txt");
console.log(msgs.filter(m => m[0] === "status").pop()[1][0]);
for (const w of ["basse sombre et roulante", "nappe mélancolique aérée", "kick techno très lourd", "arpège triste en triolets, 2 mesures",
                 "accords dub chauds", "truc vénère saturé nine inch nails", "pas trop dense façon boards of canada"]) {
  msgs.length = 0;
  dev.words(w);
  const u = msgs.find(m => m[0] === "understood"); const l = msgs.find(m => m[0] === "line");
  console.log("«", w, "»\n   ", u[1][0].replace(/\n/g, " | "), "\n    ->", l && l[1][0]);
  check(msgs.some(m => m[0] === "place"), "potards placés");
}
// commandes techniques
msgs.length = 0; dev.tech("2 mesures, division 1/16, tonique la, gamme dorien, notes C1 à C3, legato, euclidien 5");
console.log(msgs.find(m => m[0] === "techfeedback")[1][0]);
check(dev.settings.steps === 32 && dev.settings.root === 9 && dev.settings.scale === 2 && dev.settings.lowNote === 36, "commande");
check(!dev.fromLibrary, "commande -> potards");
// équivalences sur une ligne de bibliothèque
dev.words("basse acid"); console.log(msgs.find(m => m[0] === "fiche") ? "" : "");
const fiche = msgs.filter(m => m[0] === "fiche").pop()[1][0];
console.log("\n" + fiche + "\n");
// empreintes
let same = 0, n = 0;
for (let i = 0; i < dev.lib.all.length; i += 97) { const p = dev.lib.all[i]; const c = dev.lib.toClip(p, i % 12, core.defaultCentre(p.role)); n++; if (core.Library.fingerprintOf(c, i % 12) === p.fingerprint) same++; }
console.log("empreintes", same, "/", n); check(same === n, "empreintes");
// state
msgs.length = 0; dev.generateNew(); const st = msgs.find(m => m[0] === "state"); console.log("state", st && st[1][0]);
check(!!st, "state");
const dev2 = new core.Device(() => {}); dev2.settings = Object.assign({}, dev.settings); dev2.load(R + "mlg_library.txt.gz", R + "mlg_dictionary.txt"); dev2.restoreState(st[1][0]);
check(dev2.seeds.rhythm === dev.seeds.rhythm && JSON.stringify(dev2.clip.notes) === JSON.stringify(dev.clip.notes), "restauration potards");
dev.words("nappe sombre"); const st2 = dev.lastState; const dev3 = new core.Device(() => {}); dev3.load(R + "mlg_library.txt.gz", R + "mlg_dictionary.txt"); dev3.restoreState(st2);
check(dev3.fromLibrary && dev3.info.id === dev.info.id, "restauration bibliothèque");
// like / keep / bilan
msgs.length = 0; dev.like(true); dev.keep("nappe test perso"); console.log(msgs.map(m => m[1][0]).join(" / "));
dev.bilan(); console.log(msgs.find(m => m[0] === "bilan")[1][0].slice(0, 300));
// mécanique : densité stable
const a = core.generate(Object.assign({}, dev.settings, { rhythmMode: 0, density: 30, steps: 16 }), { rhythm: 5, pitch: 7, rhythmMutations: 0, pitchMutations: 0 });
const b = core.generate(Object.assign({}, dev.settings, { rhythmMode: 0, density: 60, steps: 16 }), { rhythm: 5, pitch: 7, rhythmMutations: 0, pitchMutations: 0 });
const sa = new Set(a.notes.map(x => x.start)); check([...sa].every(t => b.notes.some(x => Math.abs(x.start - t) < 1e-9)), "densité monotone");
console.log(fails ? "ECHECS " + fails : "OK coeur");
