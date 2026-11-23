"""Quatrième générateur : textures, nappes, ambient, IDM, façon Apparat/Moderat, techno industrielle
(Ancient Methods, Orphx, Perc, Adam X), techno suédoise en boucles (Beyer, Lekebusch, Drumcode 90s),
noise rock électronique (HEALTH).

Nouveautés de format :
  - Polyphonie : un motif peut avoir plusieurs voix ; lignes N / N2 / N3 / N4 (notes) et V / V2 / V3 / V4
    (vélocités), une série de lignes par mesure.
  - Ratchet : suffixe *2, *3 ou *4 sur une note = la note est répétée 2, 3 ou 4 fois dans le pas.
Usage : python3 tools/generate_textures.py   (écrit Library/tex_*.txt, résultat déterministe)"""
import random
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "Library"
rng = random.Random(777)

MINOR = [0, 2, 3, 5, 7, 8, 10]
DORIAN = [0, 2, 3, 5, 7, 9, 10]
PHRYG = [0, 1, 3, 5, 7, 8, 10]
MAJOR = [0, 2, 4, 5, 7, 9, 11]
LYDIAN = [0, 2, 4, 6, 7, 9, 11]
SCALES = {"mineur": MINOR, "dorien": DORIAN, "phrygien": PHRYG, "majeur": MAJOR, "lydien": LYDIAN}

PROGS = {  # degrés (0 = I) — progressions lentes typiques ambient / mélancoliques
    "mineur": [[0, 5, 2, 6], [0, 3, 5, 4], [0, 5], [0, 3], [0, 6, 5, 6], [0, 2, 5, 6], [0, 0, 5, 5], [0, 3, 0, 4],
               [5, 6, 0, 0], [0, 4, 5, 3]],
    "dorien": [[0, 3], [0, 3, 0, 6], [0, 1, 3, 0]],
    "phrygien": [[0, 1], [0, 1, 0, 6], [0, 6, 1, 0]],
    "majeur": [[0, 4, 5, 3], [0, 3], [0, 5, 3, 4], [3, 0, 4, 5]],
    "lydien": [[0, 1], [0, 1, 0, 4]],
}


def chord_tones(scale, degree, kind="triad"):
    idx = [degree, degree + 2, degree + 4] + ([degree + 6] if kind == "7" else []) + ([degree + 8] if kind == "9" else [])
    out = []
    for i in idx:
        octv, d = divmod(i, 7)
        out.append(scale[d] + 12 * octv)
    if kind == "sus2":
        octv, d = divmod(degree + 1, 7); out[1] = scale[d] + 12 * octv
    return out


def voice_lead(prev, tones, n_voices, lo=-12, hi=19):
    """Choisit pour chaque voix la note d'accord la plus proche de la voix précédente (conduite des voix)."""
    cands = sorted({t + 12 * k for t in tones for k in range(-2, 3) if lo <= t + 12 * k <= hi})
    if prev is None:
        # premier accord : notes de l'accord empilées dans l'ordre, octave au-dessus si plus de voix que de notes
        res = []
        for i in range(n_voices):
            n = tones[i % len(tones)] + 12 * (i // len(tones))
            while res and n <= res[-1]: n += 12
            res.append(n)
        return res
    res = []
    for v in prev[:n_voices]:
        options = [c for c in cands if c not in res]
        res.append(min(options, key=lambda c: abs(c - v)) if options else v)
    res = sorted(res)
    # 1) la basse (voix la plus grave) joue la fondamentale de l'accord, au plus près de l'ancienne basse
    roots = [c for c in cands if (c - tones[0]) % 12 == 0 and c < (res[1] if len(res) > 1 else 99)]
    if roots:
        res[0] = min(roots, key=lambda c: abs(c - prev[0]))
    # 2) chaque note de l'accord doit être présente : on remplace une note doublée par la note manquante
    for t in tones[:n_voices]:
        if any((r - t) % 12 == 0 for r in res): continue
        pcs = [(r % 12) for r in res]
        dup = [i for i in range(1, len(res)) if pcs.count(pcs[i]) > 1]
        i = dup[-1] if dup else len(res) - 1
        opts = [c for c in cands if (c - t) % 12 == 0 and c not in res]
        if opts: res[i] = min(opts, key=lambda c: abs(c - res[i]))
    return sorted(res)


# ------------------------------------------------------------------ écriture
class Pat:
    def __init__(self, kind, bars, voices=1):
        self.kind, self.bars, self.nv = kind, bars, voices
        self.N = [["."] * (16 * bars) for _ in range(voices)]
        self.V = [["."] * (16 * bars) for _ in range(voices)]

    def note(self, v, step, tok, vel, length=1):
        if step >= len(self.N[v]): return
        self.N[v][step] = str(tok); self.V[v][step] = str(int(max(1, min(127, vel))))
        for k in range(step + 1, min(len(self.N[v]), step + length)):
            if self.N[v][k] == ".": self.N[v][k] = "-"
            else: break

    def empty(self):
        return all(t in ".-" for row in self.N for t in row)

    def key(self):
        return " | ".join(" ".join(r) for r in self.N)

    def render(self, head):
        lines = [head]
        for b in range(self.bars):
            for v in range(self.nv):
                sfx = "" if v == 0 else str(v + 1)
                lines.append(f"N{sfx:<2s}" + " ".join(self.N[v][b * 16:(b + 1) * 16]))
                lines.append(f"V{sfx:<2s}" + " ".join(self.V[v][b * 16:(b + 1) * 16]))
        return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ AMBIENT / TEXTURES
def drone(_):
    bars = rng.choice([4, 8, 8, 16])
    voices = rng.choice([1, 2, 2, 3])
    sets = [[0], [0, 7], [0, 12], [0, 7, 12], [0, 5], [0, 7, 14], [-12, 0], [0, 3, 7]]
    notes = rng.choice([s for s in sets if len(s) >= voices] or [[0, 7, 12]])[:voices]
    p = Pat("pad", bars, voices)
    seg = rng.choice([4, 8, bars])  # la note est rejouée toutes les seg mesures
    for v, n in enumerate(notes):
        offset = v * rng.choice([0, 2, 4, 8])
        for start in range(0, bars, seg):
            p.note(v, start * 16 + offset, n, rng.uniform(60, 90), seg * 16 - offset)
    return p, "Drone", "ambient", f"drone-{voices}v"


def pad_prog(_):
    mode = rng.choice(["mineur", "mineur", "mineur", "dorien", "phrygien", "majeur", "lydien"])
    scale = SCALES[mode]; prog = rng.choice(PROGS[mode])
    bars_per = rng.choice([1, 2, 2, 4])
    bars = min(16, len(prog) * bars_per)
    nv = rng.choice([3, 3, 4])
    kind = rng.choice(["triad", "triad", "7", "sus2", "9"])
    stagger = rng.choice([0, 0, 2, 4, 8])  # les voix entrent l'une après l'autre
    p = Pat("pad", bars, nv)
    prev = None
    for ci, deg in enumerate(prog):
        if ci * bars_per >= bars: break
        tones = chord_tones(scale, deg, kind if kind != "9" or nv >= 4 else "triad")
        voicing = voice_lead(prev, tones, nv); prev = voicing
        start = ci * bars_per * 16; length = bars_per * 16
        for v, n in enumerate(voicing):
            off = v * stagger if stagger * (nv - 1) < length else 0
            p.note(v, start + off, n, rng.uniform(55, 85) - v * 4, length - off)
    return p, f"Nappe {mode}", "ambient", f"pad-{mode}-{kind}"


def floating(_):
    """Notes isolées qui reviennent en boucles de longueurs différentes (façon Eno / Ghosts)."""
    bars = rng.choice([4, 8])
    scale = SCALES[rng.choice(["mineur", "dorien", "majeur", "lydien", "phrygien"])]
    nv = rng.choice([2, 3])
    p = Pat("pad", bars, nv)
    for v in range(nv):
        L = rng.choice([11, 13, 17, 19, 23, 29])  # boucles premières entre elles : jamais deux fois pareil
        pitch = rng.choice(scale) + 12 * rng.choice([0, 1])
        start = rng.randrange(L)
        for s in range(start, bars * 16, L):
            p.note(v, s, pitch, rng.uniform(45, 85), rng.choice([2, 4, 6]))
    return p, "Notes flottantes", "ambient", "floating"


def boc_melody(_):
    """Mélodie simple de 2 à 4 notes, lente, sur 4 mesures, façon Boards of Canada."""
    scale = SCALES[rng.choice(["majeur", "dorien", "mineur", "lydien"])]
    motif_len = rng.choice([2, 3, 4])
    motif = [rng.choice(scale[:6]) + 12 for _ in range(motif_len)]
    rhythm = sorted(rng.sample(range(0, 16, 2), motif_len))
    p = Pat("melody", 4, 1)
    for b in range(4):
        m = motif if b != 3 else motif[:-1] + [rng.choice(scale) + 12]
        for i, s in enumerate(rhythm):
            nxt = rhythm[i + 1] if i + 1 < len(rhythm) else 16
            p.note(0, b * 16 + s, m[i], rng.uniform(65, 95), nxt - s)
    return p, "Mélodie nostalgique", "boc", "boc"


def dub_chord(_):
    """Accord dub techno / Basic Channel : stab mineur 7 / 9 en contretemps, répété."""
    scale = SCALES[rng.choice(["mineur", "dorien"])]
    tones = chord_tones(scale, 0, rng.choice(["7", "9", "sus2"]))[:3]
    pos = rng.choice([[3, 11], [2, 10], [3, 7, 11, 15], [6, 14], [3, 10, 14], [4, 11]])
    bars = rng.choice([1, 2, 4])
    p = Pat("stab", bars, 3)
    for b in range(bars):
        for s in pos:
            for v, n in enumerate(tones):
                p.note(v, b * 16 + s, n, rng.uniform(70, 100), 2)
    return p, "Accord dub", "dub-techno", "dub-chord"


# ------------------------------------------------------------------ IDM
def idm_drill(_):
    """Percussions cassées avec ratchets (drill) : beaucoup de silence puis des rafales."""
    bars = rng.choice([1, 2, 2, 4])
    voices = rng.choice([["SN"], ["CH"], ["SN", "CH"], ["RS", "HT"], ["PC", "SN"]])
    p = Pat("perc", bars, 1)
    for b in range(bars):
        anchors = [0] + rng.sample(range(1, 16), rng.randint(2, 5))
        for s in sorted(anchors):
            tok = rng.choice(voices)
            if rng.random() < .45: tok += rng.choice(["*2", "*3", "*4"])
            p.note(0, b * 16 + s, tok, rng.uniform(60, 125))
        if rng.random() < .5:  # rafale de fin de mesure
            for s in range(rng.choice([12, 13, 14]), 16):
                p.note(0, b * 16 + s, voices[0] + "*" + str(rng.choice([2, 3, 4])), 70 + (s - 12) * 12)
    return p, "Drill IDM", "idm", "drill"


def idm_shift_arp(_):
    """Arpège dont la boucle ne fait pas 16 pas (5, 7, 9…) : la forme change à chaque mesure."""
    scale = SCALES[rng.choice(["mineur", "dorien", "majeur", "lydien", "phrygien"])]
    L = rng.choice([5, 6, 7, 9, 10, 11])
    cell = [rng.choice(scale) + 12 * rng.choice([0, 0, 1]) for _ in range(L)]
    cell[0] = 0
    gaps = [rng.random() < .2 for _ in range(L)]; gaps[0] = False
    bars = rng.choice([2, 4])
    p = Pat("melody", bars, 1)
    for s in range(bars * 16):
        i = s % L
        if not gaps[i]: p.note(0, s, cell[i], (105 if i == 0 else 75) + rng.uniform(-6, 6))
    return p, f"Arpège glissant en {L}", "idm", f"shift{L}"


def idm_melody(_):
    """Mélodie très simple de peu de notes (Aphex) — à poser sur un rythme complexe."""
    scale = SCALES[rng.choice(["majeur", "lydien", "mineur", "dorien"])]
    notes = rng.sample(scale, rng.choice([2, 3, 4]))
    bars = rng.choice([2, 4])
    p = Pat("melody", bars, 1)
    rhythm = rng.choice([[0, 6, 12], [0, 4, 8, 12], [0, 3, 6, 10], [0, 8], [0, 2, 8, 10]])
    for b in range(bars):
        for i, s in enumerate(rhythm):
            p.note(0, b * 16 + s, notes[(i + b) % len(notes)] + 12, rng.uniform(70, 100), 3)
    return p, "Mélodie IDM", "idm", "idm-melody"


def boc_beat(_):
    """Beat hip-hop lent façon BoC (kick + caisse + charleston sur 3 voix)."""
    bars = rng.choice([1, 2])
    p = Pat("drums", bars, 3)
    kick = rng.choice([[0, 10], [0, 7, 10], [0, 3, 10], [0, 8, 10], [0, 6, 11]])
    hat_swing = rng.choice([[0, 2, 4, 6, 8, 10, 12, 14], [0, 3, 4, 7, 8, 11, 12, 15], [2, 6, 10, 14]])
    for b in range(bars):
        for s in kick: p.note(0, b * 16 + s, "BD", rng.uniform(95, 115))
        for s in [4, 12]: p.note(1, b * 16 + s, "SN", rng.uniform(100, 118))
        if rng.random() < .4: p.note(1, b * 16 + rng.choice([7, 15]), "SN", 45)
        for s in hat_swing: p.note(2, b * 16 + s, "CH", rng.uniform(50, 85))
    return p, "Beat lent hip-hop", "boc", "boc-beat"


# ------------------------------------------------------------------ APPARAT / MODERAT
def halftime_beat(_):
    bars = rng.choice([1, 2])
    p = Pat("drums", bars, 3)
    kick = rng.choice([[0, 3, 10], [0, 6, 14], [0, 11], [0, 3, 6, 11], [0, 7, 10, 14]])
    for b in range(bars):
        for s in kick: p.note(0, b * 16 + s, "BD", rng.uniform(100, 120))
        p.note(1, b * 16 + 8, rng.choice(["SN", "CL"]), 120)
        for s in rng.sample([5, 7, 13, 15], rng.randint(0, 2)): p.note(1, b * 16 + s, "SN", 40)
        hats = rng.choice([list(range(0, 16, 2)), list(range(0, 16)), [2, 6, 10, 14], [0, 3, 6, 9, 12, 14]])
        for s in hats: p.note(2, b * 16 + s, "CH", 55 + (25 if s % 4 == 2 else 0) + rng.uniform(-8, 8))
    return p, "Beat demi-temps", "moderat", "halftime"


def sub_synco(_):
    bars = rng.choice([1, 2, 4])
    pool = rng.choice([[0], [0, -2], [0, 3], [0, 5], [0, -5], [0, 7]])
    p = Pat("bass", bars, 1)
    rhythm = rng.choice([[0, 3, 10], [0, 6, 11], [0, 7, 10, 14], [0, 3, 6, 11], [0, 11]])
    for b in range(bars):
        for i, s in enumerate(rhythm):
            nxt = rhythm[i + 1] if i + 1 < len(rhythm) else 16
            n = 0 if (i == 0 or len(pool) == 1) else rng.choice(pool)
            if b % 2 == 1 and i == len(rhythm) - 1 and len(pool) > 1: n = pool[-1]
            p.note(0, b * 16 + s, n, rng.uniform(95, 120), nxt - s)
    return p, "Sub syncopée", "moderat", "sub"


def melancholic_chords(_):
    scale = SCALES[rng.choice(["mineur", "mineur", "dorien"])]
    prog = rng.choice(PROGS["mineur"])
    nv = 3
    rhythm = rng.choice([[0], [0, 6, 10], [0, 3, 8, 11], [2, 6, 10, 14], [0, 10]])
    bars = min(8, len(prog) * rng.choice([1, 2]))
    per = bars // len(prog) if bars >= len(prog) else 1
    p = Pat("stab", bars, nv); prev = None
    for b in range(bars):
        deg = prog[min(len(prog) - 1, b // max(1, per))]
        voicing = voice_lead(prev, chord_tones(scale, deg, rng.choice(["triad", "7"])), nv); prev = voicing
        for i, s in enumerate(rhythm):
            nxt = rhythm[i + 1] if i + 1 < len(rhythm) else 16
            for v, n in enumerate(voicing):
                p.note(v, b * 16 + s, n + 12, rng.uniform(70, 100), max(1, nxt - s - 1) if len(rhythm) > 1 else 16)
    return p, "Accords mélancoliques", "moderat", "melancholic"


def offbeat_pluck(_):
    scale = SCALES[rng.choice(["mineur", "dorien", "phrygien"])]
    notes = [rng.choice(scale) + 12 for _ in range(rng.choice([2, 3, 4]))]
    bars = rng.choice([1, 2, 4])
    p = Pat("melody", bars, 1)
    pos = rng.choice([[2, 6, 10, 14], [2, 5, 10, 13], [3, 6, 11, 14], [2, 7, 10, 15]])
    k = 0
    for b in range(bars):
        for s in pos:
            p.note(0, b * 16 + s, notes[k % len(notes)], rng.uniform(75, 105)); k += 1
    return p, "Pluck contretemps", "moderat", "pluck"


# ------------------------------------------------------------------ TECHNO INDUSTRIELLE
def rhythmic_noise(_):
    """Rhythmic noise : doubles croches de métal, accents durs, trous, ratchets."""
    bars = rng.choice([1, 2, 4])
    voices = rng.choice([["PC"], ["CB", "PC"], ["RS", "PC"], ["HT", "PC"], ["CL", "RS"]])
    p = Pat("perc", bars, 1)
    acc = set(rng.sample(range(16), rng.randint(3, 6)))
    holes = set(rng.sample([0, 4, 8, 12], rng.randint(1, 4)))
    for b in range(bars):
        for s in range(16):
            if s in holes: continue
            if s not in acc and rng.random() < .35: continue
            tok = voices[0] if s in acc else voices[-1]
            if rng.random() < .12: tok += "*2"
            p.note(0, b * 16 + s, tok, 122 if s in acc else rng.uniform(55, 85))
    return p, "Rhythmic noise", "industrial-techno", "noise"


def droney_bass(_):
    """Basse bourdonnante façon Perc / Ancient Methods (~120-130 BPM) : une note, accents qui grondent."""
    bars = rng.choice([1, 2, 4])
    pool = rng.choice([[0], [0, 1], [0, -2], [0, 12], [0, 6]])
    p = Pat("bass", bars, 1)
    shape = rng.choice(["..xx", ".xxx", ".x.x", "..x.", ".xx."])
    acc = rng.randrange(1, 4)
    for b in range(bars):
        for beat in range(4):
            for i, c in enumerate(shape):
                if c != "x": continue
                s = b * 16 + beat * 4 + i
                n = 0 if (len(pool) == 1 or rng.random() < .8) else pool[1]
                p.note(0, s, n, 120 if i == acc else rng.uniform(70, 90), 2 if i == 3 or shape[i + 1:i + 2] == "." else 1)
    return p, "Basse grondante", "industrial-techno", "droney"


def ebm_techno_seq(_):
    """Séquence hybride EBM-techno (Orphx / Adam X) : doubles croches entre kicks, gate qui varie."""
    bars = rng.choice([2, 4])
    pool = rng.choice([[0, 12], [0, 1], [0, 3, 12], [0, 7], [0]])
    p = Pat("bass", bars, 1)
    gates = [".xxx", "x.xx", ".x.x", "xx.x", "..xx"]
    g1, g2 = rng.choice(gates), rng.choice(gates)
    for b in range(bars):
        for beat in range(4):
            g = g2 if (beat == 3 and b % 2 == 1) else g1
            for i, c in enumerate(g):
                if c == "x":
                    n = 0 if (i != 3 or len(pool) == 1) else rng.choice(pool[1:])
                    p.note(0, b * 16 + beat * 4 + i, n, 110 if i == 2 else rng.uniform(78, 95))
    return p, "Séquence EBM-techno", "industrial-techno", "ebm-techno"


# ------------------------------------------------------------------ TECHNO SUÉDOISE EN BOUCLES
def swedish_tom_loop(_):
    """Boucle de toms / percussions d'une mesure qui tourne, variation en mesure 4 (Drumcode 90s)."""
    bars = rng.choice([2, 4, 4])
    voices = rng.choice([["LT", "MT"], ["MT", "HT"], ["LT", "MT", "HT"], ["PC", "LT"], ["CB", "PC"]])
    cell = [rng.random() < .45 for _ in range(16)]
    for k in (0, 4, 8, 12):  # on évite les toms graves sur le kick
        if voices[0] == "LT": cell[k] = False
    if not any(cell): cell[2] = True
    pitches = [rng.choice(voices) for _ in range(16)]
    p = Pat("perc", bars, 1)
    for b in range(bars):
        c = cell[:]
        if b == bars - 1:
            for s in range(12, 16): c[s] = rng.random() < .7
        for s in range(16):
            if c[s]: p.note(0, b * 16 + s, pitches[s], 115 if s % 4 == 2 else rng.uniform(70, 95))
    return p, "Boucle de toms", "swedish-techno", "tom-loop"


def swedish_ride(_):
    bars = rng.choice([1, 2])
    p = Pat("perc", bars, 1)
    tok = rng.choice(["CY", "CH", "SH"])
    for b in range(bars):
        for s in range(16):
            v = {0: 70, 1: 55, 2: 110, 3: 60}[s % 4] + rng.uniform(-6, 6)
            p.note(0, b * 16 + s, tok, v)
    return p, "Ride en doubles croches", "swedish-techno", "ride16"


def one_note_stab(_):
    """Stab percussif d'une seule note, en boucle (le peu de mélodie de la techno en boucles)."""
    bars = rng.choice([1, 2, 4])
    pos = rng.choice([[3], [3, 11], [2, 7, 10], [6, 14], [3, 6, 11, 14], [1, 7, 13], [3, 9, 15]])
    n = rng.choice([0, 0, 12, 7, -5, 3])
    p = Pat("stab", bars, 1)
    for b in range(bars):
        for s in pos: p.note(0, b * 16 + s, n, rng.uniform(90, 120))
    return p, "Stab une note", "swedish-techno", "stab1"


# ------------------------------------------------------------------ HEALTH / NOISE ROCK
def tribal_toms(_):
    bars = rng.choice([1, 2])
    p = Pat("drums", bars, 2)
    for b in range(bars):
        for s in rng.choice([[0, 3, 6, 8, 11, 14], [0, 2, 4, 6, 8, 10, 12, 14], [0, 3, 8, 10, 11]]):
            p.note(0, b * 16 + s, rng.choice(["LT", "MT"]), rng.uniform(100, 124))
        p.note(1, b * 16 + 8, "SN", 125)
        if rng.random() < .5: p.note(1, b * 16 + 4, "SN", 125)
    return p, "Toms tribaux noise rock", "noise-rock", "tribal"


def fuzz_bass(_):
    bars = rng.choice([1, 2])
    p = Pat("bass", bars, 1)
    rhythm = rng.choice([[0, 1, 2, 3, 8, 9, 10], [0, 3, 6, 8, 11, 14], [0, 2, 3, 8, 10, 11], [0, 4, 6, 8, 12, 14]])
    pool = rng.choice([[0, 1], [0, -2], [0, 3], [0, 5, 6]])
    for b in range(bars):
        for i, s in enumerate(rhythm):
            n = 0 if i == 0 or rng.random() < .65 else rng.choice(pool[1:])
            p.note(0, b * 16 + s, n, 118 + rng.uniform(-5, 5))
    return p, "Basse fuzz", "noise-rock", "fuzz"


# ------------------------------------------------------------------ DARK ELECTRO (façon :wumpscut:)
HARM = [0, 2, 3, 5, 7, 8, 11]  # mineur harmonique (sensible = couleur gothique)


def gothic_lead(_):
    """Mélodie sombre mais accrocheuse (mineur harmonique), question-réponse sur 2 ou 4 mesures."""
    scale = rng.choice([HARM, MINOR, HARM])
    rhythm = rng.choice([[0, 2, 4, 6, 8, 10, 12, 14], [0, 3, 6, 8, 10, 12], [0, 4, 6, 8, 12, 14], [0, 2, 3, 6, 8, 11, 12, 14]])
    def phrase(end_deg):
        degs = [0]; d = 0
        for _ in range(len(rhythm) - 2):
            d = max(-2, min(7, d + rng.choice([-2, -1, -1, 1, 1, 2, 3])))
            degs.append(d)
        degs.append(end_deg)
        return [scale[x % 7] + 12 * (x // 7) + 12 for x in degs]
    A, B = phrase(rng.choice([4, 6])), phrase(0)   # A finit en suspens (V ou sensible), B revient à la tonique
    bars = rng.choice([2, 4])
    p = Pat("melody", bars, 1)
    for b in range(bars):
        m = A if b % 2 == 0 else B
        for i, s in enumerate(rhythm):
            nxt = rhythm[i + 1] if i + 1 < len(rhythm) else 16
            p.note(0, b * 16 + s, m[i], rng.uniform(85, 115) + (8 if s % 4 == 0 else 0), max(1, nxt - s - 1))
    return p, "Lead gothique", "dark-electro", "gothic-lead"


def gothic_strings(_):
    """Cordes / chœurs lents en mineur harmonique : i – VI – iv – V (V majeur grâce à la sensible)."""
    prog = rng.choice([[0, 5, 3, 4], [0, 3, 4, 0], [0, 5, 6, 4], [0, 4, 5, 3], [0, 0, 5, 4]])
    nv = rng.choice([3, 4])
    bars = len(prog) * rng.choice([1, 2])
    per = bars // len(prog)
    p = Pat("pad", bars, nv); prev = None
    for ci, deg in enumerate(prog):
        voicing = voice_lead(prev, chord_tones(HARM, deg), nv); prev = voicing
        for v, n in enumerate(voicing):
            p.note(v, ci * per * 16, n, rng.uniform(70, 95), per * 16)
    return p, "Cordes gothiques", "dark-electro", "gothic-strings"


def staccato_stabs(_):
    """Stabs d'accords staccato syncopés (mineur / mineur harmonique)."""
    scale = rng.choice([HARM, MINOR])
    prog = rng.choice([[0], [0, 5], [0, 3], [0, 4], [0, 5, 3, 4]])
    rhythm = rng.choice([[0, 3, 6, 10, 12], [0, 2, 3, 8, 10, 11], [0, 3, 8, 11, 14], [0, 6, 8, 14]])
    bars = max(len(prog), rng.choice([1, 2, 4]))
    p = Pat("stab", bars, 3); prev = None
    for b in range(bars):
        voicing = voice_lead(prev, chord_tones(scale, prog[b % len(prog)]), 3); prev = voicing
        for s in rhythm:
            for v, n in enumerate(voicing):
                p.note(v, b * 16 + s, n + 12, rng.uniform(95, 122), 1)
    return p, "Stabs staccato", "dark-electro", "stabs"


def dark_arp(_):
    """Arpège de synthé sombre en doubles croches sur accords mineurs (gothique)."""
    scale = rng.choice([HARM, MINOR, PHRYG])
    prog = rng.choice([[0], [0, 5], [0, 3], [0, 5, 3, 4], [0, 1]])
    shape = rng.choice([[0, 1, 2, 1], [0, 1, 2, 3], [0, 2, 1, 2], [2, 1, 0, 1], [0, 1, 2, 3, 2, 1]])
    bars = max(len(prog), rng.choice([1, 2, 4]))
    p = Pat("melody", bars, 1)
    for b in range(bars):
        t = chord_tones(scale, prog[b % len(prog)]); t = t + [t[0] + 12]
        for s in range(16):
            n = t[shape[s % len(shape)] % len(t)]
            p.note(0, b * 16 + s, n + 12, 105 if s % 4 == 0 else rng.uniform(70, 88))
    return p, "Arpège sombre", "dark-electro", "dark-arp"


PLAN = [  # (fonction, fichier, nombre)
    (drone, "ambient", 220), (pad_prog, "ambient", 700), (floating, "ambient", 300), (dub_chord, "ambient", 150),
    (boc_melody, "idm", 250), (boc_beat, "idm", 150), (idm_drill, "idm", 450), (idm_shift_arp, "idm", 350),
    (idm_melody, "idm", 200),
    (halftime_beat, "moderat", 250), (sub_synco, "moderat", 200), (melancholic_chords, "moderat", 300),
    (offbeat_pluck, "moderat", 200),
    (rhythmic_noise, "industrial_techno", 400), (droney_bass, "industrial_techno", 250),
    (ebm_techno_seq, "industrial_techno", 250),
    (swedish_tom_loop, "swedish", 350), (swedish_ride, "swedish", 60), (one_note_stab, "swedish", 120),
    (tribal_toms, "noise_rock", 100), (fuzz_bass, "noise_rock", 100),
    (gothic_lead, "dark_electro", 300), (gothic_strings, "dark_electro", 150), (staccato_stabs, "dark_electro", 200),
    (dark_arp, "dark_electro", 200),
]
TYPE = {"pad": "pad", "melody": "melody", "stab": "melody", "bass": "bass", "perc": "perc", "drums": "drums"}


def main():
    out = {}; seen = set(); counters = {}
    for fn, dest, target in PLAN:
        made = tries = 0
        while made < target and tries < target * 60:
            tries += 1
            p, label, genre, tag = fn(None)
            if p.empty() or (p.kind, p.key()) in seen: continue
            seen.add((p.kind, p.key())); made += 1
            counters[fn.__name__] = counters.get(fn.__name__, 0) + 1
            n = counters[fn.__name__]
            head = (f'@{TYPE[p.kind]} id=x-{fn.__name__.replace("_", "-")}-{n:04d} name="{label} — {p.nv} voix, '
                    f'{p.bars} mes. #{n:03d}" genre={genre} bars={p.bars} steps=16 voices={p.nv} tags={tag} src=gen-textures')
            out.setdefault(dest, []).append(p.render(head))
    hdr = ("# Textures, ambient, IDM, Apparat/Moderat, techno industrielle, techno suédoise, noise rock —\n"
           "# tools/generate_textures.py.  Polyphonie : N/N2/N3/N4 + V/V2/V3/V4 par mesure.\n"
           "# Ratchet : suffixe *2 *3 *4 = note répétée dans le pas.  Notes = intervalles depuis la tonique.\n\n")
    for k, items in out.items():
        (LIB / f"tex_{k}.txt").write_text(hdr + "\n".join(items))
        print(k, len(items))


if __name__ == "__main__":
    main()
