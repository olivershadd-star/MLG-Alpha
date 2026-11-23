// MLG Alpha — cœur du module Max for Live (tourne dans [node.script]).
//
// Contient tout ce qui ne demande pas de précision temporelle :
//   - le générateur des potards (seeds, mutations, verrous) ;
//   - la bibliothèque classée (Resources/mlg_library.txt.gz) et le dictionnaire ;
//   - le traducteur mots -> étiquettes / styles / rôles, et le tirage pondéré ;
//   - la fiche technique, les réglages équivalents des potards, les commandes techniques ;
//   - la bibliothèque perso, l'apprentissage (J'aime / Bof) et les statistiques.
//
// Il envoie au patch des messages simples : « clip … », « place nom valeur », « line texte »…
// La lecture en rythme se fait à côté, dans mlg_player.js ([js] de Max), calée sur Live.

"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");
const zlib = require("zlib");
const crypto = require("crypto");

let maxApi = null;
try { maxApi = require("max-api"); } catch (e) { maxApi = null; }   // hors de Max : tests

// ============================================================================
// Noms

const SCALES = [
    [0, 2, 4, 5, 7, 9, 11], [0, 2, 3, 5, 7, 8, 10], [0, 2, 3, 5, 7, 9, 10], [0, 1, 3, 5, 7, 8, 10],
    [0, 2, 4, 6, 7, 9, 11], [0, 2, 4, 5, 7, 9, 10], [0, 1, 3, 5, 6, 8, 10], [0, 2, 3, 5, 7, 8, 11],
    [0, 2, 3, 5, 7, 9, 11], [0, 2, 4, 7, 9], [0, 3, 5, 7, 10], [0, 3, 5, 6, 7, 10],
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]];
const SCALE_NAMES = ["Majeur", "Mineur naturel", "Dorien", "Phrygien", "Lydien", "Mixolydien", "Locrien",
    "Mineur harmonique", "Mineur mélodique", "Penta majeure", "Penta mineure", "Blues", "Chromatique"];
const DIVISIONS = ["1/4", "1/8", "1/8T", "1/16", "1/16T", "1/32"];
const DIVISION_PPQ = [1.0, 0.5, 1.0 / 3.0, 0.25, 1.0 / 6.0, 0.125];
const ROOTS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const MAX_STEPS = 128;

const ROLE_KEYS = ["kick", "drums", "perc", "bass", "lead", "chords", "pad"];
const ROLE_NAMES = ["Kick", "Batterie", "Percussion", "Basse", "Mélodie / lead", "Accords", "Nappe"];
const ROLE = { kick: 0, drums: 1, perc: 2, bass: 3, lead: 4, chords: 5, pad: 6 };
const FAMILY_KEYS = ["techno", "techno-dure", "minimal-dub", "house", "acid", "ebm", "rock-indus",
    "electro-breaks", "trance-rave", "ambient", "idm", "melodique", "hors-cible"];
const FAMILY_NAMES = ["Techno", "Techno dure / indus", "Minimal / dub", "House / tech house", "Acid",
    "EBM / électro-indus", "Rock et noise indus", "Electro / breaks", "Trance / rave", "Ambient / textures",
    "IDM / Boards of Canada", "Électronique mélodique", "Hors cible"];
const HORS_CIBLE = FAMILY_KEYS.indexOf("hors-cible");
const TAG_KEYS = (
    "rectiligne hypnotique roulant martelé haché saccadé syncopé bancal boiteux cassé " +
    "régulier mécanique galopant sautillant lancinant obsédant répétitif pulsé chaloupé groovy " +
    "calme posé lent tendu nerveux agressif brutal explosif frénétique puissant lourd léger retenu montant " +
    "sombre mélancolique triste déprimé nostalgique inquiétant menaçant angoissant oppressant glacial " +
    "froid mystérieux solennel martial rêveur apaisé lumineux euphorique " +
    "mineur majeur dissonant consonant tendu-h suspendu modal exotique chromatique atonal ouvert épuré " +
    "dense chargé rempli aéré clairsemé minimal dépouillé vide ample planant flottant suspendu-t étiré serré " +
    "grave sub médium aigu profond perché " +
    "gras épais sec claquant distordu saturé grinçant métallique étouffé feutré sale crade rugueux " +
    "chaud brillant acide").split(" ");
const TAG_INDEX = new Map(TAG_KEYS.map((k, i) => [k, i]));

const tagLabel = (k) => (k === "tendu-h" ? "tendu (harmonie)" : k === "suspendu-t" ? "suspendu (temps)" : k);
const noteName = (n) => ROOTS[((n % 12) + 12) % 12] + (Math.floor(n / 12) - 2);   // C3 = 60, comme Ableton
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const num = (v, dec = 1) => {
    let s = v.toFixed(dec);
    if (s.indexOf(".") >= 0) s = s.replace(/0+$/, "").replace(/\.$/, "");
    return s.replace(".", ",");
};

// ============================================================================
// Hasard déterministe (seeds)

function rngFrom(seed) {
    let a = seed >>> 0;
    return {
        next() {   // mulberry32 : 0..1
            a = (a + 0x6D2B79F5) >>> 0;
            let t = a;
            t = Math.imul(t ^ (t >>> 15), t | 1);
            t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        },
        int(n) { return n <= 0 ? 0 : Math.floor(this.next() * n); },
        bool() { return this.next() < 0.5; },
    };
}

function derive(seed, index, salt) {
    let h = (seed ^ Math.imul(index + 1, 0x9E3779B1) ^ salt) >>> 0;
    h = Math.imul(h ^ (h >>> 16), 0x85EBCA6B) >>> 0;
    h = Math.imul(h ^ (h >>> 13), 0xC2B2AE35) >>> 0;
    return (h ^ (h >>> 16)) >>> 0;
}

function reflect(idx, size) {
    if (size <= 1) return 0;
    const period = 2 * (size - 1);
    idx %= period;
    if (idx < 0) idx += period;
    return idx < size ? idx : period - idx;
}

// ============================================================================
// Générateur des potards

const DEFAULT_SETTINGS = {
    rhythmMode: 0, steps: 16, division: 3, density: 50, pulses: 5, rotation: 0, swing: 0,
    root: 0, scale: 1, lowNote: 48, highNote: 67, maxJump: 3,
    lenMin: 50, lenMax: 100, legato: 0, velMin: 80, velMax: 110, accent: 15, octave: 0, switchAt: 0,
};

function generate(s, seeds) {
    const n = clamp(Math.round(s.steps), 1, MAX_STEPS);
    const stepPpq = DIVISION_PPQ[clamp(Math.round(s.division), 0, 5)];
    const swing = clamp(s.swing / 100, 0, 1);
    const gate = new Array(MAX_STEPS).fill(false);
    const vel = new Array(MAX_STEPS).fill(100);
    const len = new Array(MAX_STEPS).fill(1);
    const vlo = Math.min(s.velMin, s.velMax), vhi = Math.max(s.velMin, s.velMax);
    const llo = Math.min(s.lenMin, s.lenMax) / 100, lhi = Math.max(s.lenMin, s.lenMax) / 100;

    // rythme : on tire toujours 128 valeurs, pour que densité et nombre de pas restent stables
    const rr = rngFrom(seeds.rhythm);
    const chance = [];
    for (let i = 0; i < MAX_STEPS; ++i) {
        chance.push(rr.next());
        vel[i] = vlo + rr.int(vhi - vlo + 1);
        len[i] = llo + rr.next() * (lhi - llo);
    }
    if (Math.round(s.rhythmMode) === 1) {
        const k = clamp(Math.round(s.pulses), 0, n);
        const rot = ((Math.round(s.rotation) % n) + n) % n;
        for (let i = 0; i < n; ++i) {
            const idx = (i + n - rot) % n;
            gate[i] = k > 0 && ((idx * k) % n) < k;
        }
    } else {
        for (let i = 0; i < n; ++i) gate[i] = chance[i] < s.density / 100;
    }
    for (let m = 0; m < seeds.rhythmMutations; ++m) {
        const mr = rngFrom(derive(seeds.rhythm, m, 0x52594854));
        const flips = 1 + mr.int(2);
        for (let f = 0; f < flips; ++f) { const i = mr.int(n); gate[i] = !gate[i]; }
        vel[mr.int(n)] = vlo + mr.int(vhi - vlo + 1);
    }
    if (!gate.slice(0, n).some(Boolean)) gate[0] = true;

    // hauteurs : marche aléatoire dans les notes de la gamme entre note basse et note haute
    const sc = SCALES[clamp(Math.round(s.scale), 0, SCALES.length - 1)];
    const lo = Math.min(s.lowNote, s.highNote), hi = Math.max(s.lowNote, s.highNote);
    const notes = [];
    for (let note = lo; note <= hi; ++note)
        if (sc.indexOf((((note - s.root) % 12) + 12) % 12) >= 0) notes.push(note);
    if (!notes.length) notes.push(lo);
    const size = notes.length, jump = Math.max(0, Math.round(s.maxJump));
    const pr = rngFrom(seeds.pitch);
    const melody = [];
    let idx = Math.floor(pr.next() * size);
    for (let j = 0; j < MAX_STEPS; ++j) {
        melody.push(reflect(idx, size));
        idx = melody[j] + pr.int(2 * jump + 1) - jump;
    }
    const active = gate.slice(0, n).filter(Boolean).length;
    for (let m = 0; m < seeds.pitchMutations; ++m) {
        const mp = rngFrom(derive(seeds.pitch, m, 0x50495443));
        const count = 1 + mp.int(3);
        for (let c = 0; c < count; ++c) {
            const j = mp.int(Math.max(1, active));
            const delta = (1 + mp.int(Math.max(1, jump))) * (mp.bool() ? 1 : -1);
            melody[j] = reflect(melody[j] + delta, size);
        }
    }

    // assemblage en clip (ligne monophonique)
    const steps = [];
    let k = 0;
    for (let i = 0; i < n; ++i) {
        if (!gate[i]) continue;
        steps.push({
            i, pitch: notes[melody[k % MAX_STEPS]],
            vel: clamp(vel[i] + (i % 4 === 0 ? s.accent : 0), 1, 127),
            len: Math.max(0.05, len[i]),
        });
        ++k;
    }
    const legato = s.legato > 0.5;
    const startOf = (i) => i * stepPpq + (i & 1 ? swing * 0.5 * stepPpq : 0);
    const cycle = n * stepPpq;
    const clip = { lengthPpq: cycle, stepPpq, stepsPerBar: Math.round(4 / stepPpq), drums: false, notes: [] };
    for (let a = 0; a < steps.length; ++a) {
        const st = steps[a];
        let d = 1;
        if (legato) { d = a + 1 < steps.length ? steps[a + 1].i - st.i : n - st.i + steps[0].i; }
        const length = legato ? d + 0.6 : st.len;
        const start = startOf(st.i);
        const nextStart = a + 1 < steps.length ? startOf(steps[a + 1].i) : cycle + startOf(steps[0].i);
        let end = start + length * stepPpq;
        end = legato ? Math.min(end, nextStart + 0.02) : Math.min(end, nextStart);
        if (end <= start) end = start + 0.01;
        clip.notes.push({ start, length: end - start, pitch: st.pitch, velocity: st.vel });
    }
    return clip;
}

// ============================================================================
// Traducteur

function normalise(text) {
    let s = String(text).toLowerCase();
    s = s.normalize("NFD").replace(/[̀-ͯ]/g, "");          // accents
    s = s.replace(/œ/g, "oe").replace(/æ/g, "ae").replace(/[’'\-]/g, " ");
    s = s.replace(/[^a-z0-9/.]+/g, " ");
    return s.split(" ").filter(Boolean).join(" ");
}

class Translator {
    constructor() { this.phrases = new Map(); this.maxWords = 1; }

    load(text) {
        for (let line of text.split(/\r?\n/)) {
            line = line.trim();
            if (!line || line.startsWith("#") || line.indexOf("=") < 0) continue;
            const head = line.slice(0, line.indexOf("=")).trim();
            const body = line.slice(line.indexOf("=") + 1);
            const sp = head.indexOf(" ");
            const kind = sp < 0 ? head : head.slice(0, sp);
            const targets = sp < 0 ? [] : head.slice(sp + 1).split(",").map((t) => t.trim()).filter(Boolean);
            for (const form of body.split(",")) {
                const key = normalise(form);
                if (!key) continue;
                this.maxWords = Math.max(this.maxWords, key.split(" ").length);
                if (!this.phrases.has(key)) this.phrases.set(key, []);
                const v = this.phrases.get(key);
                if (!targets.length) v.push([kind, ""]);
                for (const t of targets)
                    if (!v.some(([k2, t2]) => k2 === kind && t2 === t)) v.push([kind, t]);
            }
        }
    }

    parse(text) {
        const q = { tags: new Map(), families: new Set(), roles: new Set(), triplet: false, binary: false, bars: 0,
                    understood: [], unknown: [] };
        const toks = normalise(text).split(" ").filter(Boolean);
        const stop = new Set(("de la le les un une des et avec qui en du au aux pour truc quelque chose me moi je veux " +
            "voudrais genre style type fais donne mets fait ca cette ce son sa ses mon ma a y il faut comme sur dans ou " +
            "mais plus moins bon tout trucs facon of the and").split(" "));
        const numbers = { une: 1, un: 1, deux: 2, trois: 3, quatre: 4, cinq: 5, six: 6, sept: 7, huit: 8 };
        let mod = 1, neg = false;

        for (let i = 0; i < toks.length;) {
            if (i + 1 < toks.length && toks[i + 1].startsWith("mesure")) {
                const n = parseInt(toks[i], 10) || numbers[toks[i]] || 0;
                if (n > 0) {
                    q.bars = clamp(n, 1, 8);
                    q.understood.push(q.bars + " mesure" + (q.bars > 1 ? "s" : ""));
                    i += 2;
                    continue;
                }
            }
            let hit = null, len = Math.min(this.maxWords, toks.length - i);
            for (; len > 0; --len) {
                const phrase = toks.slice(i, i + len).join(" ");
                if (this.phrases.has(phrase)) { hit = this.phrases.get(phrase); break; }
            }
            if (!hit) {
                if (!stop.has(toks[i]) && toks[i].length > 2 && !/^\d+$/.test(toks[i]) && q.unknown.indexOf(toks[i]) < 0)
                    q.unknown.push(toks[i]);
                ++i;
                continue;
            }
            i += len;
            let consumed = false;
            const what = [];
            for (const [kind, target] of hit) {
                if (kind === "mod") mod = parseFloat(target);
                else if (kind === "neg") neg = true;
                else if (kind === "tag") {
                    const t = TAG_INDEX.get(target);
                    if (t === undefined) continue;
                    q.tags.set(t, (q.tags.get(t) || 0) + (neg ? -1 : 1) * mod);
                    const w = (neg ? "pas " : "") + tagLabel(target);
                    if (what.indexOf(w) < 0) what.push(w);
                    consumed = true;
                } else if (kind === "family" && !neg) {
                    const f = Math.max(0, FAMILY_KEYS.indexOf(target));
                    q.families.add(f);
                    if (what.indexOf(FAMILY_NAMES[f]) < 0) what.push(FAMILY_NAMES[f]);
                    consumed = true;
                } else if (kind === "role" && !neg) {
                    const r = ROLE_KEYS.indexOf(target);
                    if (r >= 0) { q.roles.add(r); if (what.indexOf(ROLE_NAMES[r].toLowerCase()) < 0) what.push(ROLE_NAMES[r].toLowerCase()); }
                    consumed = true;
                } else if (kind === "tech") {
                    if (target === "triplet") { q.triplet = true; what.push("triolets"); }
                    if (target === "binary") { q.binary = true; what.push("binaire"); }
                    consumed = true;
                }
            }
            if (consumed) {
                for (const w of what)
                    q.understood.push(Math.abs(mod - 1) > 0.01 && !w.startsWith("pas ") ? (mod > 1 ? "très " : "un peu ") + w : w);
                mod = 1;
                neg = false;
            }
        }
        return q;
    }
}

function querySummary(q) {
    if (!q.understood.length) return "Rien de reconnu : tirage au hasard dans tout ce qui est en cible.";
    let s = "Compris : " + q.understood.join(" · ");
    if (q.unknown.length) s += "   (mots inconnus : " + q.unknown.join(", ") + ")";
    return s;
}

const emptyQuery = () => ({ tags: new Map(), families: new Set(), roles: new Set(), triplet: false, binary: false,
                            bars: 0, understood: [], unknown: [] });

// ============================================================================
// Bibliothèque

// Empreinte : (temps en 1/12 de pas, hauteur relative), période minimale, octave ramenée.
function fingerprintEvents(ev, stepsPerBar, bars, drums) {
    if (!ev.length) return "";
    ev = ev.map((e) => [e[0], e[1]]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    if (!drums) {
        let lo = Infinity;
        for (const e of ev) lo = Math.min(lo, e[1]);
        const shift = Math.floor(lo / 12) * 12;
        for (const e of ev) e[1] -= shift;
    }
    const bar = stepsPerBar * 12;
    let period = bars;
    for (let b = 1; b < bars; ++b) {
        if (bars % b) continue;
        const first = ev.filter((e) => e[0] < b * bar);
        if (first.length * (bars / b) !== ev.length) continue;
        const set = new Set(first.map((e) => e[0] + ":" + e[1]));
        if (ev.every((e) => set.has((e[0] % (b * bar)) + ":" + e[1]))) { period = b; break; }
    }
    const body = ev.filter((e) => e[0] < period * bar).map((e) => e[0] + "," + e[1]).join(" ");
    return crypto.createHash("sha1").update(stepsPerBar + "|" + (drums ? 1 : 0) + "|" + period + "|" + body).digest("hex").slice(0, 16);
}

const defaultCentre = (role) => (role === ROLE.bass ? 43 : role === ROLE.lead ? 64 : role === ROLE.chords ? 62 : 60);

function dataFolder() {
    const base = process.env.APPDATA || (process.platform === "darwin"
        ? path.join(os.homedir(), "Library", "Application Support") : path.join(os.homedir(), ".config"));
    const d = path.join(base, "ANKS Labs", "MLG Alpha");
    try { fs.mkdirSync(d, { recursive: true }); } catch (e) { /* rien */ }
    return d;
}

class Library {
    constructor() {
        this.all = [];
        this.byFp = new Map();
        this.byId = new Map();
        this.dict = new Translator();
        this.deltas = new Map();     // id -> Map(étiquette -> renfort)
        this.likeScore = new Map();
        this.stats = new Map();      // id -> {proposed, skipped, listened, liked, disliked, kept}
        this.recent = [];
        this.lastNote = "";
        this.ready = false;
        this.folder = dataFolder();
    }

    load(libraryGz, dictionaryTxt) {
        this.dict.load(fs.readFileSync(dictionaryTxt, "utf8"));
        this.parse(zlib.gunzipSync(fs.readFileSync(libraryGz)).toString("utf8"), false);
        const perso = path.join(this.folder, "perso.txt");
        if (fs.existsSync(perso)) this.parse(fs.readFileSync(perso, "utf8"), true);
        this.loadLearning();
        this.ready = true;
    }

    index(p) {
        let sum = 0;
        for (const e of p.events) sum += e.p;
        p.meanPitch = p.events.length ? sum / p.events.length : 0;
        p.fingerprint = fingerprintEvents(p.events.map((e) => [e.t, e.p]), p.steps, p.bars, p.drums);
    }

    parse(text, personal) {
        for (const line of text.split("\n")) {
            if (!line || line[0] === "#") continue;
            const f = line.split("|");
            if (f.length < 11) continue;
            const p = {
                id: f[0], role: Math.max(0, ROLE_KEYS.indexOf(f[1])), family: Math.max(0, FAMILY_KEYS.indexOf(f[2])),
                bars: clamp(parseInt(f[3], 10) || 1, 1, 16), steps: clamp(parseInt(f[4], 10) || 16, 1, 64),
                drums: f[6] === "1", name: f[9], personal, words: f[11] || "", settings: f[12] || "",
                tags: [], events: [],
            };
            for (const item of f[7].split(",")) {
                const c = item.indexOf(":");
                if (c < 0) continue;
                const t = TAG_INDEX.get(item.slice(0, c));
                if (t !== undefined) p.tags.push([t, parseInt(item.slice(c + 1), 10) || 1]);
            }
            for (const ev of f[10].split(" ")) {
                if (!ev) continue;
                const v = ev.split(",");
                if (v.length < 4) continue;
                p.events.push({ t: +v[0], l: +v[1], p: +v[2], v: +v[3] });
            }
            if (!p.events.length) continue;
            this.index(p);
            this.byFp.set(p.fingerprint, this.all.length);
            this.byId.set(p.id, this.all.length);
            this.all.push(p);
        }
    }

    toClip(p, root, centre) {
        const stepPpq = 4 / p.steps;
        const clip = { lengthPpq: 4 * p.bars, stepPpq, stepsPerBar: p.steps, drums: p.drums, notes: [] };
        const base = root + 12 * Math.round((centre - root - p.meanPitch) / 12);
        for (const e of p.events) {
            const start = e.t / 12 * stepPpq;
            if (start >= clip.lengthPpq) continue;
            clip.notes.push({ start, length: Math.max(0.02, e.l / 12 * stepPpq),
                              pitch: clamp(p.drums ? e.p : base + e.p, 0, 127), velocity: clamp(e.v, 1, 127) });
        }
        clip.notes.sort((a, b) => a.start - b.start || a.pitch - b.pitch);
        return clip;
    }

    static fingerprintOf(clip, root) {
        const ev = clip.notes.map((n) => [Math.round(n.start / clip.stepPpq * 12), clip.drums ? n.pitch : n.pitch - root]);
        return fingerprintEvents(ev, clip.stepsPerBar, Math.max(1, Math.round(clip.lengthPpq / 4)), clip.drums);
    }

    tagDelta(id, t) { const d = this.deltas.get(id); return d && d.has(t) ? d.get(t) : 0; }

    draw(q, kick, rand) {
        if (!this.ready) return -1;
        const kickOnsets = kick ? kick.notes.filter((n) => n.pitch === 36).map((n) => n.start % 1) : [];
        let wantsPositive = false;
        for (const w of q.tags.values()) if (w > 0) wantsPositive = true;
        const recent = new Set(this.recent);

        for (let pass = 0; pass < 4; ++pass) {   // style + mots exigés ; style + mots préférés ; sans le style…
            const useFamily = pass < 2, strict = pass % 2 === 0;
            const cand = [];
            let total = 0;
            for (let i = 0; i < this.all.length; ++i) {
                const p = this.all[i];
                if (q.roles.size && !q.roles.has(p.role)) continue;
                if (useFamily && q.families.size) { if (!q.families.has(p.family)) continue; }
                else if (p.family === HORS_CIBLE && !p.personal && !q.families.has(HORS_CIBLE)) continue;
                const trip = p.steps === 12 || p.steps === 24;
                if (q.triplet && !trip) continue;
                if (q.binary && trip) continue;

                let score = 1;
                if (q.bars > 0 && p.bars !== q.bars) score *= 0.1;
                if (q.tags.size) {
                    let s = 0, matched = false;
                    for (const [t, w] of q.tags) {
                        let conf = 0;
                        for (const [pt, c] of p.tags) if (pt === t) conf = c;
                        if (conf > 0) conf += this.tagDelta(p.id, t);
                        if (conf > 0 && w > 0) matched = true;
                        s += w * Math.max(0, conf) / 9 * (w < 0 ? 1.5 : 1);
                    }
                    if (strict) {
                        if (wantsPositive && (!matched || s <= 0)) continue;
                        score *= wantsPositive ? s * s : Math.max(0.05, 1 + s);
                    } else score *= Math.max(0.02, 1 + 3 * s);
                }
                const ls = this.likeScore.get(p.id);
                if (ls !== undefined) score *= clamp(1 + 0.3 * ls, 0.1, 3);
                if (recent.has(p.id)) score *= 0.03;
                const st = this.stats.get(p.id);
                if (!st || st.proposed === 0) score *= 1.3;
                if (p.personal) score *= 1.5;
                if (kickOnsets.length && p.role === ROLE.bass) {
                    const sp = 4 / p.steps;
                    let on = 0, hit = 0;
                    for (const e of p.events) {
                        const t = (e.t / 12 * sp) % 1;
                        ++on;
                        if (kickOnsets.some((k) => Math.abs(k - t) < 0.01)) ++hit;
                    }
                    score *= 1.6 - 1.2 * (on ? hit / on : 0);
                }
                if (score > 0) { cand.push([i, score]); total += score; }
            }
            if (!cand.length) continue;
            this.lastNote = ["", "Aucune ligne de ce style ne porte tous ces mots : voici la plus proche.",
                "Rien dans ce style : cherché dans tous les styles.",
                "Aucune ligne ne réunit tout ça : voici la plus proche, tous styles confondus."][pass];
            let r = rand() * total;
            for (const [i, s] of cand) { r -= s; if (r <= 0) return i; }
            return cand[cand.length - 1][0];
        }
        this.lastNote = "Rien ne correspond dans la bibliothèque : ligne générée avec les potards, réglés d'après tes mots.";
        return -1;
    }

    savePersonal(clip, root, words, meaning, role, family, settings) {
        if (!clip.notes.length) return "Rien à garder : la ligne est vide.";
        const fp = Library.fingerprintOf(clip, root);
        const dupIdx = this.byFp.get(fp);
        const dup = dupIdx !== undefined ? this.all[dupIdx] : null;
        if (dup && dup.personal) return "Déjà gardée dans ta bibliothèque : « " + dup.name + " ».";

        const p = {
            id: "perso-" + Date.now(), name: words || "Ligne gardée " + new Date().toLocaleString("fr-BE"),
            words, role, family, steps: clip.stepsPerBar, bars: Math.max(1, Math.round(clip.lengthPpq / 4)),
            drums: clip.drums, personal: true, settings, tags: [], events: [],
        };
        let lo = 127;
        for (const n of clip.notes) lo = Math.min(lo, n.pitch - root);
        const shift = clip.drums ? 0 : Math.floor(lo / 12) * 12;
        for (const n of clip.notes)
            p.events.push({ t: Math.round(n.start / clip.stepPpq * 12), l: Math.max(1, Math.round(n.length / clip.stepPpq * 12)),
                            p: clip.drums ? n.pitch : n.pitch - root - shift, v: n.velocity });
        for (const [t, w] of meaning.tags) if (w > 0 && p.tags.length < 5) p.tags.push([t, 7]);
        if (!p.tags.length && dup) p.tags = dup.tags.slice();
        this.index(p);

        const clean = (s) => String(s || "").replace(/\|/g, "/").replace(/\n/g, " ");
        const grid = p.steps === 12 ? "1/8T" : p.steps === 24 ? "1/16T" : "1/16";
        const line = [p.id, ROLE_KEYS[p.role], FAMILY_KEYS[p.family], p.bars, p.steps, grid, p.drums ? 1 : 0,
            p.tags.map(([t, c]) => TAG_KEYS[t] + ":" + c).join(","), p.fingerprint, clean(p.name),
            p.events.map((e) => e.t + "," + e.l + "," + e.p + "," + e.v).join(" "), clean(words), clean(settings)].join("|");
        fs.appendFileSync(path.join(this.folder, "perso.txt"), line + "\n", "utf8");

        this.byFp.set(p.fingerprint, this.all.length);
        this.byId.set(p.id, this.all.length);
        this.all.push(p);
        this.noteKept(p.id);
        return dup ? "Cette ligne existe déjà dans la bibliothèque (« " + dup.name + " ») : gardée quand même avec tes mots."
                   : "Gardée dans ta bibliothèque perso.";
    }

    statFor(id) {
        if (!this.stats.has(id)) this.stats.set(id, { proposed: 0, skipped: 0, listened: 0, liked: 0, disliked: 0, kept: 0 });
        return this.stats.get(id);
    }

    like(id, context, up) {
        const i = this.byId.get(id);
        if (i === undefined) return;
        const p = this.all[i];
        this.likeScore.set(id, (this.likeScore.get(id) || 0) + (up ? 1 : -1));
        if (!this.deltas.has(id)) this.deltas.set(id, new Map());
        const d = this.deltas.get(id);
        let asked = false;
        for (const [t] of p.tags)
            if ((context.tags.get(t) || 0) > 0) { asked = true; d.set(t, clamp((d.get(t) || 0) + (up ? 1 : -1), -6, 6)); }
        if (!asked)
            for (const [t] of p.tags) d.set(t, clamp((d.get(t) || 0) + (up ? 0.5 : -0.5), -6, 6));
        const s = this.statFor(id);
        if (up) s.liked++; else s.disliked++;
        this.saveLearning();
        this.saveStats();
    }

    resetLearning() {
        this.deltas.clear();
        this.likeScore.clear();
        for (const s of this.stats.values()) { s.liked = 0; s.disliked = 0; }
        try { fs.unlinkSync(path.join(this.folder, "apprentissage.txt")); } catch (e) { /* rien */ }
        this.saveStats();
    }

    loadLearning() {
        const read = (f) => { try { return fs.readFileSync(path.join(this.folder, f), "utf8"); } catch (e) { return ""; } };
        for (const line of read("apprentissage.txt").split(/\r?\n/)) {
            const f = line.split("|");
            if (f.length < 2) continue;
            this.likeScore.set(f[0], parseInt(f[1], 10) || 0);
            if (f[2]) {
                const d = new Map();
                for (const item of f[2].split(",")) {
                    const [k, v] = item.split(":");
                    if (TAG_INDEX.has(k)) d.set(TAG_INDEX.get(k), parseFloat(v) || 0);
                }
                this.deltas.set(f[0], d);
            }
        }
        for (const line of read("stats.txt").split(/\r?\n/)) {
            const f = line.split(" ");
            if (f.length < 7) continue;
            this.stats.set(f[0], { proposed: +f[1], skipped: +f[2], listened: +f[3], liked: +f[4], disliked: +f[5], kept: +f[6] });
        }
    }

    saveLearning() {
        const ids = new Set([...this.likeScore.keys(), ...this.deltas.keys()]);
        let out = "";
        for (const id of ids) {
            const d = this.deltas.get(id);
            const parts = d ? [...d].map(([t, v]) => TAG_KEYS[t] + ":" + v.toFixed(1)) : [];
            out += id + "|" + (this.likeScore.get(id) || 0) + "|" + parts.join(",") + "\n";
        }
        fs.writeFileSync(path.join(this.folder, "apprentissage.txt"), out, "utf8");
    }

    saveStats() {
        let out = "";
        for (const [id, s] of this.stats)
            out += [id, s.proposed, s.skipped, s.listened, s.liked, s.disliked, s.kept].join(" ") + "\n";
        fs.writeFileSync(path.join(this.folder, "stats.txt"), out, "utf8");
    }

    noteProposed(id) {
        this.statFor(id).proposed++;
        this.recent.push(id);
        if (this.recent.length > 60) this.recent.shift();
        this.saveStats();
    }

    noteListenTime(id, seconds) {
        if (seconds < 4) this.statFor(id).skipped++;
        else if (seconds > 30) this.statFor(id).listened++;
        else return;
        this.saveStats();
    }

    noteKept(id) { this.statFor(id).kept++; this.saveStats(); }

    report() {
        const tot = { proposed: 0, skipped: 0, listened: 0, liked: 0, disliked: 0, kept: 0 };
        const perFam = FAMILY_KEYS.map(() => ({ proposed: 0, skipped: 0, listened: 0, liked: 0, kept: 0 }));
        const size = FAMILY_KEYS.map(() => 0);
        let perso = 0, seen = 0;
        for (const p of this.all) { size[p.family]++; if (p.personal) perso++; }
        const liked = [];
        for (const [id, s] of this.stats) {
            for (const k in tot) tot[k] += s[k];
            const i = this.byId.get(id);
            if (i === undefined) continue;
            if (s.proposed > 0) seen++;
            const f = perFam[this.all[i].family];
            f.proposed += s.proposed; f.skipped += s.skipped; f.listened += s.listened; f.liked += s.liked; f.kept += s.kept;
            if (s.liked > 0) liked.push([s.liked, this.all[i].name]);
        }
        liked.sort((a, b) => b[0] - a[0]);
        const n = this.all.length;
        let r = "BILAN\n\n";
        r += "Bibliothèque : " + n + " lignes, dont " + perso + " dans ta bibliothèque perso.\n";
        r += "Déjà proposées au moins une fois : " + seen + " (" + num(n ? 100 * seen / n : 0) + " %). Jamais entendues : " + (n - seen) + ".\n\n";
        r += "Propositions : " + tot.proposed + "   écartées vite (< 4 s) : " + tot.skipped + "   écoutées longtemps (> 30 s) : " + tot.listened + "\n";
        r += "J'aime : " + tot.liked + "   Bof : " + tot.disliked + "   gardées : " + tot.kept + "\n\n";
        r += "Par style : proposées / écartées vite / écoutées longtemps / aimées / gardées (taille du style)\n";
        FAMILY_KEYS.forEach((k, f) => {
            const s = perFam[f];
            r += "  " + FAMILY_NAMES[f] + " : " + [s.proposed, s.skipped, s.listened, s.liked, s.kept].join(" / ") + "  (" + size[f] + ")\n";
        });
        if (liked.length) {
            r += "\nLes plus aimées :\n";
            for (const [c, name] of liked.slice(0, 8)) r += "  " + name + " (" + c + ")\n";
        }
        r += "\nFichiers : " + this.folder;
        return r;
    }
}

// ============================================================================
// Fiche technique, réglages équivalents, commandes

function gridName(spb) {
    return ({ 4: "noires (1/4)", 8: "croches (1/8)", 12: "croches de triolet (1/8T)", 16: "doubles croches (1/16)",
              24: "doubles croches de triolet (1/16T)", 32: "triples croches (1/32)" })[spb] || spb + " pas par mesure";
}
const divisionFor = (spb) => ({ 4: 0, 8: 1, 12: 2, 24: 4, 32: 5 })[spb] ?? 3;
const DRUM_NAMES = { 36: "kick", 37: "rimshot", 38: "caisse claire", 39: "clap", 42: "charleston fermé",
    46: "charleston ouvert", 45: "tom grave", 47: "tom médium", 50: "tom aigu", 51: "ride", 56: "cloche", 70: "shaker", 75: "claves" };

function describe(c, info, root) {
    const bars = Math.max(1, Math.round(c.lengthPpq / 4));
    const totalSteps = Math.max(1, Math.round(c.lengthPpq / c.stepPpq));
    let r = info.source + (info.name ? " : " + info.name : "") + "\n";
    if (info.role >= 0) r += ROLE_NAMES[info.role] + " · " + FAMILY_NAMES[Math.max(0, info.family)] + "\n";
    if (info.tags && info.tags.length)
        r += "Étiquettes : " + info.tags.map(([t, cf]) => tagLabel(TAG_KEYS[t]) + " " + cf + "/9").join(", ") + "\n";
    r += "\nLongueur : " + bars + " mesure" + (bars > 1 ? "s" : "") + " en 4/4, grille en " + gridName(c.stepsPerBar) + " = " + totalSteps + " pas.\n";
    if (!c.notes.length) return r + "Aucune note.";

    const starts = [];
    for (const n of c.notes) if (!starts.length || Math.abs(n.start - starts[starts.length - 1]) > 1e-6) starts.push(n.start);
    r += "Notes : " + c.notes.length + " notes, " + starts.length + " attaques, densité " + Math.round(100 * starts.length / totalSteps) +
         " % (environ " + num(starts.length / bars) + " par mesure).\n";

    let onBeat = 0, off8 = 0, other = 0, offGrid = 0;
    for (const t of starts) {
        const inBeat = t % 1, st = t / c.stepPpq;
        if (Math.abs(st - Math.round(st)) > 0.02) offGrid++;
        if (inBeat < 1e-3 || inBeat > 1 - 1e-3) onBeat++;
        else if (Math.abs(inBeat - 0.5) < 1e-3) off8++;
        else other++;
    }
    const n = starts.length;
    r += "Placement : " + Math.round(100 * onBeat / n) + " % sur les temps, " + Math.round(100 * off8 / n) +
         " % sur le « et » (croche à contretemps), " + Math.round(100 * other / n) + " % entre les deux" +
         (c.stepsPerBar % 3 === 0 ? " (triolets)" : " (syncopes)");
    if (offGrid) r += ", " + offGrid + " notes hors grille (swing, ratchets ou demi-pas)";
    r += ".\n";

    let lmin = Infinity, lmax = 0, lsum = 0;
    for (const x of c.notes) { const l = x.length / c.stepPpq; lmin = Math.min(lmin, l); lmax = Math.max(lmax, l); lsum += l; }
    const lmean = lsum / c.notes.length;
    r += "Durées : de " + num(lmin, 2) + " à " + num(lmax, 2) + " pas, moyenne " + num(lmean, 2) +
         (lmean < 0.6 ? " : notes courtes, piquées (staccato)." : lmean > 3 ? " : notes longues, tenues." : " pas.");
    let overlaps = 0;
    for (let i = 1; i < c.notes.length; ++i) {
        const a = c.notes[i - 1], b = c.notes[i];
        if (a.start + a.length > b.start + 1e-3 && a.start < b.start) overlaps++;
    }
    if (overlaps) r += " " + overlaps + " notes se chevauchent (legato : glide sur un synthé mono).";
    r += "\n";

    let vmin = 127, vmax = 0;
    for (const x of c.notes) { vmin = Math.min(vmin, x.velocity); vmax = Math.max(vmax, x.velocity); }
    r += "Vélocités : " + vmin + " à " + vmax + (vmax - vmin < 8 ? " : toutes pareilles, jeu de machine."
         : vmax - vmin > 40 ? " : accents très marqués, ghost notes." : " : accents légers.") + "\n";

    let poly = 1;
    for (let i = 0; i < c.notes.length;) {
        let j = i;
        while (j < c.notes.length && Math.abs(c.notes[j].start - c.notes[i].start) < 1e-6) ++j;
        poly = Math.max(poly, j - i);
        i = j;
    }
    if (poly > 1 && !c.drums) r += "Polyphonie : jusqu'à " + poly + " notes ensemble (accords).\n";

    if (c.drums) {
        const count = new Map();
        for (const x of c.notes) count.set(x.pitch, (count.get(x.pitch) || 0) + 1);
        r += "Instruments : " + [...count].sort((a, b) => a[0] - b[0])
            .map(([p, k]) => (DRUM_NAMES[p] || "percussion") + " (" + p + ") x" + k).join(", ") + ".\n";
    } else {
        let lo = 127, hi = 0;
        const pcs = new Set();
        for (const x of c.notes) { lo = Math.min(lo, x.pitch); hi = Math.max(hi, x.pitch); pcs.add((((x.pitch - root) % 12) + 12) % 12); }
        r += "Hauteurs : de " + noteName(lo) + " à " + noteName(hi) + " (" + (hi - lo) + " demi-tons), " + pcs.size +
             " notes différentes : " + [...pcs].sort((a, b) => a - b).map((pc) => ROOTS[(pc + root) % 12]).join(" ");
        if (pcs.has(3) && !pcs.has(4)) r += " : couleur mineure";
        else if (pcs.has(4) && !pcs.has(3)) r += " : couleur majeure";
        if (pcs.has(1) || pcs.has(6)) r += ", avec des notes de tension (seconde mineure, triton)";
        r += ".\n";
        if (poly === 1 && c.notes.length > 1) {
            let sum = 0, big = 0;
            for (let i = 1; i < c.notes.length; ++i) {
                const d = Math.abs(c.notes[i].pitch - c.notes[i - 1].pitch);
                sum += d; big = Math.max(big, d);
            }
            r += "Intervalles : écart moyen " + num(sum / (c.notes.length - 1)) + " demi-tons, plus grand saut " + big +
                 (big === 12 ? " (une octave)" : big > 12 ? " (plus d'une octave)" : "") + ".\n";
        }
    }
    if (bars > 1) {
        const barOf = (b) => c.notes.filter((x) => x.start >= b * 4 - 1e-6 && x.start < (b + 1) * 4 - 1e-6)
            .map((x) => Math.round((x.start - b * 4) * 48) + ":" + x.pitch).join(" ");
        const first = barOf(0);
        let same = 0;
        for (let b = 1; b < bars; ++b) if (barOf(b) === first) same++;
        r += same === bars - 1 ? "Structure : la même mesure répétée.\n"
           : same === 0 ? "Structure : chaque mesure varie (phrase de " + bars + " mesures).\n"
           : "Structure : " + same + " mesures reprennent la première, les autres varient.\n";
    }
    r += "\nCommandes : « 2 mesures », « division 1/16 », « triolets », « 12 pas », « densité 40 », « euclidien 5 », " +
         "« swing 30 », « tonique la », « gamme dorien », « notes C1 à C3 », « legato », « vélocité 80 120 », " +
         "« durée 50 100 », « écart 4 », « génère », « mute ».";
    return r;
}

function equivalentSettings(c, root) {
    const s = {};
    const total = clamp(Math.round(c.lengthPpq / c.stepPpq), 1, MAX_STEPS);
    s.division = divisionFor(c.stepsPerBar);
    s.steps = total;
    s.rhythmMode = 0; s.swing = 0; s.accent = 0;
    if (!c.notes.length) return s;
    const onSteps = new Set(c.notes.map((n) => Math.floor(n.start / c.stepPpq + 1e-6)));
    s.density = clamp(Math.round(100 * onSteps.size / total), 0, 100);
    const lens = [];
    let vmin = 127, vmax = 1, lo = 127, hi = 0, jump = 0, overlap = false;
    const pcs = new Set();
    c.notes.forEach((n, i) => {
        lens.push(n.length / c.stepPpq * 100);
        vmin = Math.min(vmin, n.velocity); vmax = Math.max(vmax, n.velocity);
        lo = Math.min(lo, n.pitch); hi = Math.max(hi, n.pitch);
        pcs.add((((n.pitch - root) % 12) + 12) % 12);
        if (i > 0) {
            const a = c.notes[i - 1];
            jump = Math.max(jump, Math.abs(n.pitch - a.pitch));
            if (a.start + a.length > n.start + 1e-3 && a.start < n.start) overlap = true;
        }
    });
    lens.sort((a, b) => a - b);
    s.lenMin = clamp(Math.round(lens[Math.floor(lens.length / 10)]), 5, 400);
    s.lenMax = clamp(Math.round(lens[Math.floor(lens.length * 9 / 10)]), 5, 400);
    s.velMin = vmin; s.velMax = vmax;
    s.legato = overlap ? 1 : 0;
    if (!c.drums) {
        s.lowNote = clamp(lo, 24, 108);
        s.highNote = clamp(hi, 24, 108);
        s.maxJump = clamp(Math.floor((jump + 1) / 2), 0, 12);
        for (const sc of [1, 0, 2, 3, 7, 5, 4, 8, 6, 11, 12])
            if ([...pcs].every((pc) => SCALES[sc].indexOf(pc) >= 0)) { s.scale = sc; break; }
    }
    return s;
}

function parseNoteName(tok) {
    const t = String(tok).toLowerCase().trim();
    for (const [n, v] of [["do", 0], ["re", 2], ["mi", 4], ["fa", 5], ["sol", 7], ["la", 9], ["si", 11],
                          ["c", 0], ["d", 2], ["e", 4], ["f", 5], ["g", 7], ["a", 9], ["b", 11]]) {
        if (!t.startsWith(n)) continue;
        let rest = t.slice(n.length), pc = v;
        if (rest.startsWith("#")) { pc++; rest = rest.slice(1); }
        else if (rest.startsWith("b") && rest.length > 1) { pc--; rest = rest.slice(1); }
        if (!rest || !/^-?\d+$/.test(rest)) return -1;
        return clamp((parseInt(rest, 10) + 2) * 12 + pc, 0, 127);
    }
    return -1;
}

function parseTechnical(text, currentDivision) {
    const cmd = { params: {}, done: [], unknown: [], generate: false, mutate: false };
    const toks = normalise(String(text).replace(/%/g, " ").replace(/#/g, "diese ")).split(" ").filter(Boolean);
    const spbOf = [4, 8, 12, 16, 24, 32];
    let division = currentDivision;
    const isNum = (t) => /^\d+$/.test(t || "");
    const scaleWords = { majeur: 0, majeure: 0, mineur: 1, mineure: 1, naturel: 1, dorien: 2, phrygien: 3, lydien: 4,
                         mixolydien: 5, locrien: 6, harmonique: 7, melodique: 8, blues: 11, chromatique: 12 };
    const divWords = { "1/4": 0, noires: 0, "1/8": 1, croches: 1, "1/8t": 2, "1/16": 3, doubles: 3, "1/16t": 4, "1/32": 5, triples: 5 };
    const setDiv = (d) => { division = d; cmd.params.division = d; cmd.done.push("division " + DIVISIONS[d]); };

    for (let i = 0; i < toks.length; ++i) {
        const t = toks[i], next = toks[i + 1] || "", next2 = toks[i + 2] || "";
        if (isNum(t) && next.startsWith("mesure")) {
            const bars = clamp(parseInt(t, 10), 1, 8);
            cmd.params.steps = Math.min(MAX_STEPS, bars * spbOf[division]);
            cmd.done.push(bars + " mesure" + (bars > 1 ? "s" : "")); ++i;
        } else if (isNum(t) && next === "pas") {
            cmd.params.steps = clamp(parseInt(t, 10), 1, MAX_STEPS); cmd.done.push(t + " pas"); ++i;
        } else if (t in divWords && !((t === "doubles" || t === "triples") && next !== "croches")) {
            let d = divWords[t];
            if (t === "doubles" || t === "triples") ++i;
            if (toks[i + 1] === "t" || (toks[i + 1] || "").startsWith("triolet")) { d = d === 1 ? 2 : d === 3 ? 4 : d; ++i; }
            setDiv(d);
        } else if (["division", "grille", "de", "et", "en", "a", "sur", "gamme", "mode", "notes", "registre", "tessiture"].indexOf(t) >= 0) {
            /* mots de liaison */
        } else if (t.startsWith("triolet") || t === "ternaire") setDiv(division <= 1 ? 2 : 4);
        else if (t === "binaire") setDiv(division === 2 ? 1 : 3);
        else if (t === "densite" && isNum(next)) {
            cmd.params.density = clamp(+next, 0, 100); cmd.params.rhythmMode = 0; cmd.done.push("densité " + next + " %"); ++i;
        } else if (t === "swing" && isNum(next)) { cmd.params.swing = clamp(+next, 0, 100); cmd.done.push("swing " + next + " %"); ++i; }
        else if (t.startsWith("euclid")) {
            cmd.params.rhythmMode = 1;
            let d = "rythme euclidien";
            if (isNum(next)) {
                cmd.params.pulses = +next; d += " " + next + " impulsions"; ++i;
                if (toks[i + 1] === "sur" && isNum(toks[i + 2])) { cmd.params.steps = clamp(+toks[i + 2], 1, MAX_STEPS); d += " sur " + toks[i + 2]; i += 2; }
            }
            cmd.done.push(d);
        } else if (t === "aleatoire" || t === "hasard") { cmd.params.rhythmMode = 0; cmd.done.push("rythme aléatoire"); }
        else if (t === "rotation" && isNum(next)) { cmd.params.rotation = +next; cmd.done.push("rotation " + next); ++i; }
        else if (t === "impulsions" && isNum(next)) { cmd.params.pulses = +next; cmd.params.rhythmMode = 1; cmd.done.push(next + " impulsions"); ++i; }
        else if (t === "tonique" || t === "tonalite" || t === "cle") {
            const nn = parseNoteName(next + "0");
            if (nn >= 0) {
                let pc = nn % 12, skip = 1;
                if (next2 === "diese") { pc = (pc + 1) % 12; ++skip; }
                if (next2 === "bemol") { pc = (pc + 11) % 12; ++skip; }
                cmd.params.root = pc; cmd.done.push("tonique " + ROOTS[pc]); i += skip;
            }
        } else if (t === "penta" || t === "pentatonique") {
            const maj = next.startsWith("maj");
            cmd.params.scale = maj ? 9 : 10; cmd.done.push(SCALE_NAMES[maj ? 9 : 10]);
            if (next.startsWith("maj") || next.startsWith("min")) ++i;
        } else if (t in scaleWords) {
            let sc = scaleWords[t];
            if (t.startsWith("mineur") && next === "harmonique") { sc = 7; ++i; }
            else if (t.startsWith("mineur") && next === "melodique") { sc = 8; ++i; }
            else if (t.startsWith("mineur") && next === "naturel") ++i;
            cmd.params.scale = sc; cmd.done.push("gamme " + SCALE_NAMES[sc]);
        } else if (parseNoteName(t) >= 0) {
            let j = i + 1;
            if (toks[j] === "a" || toks[j] === "au" || toks[j] === "jusqu") ++j;
            const a = parseNoteName(t), b = j < toks.length ? parseNoteName(toks[j]) : -1;
            if (b >= 0) {
                cmd.params.lowNote = clamp(Math.min(a, b), 24, 108);
                cmd.params.highNote = clamp(Math.max(a, b), 24, 108);
                cmd.done.push("notes de " + noteName(Math.min(a, b)) + " à " + noteName(Math.max(a, b)));
                i = j;
            } else cmd.unknown.push(t);
        } else if (["legato", "lie", "liees", "glide"].indexOf(t) >= 0) { cmd.params.legato = 1; cmd.done.push("legato"); }
        else if (t === "staccato" || t === "detache") { cmd.params.legato = 0; cmd.done.push("sans legato"); }
        else if (t === "sans" && next === "legato") { cmd.params.legato = 0; cmd.done.push("sans legato"); ++i; }
        else if ((t.startsWith("velocite") || t === "duree") && isNum(next)) {
            let j = i + 2;
            if (toks[j] === "a") ++j;
            const a = +next, b = isNum(toks[j]) ? +toks[j] : a;
            const lo = Math.min(a, b), hi = Math.max(a, b);
            if (t === "duree") {
                cmd.params.lenMin = clamp(lo, 5, 400); cmd.params.lenMax = clamp(hi, 5, 400);
                cmd.done.push("durée " + lo + " à " + hi + " %");
            } else {
                cmd.params.velMin = clamp(lo, 1, 127); cmd.params.velMax = clamp(hi, 1, 127);
                cmd.done.push("vélocité " + lo + " à " + hi);
            }
            i = isNum(toks[j]) ? j : i + 1;
        } else if (t === "ecart" && isNum(next)) { cmd.params.maxJump = clamp(+next, 0, 12); cmd.done.push("écart " + next); ++i; }
        else if (t === "accent" && isNum(next)) { cmd.params.accent = clamp(+next, 0, 40); cmd.done.push("accent " + next); ++i; }
        else if (t.startsWith("gener") || t === "nouvelle" || t === "nouveau") { cmd.generate = true; cmd.done.push("nouvelle ligne"); }
        else if (t.startsWith("mute") || t.startsWith("variation") || t === "varie") { cmd.mutate = true; cmd.done.push("variation"); }
        else if (!isNum(t)) cmd.unknown.push(t);
    }
    return cmd;
}

// ============================================================================
// L'appareil : état et messages

class Device {
    constructor(out) {
        this.out = out;                     // (selector, ...args) -> vers le patch
        this.lib = new Library();
        this.settings = Object.assign({}, DEFAULT_SETTINGS);
        this.seeds = { rhythm: (Math.random() * 4294967296) >>> 0, pitch: (Math.random() * 4294967296) >>> 0,
                       rhythmMutations: 0, pitchMutations: 0 };
        this.lockRhythm = false;
        this.lockPitch = false;
        this.fromLibrary = false;
        this.libIndex = -1;
        this.clip = null;
        this.info = { source: "Potards", name: "", role: -1, family: -1, tags: [] };
        this.kick = null;
        this.lastQuery = emptyQuery();
        this.shownSince = 0;
        this.pendingLibId = "";
        this.random = Math.random;
    }

    load(libraryGz, dictionaryTxt) {
        try {
            const t0 = Date.now();
            this.lib.load(libraryGz, dictionaryTxt);
            this.out("status", "Bibliothèque : " + this.lib.all.length + " lignes (" + (Date.now() - t0) + " ms)");
            if (this.pendingLibId) { this.restoreLibrary(this.pendingLibId); this.pendingLibId = ""; }
        } catch (e) {
            this.out("status", "Bibliothèque introuvable : " + e.message);
        }
    }

    // --- envois vers le patch ---
    publish() {
        const c = this.clip;
        const flat = [];
        for (const n of c.notes) flat.push(+n.start.toFixed(5), +n.length.toFixed(5), n.pitch, n.velocity);
        this.out("clip", +c.lengthPpq.toFixed(5), +c.stepPpq.toFixed(6), c.stepsPerBar, c.drums ? 1 : 0, ...flat);
        let t = this.info.source + (this.info.name ? " : " + this.info.name : "");
        if (this.info.role >= 0) t += "  —  " + ROLE_NAMES[this.info.role] + " · " + FAMILY_NAMES[Math.max(0, this.info.family)];
        this.out("line", t);
        this.out("fiche", describe(c, this.info, this.settings.root));
        this.out("seeds", String(this.seeds.rhythm), String(this.seeds.pitch));
        this.out("libline", this.fromLibrary ? 1 : 0);
        this.saveState();
    }

    saveState() {
        const s = [this.fromLibrary && this.libIndex >= 0 ? this.lib.all[this.libIndex].id : "-", this.seeds.rhythm,
                   this.seeds.pitch, this.seeds.rhythmMutations, this.seeds.pitchMutations, this.lockRhythm ? 1 : 0,
                   this.lockPitch ? 1 : 0].join("_");
        if (s !== this.lastState) { this.lastState = s; this.out("state", s); }
    }

    restoreState(s) {
        if (!s || s === this.lastState) return;
        const f = String(s).split("_");
        if (f.length < 7) return;
        this.seeds = { rhythm: +f[1] >>> 0, pitch: +f[2] >>> 0, rhythmMutations: +f[3] || 0, pitchMutations: +f[4] || 0 };
        this.lockRhythm = f[5] === "1";
        this.lockPitch = f[6] === "1";
        this.out("locks", this.lockRhythm ? 1 : 0, this.lockPitch ? 1 : 0);
        this.lastState = s;
        if (f[0] !== "-") {
            if (this.lib.ready) this.restoreLibrary(f[0]);
            else { this.pendingLibId = f[0]; this.rebuild(); }
        } else this.rebuild();
    }

    restoreLibrary(id) {
        const i = this.lib.byId.get(id);
        if (i !== undefined) this.setLibraryLine(i, false); else this.rebuild();
    }

    // --- potards ---
    rebuild() {
        this.clip = generate(this.settings, this.seeds);
        this.info = { source: "Potards", name: "seeds " + this.seeds.rhythm + " / " + this.seeds.pitch, role: -1, family: -1, tags: [] };
        this.publish();
    }

    leaveLibrary() {
        if (this.fromLibrary) { this.closeListening(); this.fromLibrary = false; this.libIndex = -1; }
    }

    param(name, value) {
        if (!(name in this.settings)) return;
        this.settings[name] = +value;
        if (name === "switchAt") return;
        if (this.fromLibrary && (name === "root" || name === "octave")) { this.refreshLibraryClip(); this.publish(); return; }
        if (name === "octave") return;
        this.leaveLibrary();
        this.rebuild();
    }

    // Plusieurs potards d'un coup (commandes, repli) : une seule régénération.
    setParams(obj, rebuild = true) {
        for (const k in obj) {
            if (!(k in this.settings)) continue;
            this.settings[k] = +obj[k];
            this.out("place", "p_" + k, +obj[k]);
        }
        if (rebuild) { this.leaveLibrary(); this.rebuild(); }
    }

    generateNew() {
        if (!this.lockRhythm) { this.seeds.rhythm = (this.random() * 4294967296) >>> 0; this.seeds.rhythmMutations = 0; }
        if (!this.lockPitch) { this.seeds.pitch = (this.random() * 4294967296) >>> 0; this.seeds.pitchMutations = 0; }
        this.leaveLibrary();
        this.rebuild();
    }

    mutate() {
        if (!this.lockRhythm) this.seeds.rhythmMutations++;
        if (!this.lockPitch) this.seeds.pitchMutations++;
        this.leaveLibrary();
        this.rebuild();
    }

    setSeeds(r, p) {
        r = Number(r) >>> 0; p = Number(p) >>> 0;
        if (r !== this.seeds.rhythm) { this.seeds.rhythm = r; this.seeds.rhythmMutations = 0; }
        if (p !== this.seeds.pitch) { this.seeds.pitch = p; this.seeds.pitchMutations = 0; }
        this.leaveLibrary();
        this.rebuild();
    }

    // --- bibliothèque ---
    closeListening() {
        if (this.fromLibrary && this.libIndex >= 0)
            this.lib.noteListenTime(this.lib.all[this.libIndex].id, (Date.now() - this.shownSince) / 1000);
    }

    refreshLibraryClip() {
        const p = this.lib.all[this.libIndex];
        const centre = defaultCentre(p.role) + 12 * Math.round(this.settings.octave);
        this.clip = this.lib.toClip(p, Math.round(this.settings.root), centre);
        this.info = { source: p.personal ? "Bibliothèque perso" : "Bibliothèque", id: p.id, name: p.name,
                      role: p.role, family: p.family, tags: p.tags };
        if (p.role === ROLE.kick || p.role === ROLE.drums) this.kick = this.clip;
    }

    setLibraryLine(i, count = true) {
        this.closeListening();
        this.libIndex = i;
        this.fromLibrary = true;
        this.refreshLibraryClip();
        // les potards se placent sur les réglages équivalents (sans régénérer)
        this.setParams(equivalentSettings(this.clip, Math.round(this.settings.root)), false);
        if (count) this.lib.noteProposed(this.lib.all[i].id);
        this.shownSince = Date.now();
        this.publish();
    }

    fallbackFromTags(q) {
        const w = (keys) => keys.reduce((s, k) => s + (q.tags.get(TAG_INDEX.get(k)) || 0), 0);
        const p = {};
        if (w(["dense", "rempli", "chargé", "frénétique", "nerveux"]) > 0) p.density = 80;
        if (w(["aéré", "clairsemé", "minimal", "dépouillé", "vide", "calme", "posé"]) > 0) p.density = 25;
        if (w(["grave", "sub", "profond", "lourd"]) > 0) { p.lowNote = 28; p.highNote = 43; }
        if (w(["aigu", "perché", "brillant", "léger"]) > 0) { p.lowNote = 72; p.highNote = 88; }
        if (w(["médium"]) > 0) { p.lowNote = 55; p.highNote = 70; }
        if (w(["mineur", "sombre", "mélancolique", "triste", "déprimé", "menaçant"]) > 0) p.scale = 1;
        if (w(["majeur", "lumineux", "euphorique", "apaisé"]) > 0) p.scale = 0;
        if (w(["dissonant", "chromatique", "atonal", "angoissant"]) > 0) p.scale = 12;
        if (w(["modal", "mystérieux"]) > 0) p.scale = 2;
        if (w(["exotique"]) > 0) p.scale = 7;
        if (w(["étiré", "planant", "lent", "flottant", "suspendu-t"]) > 0) { p.lenMin = 200; p.lenMax = 400; }
        if (w(["serré", "sec", "haché", "claquant", "saccadé"]) > 0) { p.lenMin = 20; p.lenMax = 50; }
        if (w(["syncopé", "groovy", "chaloupé", "bancal"]) > 0) p.swing = 25;
        if (w(["martelé", "régulier", "mécanique", "martial", "rectiligne"]) > 0) { p.rhythmMode = 1; p.pulses = 4; }
        if (w(["agressif", "brutal", "puissant", "explosif"]) > 0) { p.velMin = 100; p.velMax = 127; }
        this.setParams(p, false);
        this.generateNew();
    }

    words(text) {
        if (!this.lib.ready) return this.out("understood", "La bibliothèque se charge encore, réessaie dans une seconde.");
        this.lastQuery = this.lib.dict.parse(text);
        this.again();
    }

    again() {
        if (!this.lib.ready) return this.out("understood", "La bibliothèque se charge encore, réessaie dans une seconde.");
        const i = this.lib.draw(this.lastQuery, this.kick, this.random);
        let msg = querySummary(this.lastQuery);
        if (i < 0) this.fallbackFromTags(this.lastQuery); else this.setLibraryLine(i);
        if (this.lib.lastNote) msg += "\n" + this.lib.lastNote;
        this.out("understood", msg);
    }

    tech(text) {
        const cmd = parseTechnical(text, Math.round(this.settings.division));
        const has = Object.keys(cmd.params).length > 0;
        if (has) this.setParams(cmd.params, !cmd.generate && !cmd.mutate);
        if (cmd.generate) this.generateNew(); else if (cmd.mutate) this.mutate();
        let out = "";
        if (cmd.done.length) out += "Fait : " + cmd.done.join(", ") + ".";
        if (cmd.unknown.length) out += (out ? "  " : "") + "Pas compris : " + cmd.unknown.join(" ") + ".";
        this.out("techfeedback", out || "Rien à faire.");
    }

    like(up) {
        if (!this.fromLibrary || this.libIndex < 0)
            return this.out("understood", "J'aime / Bof servent à la bibliothèque : tire d'abord une ligne avec des mots.");
        this.lib.like(this.lib.all[this.libIndex].id, this.lastQuery, up);
        this.out("understood", up ? "Noté : cette ligne remontera plus souvent avec ces mots."
                                  : "Noté : cette ligne sortira moins souvent avec ces mots.");
    }

    settingsString() {
        return Object.keys(this.settings).map((k) => k + "=" + this.settings[k])
            .concat(["seedRhythm=" + this.seeds.rhythm, "mutRhythm=" + this.seeds.rhythmMutations,
                     "seedPitch=" + this.seeds.pitch, "mutPitch=" + this.seeds.pitchMutations]).join(";");
    }

    keep(words) {
        if (!this.lib.ready) return this.out("understood", "La bibliothèque se charge encore, réessaie dans une seconde.");
        const meaning = this.lib.dict.parse(words);
        let role = ROLE.lead, family = FAMILY_KEYS.indexOf("techno");
        if (this.fromLibrary && this.libIndex >= 0) {
            const p = this.lib.all[this.libIndex];
            role = p.role; family = p.family;
            this.lib.noteKept(p.id);
        } else if (this.clip.notes.length) {
            const mean = this.clip.notes.reduce((s, n) => s + n.pitch, 0) / this.clip.notes.length;
            if (mean < 50) role = ROLE.bass;
        }
        if (meaning.roles.size) role = [...meaning.roles][0];
        else if (this.lastQuery.roles.size && !this.fromLibrary) role = [...this.lastQuery.roles][0];
        if (meaning.families.size) family = [...meaning.families][0];
        else if (this.lastQuery.families.size && !this.fromLibrary) family = [...this.lastQuery.families][0];
        this.out("understood", this.lib.savePersonal(this.clip, Math.round(this.settings.root), words, meaning, role, family,
                                                     this.fromLibrary ? "" : this.settingsString()));
    }

    // la ligne vient d'être écrite dans un clip d'Ableton : on la compte comme gardée
    written() { if (this.fromLibrary && this.libIndex >= 0) this.lib.noteKept(this.lib.all[this.libIndex].id); }

    bilan() { this.out("bilan", this.lib.ready ? this.lib.report() : "La bibliothèque se charge encore."); }
    reset() { this.lib.resetLearning(); this.bilan(); }
}

// ============================================================================
// Branchement à Max

if (maxApi) {
    const out = (sel, ...args) => { maxApi.outlet(sel, ...args); };
    const dev = new Device(out);
    // textedit peut préfixer son contenu par « text » : on l'enlève
    const joined = (args) => args.map(String).join(" ").replace(/^text\s*/, "");
    // fichiers de la bibliothèque : à côté du script, ou chemins envoyés par le patch ([absolutepath])
    let libPath = "", dictPath = "";
    const tryLoad = () => { if (libPath && dictPath && !dev.lib.ready) dev.load(libPath, dictPath); };
    const near = (f) => path.join(__dirname, f);
    maxApi.addHandlers({
        libfile: (...a) => { const p = joined(a); if (fs.existsSync(p)) { libPath = p; tryLoad(); } },
        dictfile: (...a) => { const p = joined(a); if (fs.existsSync(p)) { dictPath = p; tryLoad(); } },
        param: (name, value) => dev.param(String(name), value),
        generate: () => dev.generateNew(),
        mutate: () => dev.mutate(),
        lockr: (v) => { dev.lockRhythm = !!+v; dev.saveState(); },
        lockp: (v) => { dev.lockPitch = !!+v; dev.saveState(); },
        seedr: (...a) => dev.setSeeds(joined(a).replace(/\D/g, "") || 0, dev.seeds.pitch),
        seedp: (...a) => dev.setSeeds(dev.seeds.rhythm, joined(a).replace(/\D/g, "") || 0),
        words: (...a) => dev.words(joined(a)),
        again: () => dev.again(),
        tech: (...a) => dev.tech(joined(a)),
        like: (v) => dev.like(!!+v),
        keep: (...a) => dev.keep(joined(a)),
        written: () => dev.written(),
        bilan: () => dev.bilan(),
        reset: () => dev.reset(),
        restore: (...a) => dev.restoreState(joined(a)),
        refresh: () => dev.clip && dev.publish(),
    });
    dev.rebuild();
    if (fs.existsSync(near("mlg_library.txt.gz")) && fs.existsSync(near("mlg_dictionary.txt"))) {
        libPath = near("mlg_library.txt.gz");
        dictPath = near("mlg_dictionary.txt");
    }
    maxApi.outlet("ready");
    setTimeout(tryLoad, 50);
}

module.exports = { generate, Translator, Library, Device, describe, equivalentSettings, parseTechnical, parseNoteName,
                   normalise, querySummary, emptyQuery, TAG_KEYS, ROLE_KEYS, FAMILY_KEYS, defaultCentre };
