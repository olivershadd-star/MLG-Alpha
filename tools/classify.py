"""Classe la bibliothèque MLG Alpha et la compile pour le plugin.

Lit tous les Library/*.txt, puis pour chaque motif :
  - le convertit en liste de notes (temps et durée en 1/12 de pas, hauteur, vélocité) ;
  - range le motif dans l'une des 12 familles (ou « hors cible ») ;
  - lui donne son rôle (kick, batterie, percu, basse, lead, accords, nappe) ;
  - calcule des mesures objectives (densité, durées, registre, intervalles, syncope…) ;
  - choisit 3 à 5 étiquettes parmi les 100 mots, avec une confiance de 1 à 9 ;
  - extrait la ligne de kick des batteries complètes ;
  - retire les doublons (même rythme et mêmes notes, vélocités ignorées).

Sortie : Resources/mlg_library.txt.gz (lu par le plugin) et un rapport sur la sortie standard.
Usage : python3 tools/classify.py
"""
import gzip, os, re, sys, glob, hashlib, collections, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "Library")
OUT = os.path.join(ROOT, "Resources", "mlg_library.txt.gz")
SUB = 12  # sous-divisions d'un pas (gère demi-pas et ratchets 2/3/4)

DRUMS = {"BD": 36, "RS": 37, "SN": 38, "CL": 39, "CH": 42, "OH": 46, "LT": 45, "MT": 47,
         "HT": 50, "CY": 51, "CB": 56, "SH": 70, "PC": 75}

# ---------------------------------------------------------------- familles
FAMILIES = ["techno", "techno-dure", "minimal-dub", "house", "acid", "ebm", "rock-indus",
            "electro-breaks", "trance-rave", "ambient", "idm", "melodique", "hors-cible"]
GENRE_FAMILY = {
    "techno": "techno", "hardgroove": "techno", "hard-techno": "techno-dure",
    "industrial-techno": "techno-dure", "swedish-techno": "techno-dure",
    "minimal": "minimal-dub", "dub-techno": "minimal-dub", "dub": "minimal-dub",
    "house": "house", "tech-house": "house", "deep-house": "house", "ukg": "house", "disco": "house",
    "funk": "house", "boogie": "house", "amapiano": "house", "gqom": "house",
    "acid": "acid",
    "ebm": "ebm", "electro-industrial": "ebm", "dark-electro": "ebm", "aggrotech": "ebm", "industrial": "ebm",
    "industrial-rock": "rock-indus", "noise-rock": "rock-indus", "industrial-metal": "rock-indus",
    "metal": "rock-indus", "prog-metal": "rock-indus", "rock": "rock-indus",
    "electro": "electro-breaks", "breaks": "electro-breaks", "miami-bass": "electro-breaks",
    "dnb": "electro-breaks", "uk-bass": "electro-breaks", "footwork": "electro-breaks",
    "hiphop": "electro-breaks", "trap": "electro-breaks", "dubstep": "electro-breaks", "dembow": "electro-breaks",
    "trance": "trance-rave", "rave": "trance-rave", "psytrance": "trance-rave", "progressive": "trance-rave",
    "ambient": "ambient", "drone": "ambient", "pad": "ambient",
    "idm": "idm", "boc": "idm",
    "moderat": "melodique", "melodic-techno": "melodique", "synthwave": "melodique",
    "berlin-school": "melodique", "arp": "melodique", "pop": "melodique",
    "majeur": "melodique", "mineur": "melodique", "modal": "melodique",
    "offbeat": "minimal-dub",
}
TRIPLET_FAMILY = {"trip-trap": "electro-breaks", "trip-fill": "electro-breaks", "trip-arp": "melodique",
                  "trip-bass": "techno", "trip-hats-12": "techno", "trip-hats-24": "techno",
                  "jazz-ternary": "hors-cible"}

# ---------------------------------------------------------------- les 100 mots
WORDS = {
    "mouvement": "rectiligne hypnotique roulant martelé haché saccadé syncopé bancal boiteux cassé "
                 "régulier mécanique galopant sautillant lancinant obsédant répétitif pulsé chaloupé groovy",
    "energie": "calme posé lent tendu nerveux agressif brutal explosif frénétique puissant lourd léger retenu montant",
    "humeur": "sombre mélancolique triste déprimé nostalgique inquiétant menaçant angoissant oppressant glacial "
              "froid mystérieux solennel martial rêveur apaisé lumineux euphorique",
    "harmonie": "mineur majeur dissonant consonant tendu-h suspendu modal exotique chromatique atonal ouvert épuré",
    "espace": "dense chargé rempli aéré clairsemé minimal dépouillé vide ample planant flottant suspendu-t étiré serré",
    "registre": "grave sub médium aigu profond perché",
    "matiere": "gras épais sec claquant distordu saturé grinçant métallique étouffé feutré sale crade rugueux "
               "chaud brillant acide",
}
CATEGORY = {w: c for c, ws in WORDS.items() for w in ws.split()}
assert len(CATEGORY) == 100, len(CATEGORY)

# ---------------------------------------------------------------- lecture
HDR = re.compile(r'(\w+)=("[^"]*"|\S+)')
TOK = re.compile(r'^(-?\d+|[A-Z]{2})([as]*)(?:\*(\d))?([as]*)$')


def parse_file(path):
    pats, cur = [], None
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if line.startswith("#"):
            continue
        if line.startswith("@"):
            typ = line.split()[0][1:]
            h = {k: v.strip('"') for k, v in HDR.findall(line)}
            cur = {"type": typ, "h": h, "lines": [], "file": os.path.basename(path)}
            pats.append(cur)
        elif line.strip() and cur is not None:
            cur["lines"].append(line)
    return pats


def note_lines(p, steps, bars):
    """Lignes N/V -> notes. Renvoie [(t, l, p, v, slide)] avec p entier (intervalle) ou nom de batterie."""
    voices = collections.OrderedDict()
    vels = collections.defaultdict(list)
    for ln in p["lines"]:
        head, *toks = ln.split()
        if re.fullmatch(r"N\d?", head):
            voices.setdefault(head[1:] or "1", []).append(toks)
        elif re.fullmatch(r"V\d?", head):
            vels[head[1:] or "1"].append(toks)
    notes = []
    for vk, rows in voices.items():
        last = None
        for bi, toks in enumerate(rows):
            vrow = vels[vk][bi] if bi < len(vels[vk]) else []
            n = len(toks)
            for si, tk in enumerate(toks):
                t = (bi * n + si) * SUB
                if tk == ".":
                    last = None
                    continue
                if tk == "-":
                    if last is not None:
                        last[1] += SUB
                    continue
                m = TOK.match(tk)
                if not m:
                    raise ValueError("jeton " + tk)
                val = m.group(1)
                flags = m.group(2) + m.group(4)
                rat = int(m.group(3) or 1)
                pitch = int(val) if val.lstrip("-").isdigit() else val
                vt = vrow[si] if si < len(vrow) else "."
                v = int(vt) if vt.isdigit() else (120 if "a" in flags else 100)
                if rat > 1:
                    sub = SUB // rat
                    for r in range(rat):
                        notes.append([t + r * sub, max(1, sub - 1), pitch, v if r == 0 else max(1, v - 12), False])
                    last = None
                else:
                    last = [t, SUB, pitch, v, "s" in flags]
                    notes.append(last)
    return notes


def grid_lines(p, steps, bars):
    total = steps * bars
    acc = set()
    rows = []
    for ln in p["lines"]:
        head, *rest = ln.split(None, 1)
        s = "".join(rest).replace(" ", "")
        if head == "AC":
            acc = {i for i, c in enumerate(s) if c != "."}
            continue
        if head == "R":
            head = "CH"  # rythme de jeu d'accords, traité à part
        rows.append((head, s))
    notes = []
    for head, s in rows:
        if len(s) < total and len(s) > 0:
            s = (s * (total // len(s) + 1))[:total]
        for i, c in enumerate(s[:total]):
            t = i * SUB
            v = 120 if (c == "X" or i in acc) else 100
            if c in "xX":
                notes.append([t, SUB // 2, head, v, False])
            elif c == "r":
                notes.append([t, SUB // 2 - 1, head, v, False])
                notes.append([t + SUB // 2, SUB // 2 - 1, head, v - 15, False])
            elif c == "h":
                notes.append([t + SUB // 2, SUB // 2 - 1, head, v, False])
    return notes


# ---------------------------------------------------------------- accords
MAJ = [0, 2, 4, 5, 7, 9, 11]
MIN = [0, 2, 3, 5, 7, 8, 10]
ROMAN = re.compile(r'^([b#]?)(VII|VI|V|IV|III|II|I|vii|vi|v|iv|iii|ii|i)(.*)$')


def chord_notes(sym, minor_key):
    sym, _, slash = sym.partition("/")
    m = ROMAN.match(sym)
    if not m:
        return None
    acc, num, suf = m.groups()
    deg = ["i", "ii", "iii", "iv", "v", "vi", "vii"].index(num.lower())
    if acc:
        root = MAJ[deg] + (-1 if acc == "b" else 1)
    else:
        root = (MIN if minor_key else MAJ)[deg]
    minor = num.islower()
    scale = MIN if minor_key else MAJ
    if suf.startswith("m") and not suf.startswith("maj"):
        minor, suf = True, suf[1:]
    elif suf.startswith("M") and not suf.startswith("M-"):
        minor, suf = False, suf[1:]
    tri = [0, 3, 7] if minor else [0, 4, 7]
    if "dim" in suf:
        tri = [0, 3, 6]
    if suf.startswith("5"):
        tri = [0, 7]
    if "sus2" in suf:
        tri = [0, 2, 7]
    if "sus4" in suf:
        tri = [0, 5, 7]
    if "-5" in suf:
        tri = [x if x != 7 else 6 for x in tri]
    ext = []
    if "maj7" in suf:
        ext.append(11)
    elif "dom7" in suf:
        ext.append(10)
    elif "7" in suf or "9" in suf.replace("add9", "").replace("69", ""):
        sev = (scale[(deg + 6) % 7] - scale[deg]) % 12 if not acc else (10 if minor else 11)
        ext.append(sev)
    if "9" in suf:
        ext.append(14)
    if "6" in suf:
        ext.append(9)
    tones = sorted(set(tri + ext))
    bass = root
    if slash:
        sm = ROMAN.match(slash)
        if sm:
            d2 = ["i", "ii", "iii", "iv", "v", "vi", "vii"].index(sm.group(2).lower())
            bass = MAJ[d2] + (-1 if sm.group(1) == "b" else 1 if sm.group(1) == "#" else 0)
    return root, tones, bass


def voice(prev, root, tones):
    """Choisit le renversement le plus proche de l'accord précédent (notes entre -3 et 16)."""
    best = None
    for octv in (-12, 0, 12):
        for inv in range(len(tones)):
            ns = [root + octv + x for x in tones]
            for k in range(inv):
                ns[k] += 12
            ns.sort()
            if ns[0] < -3 or ns[-1] > 17:
                continue
            cost = sum(abs(a - b) for a, b in zip(ns, prev)) if prev and len(prev) == len(ns) else abs(ns[0] - 4)
            if best is None or cost < best[0]:
                best = (cost, ns)
    return best[1] if best else [root + x for x in tones]


def chords_pattern(p, steps, bars):
    syms = []
    for ln in p["lines"]:
        if ln.startswith("C "):
            syms += ln.split()[1:]
    minor_key = bool(syms) and (syms[0].startswith("i") and not syms[0].startswith("I")) \
        or p["h"].get("genre") == "mineur"
    notes, prev, bar = [], None, 0
    for sym in syms:
        if sym == "-":
            for n in notes[-(len(prev) + 1 if prev else 0):]:
                n[1] += steps * SUB
            bar += 1
            continue
        c = chord_notes(sym, minor_key)
        if not c:
            bar += 1
            continue
        root, tones, bass = c
        vs = voice(prev, root, tones)
        prev = vs
        t = bar * steps * SUB
        b = bass % 12 - 12 if bass % 12 <= 5 else bass % 12 - 24
        notes.append([t, steps * SUB - 2, b, 90, False])
        for i, x in enumerate(vs):
            notes.append([t, steps * SUB - 2, x, 84 - 3 * i, False])
        bar += 1
    return notes, max(bar, 1)


def rhythm_pattern(p, steps, bars):
    s = "".join(ln.split(None, 1)[1].replace(" ", "") for ln in p["lines"] if ln.startswith("R "))
    notes = []
    for i, c in enumerate(s):
        if c in "xX":
            for x in (0, 3, 7, 12):
                notes.append([i * SUB, SUB - 2, x, 100 if c == "X" else 92, False])
    return notes


# ---------------------------------------------------------------- mesures
def measures(pat):
    ns, steps, bars = pat["notes"], pat["steps"], pat["bars"]
    total = steps * bars
    starts = sorted({n[0] for n in ns})
    m = {}
    m["onsets"] = len(starts)
    m["density"] = len({n[0] // SUB for n in ns}) / total if total else 0
    lens = [n[1] / SUB for n in ns]
    m["len"] = statistics.mean(lens) if lens else 0
    vels = [n[3] for n in ns]
    m["vmin"], m["vmax"] = (min(vels), max(vels)) if vels else (0, 0)
    m["vstd"] = statistics.pstdev(vels) if len(vels) > 1 else 0
    on_beat = off8 = off16 = 0
    triplet = steps in (12, 24)
    per_beat = steps // 4 if steps >= 4 else 1
    for t in starts:
        st = t / SUB
        pos = st % per_beat if per_beat else 0
        if pos == 0:
            on_beat += 1
        elif not triplet and per_beat == 4 and pos == 2:
            off8 += 1
        else:
            off16 += 1
    n = max(1, len(starts))
    m["onbeat"], m["off8"], m["off16"] = on_beat / n, off8 / n, off16 / n
    m["sub_hits"] = sum(1 for t in starts if t % SUB) / n
    # répétition entre mesures
    barsets = [frozenset((n[0] - b * steps * SUB, n[2]) for n in ns if b * steps * SUB <= n[0] < (b + 1) * steps * SUB)
               for b in range(bars)]
    m["repeat"] = (sum(1 for b in barsets[1:] if b == barsets[0]) / (bars - 1)) if bars > 1 else 1.0
    # régularité des intervalles entre attaques
    gaps = [b - a for a, b in zip(starts, starts[1:])]
    m["gapvar"] = (statistics.pstdev(gaps) / statistics.mean(gaps)) if len(gaps) > 1 and statistics.mean(gaps) else 0
    if pat["abs"]:
        m.update(pmean=0, prange=0, jump=0, pcs=set(), poly=1, insts=len({n[2] for n in ns}))
    else:
        ps = [n[2] for n in ns]
        m["pmean"] = statistics.mean(ps) if ps else 0
        m["prange"] = (max(ps) - min(ps)) if ps else 0
        mono = sorted(ns, key=lambda n: (n[0], n[2]))
        iv = [abs(b[2] - a[2]) for a, b in zip(mono, mono[1:]) if b[0] != a[0]]
        m["jump"] = statistics.mean(iv) if iv else 0
        m["pcs"] = {p % 12 for p in ps}
        poly = collections.Counter(n[0] for n in ns)
        m["poly"] = max(poly.values()) if poly else 1
        m["insts"] = 1
    return m


def clamp(x):
    return max(0.0, min(1.0, x))


def score_words(pat, m):
    fam, role, src_tags = pat["family"], pat["role"], pat["srctags"]
    d, L, sync = m["density"], m["len"], m["off16"]
    vrange = m["vmax"] - m["vmin"]
    pcs = m["pcs"]
    melodic = not pat["abs"]
    low = melodic and m["pmean"] < -6
    high = melodic and m["pmean"] > 12
    minor = 3 in pcs and 4 not in pcs
    major = 4 in pcs and 3 not in pcs
    diss = len(pcs & {1, 6, 11})
    chrom = len(pcs - set(MIN) - set(MAJ)) + (1 if (3 in pcs and 4 in pcs) else 0)
    longn = L >= 6
    S = {}
    F = lambda *fs: fam in fs
    R = lambda *rs: role in rs
    has = lambda *ts: any(t in src_tags for t in ts)
    # mouvement
    S["rectiligne"] = clamp((m["repeat"] - 0.5) * 2) * clamp(1 - m["gapvar"]) * (0.9 if d > 0.4 else 0.5)
    S["hypnotique"] = clamp(m["repeat"]) * 0.6 + (0.3 if F("techno", "techno-dure", "minimal-dub") else 0) + (0.2 if has("poly", "fam_rolling") or any(t.startswith("poly") for t in src_tags) else 0)
    S["roulant"] = (0.8 if has("fam_rolling", "trance-16th", "trance-bass") else 0) + clamp((d - 0.45) * 2) * 0.6 * (1 if R("bass") else 0.5)
    S["martelé"] = clamp(m["onbeat"] * 1.2) * clamp(d * 3) * (0.9 if m["vmax"] > 110 else 0.6) * (1 if F("techno-dure", "ebm", "rock-indus") else 0.7)
    S["haché"] = clamp(L < 0.6) * clamp(d * 2) * 0.8 + (0.3 if m["sub_hits"] > 0.1 else 0)
    S["saccadé"] = clamp(m["gapvar"]) * 0.6 + (0.3 if L < 0.7 else 0)
    S["syncopé"] = clamp(sync * 1.6)
    S["bancal"] = clamp(m["gapvar"] - 0.4) * 0.8 + (0.4 if has("drunk") else 0)
    S["boiteux"] = (0.7 if has("bass-gallop,A") or any(t.startswith(("poly5", "poly7", "prog-5", "prog-7")) for t in src_tags) else 0) + clamp(m["gapvar"] - 0.6) * 0.4
    S["cassé"] = (0.7 if F("idm", "electro-breaks") and m["gapvar"] > 0.5 else 0) + (0.3 if has("drill") else 0)
    S["régulier"] = clamp(1 - m["gapvar"]) * 0.8 + (0.1 if m["onbeat"] > 0.5 else 0)
    S["mécanique"] = clamp(1 - m["gapvar"]) * clamp(1 - m["vstd"] / 15) * 0.9 + (0.2 if F("ebm") else 0)
    S["galopant"] = 0.9 if has("bass-gallop,A", "metal-double") else (0.5 if (m["off16"] > 0.3 and d > 0.4 and m["gapvar"] > 0.3) else 0)
    S["sautillant"] = clamp(m["off8"] * 1.5) * (0.8 if L < 1.2 else 0.4) + (0.3 if F("house") else 0)
    S["lancinant"] = clamp(m["repeat"]) * (0.7 if (melodic and m["prange"] <= 7 and longn is False and d < 0.5) else 0.2) + (0.2 if minor else 0)
    S["obsédant"] = clamp(m["repeat"]) * (0.6 if (melodic and len(pcs) <= 3) else 0.3)
    S["répétitif"] = clamp(m["repeat"]) * 0.8 + (0.15 if len(pcs) <= 2 else 0)
    S["pulsé"] = clamp(m["onbeat"] + m["off8"]) * clamp(1 - m["gapvar"]) * 0.7 + (0.2 if F("trance-rave", "techno") else 0)
    S["chaloupé"] = (0.8 if has("jazz-swing", "light-swing") else 0) + (0.5 if F("house", "minimal-dub") and sync > 0.3 else 0)
    S["groovy"] = clamp(sync * 1.2) * clamp(vrange / 50) + (0.3 if F("house", "electro-breaks") else 0)
    # énergie
    S["calme"] = clamp(1 - d * 2.5) * (0.9 if m["vmax"] < 105 else 0.5) + (0.2 if F("ambient") else 0)
    S["posé"] = clamp(1 - d * 2) * clamp(1 - m["gapvar"]) * 0.8
    S["lent"] = clamp(L / 8) * 0.8 + (0.2 if d < 0.15 else 0)
    S["tendu"] = (0.4 if F("techno-dure", "ebm", "rock-indus") else 0) + clamp(sync) * 0.3 + (0.3 if diss else 0)
    S["nerveux"] = clamp((d - 0.4) * 2) * (0.6 if L < 0.8 else 0.3) + clamp(m["gapvar"]) * 0.3
    S["agressif"] = (0.5 if F("ebm", "techno-dure", "rock-indus") else 0) + clamp((m["vmax"] - 105) / 20) * 0.4 + (0.2 if d > 0.5 else 0)
    S["brutal"] = (0.5 if F("rock-indus", "techno-dure") else 0) + clamp((m["vmax"] - 115) / 12) * 0.3 + (0.2 if has("metal-double", "indus-metal", "noise") else 0)
    S["explosif"] = clamp((vrange - 40) / 40) * 0.6 + (0.3 if has("fill") or R("drums") and d > 0.6 else 0)
    S["frénétique"] = clamp((d - 0.6) * 3) * 0.8 + (0.4 if has("drill", "metal-double") else 0)
    S["puissant"] = clamp((m["vmax"] - 105) / 20) * 0.5 + (0.3 if low or R("kick") else 0) + (0.2 if m["onbeat"] > 0.5 else 0)
    S["lourd"] = (0.5 if low or R("kick") else 0) + (0.3 if has("halftime", "metal-halftime") else 0) + clamp(L / 4) * 0.2
    S["léger"] = (0.6 if R("perc") and m["vmax"] < 105 else 0) + (0.3 if high else 0) + (0.3 if has("light-tick16", "light-sparse", "light-poly", "minimal-click") else 0)
    S["retenu"] = clamp(1 - d * 3) * 0.6 + (0.3 if m["vmax"] < 95 else 0)
    S["montant"] = 0.8 if has("vel-crescendo", "trance-clap") else 0
    # humeur
    S["sombre"] = (0.5 if minor else 0) + (0.3 if F("techno-dure", "ebm", "minimal-dub", "techno") else 0) + (0.2 if low else 0) + (0.3 if has("dark-arp", "gothic-lead") else 0)
    S["mélancolique"] = (0.7 if has("melancholic") else 0) + (0.4 if minor and F("melodique", "idm", "ambient") else 0) + (0.2 if longn and minor else 0)
    S["triste"] = (0.5 if minor and d < 0.35 and melodic else 0) + (0.2 if F("ambient", "idm") and minor else 0)
    S["déprimé"] = (0.4 if minor and low and d < 0.3 else 0) + (0.2 if F("ambient") and minor and longn else 0)
    S["nostalgique"] = (0.7 if has("boc", "boc-beat") else 0) + (0.4 if F("idm") and melodic else 0) + (0.2 if major and F("melodique") else 0)
    S["inquiétant"] = (0.5 if diss else 0) + (0.3 if minor and low else 0) + (0.2 if F("ambient", "ebm") else 0)
    S["menaçant"] = (0.4 if low else 0) + (0.3 if diss else 0) + (0.3 if F("techno-dure", "ebm") else 0)
    S["angoissant"] = (0.5 if diss >= 2 or chrom >= 2 else 0) + (0.3 if F("techno-dure", "ebm") and melodic else 0)
    S["oppressant"] = (0.4 if F("techno-dure", "rock-indus") else 0) + (0.3 if d > 0.5 and low else 0) + (0.2 if has("noise") else 0)
    S["glacial"] = (0.4 if F("techno-dure", "ebm") and melodic and longn else 0) + (0.4 if F("ambient") and minor else 0) + (0.2 if diss else 0)
    S["froid"] = (0.5 if F("ebm", "techno-dure", "techno") else 0) + clamp(1 - m["vstd"] / 20) * 0.3
    S["mystérieux"] = (0.4 if F("ambient", "idm") else 0) + (0.3 if diss or chrom else 0) + (0.2 if d < 0.3 else 0)
    S["solennel"] = (0.5 if R("pad") and minor else 0) + (0.3 if longn and d < 0.2 else 0)
    S["martial"] = (0.8 if F("ebm") and R("drums", "perc", "kick") else 0) + (0.3 if m["onbeat"] > 0.6 and m["gapvar"] < 0.3 else 0)
    S["rêveur"] = (0.5 if F("ambient", "idm", "melodique") and melodic else 0) + (0.3 if has("floating") else 0) + (0.2 if longn else 0)
    S["apaisé"] = (0.5 if F("ambient") else 0) + clamp(1 - d * 3) * 0.3 + (0.2 if major else 0)
    S["lumineux"] = (0.6 if major else 0) + (0.3 if high else 0) + (0.2 if F("trance-rave", "melodique") and not minor else 0)
    S["euphorique"] = (0.5 if F("trance-rave") else 0) + (0.3 if major else 0) + (0.2 if d > 0.5 else 0)
    # harmonie
    S["mineur"] = 0.9 if minor else 0
    S["majeur"] = 0.9 if major else 0
    S["dissonant"] = clamp(diss / 2) * 0.9
    S["consonant"] = (0.7 if melodic and not diss and not chrom and len(pcs) >= 2 else 0)
    S["tendu-h"] = (0.5 if 6 in pcs else 0) + (0.3 if 1 in pcs else 0)
    S["suspendu"] = (0.8 if has("pad-mineur-sus2") else 0) + (0.4 if melodic and 3 not in pcs and 4 not in pcs and (2 in pcs or 5 in pcs) else 0)
    S["modal"] = (0.6 if (2 in pcs and 9 in pcs and 3 in pcs) or (1 in pcs and 3 in pcs) else 0) + (0.3 if pat["h"].get("genre") == "modal" else 0)
    S["exotique"] = (0.6 if (1 in pcs and 4 in pcs) or (3 in pcs and 11 in pcs and 8 in pcs) else 0)
    S["chromatique"] = clamp(chrom / 2) * 0.8
    S["atonal"] = (0.9 if has("atonal", "noise") else 0) + (0.4 if len(pcs) >= 8 else 0)
    S["ouvert"] = (0.6 if melodic and pcs and pcs <= {0, 7, 5, 2} and len(pcs) >= 2 else 0) + (0.2 if m["prange"] >= 12 else 0)
    S["épuré"] = (0.7 if melodic and len(pcs) <= 2 else 0) + (0.2 if d < 0.25 else 0)
    # espace
    S["dense"] = clamp((d - 0.5) * 2.5)
    S["chargé"] = clamp((d - 0.55) * 2) * 0.6 + (0.4 if m["poly"] >= 4 or m["insts"] >= 5 else 0)
    S["rempli"] = clamp((d - 0.45) * 2) * 0.7 + (0.3 if L >= 1 and d > 0.4 else 0)
    S["aéré"] = clamp((0.4 - d) * 3) * 0.8
    S["clairsemé"] = clamp((0.25 - d) * 5) * 0.9
    S["minimal"] = clamp((0.3 - d) * 4) * 0.5 + (0.4 if F("minimal-dub") else 0) + (0.2 if len(pcs) <= 2 else 0)
    S["dépouillé"] = clamp((0.2 - d) * 6) * 0.7 + (0.2 if m["insts"] <= 1 and len(pcs) <= 2 else 0)
    S["vide"] = clamp((0.1 - d) * 12) * 0.8
    S["ample"] = (0.6 if R("pad") else 0) + (0.3 if m["prange"] >= 12 else 0)
    S["planant"] = (0.7 if longn and F("ambient", "melodique", "trance-rave") else 0) + (0.3 if R("pad") else 0)
    S["flottant"] = (0.7 if has("floating", "droney") else 0) + (0.4 if longn and d < 0.25 else 0)
    S["suspendu-t"] = (0.5 if d < 0.15 and longn else 0) + (0.3 if has("droney", "drone-2v", "drone-3v") else 0)
    S["étiré"] = clamp(L / 12) * 0.9
    S["serré"] = clamp(1 - L) * clamp(d * 2) * 0.8
    # registre (les batteries n'ont pas de registre mélodique)
    if melodic:
        pm = m["pmean"]
        S["grave"] = clamp((-3 - pm) / 6) if R("bass") else clamp((-6 - pm) / 6)
        S["sub"] = 0.8 if has("sub", "fam_rumble") else (0.5 if R("bass") and m["prange"] <= 5 and pm <= 0 else 0)
        S["médium"] = clamp(1 - abs(pm - 5) / 7) * (0.6 if R("lead", "chords") else 0.3)
        S["aigu"] = clamp((pm - 12) / 8)
        S["profond"] = (0.5 if low and longn else 0) + (0.3 if has("fam_rumble") else 0)
        S["perché"] = clamp((pm - 17) / 6)
    else:
        S["grave"] = 0.6 if R("kick") else 0
        S["profond"] = 0.4 if R("kick") and F("minimal-dub", "techno") else 0
        S["aigu"] = 0.5 if R("perc") and all(n[2] in (42, 70, 37, 56, 51, 75, 46) for n in pat["notes"]) else 0
    # matière : seulement des tendances (dépend du synthé), confiance plafonnée
    cap = 0.55
    S["gras"] = min(cap, (0.4 if R("bass") and L >= 1 else 0) + (0.2 if F("ebm", "acid") else 0))
    S["épais"] = min(cap, 0.4 if R("pad") and m["poly"] >= 4 else 0)
    S["sec"] = min(cap, 0.5 if L < 0.6 else 0)
    S["claquant"] = min(cap, (0.3 if L < 0.6 else 0) + (0.3 if m["vmax"] >= 115 else 0))
    S["distordu"] = min(cap, 0.5 if has("fuzz", "indus-metal") else 0)
    S["saturé"] = min(cap, 0.4 if F("rock-indus", "techno-dure") and R("bass", "lead") else 0)
    S["grinçant"] = min(cap, 0.4 if has("noise") or (diss and F("techno-dure", "rock-indus")) else 0)
    S["métallique"] = min(cap, 0.5 if R("perc") and any(n[2] in (56, 51, 37) for n in pat["notes"]) else (0.3 if has("noise") else 0))
    S["étouffé"] = min(cap, 0.4 if F("minimal-dub") and R("chords", "pad") else 0)
    S["feutré"] = min(cap, 0.4 if m["vmax"] < 90 else 0)
    S["sale"] = min(cap, (0.3 if F("techno-dure", "rock-indus") else 0) + (0.2 if has("noise", "fuzz") or diss else 0))
    S["crade"] = min(cap, 0.3 if has("noise") else 0)
    S["rugueux"] = min(cap, 0.3 if F("techno-dure", "rock-indus") else 0)
    S["chaud"] = min(cap, 0.4 if F("minimal-dub", "house") and R("chords", "pad", "bass") else 0)
    S["brillant"] = min(cap, 0.4 if high else 0)
    S["acide"] = 0.9 if F("acid") and R("bass", "lead") else 0
    return S


def pick_tags(S):
    ranked = sorted(S.items(), key=lambda kv: -kv[1])
    out, per_cat = [], collections.Counter()
    for w, s in ranked:
        if len(out) >= 5:
            break
        if s <= 0.05:
            break
        if per_cat[CATEGORY[w]] >= 2:
            continue
        if len(out) >= 3 and s < 0.5:
            break
        out.append((w, max(1, min(9, round(s * 9)))))
        per_cat[CATEGORY[w]] += 1
    return out


# ---------------------------------------------------------------- rôle
def role_of(pat):
    typ = pat["type"]
    ns = pat["notes"]
    if pat["abs"]:
        insts = {n[2] for n in ns}
        if insts == {36}:
            return "kick"
        return "drums" if (36 in insts and len(insts) >= 2) else "perc"
    if typ in ("bass", "acid"):
        return "bass"
    poly = collections.Counter(n[0] for n in ns)
    mx = max(poly.values()) if poly else 1
    L = statistics.mean(n[1] for n in ns) / SUB if ns else 0
    if typ in ("chords", "pad") or mx >= 2:
        if mx >= 2:
            return "pad" if L >= 6 else "chords"
        return "pad" if L >= 4 else "lead"
    if L >= 8:
        return "pad"
    return "lead"


# ---------------------------------------------------------------- compilation
def build():
    files = sorted(glob.glob(os.path.join(LIB, "*.txt")))
    # écrits à la main et sources réelles d'abord : ce sont eux qu'on garde en cas de doublon
    pri = lambda f: (0 if not os.path.basename(f).startswith(("gen_", "fill_", "tex_", "techno_", "industrial_", "bass_neural")) else 1, f)
    files.sort(key=pri)
    pats = []
    errors = 0
    for f in files:
        for p in parse_file(f):
            h = p["h"]
            steps = int(h.get("steps", 16))
            bars = int(h.get("bars", 1))
            try:
                kinds = {ln.split()[0] for ln in p["lines"]}
                if p["type"] == "chords" or "C" in kinds:
                    notes, bars = chords_pattern(p, steps, bars)
                elif p["type"] == "rhythm":
                    notes = rhythm_pattern(p, steps, bars)
                elif any(re.fullmatch(r"N\d?", k) for k in kinds):
                    notes = note_lines(p, steps, bars)
                    nb = max(len([ln for ln in p["lines"] if ln.split()[0] == "N"]), 1)
                    bars = max(bars, nb) if nb > 1 else bars
                    if nb == 1 and bars > 1:  # une seule mesure écrite : on la répète
                        one = [n[:] for n in notes]
                        for b in range(1, bars):
                            notes += [[n[0] + b * steps * SUB] + n[1:] for n in one]
                else:
                    notes = grid_lines(p, steps, bars)
            except Exception as e:
                errors += 1
                continue
            if not notes:
                continue
            isabs = any(isinstance(n[2], str) for n in notes)
            if isabs:
                notes = [n for n in notes if isinstance(n[2], str)]
                for n in notes:
                    n[2] = DRUMS[n[2]]
            genre = h.get("genre", "")
            srctags = set(h.get("tags", "").split(",")) | set(h.get("tags", "").split()) | {h.get("tags", "")}
            fam = GENRE_FAMILY.get(genre, "hors-cible")
            if genre == "triplet":
                fam = TRIPLET_FAMILY.get(h.get("tags", ""), "techno")
            pat = {"id": h.get("id", "?"), "name": h.get("name", ""), "type": p["type"], "h": h,
                   "steps": steps, "bars": bars, "abs": isabs, "notes": notes, "family": fam,
                   "srctags": srctags, "src": h.get("src", "main")}
            pats.append(pat)
    # lignes de kick extraites des batteries complètes
    extra = []
    for pat in pats:
        if pat["abs"]:
            kick = [n[:] for n in pat["notes"] if n[2] == 36]
            if kick and len(kick) < len(pat["notes"]):
                k = dict(pat)
                k.update(id=pat["id"] + "-kick", name=pat["name"] + " (kick)", notes=kick)
                extra.append(k)
    pats += extra
    # rôles, mesures, contrôle qualité
    kept, seen = [], set()
    dup = rej = 0
    for pat in pats:
        pat["notes"].sort(key=lambda n: (n[0], n[2]))
        pat["role"] = role_of(pat)
        if pat["role"] == "bass":  # une basse reste dans le grave : on la descend d'octave si besoin
            while statistics.mean(n[2] for n in pat["notes"]) > 6:
                for n in pat["notes"]:
                    n[2] -= 12
        m = measures(pat)
        if pat["src"] == "neuralacid":
            # tri des basses NeuralAcid : on écarte les lignes trop vides, trop larges ou trop sautillantes
            if m["onsets"] < 6 or m["prange"] > 26 or m["jump"] > 8:
                pat["family"] = "hors-cible"
                rej += 1
        # empreinte : rythme + notes de la période minimale, vélocités ignorées
        per = pat["steps"] * SUB
        total = per * pat["bars"]
        key_full = tuple((n[0], n[2]) for n in pat["notes"])
        period = total
        for b in range(1, pat["bars"] + 1):
            if pat["bars"] % b:
                continue
            P = b * per
            first = tuple((t, p) for t, p in key_full if t < P)
            if all((t % P, p) in set(first) for t, p in key_full) and len(key_full) == len(first) * (total // P):
                period = P
                break
        fp_src = (pat["abs"], pat["steps"], period, tuple((t, p) for t, p in key_full if t < period))
        fp = hashlib.sha1(repr(fp_src).encode()).hexdigest()[:16]
        if fp in seen:
            dup += 1
            continue
        seen.add(fp)
        pat["fp"] = fp
        pat["m"] = m
        pat["raw"] = score_words(pat, m)
        kept.append(pat)
    # étiquettes distinctives : on mélange le score brut et l'écart à la moyenne de la bibliothèque,
    # pour qu'un mot présent partout (« syncopé ») ne colle pas à tous les motifs
    stats = {}
    for w in CATEGORY:
        vals = [p["raw"].get(w, 0) for p in kept]
        mu = statistics.mean(vals)
        sd = statistics.pstdev(vals) or 1
        stats[w] = (mu, sd)
    for p in kept:
        S = {}
        for w, raw in p["raw"].items():
            mu, sd = stats[w]
            z = clamp((raw - mu) / (2.5 * sd) + 0.35) if raw > 0 else 0
            S[w] = 0.5 * raw + 0.5 * z
        p["tags"] = pick_tags(S)
    # chaque mot doit exister dans la bibliothèque : les mots trop rares vont aux motifs qui les portent le plus
    count = collections.Counter(w for p in kept for w, _ in p["tags"])
    for w in CATEGORY:
        if count[w] >= 150:
            continue
        cands = sorted((p for p in kept if p["raw"].get(w, 0) >= 0.2 and w not in dict(p["tags"])),
                       key=lambda p: -p["raw"][w])[:200 - count[w]]
        for p in cands:
            c = max(1, min(9, round(p["raw"][w] * 9)))
            if len(p["tags"]) < 5:
                p["tags"].append((w, c))
            else:
                lo = min(range(len(p["tags"])), key=lambda i: p["tags"][i][1])
                p["tags"][lo] = (w, c)
    return kept, dup, rej, errors


def grid_of(pat):
    g = pat["h"].get("grid")
    if g:
        return g
    return {12: "1/8T", 24: "1/16T", 8: "1/8", 32: "1/32"}.get(pat["steps"], "1/16")


def write(kept):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    lines = ["# MLG Alpha — bibliothèque compilée par tools/classify.py",
             "# id|rôle|famille|mesures|pas par mesure|grille|absolu|étiquettes|empreinte|nom|notes(t,l,p,v en 1/12 de pas)"]
    for p in kept:
        tags = ",".join(f"{w}:{c}" for w, c in p["tags"])
        ev = " ".join(f"{n[0]},{n[1]},{n[2]},{n[3]}" for n in p["notes"])
        name = p["name"].replace("|", "/")
        lines.append(f"{p['id']}|{p['role']}|{p['family']}|{p['bars']}|{p['steps']}|{grid_of(p)}|{1 if p['abs'] else 0}|{tags}|{p['fp']}|{name}|{ev}")
    data = ("\n".join(lines) + "\n").encode("utf-8")
    with gzip.open(OUT, "wb", compresslevel=9) as f:
        f.write(data)
    return len(data)


if __name__ == "__main__":
    kept, dup, rej, err = build()
    size = write(kept)
    print(f"motifs gardés : {len(kept)}  doublons retirés : {dup}  NeuralAcid écartées : {rej}  erreurs : {err}")
    print(f"taille : {size/1e6:.1f} Mo brut, {os.path.getsize(OUT)/1e6:.1f} Mo compressé")
    print("familles :", collections.Counter(p["family"] for p in kept).most_common())
    print("rôles    :", collections.Counter(p["role"] for p in kept).most_common())
    tc = collections.Counter(w for p in kept for w, _ in p["tags"])
    print("étiquettes jamais utilisées :", sorted(set(CATEGORY) - set(tc)))
    print("étiquettes les plus fréquentes :", tc.most_common(15))
    print("nb d'étiquettes par motif :", collections.Counter(len(p["tags"]) for p in kept))
