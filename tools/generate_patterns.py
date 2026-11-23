"""Fabrique des motifs de basse, de synthé et de percussion à partir de règles de groove.

Principes (méthodes de rythme / programmation de groove) :
  1. Hiérarchie métrique : temps 1 > temps 3 > temps 2 et 4 > contretemps (croches) > doubles croches.
  2. Une mesure = 4 temps ; chaque temps est rempli par une « cellule » rythmique de 4 doubles croches,
     tirée dans le vocabulaire propre au style (noire, croches, contretemps, galop, roulé…).
  3. Phrasé : un motif d'une mesure est répété et varié sur 2, 3 ou 4 mesures (AAAA', ABAB', AABB, AAB…),
     la variation arrivant en fin de phrase (relance / turnaround).
  4. Hauteurs : 1 à 4 notes par motif, en intervalles depuis la tonique ; la tonique est privilégiée sur les
     temps forts, les autres notes sur les temps faibles.
  5. Vélocité : suit la force métrique et l'accent du style, + petite variation humaine ; notes fantômes
     sur les doubles croches faibles.
Usage : python3 tools/generate_patterns.py   (écrit Library/gen_*.txt, résultat déterministe)"""
import random
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "Library"
rng = random.Random(20261123)

# Force métrique de chaque double croche d'une mesure (1 = temps 1)
STRENGTH = [1.0, .2, .45, .25, .7, .2, .45, .25, .85, .2, .45, .25, .7, .2, .45, .3]

# Cellules d'un temps (4 doubles croches)
C = {
    "noire": "x...", "croches": "x.x.", "contre": "..x.", "galop": "x.xx", "galop2": "xx.x",
    "roule": ".xxx", "quatre": "xxxx", "pointe": "x..x", "anticip": "...x", "milieu": ".xx.",
    "fin": "..xx", "deux16": ".x.x", "seconde": ".x..", "vide": "....", "debut": "xx..",
    "trois": "xxx.",
}

# Styles : vocabulaire de cellules (poids), place de l'accent dans le temps, densité, notes, genre…
STYLES = {
    # ---------------- basses
    "bass-offbeat":   dict(kind="bass", genre="techno", cells={"contre": 10, "fin": 2, "milieu": 1, "vide": .5},
                           accent=2, legato=.1, swing=[0], vel=(85, 118), name="Basse contretemps"),
    "bass-rolling":   dict(kind="bass", genre="techno", cells={"roule": 10, "quatre": 2, "milieu": 1, "fin": 1},
                           accent=1, legato=0, swing=[0], vel=(80, 115), name="Basse roulante"),
    "bass-gallop":    dict(kind="bass", genre="techno", cells={"galop": 8, "galop2": 3, "croches": 2, "pointe": 1},
                           accent=0, legato=0, swing=[0], vel=(82, 120), name="Basse galop"),
    "bass-onbeat":    dict(kind="bass", genre="house", cells={"noire": 6, "croches": 4, "pointe": 3, "galop": 1, "contre": 1},
                           accent=0, legato=.25, swing=[0, 54, 58], vel=(78, 118), name="Basse sur le temps"),
    "bass-synco":     dict(kind="bass", genre="electro", cells={"pointe": 5, "contre": 3, "noire": 3, "anticip": 2, "seconde": 2, "vide": 2},
                           accent=0, legato=.15, swing=[0], vel=(80, 120), name="Basse syncopée"),
    "bass-sparse":    dict(kind="bass", genre="minimal", cells={"vide": 6, "noire": 3, "contre": 2, "anticip": 2, "seconde": 1},
                           accent=0, legato=.3, swing=[0, 54], vel=(75, 115), name="Basse clairsemée"),
    "bass-dub":       dict(kind="bass", genre="dub-techno", cells={"noire": 5, "vide": 5, "contre": 1},
                           accent=0, legato=.9, swing=[0], vel=(80, 110), name="Basse dub tenue"),
    "bass-16":        dict(kind="bass", genre="ebm", cells={"quatre": 8, "trois": 2, "galop": 2},
                           accent=0, legato=0, swing=[0], vel=(78, 118), name="Basse doubles croches"),
    "bass-garage":    dict(kind="bass", genre="ukg", cells={"noire": 3, "pointe": 3, "seconde": 2, "vide": 2, "anticip": 2},
                           accent=0, legato=.5, swing=[56, 60], vel=(80, 118), name="Basse garage"),
    "bass-acid":      dict(kind="acid", genre="acid", cells={"quatre": 5, "croches": 3, "galop": 3, "roule": 2, "trois": 2, "milieu": 1},
                           accent=0, legato=.2, swing=[0, 54], vel=(70, 127), name="Acid", slides=.15),
    # ---------------- synthés
    "syn-stab":       dict(kind="synth", genre="techno", cells={"contre": 4, "vide": 5, "anticip": 2, "seconde": 2, "noire": 1},
                           accent=2, legato=0, swing=[0, 54], vel=(85, 120), name="Stab"),
    "syn-seq":        dict(kind="synth", genre="techno", cells={"quatre": 6, "galop": 3, "galop2": 2, "croches": 2, "trois": 2},
                           accent=0, legato=0, swing=[0], vel=(70, 115), name="Séquence"),
    "syn-arp8":       dict(kind="synth", genre="trance", cells={"croches": 8, "quatre": 2},
                           accent=0, legato=.1, swing=[0], vel=(75, 112), name="Arpège croches"),
    "syn-pluck":      dict(kind="synth", genre="house", cells={"contre": 4, "pointe": 3, "croches": 2, "vide": 2, "deux16": 1},
                           accent=2, legato=.1, swing=[0, 54, 58], vel=(78, 115), name="Pluck"),
    "syn-hook":       dict(kind="synth", genre="rave", cells={"noire": 3, "croches": 3, "pointe": 3, "galop": 2, "vide": 1, "contre": 2},
                           accent=0, legato=.4, swing=[0], vel=(85, 122), name="Gimmick"),
    "syn-drone":      dict(kind="synth", genre="ambient", cells={"noire": 5, "vide": 6},
                           accent=0, legato=1.0, swing=[0], vel=(70, 100), name="Drone / nappe"),
    # ---------------- percussions (une voix ou deux)
    "perc-rim":       dict(kind="perc", genre="techno", cells={"anticip": 3, "seconde": 3, "contre": 2, "vide": 4, "deux16": 1},
                           accent=3, legato=0, swing=[0, 54], vel=(60, 115), name="Rim", voices=[["RS"], ["RS", "CL"]]),
    "perc-hats":      dict(kind="perc", genre="techno", cells={"croches": 4, "quatre": 4, "contre": 4, "deux16": 3, "galop": 2, "roule": 2},
                           accent=2, legato=0, swing=[0, 54, 58], vel=(50, 110), name="Charleston", voices=[["CH"], ["CH", "OH"]]),
    "perc-toms":      dict(kind="perc", genre="techno", cells={"pointe": 3, "anticip": 3, "vide": 4, "seconde": 2, "galop": 1},
                           accent=0, legato=0, swing=[0], vel=(70, 120), name="Toms", voices=[["LT"], ["LT", "MT"], ["LT", "MT", "HT"]]),
    "perc-shaker":    dict(kind="perc", genre="house", cells={"quatre": 6, "deux16": 3, "croches": 2},
                           accent=2, legato=0, swing=[0, 54, 58], vel=(45, 100), name="Shaker", voices=[["SH"]]),
    "perc-cowbell":   dict(kind="perc", genre="house", cells={"vide": 4, "contre": 2, "anticip": 2, "pointe": 2, "seconde": 1},
                           accent=0, legato=0, swing=[0, 54], vel=(70, 115), name="Cloche", voices=[["CB"], ["CB", "PC"]]),
    "perc-clap":      dict(kind="perc", genre="techno", cells={"vide": 5, "noire": 2, "anticip": 2, "deux16": 1},
                           accent=0, legato=0, swing=[0], vel=(80, 120), name="Clap & caisse", voices=[["CL"], ["CL", "SN"]], on24=True),
    "perc-latin-electro": dict(kind="perc", genre="tech-house", cells={"pointe": 3, "milieu": 2, "seconde": 2, "contre": 2, "vide": 2},
                           accent=0, legato=0, swing=[0, 54, 58], vel=(60, 115), name="Perc tribale", voices=[["PC"], ["PC", "LT"], ["PC", "MT", "HT"]]),
}

# Ensembles de notes (intervalles depuis la tonique) par nombre de notes
POOLS = {
    1: [[0]],
    2: [[0, 12], [0, 7], [0, 3], [0, 5], [0, 10], [0, -2], [0, 1], [0, -5]],
    3: [[0, 3, 7], [0, 7, 12], [0, 3, 5], [0, 10, 12], [0, 5, 7], [0, 3, 10], [0, 1, 7], [0, -2, 3], [0, 7, 10], [0, 12, 15]],
    4: [[0, 3, 7, 10], [0, 3, 5, 7], [0, 7, 10, 12], [0, 3, 7, 12], [0, 5, 7, 10], [0, 1, 3, 7], [0, -2, 3, 5], [0, 7, 12, 15]],
}
NOTE_COUNT_WEIGHTS = {"bass": {1: 3, 2: 4, 3: 3, 4: 2}, "acid": {1: 1, 2: 3, 3: 4, 4: 4},
                      "synth": {1: 2, 2: 3, 3: 4, 4: 4}}
STRUCTURES = {1: [["A"]], 2: [["A", "A'"], ["A", "B"]], 3: [["A", "A", "B"], ["A", "A'", "A"]],
              4: [["A", "A", "A", "A'"], ["A", "B", "A", "B'"], ["A", "A", "B", "B"], ["A", "A'", "A", "A''"]]}


def pick(weights):
    keys = list(weights); return rng.choices(keys, [weights[k] for k in keys])[0]


def make_bar_rhythm(st):
    """4 cellules ; souvent la cellule du temps 3 reprend celle du temps 1 (cohérence)."""
    cells = [pick(st["cells"]) for _ in range(4)]
    if rng.random() < .55: cells[2] = cells[0]
    if rng.random() < .4: cells[3] = cells[1]
    hits = [c == "x" for name in cells for c in C[name]]
    if st.get("on24"):  # clap/caisse : temps 2 et 4 forcés
        hits[4] = hits[12] = True
    return hits


def vary_rhythm(hits, st, amount):
    """Variation de fin de phrase : on remplace le dernier (ou les 2 derniers) temps."""
    h = hits[:]
    for beat in ([3] if amount == 1 else [2, 3]):
        new = C[pick(st["cells"])]
        for i, c in enumerate(new): h[beat * 4 + i] = c == "x"
    return h


def velocity(i, st):
    lo, hi = st["vel"]
    s = STRENGTH[i]
    if i % 4 == st["accent"]: s = max(s, .8)          # accent du style (contretemps, etc.)
    v = lo + (hi - lo) * s + rng.uniform(-6, 6)
    if s <= .25 and st["kind"] != "acid": v -= 8      # notes fantômes
    return int(max(1, min(127, round(v))))


def assign_pitches(hits, pool, kind):
    out = []; prev = 0; first = True
    for i, h in enumerate(hits):
        if not h: out.append(None); continue
        s = STRENGTH[i]
        if len(pool) == 1: out.append(pool[0]); continue
        # la première note de la mesure pose la tonique (presque toujours pour une basse)
        if first and kind != "perc" and rng.random() < (.95 if kind in ("bass", "acid") else .7):
            out.append(0); prev = 0; first = False; continue
        first = False
        p_root = (.35 + .55 * s) if kind in ("bass", "acid") else (.2 + .4 * s)
        if rng.random() < p_root: n = 0
        else:
            others = [p for p in pool if p != 0]
            # mouvement conjoint préféré : notes proches de la précédente plus probables
            w = [1.0 / (1 + abs(p - prev) / 5) for p in others]
            n = rng.choices(others, w)[0]
        out.append(n); prev = n
    return out


def vary_pitches(pitches, pool):
    p = pitches[:]
    idx = [i for i, x in enumerate(p) if x is not None and i >= 8]
    if idx and len(pool) > 1:
        i = rng.choice(idx); p[i] = rng.choice([x for x in pool if x != p[i]])
    return p


def render_tokens(rhythm, pitches, st, bars_vel):
    toks, vels = [], []
    n = len(rhythm)
    for i in range(n):
        if rhythm[i]:
            t = str(pitches[i])
            if st["kind"] == "acid":
                if bars_vel[i] >= 112: t += "a"
                nxt = next((j for j in range(i + 1, n) if rhythm[j]), None)
                if nxt == i + 1 and rng.random() < st.get("slides", 0): t += "s"
            toks.append(t); vels.append(str(bars_vel[i]))
        else:
            prev_on = next((j for j in range(i - 1, -1, -1) if rhythm[j]), None)
            max_hold = 12 if st["legato"] >= .9 else 4
            hold = prev_on is not None and all(toks[k] == "-" for k in range(prev_on + 1, i)) and (i - prev_on) <= max_hold
            if hold and st["legato"] and rng.random() < st["legato"]:
                toks.append("-"); vels.append(".")
            else:
                toks.append("."); vels.append(".")
    # nettoyage : un « - » ne peut suivre qu'une note ou un autre « - »
    for i, t in enumerate(toks):
        if t == "-" and (i == 0 or toks[i - 1] == "."): toks[i] = "."
    return toks, vels


def make_pattern(style_id, bars, notes_count):
    st = STYLES[style_id]
    A = make_bar_rhythm(st)
    B = make_bar_rhythm(st)
    if st["kind"] == "perc":
        voices = rng.choice(st["voices"]); pool = voices
    else:
        pool = rng.choice(POOLS[notes_count])
    pa = assign_pitches(A, list(range(len(pool))) if st["kind"] == "perc" else pool, "perc" if st["kind"] == "perc" else st["kind"])
    pb = assign_pitches(B, list(range(len(pool))) if st["kind"] == "perc" else pool, "perc" if st["kind"] == "perc" else st["kind"])
    struct = rng.choice(STRUCTURES[bars])
    rhythm, pitches = [], []
    for part in struct:
        base_r, base_p = (A, pa) if part.startswith("A") else (B, pb)
        r, p = base_r[:], base_p[:]
        primes = part.count("'")
        if primes:
            r = vary_rhythm(r, st, primes)
            p = [p[i] if r[i] and p[i] is not None else (None if not r[i] else None) for i in range(16)]
            fill = assign_pitches(r, list(range(len(pool))) if st["kind"] == "perc" else pool, "perc" if st["kind"] == "perc" else st["kind"])
            p = [p[i] if p[i] is not None else fill[i] for i in range(16)]
            p = vary_pitches(p, list(range(len(pool))) if st["kind"] == "perc" else pool)
        rhythm += r; pitches += p
    vel = [velocity(i % 16, st) for i in range(len(rhythm))]
    if st["kind"] == "perc":
        pitches = [pool[x] if x is not None else None for x in pitches]
    return st, struct, pool, rhythm, pitches, vel


def valid(st, rhythm, bars):
    for b in range(bars):
        count = sum(rhythm[b * 16:(b + 1) * 16])
        if count == 0: return False
        if st["kind"] in ("bass", "acid", "synth") and count > 16: return False
    total = sum(rhythm) / bars
    if st["kind"] == "acid" and total < 6: return False
    if st["kind"] == "bass" and total < 2: return False
    return True


TARGET = {"bass": 1400, "acid": 500, "synth": 1100, "perc": 900}


def main():
    files = {"bass": [], "acid": [], "synth": [], "perc": []}
    seen = set(); counters = {}
    by_kind = {}
    for sid, st in STYLES.items(): by_kind.setdefault(st["kind"], []).append(sid)
    for kind, target in TARGET.items():
        tries = 0
        while len(files[kind]) < target and tries < target * 40:
            tries += 1
            sid = rng.choice(by_kind[kind]); st = STYLES[sid]
            bars = rng.choices([1, 2, 3, 4], [4, 4, 1, 3])[0]
            ncount = 1 if kind == "perc" else pick(NOTE_COUNT_WEIGHTS[kind])
            st, struct, pool, rhythm, pitches, vel = make_pattern(sid, bars, ncount)
            if not valid(st, rhythm, bars): continue
            toks, vels = render_tokens(rhythm, pitches, st, vel)
            if kind in ("bass", "acid") and not any(t.rstrip("as") == "0" for t in toks):
                continue  # une basse doit poser la tonique
            key = (kind, " ".join(toks))
            if key in seen: continue
            seen.add(key)
            counters[sid] = counters.get(sid, 0) + 1
            n = counters[sid]
            used = len({x for x in pitches if x is not None})
            notes_lbl = (f"{used} voix" if kind == "perc" else f"{used} note" + ("s" if used > 1 else ""))
            swing = rng.choice(st["swing"])
            name = f"{st['name']} {notes_lbl} {bars} mes. #{n:03d}"
            head = (f'@{ "perc" if kind == "perc" else ("acid" if kind == "acid" else ("bass" if kind == "bass" else "melody"))} '
                    f'id=g-{sid}-{n:04d} name="{name}" genre={st["genre"]} bars={bars} steps=16 '
                    f'tags={sid},{"-".join(struct).replace(chr(39), "v")}' + (f" swing={swing}" if swing else "") + " src=gen")
            body = []
            for b in range(bars):
                body.append("N  " + " ".join(toks[b * 16:(b + 1) * 16]))
                body.append("V  " + " ".join(vels[b * 16:(b + 1) * 16]))
            files[kind].append(head + "\n" + "\n".join(body) + "\n")
    header = ("# Motifs fabriqués par règles de groove (tools/generate_patterns.py) : hiérarchie métrique,\n"
              "# cellules rythmiques par style, phrasé sur 1 à 4 mesures, 1 à 4 notes, vélocités accentuées.\n"
              "# N = notes (intervalle depuis la tonique, ou instrument pour les percussions ; a accent, s slide,\n"
              "# . silence, - tenue) ; V = vélocité de chaque note.\n\n")
    names = {"bass": "gen_bass.txt", "acid": "gen_acid.txt", "synth": "gen_synth.txt", "perc": "gen_perc.txt"}
    for k, items in files.items():
        (LIB / names[k]).write_text(header + "\n".join(items))
        print(k, len(items))


if __name__ == "__main__":
    main()
