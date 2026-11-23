"""Troisième générateur : EBM, électro-industriel, dark electro / aggrotech, rock et metal industriels.
Règles :
  - EBM : basse séquencée répétitive en doubles croches entre les kicks, souvent erratique et staccato,
    une note + octave, mineur ou phrygien (seconde mineure) ; caisse claire serrée et martiale.
  - Électro-industriel / dark electro : basses séquencées syncopées (galop, trous), lignes en mineur sombre.
  - Aggrotech : 4/4 martelé 135-150 BPM, riffs de lead rapides sur pédale de tonique.
  - Rock / metal industriel (90-120 BPM) : riffs « chug » (tonique répétée et étouffée) avec accents
    sur la seconde mineure, le triton ou l'octave ; kick syncopé contre caisse claire sur 2 et 4.
  - Percussions métalliques et « noise stabs » : peu de coups, très forts, à des places inattendues.
Usage : python3 tools/generate_industrial.py   (écrit Library/industrial_*.txt, résultat déterministe)"""
import random
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "Library"
rng = random.Random(1983)

DARK_POOLS = [[0], [0, 12], [0, 1], [0, 1, 12], [0, 3, 12], [0, -2], [0, 5], [0, 7], [0, 3, 7], [0, 1, 7],
              [0, 6], [0, 12, 13], [0, 3, 5], [0, 10, 12]]
RIFF_POOLS = [[0, 1], [0, 6], [0, 12], [0, 1, 6], [0, 3, 6], [0, 5, 6], [0, 1, 3], [0, 12, 11], [0, 7, 6], [0, 3, 5, 6]]


def mv(i, lo, hi, accents=()):
    base = {0: 1.0, 2: .7, 1: .4, 3: .5}[i % 4]
    if accents: base = 1.0 if (i % 16) in accents else .55
    return int(max(1, min(127, lo + (hi - lo) * base + rng.uniform(-5, 5))))


def ebm_bass(bars):
    """Basse EBM : doubles croches entre les kicks, gate qui coupe certaines notes, octave occasionnelle."""
    pool = rng.choice([[0], [0, 12], [0, 1], [0, 1, 12], [0, 12, -2], [0, 3, 12], [0, 5, 12]])
    gate = rng.choice(["xxxx", ".xxx", "x.xx", "xx.x", ".x.x", "xxx.", "x.x.", ".xx."])
    hits = []
    for b in range(bars):
        for beat in range(4):
            g = gate
            if b == bars - 1 and beat == 3 and rng.random() < .5:
                g = rng.choice(["xxxx", "x.xx", "xx.x"])
            hits += [c == "x" for c in g]
    p = []
    for i, h in enumerate(hits):
        if not h: p.append(None); continue
        if len(pool) == 1 or i % 4 == 0 or rng.random() < .7: p.append(0)
        else: p.append(rng.choice(pool[1:]))
    acc = set(rng.sample(range(16), rng.randint(2, 4)))
    vel = [mv(i, 72, 122, acc) if h else 0 for i, h in enumerate(hits)]
    return "bass", "Basse EBM", "ebm", hits, p, vel, rng.choice([120, 125, 130, 135])


def dark_bass(bars):
    """Basse électro-industrielle / dark electro : galop, syncopes, trous, mineur sombre."""
    pool = rng.choice(DARK_POOLS)
    cells = ["x.xx", "xx.x", "x..x", ".x.x", "x.x.", "..xx", "xxx.", "x..."]
    A = [c == "x" for _ in range(4) for c in rng.choice(cells)]
    A[0] = True
    hits = []
    for b in range(bars):
        h = A[:]
        if b % 2 == 1 and rng.random() < .5:
            tail = rng.choice(cells); h[12:16] = [c == "x" for c in tail]
        hits += h
    p = []
    prev = 0
    for i, h in enumerate(hits):
        if not h: p.append(None); continue
        if i % 16 == 0 or len(pool) == 1 or rng.random() < .55: n = 0
        else: n = rng.choice(pool[1:])
        p.append(n); prev = n
    vel = [mv(i, 80, 124) if h else 0 for i, h in enumerate(hits)]
    return "bass", "Basse électro-industrielle", "electro-industrial", hits, p, vel, rng.choice([110, 120, 128])


def chug_riff(bars):
    """Riff « chug » de rock/metal industriel : tonique répétée, accents sur notes dures."""
    pool = rng.choice(RIFF_POOLS)
    base = rng.choice(["xxxx", "x.xx", "xx.x", "x.x.", "xxx.", ".xxx"])
    A = []
    for beat in range(4):
        cell = base if rng.random() < .7 else rng.choice(["x...", "x.x.", "xx..", "x..x"])
        A += [c == "x" for c in cell]
    A[0] = True
    stabs = set(rng.sample(range(16), rng.randint(1, 3)))
    hits, p = [], []
    for b in range(bars):
        for i in range(16):
            h = A[i]; hits.append(h)
            if not h: p.append(None); continue
            if i in stabs and (b % 2 == 1 or rng.random() < .6): p.append(rng.choice(pool[1:]))
            else: p.append(0)
    vel = []
    for i, h in enumerate(hits):
        if not h: vel.append(0); continue
        vel.append(124 if p[i] not in (0, None) else int(rng.uniform(78, 98)))
    return "synth", "Riff chug", "industrial-rock", hits, p, vel, rng.choice([95, 100, 110, 120])


def pedal_riff(bars):
    """Riff sur pédale : on revient à la tonique entre chaque note de la mélodie (aggrotech / metal)."""
    melody = rng.choice([[3, 5, 6, 5], [1, 3, 1, 6], [7, 6, 5, 3], [12, 10, 7, 6], [1, 1, 3, 6], [5, 6, 7, 6],
                         [3, 7, 10, 12], [12, 13, 12, 10]])
    step = rng.choice([1, 2])  # pédale en doubles croches ou croches
    hits, p = [], []
    k = 0
    for b in range(bars):
        for i in range(16):
            on = (i % step == 0)
            hits.append(on)
            if not on: p.append(None); continue
            slot = i // step
            if slot % 2 == 0: p.append(0)
            else:
                p.append(melody[k % len(melody)]); k += 1
    vel = [int(118 + rng.uniform(-4, 4)) if (h and p[i] != 0) else (int(90 + rng.uniform(-6, 6)) if h else 0)
           for i, h in enumerate(hits)]
    return "synth", "Riff sur pédale", "aggrotech", hits, p, vel, rng.choice([135, 140, 145, 150])


def lead_aggro(bars):
    """Lead aggrotech : motif rapide de 3-4 notes répété, réponse à la mesure suivante."""
    pool = rng.choice([[0, 3, 7, 12], [0, 1, 5, 7], [0, 3, 6, 12], [0, 7, 10, 12], [0, 5, 6, 12], [0, 3, 5, 7]])
    A = [c == "x" for c in rng.choice(["x.x.x.x.x.x.x.x.", "x.xx.xx.x.xx.xx.", "xx.xx.xx.xx.xx.x", "x..x..x.x..x..x."])]
    pa = [rng.choice(pool[:3]) if h else None for h in A]
    pa[0] = 0
    pb = [((x + rng.choice([0, 0, 1, -1])) if x is not None else None) for x in pa]
    pb = [pool[min(len(pool) - 1, max(0, pool.index(x) if x in pool else 0) + 1)] if x is not None else None for x in pa]
    hits, p = [], []
    for b in range(bars):
        hits += A; p += (pb if b % 2 == 1 else pa)
    vel = [mv(i, 85, 122) if h else 0 for i, h in enumerate(hits)]
    return "synth", "Lead aggrotech", "aggrotech", hits, p, vel, rng.choice([138, 140, 145])


def march_snare(bars):
    """Caisse claire martiale / EBM : 2 et 4 + roulements et petites notes avant."""
    base = [4, 12]
    extra = rng.choice([[3, 11], [11], [14, 15], [7, 15], [2, 3, 10, 11], [13, 14, 15], [6, 14]])
    hits = []
    for b in range(bars):
        row = [False] * 16
        for i in base + extra: row[i] = True
        if b == bars - 1 and rng.random() < .5:
            for i in range(12, 16): row[i] = True
        hits += row
    voices = rng.choice([["SN"], ["SN", "CL"], ["SN", "RS"]])
    p = [None if not h else (voices[0] if (i % 16) in base or len(voices) == 1 else voices[1]) for i, h in enumerate(hits)]
    vel = [(120 if (i % 16) in base else int(rng.uniform(55, 85))) if h else 0 for i, h in enumerate(hits)]
    return "perc", "Caisse martiale", "ebm", hits, p, vel, rng.choice([120, 125, 130])


def rock_kick_snare(bars):
    """Batterie de rock industriel (kick + caisse) : caisse 2 et 4, kick syncopé, parfois demi-temps."""
    half = rng.random() < .35
    snare = [8] if half else [4, 12]
    kick_opts = [[0, 6, 10], [0, 3, 8, 10], [0, 7, 10], [0, 2, 8, 11], [0, 6, 8, 14], [0, 10], [0, 3, 6, 10, 14],
                 [0, 8, 9], [0, 2, 3, 10]]
    k1 = rng.choice(kick_opts); k2 = rng.choice(kick_opts) if rng.random() < .4 else k1
    hits, p = [], []
    for b in range(bars):
        kk = k2 if b % 2 == 1 else k1
        for i in range(16):
            if i in snare: hits.append(True); p.append("SN")
            elif i in kk: hits.append(True); p.append("BD")
            else: hits.append(False); p.append(None)
    vel = [(124 if p[i] == "SN" else int(rng.uniform(100, 120))) if h else 0 for i, h in enumerate(hits)]
    return "perc", "Kick + caisse rock indus" + (" (demi-temps)" if half else ""), "industrial-rock", hits, p, vel, rng.choice([90, 100, 110, 120])


def metal_perc(bars):
    """Percussions métalliques / noise stabs : peu de coups, très forts, places inattendues."""
    voices = rng.choice([["CB"], ["PC"], ["RS"], ["CB", "PC"], ["CY"], ["PC", "HT"], ["CL"]])
    n = rng.randint(1, 4)
    places = sorted(rng.sample([1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15], n))
    hits, p = [], []
    for b in range(bars):
        pl = places if (b % 2 == 0 or rng.random() < .6) else sorted(rng.sample([1, 3, 6, 7, 10, 11, 14, 15], n))
        for i in range(16):
            on = i in pl; hits.append(on); p.append(rng.choice(voices) if on else None)
    vel = [int(rng.uniform(108, 127)) if h else 0 for h in hits]
    return "perc", "Noise stab / métal", "industrial", hits, p, vel, rng.choice([120, 130, 140])


def factory(bars):
    """« Usine » : machine qui cogne en boucle de 3, 5 ou 7 pas sur la mesure (rythme mécanique)."""
    L = rng.choice([3, 5, 7, 6])
    loop = [True] + [rng.random() < .35 for _ in range(L - 1)]
    voices = rng.choice([["PC", "CB"], ["RS", "PC"], ["LT", "HT"], ["CL", "RS"], ["CB"]])
    hits, p, vel = [], [], []
    for i in range(bars * 16):
        on = loop[i % L]; hits.append(on)
        p.append((voices[0] if i % L == 0 else voices[-1]) if on else None)
        vel.append((125 if i % L == 0 else int(rng.uniform(70, 95))) if on else 0)
    return "perc", f"Usine en {L}", "industrial", hits, p, vel, rng.choice([115, 125, 135])


PLAN = [(ebm_bass, 450), (dark_bass, 450), (chug_riff, 400), (pedal_riff, 250), (lead_aggro, 300),
        (march_snare, 200), (rock_kick_snare, 300), (metal_perc, 250), (factory, 200)]


def main():
    out = {"bass": [], "synth": [], "perc": []}
    seen = set(); counters = {}
    for fn, target in PLAN:
        made = tries = 0
        while made < target and tries < target * 60:
            tries += 1
            bars = rng.choices([1, 2, 3, 4], [3, 4, 1, 4])[0]
            kind, label, genre, hits, p, vel, bpm = fn(bars)
            if not any(hits): continue
            toks = [str(p[i]) if h else "." for i, h in enumerate(hits)]
            vels = [str(vel[i]) if h else "." for i, h in enumerate(hits)]
            key = (kind, " ".join(toks))
            if key in seen: continue
            seen.add(key); made += 1
            counters[label] = counters.get(label, 0) + 1
            n = counters[label]
            nb = len(hits) // 16
            used = len({x for x in p if x is not None})
            what = "voix" if kind == "perc" else ("note" + ("s" if used > 1 else ""))
            atype = {"bass": "bass", "synth": "melody", "perc": "perc"}[kind]
            slug = "".join(c if c.isalnum() else "-" for c in fn.__name__)
            head = (f'@{atype} id=i-{slug}-{n:04d} name="{label} — {used} {what}, {nb} mes. #{n:03d}" '
                    f'genre={genre} bars={nb} steps=16 bpm={bpm} src=gen-industrial')
            body = []
            for b in range(nb):
                body.append("N  " + " ".join(toks[b * 16:(b + 1) * 16]))
                body.append("V  " + " ".join(vels[b * 16:(b + 1) * 16]))
            out[kind].append(head + "\n" + "\n".join(body) + "\n")
    hdr = ("# EBM, électro-industriel, aggrotech, rock et metal industriels — tools/generate_industrial.py.\n"
           "# bpm = tempo conseillé.  Même format que gen_*.txt (N = notes ou instruments, V = vélocités).\n\n")
    for k, items in out.items():
        (LIB / f"industrial_{k}.txt").write_text(hdr + "\n".join(items))
        print(k, len(items))


if __name__ == "__main__":
    main()
