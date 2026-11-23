"""Deuxième générateur : éléments techno / électro qui se placent sur un kick 4/4 et une caisse claire.
Règles tirées des méthodes de production techno :
  - Basse « consciente du kick » : les pas du kick (1, 5, 9, 13) restent vides ou très doux ;
    basse roulante = doubles croches sauf le temps, une note dominante + 1 ou 2 notes de passage.
  - Rumble : notes graves répétées juste après chaque kick, vélocité qui décroît (queue du kick).
  - Polymètre : une boucle de 3, 5, 6, 7, 9, 10, 11, 12 ou 13 pas répétée sur la grille de 16 → la ligne
    glisse par rapport à la mesure et ne retombe sur ses pieds qu'au bout de plusieurs mesures (asymétrie).
  - Euclidien E(k, n) : k coups répartis le plus régulièrement possible sur n pas, avec rotation.
  - Accents polyrythmiques : doubles croches continues accentuées toutes les 3, 5 ou 7 notes.
  - Courbes de vélocité : crescendo, decrescendo, vagues — mécanique mais vivant.
  - Atonal : intervalles durs (seconde mineure, triton, septième majeure), notes répétées, clusters.
  - Question / réponse : mesure A, réponse B, phrase ABAB' ou AAAB.
  - Relances : roulements qui se densifient et crescendo en fin de 1 ou 2 mesures.
Usage : python3 tools/generate_techno.py   (écrit Library/techno_*.txt, résultat déterministe)"""
import random
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "Library"
rng = random.Random(4242)
KICK = {0, 4, 8, 12}

TONAL_POOLS = [[0], [0, 12], [0, 7], [0, 3], [0, 10], [0, 5], [0, 3, 7], [0, 7, 12], [0, 10, 12], [0, 3, 5],
               [0, -2], [0, 12, 15], [0, 7, 10]]
ATONAL_POOLS = [[0, 1], [0, 6], [0, 11], [0, 1, 6], [0, 6, 11], [0, 1, 2], [0, 13], [0, 6, 12], [0, 1, 7],
                [0, -1], [0, 11, 13], [0, 5, 6]]
PERC_SETS = [["CH"], ["CH", "OH"], ["RS"], ["CL"], ["PC"], ["CB"], ["SH"], ["LT", "MT"], ["LT", "MT", "HT"],
             ["RS", "CL"], ["PC", "RS"], ["CY"], ["CH", "PC"], ["MT", "HT"]]


def euclid(k, n, rot=0):
    return [((i + rot) % n * k) % n < k for i in range(n)] if k > 0 else [False] * n


def vel_curve(shape, i, n, lo, hi):
    x = i / max(1, n - 1)
    if shape == "crescendo": f = x
    elif shape == "decrescendo": f = 1 - x
    elif shape == "vague": f = 0.5 + 0.5 * __import__("math").sin(x * 6.283 * 2)
    elif shape == "plat": f = 0.6
    else: f = rng.random()
    return int(max(1, min(127, lo + (hi - lo) * f + rng.uniform(-4, 4))))


def metric_vel(i, lo, hi, accent_every=None, ghost=True):
    pos = i % 4
    base = {0: 1.0, 2: .75, 1: .35, 3: .45}[pos]
    if accent_every:
        base = 1.0 if i % accent_every == 0 else (.45 if ghost else .6)
    return int(max(1, min(127, lo + (hi - lo) * base + rng.uniform(-5, 5))))


def pitches_for(hits, pool, kind, root_bias=.7):
    out = []; prev = 0
    for i, h in enumerate(hits):
        if not h: out.append(None); continue
        if len(pool) == 1: out.append(pool[0]); continue
        if kind == "perc":
            # première voix (la plus grave / principale) sur les positions fortes
            out.append(pool[0] if (i % 4 == 0 or rng.random() < .5) else rng.choice(pool[1:])); continue
        if rng.random() < root_bias: n = pool[0]
        else:
            others = pool[1:]; w = [1 / (1 + abs(p - prev) / 6) for p in others]
            n = rng.choices(others, w)[0]
        out.append(n); prev = n
    return out


# ------------------------------------------------------------------ familles
def fam_rolling(bars):
    """Basse roulante : toutes les doubles croches sauf celles du kick ; note dominante + passages."""
    pool = rng.choice([[0], [0, 12], [0, 3], [0, 7], [0, 10], [0, 3, 7], [0, -2, 3], [0, 12, 10]])
    shape = rng.choice(["xxx", "x.x", "xx.", ".xx", "xxx", "xxx"])  # ce qui suit chaque kick
    hits = []
    for b in range(bars):
        for beat in range(4):
            cell = [False] + [c == "x" for c in shape]
            if b == bars - 1 and beat == 3 and rng.random() < .4:
                cell = [False] + [rng.random() < .6 for _ in range(3)]
            hits += cell
    p = pitches_for(hits, pool, "bass", root_bias=.75)
    vel = [metric_vel(i % 16, 70, 118) if h else 0 for i, h in enumerate(hits)]
    # accent sur la 3e double croche (le contretemps) = pompe
    vel = [min(127, v + 12) if (i % 4 == 2 and v) else v for i, v in enumerate(vel)]
    return "bass", "Basse roulante (kick libre)", "techno", hits, p, vel, pool


def fam_rumble(bars):
    """Rumble : 1 à 3 notes graves juste après chaque kick, vélocité qui décroît."""
    pool = rng.choice([[0], [0], [0, -12], [0, 12], [0, -5]])
    tail = rng.choice([1, 2, 3, 2])
    hits, vel = [], []
    for _ in range(bars * 4):
        cell = [False] * 4; v = [0] * 4
        for t in range(1, tail + 1):
            cell[t] = True; v[t] = int(110 - 25 * (t - 1) + rng.uniform(-5, 5))
        hits += cell; vel += v
    p = pitches_for(hits, pool, "bass", root_bias=.85)
    return "bass", "Rumble", "techno", hits, p, vel, pool


def fam_offbeat(bars):
    """Contretemps et décalages : sur le « et », juste après, ou en doublé."""
    pool = rng.choice(TONAL_POOLS)
    variant = rng.choice(["et", "tard", "double", "et+tard", "mix"])
    hits = []
    for b in range(bars):
        for beat in range(4):
            cell = {"et": "..x.", "tard": "...x", "double": "..xx", "et+tard": "..x.", "mix": rng.choice(["..x.", "..xx", ".x.x", "..x."])}[variant]
            if variant == "et+tard" and beat % 2 == 1: cell = "...x"
            hits += [c == "x" for c in cell]
    p = pitches_for(hits, pool, "bass")
    vel = [metric_vel(i % 16, 80, 120) if h else 0 for i, h in enumerate(hits)]
    return "bass", "Basse contretemps", "techno", hits, p, vel, pool


def fam_polymeter(bars, kind):
    """Boucle de longueur impaire répétée sur la grille : la ligne glisse."""
    bars = rng.choices([2, 3, 4], [2, 1, 5])[0]  # l'asymétrie s'entend sur plusieurs mesures
    L = rng.choice([3, 5, 6, 7, 9, 10, 11, 12, 13])
    k = rng.randint(1, max(1, L - 1 if L > 4 else L // 2 + 1))
    loop = euclid(k, L, rng.randrange(L))
    if not any(loop): loop[0] = True
    total = bars * 16
    hits = [loop[i % L] for i in range(total)]
    if kind == "perc":
        pool = rng.choice(PERC_SETS)
    else:
        pool = rng.choice(TONAL_POOLS + ATONAL_POOLS[:4])
    loop_p = pitches_for(loop, pool, "perc" if kind == "perc" else "synth", root_bias=.55)
    p = [loop_p[i % L] for i in range(total)]
    loop_v = [metric_vel(i, 65, 118, accent_every=L) for i in range(L)]
    vel = [loop_v[i % L] if hits[i] else 0 for i in range(total)]
    label = f"Polymètre {k}/{L}"
    return kind, label, "techno", hits, p, vel, pool, f"poly{L}"


def fam_euclid(bars, kind):
    """Euclidien sur 16 pas, deux couches possibles (E(k,16) + rotation), parfois alterné A/B."""
    k = rng.choice([3, 4, 5, 5, 6, 7, 7, 9, 10, 11, 13])
    rot = rng.randrange(16)
    A = euclid(k, 16, rot)
    B = euclid(max(1, k + rng.choice([-2, -1, 1, 2])), 16, rot) if rng.random() < .35 else A
    hits = []
    for b in range(bars):
        hits += (B if (b % 2 == 1) else A)
    pool = rng.choice(PERC_SETS) if kind == "perc" else rng.choice(TONAL_POOLS + ATONAL_POOLS)
    p = pitches_for(hits, pool, "perc" if kind == "perc" else "synth", root_bias=.6)
    vel = [metric_vel(i % 16, 60, 118) if h else 0 for i, h in enumerate(hits)]
    return kind, f"Euclidien E({k},16)", "techno", hits, p, vel, pool, f"euclid{k}-r{rot}"


def fam_accent(bars, kind):
    """Doubles croches continues, accent toutes les 3/5/7 notes (polyrythme d'accents)."""
    every = rng.choice([3, 3, 5, 7, 6])
    gaps = rng.random() < .4
    hits = [True] * (bars * 16)
    if gaps:
        hits = [not (i % 16 in KICK) for i in range(bars * 16)]
    pool = rng.choice([["CH"], ["SH"], ["CY"], ["RS"], ["PC"], ["CH", "OH"]]) if kind == "perc" else rng.choice([[0], [0, 12], [0, 7], [0, 1], [0, 6]])
    p = []
    for i, h in enumerate(hits):
        if not h: p.append(None); continue
        if len(pool) == 1: p.append(pool[0])
        else: p.append(pool[1] if i % every == 0 and rng.random() < .7 else pool[0])
    vel = [metric_vel(i, 45, 120, accent_every=every) if h else 0 for i, h in enumerate(hits)]
    return kind, f"Accents toutes les {every}", "techno", hits, p, vel, pool, f"accent{every}"


def fam_velocity_shape(bars, kind):
    """Rythme mécanique fixe + courbe de vélocité (crescendo, vagues…)."""
    cell = rng.choice(["x.x.", "xxxx", "xx.x", ".xxx", "x..x", "..x."])
    hits = [c == "x" for c in cell] * (4 * bars)
    shape = rng.choice(["crescendo", "decrescendo", "vague", "aleatoire"])
    pool = rng.choice(PERC_SETS) if kind == "perc" else rng.choice(TONAL_POOLS[:8])
    p = pitches_for(hits, pool, "perc" if kind == "perc" else "synth", root_bias=.8)
    vel = [vel_curve(shape, i, len(hits), 40, 122) if h else 0 for i, h in enumerate(hits)]
    return kind, f"Courbe {shape}", "techno", hits, p, vel, pool, f"vel-{shape}"


def fam_atonal(bars):
    """Lignes atonales / industrielles : intervalles durs, répétitions, chromatisme."""
    pool = rng.choice(ATONAL_POOLS)
    density = rng.choice([.3, .45, .6, .8])
    A = [rng.random() < density for _ in range(16)]
    A[rng.choice([0, 2, 3])] = True
    hits = []
    for b in range(bars):
        h = A[:]
        if b == bars - 1 and bars > 1:
            for i in range(12, 16): h[i] = rng.random() < density
        hits += h
    p = pitches_for(hits, pool, "synth", root_bias=.5)
    vel = [metric_vel(i % 16, 75, 125) if x else 0 for i, x in enumerate(hits)]
    return "synth", "Atonal / industriel", "industrial", hits, p, vel, pool, "atonal"


def fam_call_response(bars):
    """Question / réponse : A sur la tonique, B qui répond (autre hauteur, rythme décalé)."""
    bars = max(2, bars)
    pool = rng.choice([[0, 3, 7], [0, 7, 10], [0, 5, 7], [0, 3, 5], [0, 12, 10], [0, 7, 12]])
    A = [False] * 16; B = [False] * 16
    for i in rng.sample(range(0, 8), rng.randint(2, 4)): A[i] = True
    for i in rng.sample(range(8, 16), rng.randint(2, 4)): B[i] = True
    A[0] = True
    bar1 = [a or b for a, b in zip(A, [False] * 16)]
    bar2 = [b for b in B]
    struct = rng.choice([["A", "B"], ["A", "B", "A", "B"], ["A", "A", "A", "B"], ["A", "B", "A", "A"]])
    struct = struct[:bars] if len(struct) >= bars else (struct * 2)[:bars]
    hits, p = [], []
    pa = pitches_for(bar1, pool, "synth", root_bias=.8)
    pb = pitches_for(bar2, pool[1:] + [pool[0]], "synth", root_bias=.2)
    for s in struct:
        hits += bar1 if s == "A" else bar2
        p += pa if s == "A" else pb
    vel = [metric_vel(i % 16, 80, 120) if h else 0 for i, h in enumerate(hits)]
    return "synth", "Question-réponse", "techno", hits, p, vel, pool, "call-" + "".join(struct)


def fam_fill(bars):
    """Relance : la densité monte vers la fin (croches → doubles croches) avec crescendo."""
    bars = rng.choice([1, 2]) if bars > 2 else bars
    total = bars * 16
    start = rng.choice([0, total // 2, total - 8])
    hits = []
    for i in range(total):
        if i < start: hits.append(False)
        else:
            x = (i - start) / max(1, total - start)
            step = 4 if x < .34 else (2 if x < .67 else 1)
            hits.append((i - start) % step == 0)
    pool = rng.choice([["SN"], ["CL"], ["LT", "MT", "HT"], ["SN", "CL"], ["RS"], ["HT", "MT", "LT"]])
    p = []
    for i, h in enumerate(hits):
        if not h: p.append(None); continue
        idx = int((i - start) / max(1, total - start) * len(pool)) if len(pool) > 1 else 0
        p.append(pool[min(idx, len(pool) - 1)])
    vel = [vel_curve("crescendo", i - start, total - start, 50, 127) if h else 0 for i, h in enumerate(hits)]
    return "perc", "Relance", "techno", hits, p, vel, pool, "fill"


# ------------------------------------------------------------------ rendu
def render(hits, pitches, vel, legato=0.0):
    toks, vels = [], []
    for i, h in enumerate(hits):
        if h:
            toks.append(str(pitches[i])); vels.append(str(vel[i]))
        else:
            if toks and toks[-1] not in "." and legato and rng.random() < legato:
                toks.append("-")
            else:
                toks.append(".")
            vels.append(".")
    return toks, vels


PLAN = [  # (famille, sortie, nombre)
    (fam_rolling, "bass", 500), (fam_rumble, "bass", 120), (fam_offbeat, "bass", 400),
    (lambda b: fam_polymeter(b, "synth"), "synth", 500), (lambda b: fam_polymeter(b, "perc"), "perc", 500),
    (lambda b: fam_euclid(b, "synth"), "synth", 400), (lambda b: fam_euclid(b, "perc"), "perc", 500),
    (lambda b: fam_accent(b, "perc"), "perc", 200), (lambda b: fam_accent(b, "synth"), "synth", 120),
    (lambda b: fam_velocity_shape(b, "perc"), "perc", 200), (lambda b: fam_velocity_shape(b, "synth"), "synth", 150),
    (fam_atonal, "synth", 500), (fam_call_response, "synth", 300), (fam_fill, "perc", 150),
]


def main():
    out = {"bass": [], "synth": [], "perc": []}
    seen = set(); counters = {}
    for fn, dest, target in PLAN:
        made = tries = 0
        while made < target and tries < target * 50:
            tries += 1
            bars = rng.choices([1, 2, 3, 4], [4, 4, 1, 3])[0]
            res = fn(bars)
            kind, label, genre, hits, pitches, vel, pool = res[:7]
            tag = res[7] if len(res) > 7 else fn.__name__ if hasattr(fn, "__name__") else "x"
            nb = len(hits) // 16
            if sum(hits) == 0: continue
            if kind == "bass" and not any(p == 0 for p in pitches if p is not None): continue
            toks, vels = render(hits, pitches, vel, legato={"synth": .2, "bass": .05, "perc": 0.0}[kind])
            key = (dest, " ".join(toks))
            if key in seen: continue
            seen.add(key); made += 1
            counters[label] = counters.get(label, 0) + 1
            n = counters[label]
            used = len({x for x in pitches if x is not None})
            what = "voix" if kind == "perc" else ("note" + ("s" if used > 1 else ""))
            atype = {"bass": "bass", "synth": "melody", "perc": "perc"}[kind]
            slug = "".join(c if c.isalnum() else "-" for c in label.lower()).strip("-")
            head = (f'@{atype} id=t-{slug}-{n:04d} name="{label} — {used} {what}, {nb} mes. #{n:03d}" '
                    f'genre={genre} bars={nb} steps=16 tags={tag} src=gen-techno')
            body = []
            for b in range(nb):
                body.append("N  " + " ".join(toks[b * 16:(b + 1) * 16]))
                body.append("V  " + " ".join(vels[b * 16:(b + 1) * 16]))
            out[dest].append(head + "\n" + "\n".join(body) + "\n")
    hdr = ("# Éléments techno / électro fabriqués par tools/generate_techno.py : basse qui laisse la place au kick,\n"
           "# rumble, contretemps, polymètres (boucles de 3 à 13 pas), euclidiens, accents polyrythmiques,\n"
           "# courbes de vélocité, lignes atonales, question-réponse, relances.  Même format que gen_*.txt.\n\n")
    for k, items in out.items():
        (LIB / f"techno_{k}.txt").write_text(hdr + "\n".join(items))
        print(k, len(items))


if __name__ == "__main__":
    main()
