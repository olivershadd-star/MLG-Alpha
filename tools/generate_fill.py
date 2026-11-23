"""Cinquième générateur : complète les familles pauvres et ajoute de nouvelles catégories.
  - Electro / breaks : percussions électro (808), ghost snares de breaks, leads électro (bleeps, arpèges).
  - Minimal / dub : clics, rims, shakers clairsemés ; accords dub variés ; blips minimaux.
  - Trance / rave : basses roulantes trance, percussions trance, stabs rave.
  - Acid : nouvelles lignes 303 (accents, slides, sauts d'octave, silences).
  - Percussions légères : clics, ticks, micro-percussions douces, textures rythmiques (ambient / IDM).
  - Les 4 accords (I, IV, V, vi) : enchaînements cycliques, chaque accord dure 1 à 4 temps.
  - Batteries complètes : rock, metal, metal industriel, metal progressif, jazz (shuffle), contretemps.
    Tout est en 4 temps, sur 16 pas par mesure.
Format : comme tex_*.txt.
Usage : python3 tools/generate_fill.py   (écrit Library/fill_*.txt, résultat déterministe)"""
import itertools
import random
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "Library"
rng = random.Random(4004)

MAJOR = [0, 2, 4, 5, 7, 9, 11]
MINOR = [0, 2, 3, 5, 7, 8, 10]
PHRYG = [0, 1, 3, 5, 7, 8, 10]


class Pat:
    def __init__(self, kind, bars, voices=1, steps=16):
        self.kind, self.bars, self.nv, self.steps = kind, bars, voices, steps
        n = steps * bars
        self.N = [["."] * n for _ in range(voices)]
        self.V = [["."] * n for _ in range(voices)]

    def note(self, v, s, tok, vel, length=1):
        if s < 0 or s >= len(self.N[v]): return
        self.N[v][s] = str(tok); self.V[v][s] = str(int(max(1, min(127, vel))))
        for k in range(s + 1, min(len(self.N[v]), s + length)):
            if self.N[v][k] == ".": self.N[v][k] = "-"
            else: break

    def empty(self): return all(t in ".-" for r in self.N for t in r)
    def key(self): return f"{self.steps}|" + " | ".join(" ".join(r) for r in self.N)

    def render(self, head):
        out = [head]; st = self.steps
        for b in range(self.bars):
            for v in range(self.nv):
                sfx = "" if v == 0 else str(v + 1)
                out.append(f"N{sfx:<2s}" + " ".join(self.N[v][b * st:(b + 1) * st]))
                out.append(f"V{sfx:<2s}" + " ".join(self.V[v][b * st:(b + 1) * st]))
        return "\n".join(out) + "\n"


def mv(i, lo, hi):
    base = {0: 1.0, 2: .7, 1: .4, 3: .5}[i % 4]
    return lo + (hi - lo) * base + rng.uniform(-5, 5)


# ------------------------------------------------------------------ ELECTRO / BREAKS
def electro_perc(_):
    bars = rng.choice([1, 2, 4])
    voices = rng.choice([["CB"], ["CL"], ["CH"], ["CH", "OH"], ["RS"], ["CB", "CL"], ["HT", "MT", "LT"]])
    p = Pat("perc", bars)
    base = [rng.random() < .35 for _ in range(16)]
    if voices[0] in ("CH",): base = [rng.random() < .8 for _ in range(16)]
    for b in range(bars):
        row = base[:] if b % 2 == 0 else [x if rng.random() < .85 else not x for x in base]
        for s in range(16):
            if row[s]: p.note(0, b * 16 + s, rng.choice(voices), mv(s, 70, 120))
    return p, "Percussion électro", "electro", "electro-perc"


def ghost_snare(_):
    """Caisse claire de break : coups forts sur 2 et 4, notes fantômes autour."""
    bars = rng.choice([1, 2])
    p = Pat("perc", bars)
    for b in range(bars):
        for s in [4, 12]: p.note(0, b * 16 + s, "SN", 120)
        for s in rng.sample([1, 3, 6, 7, 9, 10, 11, 14, 15], rng.randint(2, 5)):
            p.note(0, b * 16 + s, "SN", rng.uniform(30, 55))
    return p, "Caisse de break (ghost notes)", "breaks", "ghost-snare"


def electro_lead(_):
    """Bleeps et arpèges électro (Kraftwerk / Drexciya) : mineur ou phrygien, motif de 2 à 5 notes."""
    scale = rng.choice([MINOR, PHRYG, [0, 3, 5, 7, 10]])
    motif = [rng.choice(scale) + 12 * rng.choice([1, 1, 2]) for _ in range(rng.randint(2, 5))]
    motif[0] = 12
    rhythm = rng.choice([[0, 3, 6, 8, 11, 14], [0, 2, 4, 6, 8, 10, 12, 14], [0, 3, 6, 9, 12], [0, 1, 4, 6, 8, 9, 12, 14]])
    bars = rng.choice([1, 2, 4])
    p = Pat("melody", bars)
    k = 0
    for b in range(bars):
        for s in rhythm:
            p.note(0, b * 16 + s, motif[k % len(motif)], mv(s, 80, 115)); k += 1
    return p, "Lead électro", "electro", "electro-lead"


# ------------------------------------------------------------------ MINIMAL / DUB
def minimal_click(_):
    bars = rng.choice([1, 2, 4])
    voices = rng.choice([["RS"], ["PC"], ["SH"], ["RS", "PC"], ["CL"], ["CB"]])
    n = rng.randint(1, 4)
    pos = sorted(rng.sample([1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15], n))
    p = Pat("perc", bars)
    for b in range(bars):
        pp = pos if (b % 4 != 3 or rng.random() < .5) else sorted(rng.sample([2, 3, 6, 7, 10, 11, 14, 15], n))
        for s in pp: p.note(0, b * 16 + s, rng.choice(voices), rng.uniform(50, 100))
    return p, "Clic minimal", "minimal", "minimal-click"


def dub_chords(_):
    """Accords dub variés : mineur 7 / 9 / sus, renversements, positions et longueurs variables."""
    scale = rng.choice([MINOR, [0, 2, 3, 5, 7, 9, 10]])
    root_deg = rng.choice([0, 0, 0, 3, 5])
    kind = rng.choice(["m7", "m9", "sus2", "m11", "triad"])
    t = [scale[root_deg % 7] + 12 * (root_deg // 7)]
    for step in {"m7": [2, 4, 6], "m9": [2, 4, 8], "sus2": [1, 4], "m11": [2, 6, 10], "triad": [2, 4]}[kind]:
        d = root_deg + step; t.append(scale[d % 7] + 12 * (d // 7))
    inv = rng.randint(0, len(t) - 1)
    voicing = sorted(t[inv:] + [x + 12 for x in t[:inv]])
    pos = rng.choice([[3], [3, 11], [2, 10], [6, 14], [3, 10], [4, 11], [3, 7, 11, 15], [5, 13], [2, 7, 14]])
    length = rng.choice([1, 2, 3])
    bars = rng.choice([1, 2, 4])
    nv = len(voicing)
    p = Pat("stab", bars, nv)
    for b in range(bars):
        for s in pos:
            if b % 4 == 3 and rng.random() < .3: continue
            for v, n in enumerate(voicing): p.note(v, b * 16 + s, n, rng.uniform(65, 100), length)
    return p, f"Accord dub {kind}", "dub-techno", f"dub-{kind}"


def minimal_blip(_):
    scale = rng.choice([MINOR, [0, 3, 5, 7, 10], [0, 2, 3, 7, 10]])
    notes = [rng.choice(scale) + 12 for _ in range(rng.choice([1, 2, 3]))]
    pos = sorted(rng.sample(range(16), rng.randint(2, 5)))
    bars = rng.choice([1, 2, 4])
    p = Pat("melody", bars)
    for b in range(bars):
        for i, s in enumerate(pos): p.note(0, b * 16 + s, notes[(i + b) % len(notes)], rng.uniform(60, 100))
    return p, "Blip minimal", "minimal", "blip"


# ------------------------------------------------------------------ TRANCE / RAVE
def trance_bass(_):
    pool = rng.choice([[0], [0, 12], [0, 7], [0, -2], [0, 5]])
    cell = rng.choice([".xxx", "..xx", ".x.x", "..x.", "..xx", ".xx."])
    bars = rng.choice([1, 2, 4])
    p = Pat("bass", bars)
    prog = rng.choice([[0], [0, 0, -4, -2], [0, -4], [0, 5, 3, -2], [0, 0, 5, 3]])
    for b in range(bars):
        shift = prog[b % len(prog)]
        for beat in range(4):
            for i, c in enumerate(cell):
                if c == "x":
                    n = shift + (0 if i != 3 or len(pool) == 1 else rng.choice(pool[1:]))
                    p.note(0, b * 16 + beat * 4 + i, n, 110 if i == 2 else rng.uniform(80, 95))
    return p, "Basse trance roulante", "trance", "trance-bass"


def trance_perc(_):
    bars = rng.choice([1, 2, 4])
    kind = rng.choice(["oh", "16th", "clap", "roll"])
    p = Pat("perc", bars)
    for b in range(bars):
        if kind == "oh":
            for s in [2, 6, 10, 14]: p.note(0, b * 16 + s, "OH", rng.uniform(95, 115))
        elif kind == "16th":
            skip = rng.choice([set(), {0, 4, 8, 12}, {1, 9}, {3, 11}])
            tok = rng.choice(["CH", "SH", "CY"])
            for s in range(16):
                if s not in skip: p.note(0, b * 16 + s, tok, {0: 60, 2: 105, 1: 50, 3: 65}[s % 4] + rng.uniform(-6, 6))
        elif kind == "clap":
            for s in [4, 12] + rng.sample([7, 11, 15], rng.randint(0, 1)): p.note(0, b * 16 + s, "CL", 115)
        else:
            start = 16 * b + (0 if b < bars - 1 else 8)
            for s in range(16 * b, 16 * b + 16):
                if b == bars - 1 and s >= start: p.note(0, s, "SN", 50 + (s - start) * 9)
                elif s % 4 == 0: p.note(0, s, "SN", 70)
    return p, f"Percussion trance ({kind})", "trance", f"trance-{kind}"


def rave_stab(_):
    """Stabs rave (accords mineurs, rythmes piano house / hoover)."""
    scale = MINOR
    deg = rng.choice([0, 0, 5, 3])
    t = [scale[(deg + k) % 7] + 12 * ((deg + k) // 7) for k in (0, 2, 4)]
    pos = rng.choice([[0, 3, 6, 8, 11, 14], [0, 3, 6, 10], [2, 6, 10, 14], [0, 6, 12], [0, 3, 7, 10, 13]])
    bars = rng.choice([1, 2])
    p = Pat("stab", bars, 3)
    for b in range(bars):
        for s in pos:
            for v, n in enumerate(t): p.note(v, b * 16 + s, n + 12, rng.uniform(95, 120), 1)
    return p, "Stab rave", "rave", "rave-stab"


# ------------------------------------------------------------------ ACID
def acid_line(_):
    scale = rng.choice([MINOR, PHRYG, [0, 3, 5, 7, 10], [0, 1, 3, 6, 7, 10], [0, 2, 3, 5, 7, 9, 10]])
    bars = rng.choice([1, 1, 2, 2, 4])
    density = rng.choice([.6, .75, .9, 1.0])
    acc_every = rng.choice([None, 3, 4, 5])
    base = [rng.random() < density for _ in range(16)]; base[0] = True
    pitches = []
    cur = 0
    for s in range(16):
        r = rng.random()
        if s == 0 or r < .45: cur = 0
        elif r < .6: cur = 12
        elif r < .7: cur = rng.choice([-12, 24]) if rng.random() < .3 else 12
        else: cur = rng.choice(scale) + rng.choice([0, 0, 12])
        pitches.append(cur)
    p = Pat("acid", bars)
    for b in range(bars):
        row = base if b % 2 == 0 else [x if rng.random() < .85 else not x for x in base]
        for s in range(16):
            if not row[s]: continue
            tok = str(pitches[s])
            accent = (acc_every and s % acc_every == 0) or (not acc_every and rng.random() < .25)
            if accent: tok += "a"
            if s < 15 and row[s + 1] and rng.random() < .18: tok += "s"
            p.note(0, b * 16 + s, tok, 122 if accent else rng.uniform(72, 92))
    return p, "Acid", "acid", "acid2"


# ------------------------------------------------------------------ PERCUSSIONS LÉGÈRES
def light_perc(_):
    """Clics, ticks, micro-percussions : vélocités basses, polymètres lents, beaucoup d'air."""
    bars = rng.choice([2, 4, 4])
    voice = rng.choice(["RS", "SH", "CH", "PC", "CB", "CY"])
    style = rng.choice(["poly", "sparse", "tick16", "swing"])
    p = Pat("perc", bars)
    if style == "poly":
        L = rng.choice([3, 5, 7, 9, 11])
        for s in range(rng.randrange(L), bars * 16, L): p.note(0, s, voice, rng.uniform(25, 60))
    elif style == "sparse":
        for s in range(bars * 16):
            if rng.random() < .12: p.note(0, s, voice, rng.uniform(20, 55))
    elif style == "tick16":
        for s in range(bars * 16):
            if rng.random() < .7: p.note(0, s, voice, 30 + (20 if s % 4 == 2 else 0) + rng.uniform(-8, 8))
    else:
        for s in range(bars * 16):
            if s % 4 in (0, 3) and rng.random() < .8: p.note(0, s, voice, (45 if s % 4 == 0 else 28) + rng.uniform(-6, 6))
    if p.empty(): p.note(0, 0, voice, 40)
    return p, f"Percussion légère ({style})", "ambient", f"light-{style}"


# ------------------------------------------------------------------ LES 4 ACCORDS
FOUR = {"I": 0, "IV": 3, "V": 4, "vi": 5}  # degrés dans la gamme majeure


def four_chords(seq, beats, style):
    """seq = ordre des accords ; beats = durée de chaque accord en temps (1 à 4)."""
    total_beats = len(seq) * beats
    bars = max(1, (total_beats + 3) // 4)
    nv = 4 if style == "pad" else 3
    p = Pat("pad" if style == "pad" else "stab", bars, nv)
    prev = None
    from_lead = None
    for i, name in enumerate(seq):
        deg = FOUR[name]
        tones = [MAJOR[(deg + k) % 7] + 12 * ((deg + k) // 7) for k in (0, 2, 4)]
        # conduite des voix : chaque voix va vers la note la plus proche, basse sur la fondamentale
        cands = sorted({t + 12 * o for t in tones for o in range(-1, 3)})
        if prev is None:
            voicing = sorted(tones + ([tones[0] + 12] if nv == 4 else []))
        else:
            voicing = []
            for v in prev:
                opts = [c for c in cands if c not in voicing]
                voicing.append(min(opts, key=lambda c: abs(c - v)))
            voicing = sorted(voicing)
            roots = [c for c in cands if (c - tones[0]) % 12 == 0 and c < voicing[1]]
            if roots: voicing[0] = min(roots, key=lambda c: abs(c - prev[0]))
            for t in tones:
                if not any((x - t) % 12 == 0 for x in voicing):
                    pcs = [x % 12 for x in voicing]
                    dup = [j for j in range(1, nv) if pcs.count(pcs[j]) > 1]
                    j = dup[-1] if dup else nv - 1
                    voicing[j] = min([c for c in cands if (c - t) % 12 == 0], key=lambda c: abs(c - voicing[j]))
            voicing = sorted(voicing)
        prev = voicing
        start = i * beats * 4; length = beats * 4
        if style == "pad":
            for v, n in enumerate(voicing): p.note(v, start, n, 80 - v * 4, length)
        elif style == "stab":
            for s in range(start, start + length, 4):
                for v, n in enumerate(voicing): p.note(v, s + 2, n + 12, 100, 1)
        else:  # arpège : une voix, les notes de l'accord en croches
            for k, s in enumerate(range(start, start + length, 2)):
                p.note(0, s, voicing[k % nv] + 12, 95 if k % 4 == 0 else 78, 2)
    if style == "arp":
        p.nv = 1; p.N = p.N[:1]; p.V = p.V[:1]
    return p


# ------------------------------------------------------------------ BATTERIES COMPLÈTES
def decorate(steps, bars, rows):
    """Ajoute des variations de batteur : notes fantômes, crash d'entrée, relance de kick, roulement de fin,
    charleston ouvert, variantes de charleston. Chaque option est tirée au hasard."""
    beat = steps // (5 if steps == 20 else (3 if steps == 12 else 4))
    last = bars - 1
    base = {k: (v if callable(v) else (lambda b, v=v: v)) for k, v in rows.items()}
    out = dict(base)
    snare = "SN" if "SN" in rows else None
    if snare and rng.random() < .5:  # notes fantômes de caisse claire
        ghosts = rng.sample([s for s in range(steps) if s % beat != 0], min(3, steps // 4))[:rng.randint(1, 3)]
        out[snare] = lambda b, f=base[snare], g=ghosts: f(b) + [(s, rng.uniform(28, 50)) for s in g]
    if "BD" in rows and rng.random() < .5:  # relance de kick en fin de phrase
        extra = rng.choice([[steps - 1], [steps - 2], [steps - 3, steps - 1]])
        out["BD"] = lambda b, f=base["BD"], e=extra: f(b) + ([(s, 95) for s in e] if b == last else [])
    hat = next((h for h in ("CH", "CY") if h in rows), None)
    if hat and rng.random() < .5:  # variante de charleston : plus dense ou plus clair, accents décalés
        mode = rng.choice(["dense", "airy", "acc-off"])
        def hv(b, f=base[hat], m=mode):
            hits = f(b)
            if m == "dense": return sorted(set(hits + [(s, 55) for s in range(1, steps, 2)]))
            if m == "airy": return [h for h in hits if h[0] % beat == 0] or hits
            return [(s, v + (20 if s % beat == beat // 2 else -10)) for s, v in hits]
        out[hat] = hv
    if rng.random() < .4:  # charleston ouvert en fin de mesure
        pos = rng.choice([steps - 2, steps - beat // 2])
        out["OH"] = lambda b, p=pos: [(p, 95)]
    if bars > 1 and rng.random() < .45:  # crash d'entrée
        out["CY"] = lambda b, f=out.get("CY"): (f(b) if f else []) + ([(0, 118)] if b == 0 else [])
    if bars > 1 and rng.random() < .5:  # roulement de toms / caisse sur la fin de la dernière mesure
        roll = rng.choice([["SN"], ["HT", "MT", "LT"], ["SN", "HT", "LT"]])
        start = steps - rng.choice([beat, 2 * beat])
        def fill(b, r=roll, st=start):
            if b != last: return []
            return [(s, 80 + (s - st) * 4) for s in range(st, steps)]
        for i, t in enumerate(roll):
            prevf = out.get(t)
            out[t] = (lambda b, i=i, n=len(roll), pf=prevf, fl=fill: (
                [h for h in (pf(b) if pf else []) if not (b == last and h[0] >= start)] +
                [h for k, h in enumerate(fl(b)) if k * n // max(1, len(fl(b))) == i]))
    return out


def kit(steps, bars, rows):
    """rows : {instrument: [(pas, vélocité), ...] pour une mesure} ou fonction(b) -> liste."""
    rows = decorate(steps, bars, rows)
    inst = list(rows)
    p = Pat("drums", bars, len(inst), steps)
    for b in range(bars):
        for v, name in enumerate(inst):
            hits = rows[name](b) if callable(rows[name]) else rows[name]
            for s, vel in hits: p.note(v, b * steps + s, name, vel + rng.uniform(-5, 5))
    return p


def drums_rock(_):
    bars = rng.choice([1, 2])
    kick = rng.choice([[0, 8], [0, 6, 8], [0, 8, 10], [0, 3, 8], [0, 7, 8, 10], [0, 2, 8, 11]])
    hat = rng.choice([range(0, 16, 2), range(0, 16), range(0, 16, 4)])
    ride = rng.random() < .25
    return kit(16, bars, {"BD": [(s, 112) for s in kick], "SN": [(4, 120), (12, 120)],
                          ("CY" if ride else "CH"): [(s, 95 if s % 4 == 0 else 75) for s in hat]}), "Batterie rock", "rock", "rock"


def drums_metal(_):
    bars = rng.choice([1, 2])
    style = rng.choice(["double", "gallop", "blast", "halftime"])
    if style == "double":
        kick = rng.choice([range(16), range(0, 16, 2), [s for s in range(16) if s % 8 != 7]])
        rows = {"BD": [(s, 105) for s in kick], "SN": [(4, 122), (12, 122)], "CY": [(s, 100) for s in range(0, 16, rng.choice([2, 4]))]}
    elif style == "gallop":
        rows = {"BD": [(s, 108) for s in range(16) if s % 4 != 1], "SN": [(4, 122), (12, 122)], "CH": [(s, 90) for s in range(0, 16, 2)]}
    elif style == "blast":
        rows = {"BD": [(s, 110) for s in range(0, 16, 2)], "SN": [(s, 115) for s in range(1, 16, 2)], "CY": [(s, 95) for s in range(0, 16, 2)]}
    else:
        rows = {"BD": [(s, 110) for s in rng.choice([[0, 2, 3, 10, 11], [0, 3, 6, 11], [0, 1, 2, 10, 14], [0, 6, 7, 14]])],
                "SN": [(8, 124)], "CY": [(s, 100) for s in range(0, 16, rng.choice([2, 4]))]}
    return kit(16, bars, rows), f"Batterie metal ({style})", "metal", f"metal-{style}"


def drums_indus_metal(_):
    bars = rng.choice([1, 2])
    kick = rng.choice([[0, 3, 6, 8, 11, 14], [0, 1, 2, 8, 9, 10], [0, 4, 8, 12], [0, 3, 8, 10, 11]])
    return kit(16, bars, {"BD": [(s, 115) for s in kick], "SN": [(4, 124), (12, 124)],
                          "PC": [(s, 105) for s in rng.sample(range(16), rng.randint(2, 4))],
                          "CH": [(s, 80) for s in range(0, 16, 2)]}), "Batterie metal industriel", "industrial-metal", "indus-metal"


def drums_prog(_):
    """Metal progressif : groupes de 3 / 5 / 7 doubles croches au kick contre une caisse en 4/4 (polymètre)."""
    L = rng.choice([3, 5, 7])
    bars = rng.choice([2, 4])
    pattern = [0] + rng.sample(range(1, L), rng.randint(0, L // 2))
    return kit(16, bars, {"BD": lambda b: [(s, 112) for s in range(16) if (b * 16 + s) % L in pattern],
                          "SN": [(4, 122), (12, 122)], "CY": [(s, 95) for s in range(0, 16, 4)]}), f"Batterie metal prog (kick en {L})", "prog-metal", f"prog-{L}"


def drums_jazz(_):
    """Jazz sur la grille de 16 pas : triolets arrondis (« ding ding-a ding » = pas 0, 4, 7, 8, 12, 15),
    charleston au pied sur 2 et 4, comping libre de la caisse et du kick."""
    bars = rng.choice([1, 2, 4])
    ride = rng.choice([[(0, 95), (4, 90), (7, 65), (8, 95), (12, 90), (15, 65)],
                       [(0, 95), (4, 90), (8, 95), (12, 90)],
                       [(0, 95), (3, 60), (4, 90), (7, 65), (8, 95), (11, 60), (12, 90), (15, 65)]])
    return kit(16, bars, {"CY": ride, "CH": [(4, 70), (12, 70)],
                          "SN": lambda b: [(s, rng.uniform(35, 75)) for s in rng.sample([3, 7, 10, 11, 15], rng.randint(0, 2))],
                          "BD": lambda b: [(s, rng.uniform(40, 70)) for s in rng.sample([0, 8, 10, 15], rng.randint(0, 2))]}), "Batterie jazz (shuffle)", "jazz", "jazz-swing"


def drums_offbeat(_):
    """Batterie à contretemps : le kick évite les temps, caisse décalée (reggae one drop, dub, contretemps)."""
    bars = rng.choice([1, 2])
    style = rng.choice(["onedrop", "steppers-off", "offkick"])
    if style == "onedrop":
        rows = {"BD": [(8, 110)], "RS": [(8, 115)] + ([(rng.choice([3, 11, 14]), 60)] if rng.random() < .5 else []),
                "CH": [(s, 75) for s in rng.choice([range(2, 16, 4), range(0, 16, 2), [2, 3, 6, 7, 10, 11, 14, 15]])]}
    elif style == "steppers-off":
        rows = {"BD": [(s, 108) for s in rng.choice([[2, 6, 10, 14], [2, 6, 10, 14, 15], [3, 7, 11, 15]])],
                "SN": [(4, 115), (12, 115)], "CH": [(s, 70) for s in range(0, 16, rng.choice([1, 2]))]}
    else:
        rows = {"BD": [(s, 110) for s in rng.sample([2, 3, 6, 7, 10, 11, 14, 15], 3)], "SN": [(8, 120)], "CH": [(s, 75) for s in range(0, 16, 2)]}
    return kit(16, bars, rows), f"Batterie à contretemps ({style})", "offbeat", f"offbeat-{style}"


# ------------------------------------------------------------------ TRIOLETS (toujours en 4/4)
# grid=1/8T : 12 pas par mesure (3 par temps) ; grid=1/16T : 24 pas par mesure (6 par temps).
def triplet_hats(_):
    steps = rng.choice([12, 24])
    per = steps // 4
    bars = rng.choice([1, 2, 4])
    tok = rng.choice(["CH", "CY", "SH", "RS", "CH"])
    p = Pat("perc", bars, 1, steps)
    keep = rng.choice(["all", "skip-mid", "first-last", "random"])
    for b in range(bars):
        for s in range(steps):
            i = s % per
            if keep == "skip-mid" and per == 3 and i == 1: continue
            if keep == "first-last" and i not in (0, per - 1): continue
            if keep == "random" and i != 0 and rng.random() < .4: continue
            p.note(0, b * steps + s, tok, (100 if i == 0 else 60) + rng.uniform(-8, 8))
    return p, "Charleston en triolets", "triplet", f"trip-hats-{steps}"


def trap_rolls(_):
    """Charleston trap : croches, avec des rafales en triolets de doubles croches (24 pas)."""
    bars = rng.choice([1, 2])
    p = Pat("perc", bars, 1, 24)
    for b in range(bars):
        rolls = rng.sample(range(4), rng.randint(1, 2))
        for beat in range(4):
            if beat in rolls:
                for k in range(6): p.note(0, b * 24 + beat * 6 + k, "CH", 60 + k * 9)
            else:
                for k in (0, 3): p.note(0, b * 24 + beat * 6 + k, "CH", 95 if k == 0 else 70)
    return p, "Rafales trap en triolets", "trap", "trip-trap"


def triplet_arp(_):
    scale = rng.choice([MINOR, PHRYG, MAJOR, [0, 2, 3, 5, 7, 9, 10]])
    prog = rng.choice([[0], [0, 5], [0, 3], [0, 5, 3, 4], [0, 4]])
    shape = rng.choice([[0, 1, 2], [2, 1, 0], [0, 2, 1], [0, 1, 2, 3, 2, 1]])
    steps = 12
    bars = max(len(prog), rng.choice([1, 2, 4]))
    p = Pat("melody", bars, 1, steps)
    for b in range(bars):
        deg = prog[b % len(prog)]
        t = [scale[(deg + k) % 7] + 12 * ((deg + k) // 7) for k in (0, 2, 4)] + [scale[deg % 7] + 12 * (deg // 7) + 12]
        for s in range(steps):
            p.note(0, b * steps + s, t[shape[s % len(shape)] % len(t)] + 12, 100 if s % 3 == 0 else rng.uniform(65, 85))
    return p, "Arpège en triolets", "triplet", "trip-arp"


def triplet_bass(_):
    """Basse en triolets (feeling 12/8, shuffle) : tonique + 1 ou 2 notes."""
    pool = rng.choice([[0], [0, 12], [0, 7], [0, 3], [0, -2], [0, 5]])
    cells = ["x.x", "xx.", "x..", ".xx", "xxx", ".x."]
    A = [rng.choice(cells) for _ in range(4)]
    A[0] = "x" + A[0][1:]
    bars = rng.choice([1, 2, 4])
    p = Pat("bass", bars, 1, 12)
    for b in range(bars):
        for beat, cell in enumerate(A if b % 2 == 0 else A[:3] + [rng.choice(cells)]):
            for i, c in enumerate(cell):
                if c == "x":
                    n = 0 if (i == 0 or len(pool) == 1 or rng.random() < .6) else rng.choice(pool[1:])
                    p.note(0, b * 12 + beat * 3 + i, n, 110 if i == 0 else rng.uniform(75, 95))
    return p, "Basse en triolets", "triplet", "trip-bass"


def triplet_fill(_):
    """Roulement en triolets de doubles croches qui monte (24 pas), sur 1 mesure."""
    p = Pat("perc", 1, 1, 24)
    start = rng.choice([0, 12, 18])
    voices = rng.choice([["SN"], ["HT", "MT", "LT"], ["SN", "HT", "LT"], ["CL"]])
    for s in range(start, 24):
        if rng.random() < .85:
            k = (s - start) * len(voices) // (24 - start)
            p.note(0, s, voices[min(k, len(voices) - 1)], 55 + (s - start) * 70 / (24 - start))
    return p, "Roulement en triolets", "triplet", "trip-fill"


def jazz_ternary(_):
    """Jazz ternaire vrai, grille de 12 pas (croches de triolet) en 4/4."""
    bars = rng.choice([1, 2, 4])
    return kit(12, bars, {"CY": [(0, 95), (3, 90), (5, 65), (6, 95), (9, 90), (11, 65)],
                          "CH": [(3, 70), (9, 70)],
                          "SN": lambda b: [(s, rng.uniform(35, 75)) for s in rng.sample([2, 5, 8, 11], rng.randint(0, 2))],
                          "BD": lambda b: [(s, rng.uniform(40, 70)) for s in rng.sample([0, 6, 8, 11], rng.randint(0, 2))]}), "Batterie jazz ternaire", "jazz", "jazz-ternary"


TRIPLET_PLAN = [(triplet_hats, 250), (trap_rolls, 120), (triplet_arp, 300), (triplet_bass, 300),
                (triplet_fill, 80), (jazz_ternary, 150)]


PLAN = [
    (electro_perc, "electro", 400), (ghost_snare, "electro", 150), (electro_lead, "electro", 300),
    (minimal_click, "minimal_dub", 400), (dub_chords, "minimal_dub", 300), (minimal_blip, "minimal_dub", 200),
    (trance_bass, "trance", 350), (trance_perc, "trance", 250), (rave_stab, "trance", 150),
    (acid_line, "acid", 1000),
    (light_perc, "light_perc", 500),
    (drums_rock, "drums", 250), (drums_metal, "drums", 250), (drums_indus_metal, "drums", 200),
    (drums_prog, "drums", 200), (drums_jazz, "drums", 200), (drums_offbeat, "drums", 150),
]
TYPE = {"pad": "pad", "melody": "melody", "stab": "melody", "bass": "bass", "perc": "perc", "drums": "drums", "acid": "acid"}


def write_block(out, p, label, genre, tag, n, fname):
    head = (f'@{TYPE[p.kind]} id=f-{fname}-{n:04d} name="{label} — {p.nv} voix, {p.bars} mes. #{n:03d}" '
            f'genre={genre} bars={p.bars} steps={p.steps}' + {12: " grid=1/8T", 24: " grid=1/16T"}.get(p.steps, "") +
            f' voices={p.nv} tags={tag} src=gen-fill')
    out.append(p.render(head))


def main():
    out = {}; seen = set(); counters = {}
    for fn, dest, target in PLAN:
        made = tries = 0
        while made < target and tries < target * 80:
            tries += 1
            p, label, genre, tag = fn(None)
            if p.empty() or (p.kind, p.key()) in seen: continue
            seen.add((p.kind, p.key())); made += 1
            counters[fn.__name__] = counters.get(fn.__name__, 0) + 1
            write_block(out.setdefault(dest, []), p, label, genre, tag, counters[fn.__name__], fn.__name__.replace("_", "-"))
    # Les 4 accords : toutes les combinaisons cycliques de 2 à 4 accords, chaque accord dure 1 à 4 temps
    n = 0
    for k in (2, 3, 4):
        for seq in itertools.permutations(FOUR, k):
            if seq[0] != "I" and k < 4 and rng.random() < .5: continue
            for beats in (1, 2, 3, 4):
                for style in ("pad", "stab", "arp"):
                    p = four_chords(seq, beats, style)
                    if (p.kind, p.key()) in seen: continue
                    seen.add((p.kind, p.key())); n += 1
                    label = f'4 accords {"–".join(seq)} ({beats} temps/accord, {style})'
                    write_block(out.setdefault("four_chords", []), p, label, "pop", f"four-{style}", n, "four")
    # Triolets : après les 4 accords pour ne pas changer les tirages précédents
    for fn, target in TRIPLET_PLAN:
        made = tries = 0
        while made < target and tries < target * 80:
            tries += 1
            p, label, genre, tag = fn(None)
            if p.empty() or (p.kind, p.key()) in seen: continue
            seen.add((p.kind, p.key())); made += 1
            counters[fn.__name__] = counters.get(fn.__name__, 0) + 1
            write_block(out.setdefault("triplets", []), p, label, genre, tag, counters[fn.__name__], fn.__name__.replace("_", "-"))
    hdr = ("# Familles complétées et nouvelles catégories — tools/generate_fill.py.\n"
           "# Tout est en 4/4. Grille normale : 16 pas. Triolets : grid=1/8T (12 pas) ou grid=1/16T (24 pas).\n"
           "# Polyphonie N/N2… + V/V2… ; ratchet *n ; notes = intervalles depuis la tonique.\n\n")
    for k, items in out.items():
        (LIB / f"fill_{k}.txt").write_text(hdr + "\n".join(items))
        print(k, len(items))


if __name__ == "__main__":
    main()
