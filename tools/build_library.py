"""Construit les fichiers de la bibliothèque MLG Alpha écrits pour le projet (motifs de base de la musique
électronique, écrits à partir des règles de chaque genre).  Usage : python3 tools/build_library.py
Les positions de pas sont comptées à partir de 1 (1, 5, 9, 13 = les quatre temps d'une mesure de 16 pas)."""
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "Library"

# ---------------------------------------------------------------- outils
Q = [1, 5, 9, 13]                 # les 4 temps
OFF = [3, 7, 11, 15]              # contretemps à la croche
E8 = list(range(1, 17, 2))        # croches
S16 = list(range(1, 17))          # doubles croches
OFF16 = list(range(2, 17, 2))     # doubles croches « faibles »
BEAT24 = [5, 13]                  # temps 2 et 4

def grid(hits, steps=16, accents=()):
    cells = ["."] * steps
    for h in hits:
        cells[h - 1] = "X" if h in accents else "x"
    return "".join(cells)

def drums(pid, name, genre, rows, bars=1, tags=""):
    """rows : {inst: positions} pour 1 mesure, ou {inst: [positions mesure 1, positions mesure 2...]}"""
    lines = [f'@drums id={pid} name="{name}" genre={genre} bars={bars} steps=16' + (f" tags={tags}" if tags else "")]
    order = ["BD", "SN", "CL", "RS", "CH", "OH", "CY", "LT", "MT", "HT", "CB", "SH", "PC"]
    for k in order:
        if k not in rows: continue
        v = rows[k]
        per_bar = v if (bars > 1 and v and isinstance(v[0], list)) else [v] * bars
        lines.append(f"{k:2s} " + " ".join(grid(b) for b in per_bar))
    return "\n".join(lines) + "\n"

def line(kind, pid, name, genre, notes, bars=1, tags="", extra=""):
    toks = notes.split()
    assert len(toks) == 16 * bars, (pid, len(toks))
    head = f'@{kind} id={pid} name="{name}" genre={genre} bars={bars} steps=16' + (f" tags={tags}" if tags else "") + (f" {extra}" if extra else "")
    bars_txt = [" ".join(toks[i * 16:(i + 1) * 16]) for i in range(bars)]
    return head + "\n" + "\n".join("N  " + b for b in bars_txt) + "\n"

# ---------------------------------------------------------------- BATTERIE
def build_drums():
    out = []
    add = lambda *a, **k: out.append(drums(*a, **k))

    # --- Techno (kick 4/4, clap 2-3 places, charleston qui varie)
    add("tk-basic", "Techno de base", "techno", {"BD": Q, "CL": BEAT24, "OH": OFF})
    add("tk-hats16", "Techno doubles croches", "techno", {"BD": Q, "CL": BEAT24, "CH": S16, "OH": OFF})
    add("tk-noclap", "Techno sans clap", "techno", {"BD": Q, "CH": OFF16, "OH": OFF})
    add("tk-clap4", "Techno clap sur le 4", "techno", {"BD": Q, "CL": [13], "OH": OFF, "CH": [2, 6, 10, 14]})
    add("tk-ride", "Techno ride", "techno", {"BD": Q, "CL": BEAT24, "CY": OFF, "CH": OFF16})
    add("tk-ride16", "Techno ride en continu", "techno", {"BD": Q, "CY": S16, "OH": OFF, "RS": [8, 15]})
    add("tk-pickup", "Techno kick de relance", "techno", {"BD": Q + [16], "CL": BEAT24, "OH": OFF, "CH": OFF16})
    add("tk-pickup15", "Techno double kick", "techno", {"BD": Q + [15], "CL": BEAT24, "OH": OFF})
    add("tk-gallop", "Techno galop", "techno", {"BD": Q, "CL": BEAT24, "CH": [2, 3, 6, 7, 10, 11, 14, 15], "OH": OFF})
    add("tk-rim", "Techno rim syncopé", "techno", {"BD": Q, "CL": BEAT24, "OH": OFF, "RS": [4, 7, 12, 15]})
    add("tk-perc", "Techno percussions", "techno", {"BD": Q, "CL": BEAT24, "OH": OFF, "PC": [3, 6, 11, 14]})
    add("tk-perc2", "Techno perc 3 contre 4", "techno", {"BD": Q, "OH": OFF, "PC": [1, 4, 7, 10, 13, 16]}, tags="polyrythme")
    add("tk-snareroll", "Techno caisse claire en fin", "techno", {"BD": Q, "CL": BEAT24, "OH": OFF, "SN": [14, 15, 16]})
    add("tk-2bar", "Techno 2 mesures", "techno",
        {"BD": [Q, Q + [15]], "CL": [BEAT24, [5, 13, 16]], "OH": [OFF, OFF], "CH": [OFF16, OFF16]}, bars=2)
    add("tk-dub", "Dub techno", "dub-techno", {"BD": Q, "RS": [7, 15], "CH": OFF16, "OH": OFF, "SH": S16})
    add("tk-dub2", "Dub techno rim décalé", "dub-techno", {"BD": Q, "RS": [4, 11], "OH": OFF, "CH": [2, 6, 10, 14]})
    add("tk-minimal", "Minimal", "minimal", {"BD": Q, "RS": [4, 10, 15], "CH": OFF16, "OH": [11]})
    add("tk-minimal2", "Minimal clic", "minimal", {"BD": Q, "CL": [13], "RS": [3, 8, 14], "PC": [6, 12]})
    add("tk-minimal3", "Minimal kick décalé", "minimal", {"BD": [1, 5, 9, 12, 13], "CL": BEAT24, "CH": [3, 7, 11, 15, 16]})
    add("tk-hardgroove", "Hardgroove", "hardgroove", {"BD": Q, "CL": BEAT24, "CY": OFF, "CH": S16, "PC": [3, 4, 8, 11, 14]})
    add("tk-hardgroove2", "Hardgroove toms", "hardgroove", {"BD": Q, "CL": BEAT24, "OH": OFF, "LT": [4, 10], "MT": [7, 15], "CH": OFF16})
    add("tk-hard", "Hard techno", "hard-techno", {"BD": Q, "CL": BEAT24, "OH": OFF, "CH": S16})
    add("tk-hard-roll", "Hard techno relance", "hard-techno", {"BD": [1, 5, 9, 13, 14, 15, 16], "CL": BEAT24, "OH": OFF})
    add("tk-industrial", "Techno industrielle", "industrial", {"BD": Q, "SN": [5, 13, 16], "CL": [5, 13], "CH": S16, "PC": [2, 8, 11]})
    add("tk-industrial2", "Industriel cassé", "industrial", {"BD": [1, 4, 7, 9, 13], "SN": [5, 13], "CH": E8, "PC": [11, 15]})
    add("tk-schranz", "Schranz", "hard-techno", {"BD": Q, "CL": [3, 5, 7, 11, 13, 15], "CH": S16, "OH": OFF})
    add("tk-rumble", "Techno rumble (kick seul + hats)", "techno", {"BD": Q, "OH": OFF, "CH": [2, 4, 8, 10, 12, 16]}, tags="rumble")
    add("tk-detroit", "Detroit", "techno", {"BD": Q, "CL": BEAT24, "CH": E8, "OH": OFF, "RS": [7, 12]})
    add("tk-detroit2", "Detroit shuffle", "techno", {"BD": Q, "CL": BEAT24, "CH": [1, 3, 4, 7, 8, 11, 12, 15, 16], "OH": OFF})
    add("tk-acid", "Acid techno", "acid", {"BD": Q, "CL": BEAT24, "CH": S16, "OH": OFF, "CB": [4, 12]})

    # --- House
    add("hs-basic", "House de base", "house", {"BD": Q, "CL": BEAT24, "OH": OFF, "CH": E8})
    add("hs-chicago", "Chicago house", "house", {"BD": Q, "CL": BEAT24, "OH": OFF, "CH": S16, "CB": [8, 15]})
    add("hs-jack", "Jack", "house", {"BD": Q, "CL": [5, 8, 13], "OH": OFF, "CH": OFF16})
    add("hs-shaker", "House shaker", "house", {"BD": Q, "CL": BEAT24, "OH": OFF, "SH": S16})
    add("hs-deep", "Deep house", "deep-house", {"BD": Q, "CL": BEAT24, "OH": OFF, "RS": [8, 11], "SH": OFF16})
    add("hs-deep2", "Deep house rim", "deep-house", {"BD": Q, "SN": [13], "RS": [4, 7, 12], "OH": OFF})
    add("hs-tech", "Tech house", "tech-house", {"BD": Q, "CL": BEAT24, "OH": OFF, "CH": [2, 4, 6, 8, 10, 12, 14, 16], "PC": [7, 14]})
    add("hs-tech2", "Tech house groove", "tech-house", {"BD": Q, "CL": BEAT24, "OH": OFF, "CH": [1, 2, 4, 5, 6, 8, 9, 10, 12, 13, 14, 16], "RS": [11]})
    add("hs-tech3", "Tech house perc", "tech-house", {"BD": Q, "CL": BEAT24, "OH": OFF, "PC": [4, 7, 10, 15], "CH": OFF16})
    add("hs-garage", "Garage house", "house", {"BD": Q, "CL": BEAT24, "OH": OFF, "CH": [3, 4, 7, 8, 11, 12, 15, 16]})
    add("hs-disco", "Disco house", "house", {"BD": Q, "SN": BEAT24, "CL": BEAT24, "OH": OFF, "CH": S16})
    add("hs-french", "Filter house", "house", {"BD": Q, "CL": BEAT24, "OH": OFF16, "CH": S16})
    add("hs-progressive", "Progressive house", "progressive", {"BD": Q, "CL": BEAT24, "OH": OFF, "CH": S16, "CY": E8})
    add("hs-acid", "Acid house", "acid", {"BD": Q, "CL": BEAT24, "OH": OFF, "CH": S16, "CB": [11]})
    add("hs-2bar", "House 2 mesures", "house",
        {"BD": [Q, Q], "CL": [BEAT24, [5, 13, 15]], "OH": [OFF, OFF], "CH": [E8, S16]}, bars=2)

    # --- Electro / Miami / EBM / synthwave / trance
    add("el-808", "Electro 808", "electro", {"BD": [1, 7, 11], "SN": BEAT24, "CH": S16})
    add("el-808b", "Electro 808 variante", "electro", {"BD": [1, 4, 7, 11, 14], "SN": BEAT24, "CH": E8, "CB": [3, 11]})
    add("el-drexciya", "Electro rapide", "electro", {"BD": [1, 4, 9, 11], "SN": [5, 13, 15], "CH": S16, "HT": [8], "LT": [16]})
    add("el-2bar", "Electro 2 mesures", "electro",
        {"BD": [[1, 7, 11], [1, 4, 7, 10, 12]], "SN": [BEAT24, [5, 13, 16]], "CH": [S16, S16]}, bars=2)
    add("ebm-1", "EBM", "ebm", {"BD": Q, "SN": BEAT24, "CH": OFF})
    add("ebm-2", "EBM martial", "ebm", {"BD": Q, "SN": [5, 13, 15], "CL": BEAT24, "CH": E8})
    add("ebm-3", "EBM lent", "ebm", {"BD": [1, 9, 11], "SN": BEAT24, "CH": OFF})
    add("sw-1", "Synthwave", "synthwave", {"BD": [1, 9], "SN": BEAT24, "CH": E8})
    add("sw-2", "Synthwave motorik", "synthwave", {"BD": [1, 7, 9], "SN": BEAT24, "CH": S16})
    add("tr-1", "Trance", "trance", {"BD": Q, "CL": BEAT24, "OH": OFF, "CH": OFF16, "CY": OFF})
    add("tr-2", "Trance roulante", "trance", {"BD": Q, "CL": BEAT24, "OH": OFF, "CH": S16, "SN": [16]})
    add("tr-psy", "Psytrance", "psytrance", {"BD": Q, "CL": [5, 13], "OH": OFF, "CH": OFF16}, tags="basse-roulante")

    # --- Breaks / bass music
    add("br-big", "Big beat", "breaks", {"BD": [1, 8, 11], "SN": BEAT24, "CH": E8, "OH": [15]})
    add("br-nu", "Nu skool breaks", "breaks", {"BD": [1, 4, 11], "SN": [5, 13], "CH": S16, "OH": [7, 15]})
    add("br-2step", "2-step", "ukg", {"BD": [1, 11], "SN": BEAT24, "CH": [3, 7, 9, 11, 15], "RS": [8, 14]})
    add("br-bass", "UK bass", "uk-bass", {"BD": [1, 7, 11], "CL": BEAT24, "CH": [3, 4, 7, 8, 11, 12, 15], "PC": [10, 16]})
    add("br-halftime", "Half-time", "dubstep", {"BD": [1, 4], "SN": [9], "CH": E8, "OH": [15]})
    add("br-dnb", "DnB deux temps", "dnb", {"BD": [1, 11], "SN": BEAT24, "CH": E8})
    add("br-dnb-roller", "DnB roller", "dnb", {"BD": [1, 8, 11], "SN": BEAT24, "CH": S16, "RS": [15]})
    add("br-jungle", "Jungle simple", "dnb", {"BD": [1, 3, 11], "SN": [5, 8, 13, 16], "CH": E8})
    add("br-footwork", "Footwork / juke", "footwork", {"BD": [1, 4, 7, 9, 12, 15], "CL": [5, 13], "CH": E8})
    add("br-trap", "Trap", "trap", {"BD": [1, 8, 11], "CL": [9], "CH": E8})
    add("br-trap-roll", "Trap roulement", "trap", {"BD": [1, 11], "CL": [9], "CH": [1, 3, 5, 7, 9, 10, 11, 12, 13, 14, 15, 16]})
    add("br-reggaeton", "Dembow électronique", "dembow", {"BD": Q, "SN": [4, 7, 12, 15], "CH": E8})
    add("br-gqom", "Gqom", "gqom", {"BD": [1, 4, 7, 11], "PC": [3, 6, 10, 14], "CL": [13]})
    add("br-amapiano", "Log drum (amapiano)", "amapiano", {"BD": Q, "SH": S16, "CL": BEAT24, "RS": [4, 7, 12]})

    # --- Breaks de fin / transitions pour l'électro
    add("fill-snare16", "Roulement caisse claire 16", "fill", {"SN": S16, "BD": Q})
    add("fill-snare8", "Roulement caisse claire 8", "fill", {"SN": E8, "BD": [1]})
    add("fill-clap", "Montée clap", "fill", {"CL": [9, 11, 13, 14, 15, 16], "BD": Q})
    add("fill-toms", "Toms descendants", "fill", {"HT": [9, 10], "MT": [11, 12], "LT": [13, 14], "BD": [1, 5, 15, 16]})
    add("fill-stop", "Coupure", "fill", {"BD": [1], "CY": [1]})

    head = ("# Motifs de batterie électroniques écrits pour MLG Alpha (motifs de base des genres, libres).\n"
            "# Format identique à drums_pocket_operations.txt. Notes : BD 36, RS 37, SN 38, CL 39, CH 42, OH 46,\n"
            "# LT 45, MT 47, HT 50, CY (ride) 51, CB 56, SH 70, PC (percussion) 75.\n\n")
    return head + "\n".join(out)

# ---------------------------------------------------------------- ACID (notation 303)
# Un jeton par pas : intervalle en demi-tons depuis la tonique (0, 3, 7, 12, -2…),
# suffixe a = accent, s = slide vers la note suivante ; « . » = silence ; « - » = note tenue.
ACID = [
    ("acid-01", "Racine qui saute", "0 0 12 0 . 0 12a 0 0 . 0 12 0 3 . 12s"),
    ("acid-02", "Phuture", "0 . 0 0a 12 . 0 0 3s 0 . 0 12a . 0 10"),
    ("acid-03", "Mineur classique", "0 0a 3 0 7s 12 0 0 10 0a 3 0 5s 7 0 12"),
    ("acid-04", "Octaves glissées", "0 12s 0 12s 0 12s 0 0a 0 12s 0 12s 3 15s 3 0a"),
    ("acid-05", "Phrygien", "0 1s 0 0a . 0 1 0 12 0 1s 0 . 0a 1 13"),
    ("acid-06", "Tritons", "0 . 6a 0 12 . 6 0 0a . 6 12s 0 6 . 0"),
    ("acid-07", "Galop", "0 . 0a 0 . 12 0 0 . 3a 3 . 0 0 12s 0"),
    ("acid-08", "Montée", "0 3 5 7a 0 3 5 7 10a 12 0 3 5 7 10 12s"),
    ("acid-09", "Descente", "12a 10 7 5 3 0 . 0 12a 10s 7 5 3 0 -2 0"),
    ("acid-10", "Pompe", "0a . 0 . 0a . 0 . 0a . 0 . 0a 3 5s 0"),
    ("acid-11", "Ping-pong", "0 12 0 12 3 15a 3 15 5 17 5 17s 7 19 0a 12"),
    ("acid-12", "Hypnotique", "0 0 0a 0 0 0 0a 0 0 0 0a 0 0 3s 0 0"),
    ("acid-13", "Syncopé", ". 0a . 0 12 . 0 . 0a . 12s 0 . 0 7 ."),
    ("acid-14", "Squelch long", "0 - - 12s 0 - 3a - 0 - - 12s 7 - 0a -"),
    ("acid-15", "Rebond", "0 0 12a 0 0 12 0 0a 10 0 12 0 0 7s 0 12"),
    ("acid-16", "Sombre", "0 1 0 . 0a 1s 0 . 0 1 0 . -1a 0 . 0"),
    ("acid-17", "Mineur 7", "0 3 7 10a 12 10 7 3 0a 3 7s 10 12a 10 7 3"),
    ("acid-18", "Questions-réponses", "0 . 0a 3 . 0 . . 12 . 12a 10s 7 . 5 3"),
    ("acid-19", "Basse + aigu", "0 . 24a . 0 . 0 . 0 . 24a . 0 12s 0 ."),
    ("acid-20", "Relance", "0 0 0 0a 3 3 3 3a 5 5 5 5a 7 7s 10 12a"),
    ("acid-21", "Ostinato", "0a 0 3 0 0a 0 5 0 0a 0 7 0 0a 0 5s 3"),
    ("acid-22", "Glissades", "0s 3s 5s 7a 0s 3s 5s 7a 0 3 5 7a 10s 7s 5s 3"),
    ("acid-23", "Funk acid", "0 . 0 12a . 0 10 . 0 0a . 7 . 10s 12 ."),
    ("acid-24", "Minimal acid", "0 . . 0a . . 0 . . 0a . . 0 . 3s ."),
    ("acid-25", "Blues acid", "0 3 0 3a 5 6s 7 . 0 3 0a 10 . 7 5 3"),
    ("acid-26", "Accents décalés", "0 0a 0 0 0a 0 0 0a 0 0 0a 0 0 0a 12 0"),
    ("acid-27", "Dorien", "0 2 3 5a 7 9 10 12 0a 2 3 5 7s 9 10 12a"),
    ("acid-28", "Dramatique", "0a . . 0 1s 0 . 0 0a . . 0 -2s 0 . 3"),
    ("acid-29", "Rapide", "0 12 0 12a 0 12 0 12 0 12a 0 12 3 15s 3 15a"),
    ("acid-30", "Psy roulant", ". 0 0a 0 . 0 0 0a . 0 0a 0 . 0 12s 0"),
    ("acid-31", "Deux mesures A", "0 0a 12 0 3 0 12s 0 0 0a 12 0 3 0 7s 0 "
                                   "0 0a 12 0 3 0 12s 0 10 10a 22 10 3s 5 7 12a"),
    ("acid-32", "Deux mesures B", "0 . 0a . 0 3s . 0 . 0a . 0 7 . 0 . "
                                   "0 . 0a . 0 3s . 0 12a 10 7 5 3s 0 -2 0"),
]

# ---------------------------------------------------------------- BASSES
BASS = [
    ("bs-offbeat", "Basse au contretemps", "techno", ". . 0 . . . 0 . . . 0 . . . 0 ."),
    ("bs-offbeat16", "Contretemps doublé", "techno", ". . 0 0 . . 0 0 . . 0 0 . . 0 0"),
    ("bs-rolling", "Basse roulante", "techno", ". 0 0 0 . 0 0 0 . 0 0 0 . 0 0 0"),
    ("bs-psy", "Basse psytrance", "psytrance", ". 0 0 0 . 0 0 0 . 0 0 0 . 0 0 12"),
    ("bs-gallop", "Galop", "techno", "0 . 0 0 0 . 0 0 0 . 0 0 0 . 0 0"),
    ("bs-16th", "Doubles croches", "ebm", "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"),
    ("bs-ebm", "EBM octave", "ebm", "0 0 12 0 0 0 12 0 0 0 12 0 0 0 12 0"),
    ("bs-ebm2", "EBM 4 notes", "ebm", "0 0 0 0 0 0 0 0 3 3 3 3 5 5 7 7"),
    ("bs-octave", "House octave", "house", "0 . 12 . 0 . 12 . 0 . 12 . 0 . 12 ."),
    ("bs-house", "House syncopée", "house", "0 . . 0 . . 12 . 0 . . 0 . 10 . 7"),
    ("bs-deep", "Deep house", "deep-house", "0 - - . . . 7 . 10 - - . . . 7 ."),
    ("bs-dub", "Dub techno", "dub-techno", "0 - - - - - . . 0 - - - . . 7 ."),
    ("bs-sub", "Sub tenu", "sub", "0 - - - - - - - 0 - - - - - - -"),
    ("bs-sub-move", "Sub en mouvement", "sub", "0 - - - - - - - -2 - - - 3 - - -"),
    ("bs-electro", "Electro", "electro", "0 . . 0 . . 0 . . . 0 . 12 . 10 ."),
    ("bs-electro2", "Electro syncopée", "electro", "0 . . . . . 0 . . 0 . . 3 . 0 ."),
    ("bs-synthwave", "Synthwave croches", "synthwave", "0 . 0 . 0 . 0 . 0 . 0 . 0 . 0 ."),
    ("bs-synthwave2", "Synthwave octaves", "synthwave", "0 . 12 . 0 . 12 . 0 . 12 . 0 . 12 ."),
    ("bs-trance", "Trance contretemps", "trance", ". . 0 0 . . 0 0 . . 0 0 . . 0 0"),
    ("bs-minimal", "Minimal", "minimal", ". . . 0 . . . . . . 0 . . . . 0"),
    ("bs-minimal2", "Minimal clic", "minimal", "0 . . . . . 0 . . 0 . . . . . ."),
    ("bs-tech-house", "Tech house", "tech-house", ". . 0 . . 0 0 . . . 0 . . 0 12 ."),
    ("bs-ukg", "UK garage", "ukg", "0 - . . . . 0 . . . 7 - . . 5 ."),
    ("bs-dnb", "Reese DnB", "dnb", "0 - - - - - - - - - 3 - - - -2 -"),
    ("bs-dubstep", "Wobble half-time", "dubstep", "0 - - - - - 0 . 0 - - - 3 - 0 ."),
    ("bs-industrial", "Industrielle", "industrial", "0 0 . 0 0 . 0 0 . 0 1 . 0 0 . 0"),
    ("bs-hardgroove", "Hardgroove", "hardgroove", ". 0 . 0 . 0 12 . . 0 . 0 . 0 10 ."),
    ("bs-2bar", "Techno 2 mesures", "techno", ". . 0 . . . 0 . . . 0 . . . 0 . "
                                             ". . 0 . . . 0 . . . 3 . . . 5 ."),
    ("bs-arp-bass", "Basse arpégée", "techno", "0 7 12 7 0 7 12 7 0 7 12 7 0 7 12 15"),
    ("bs-berlin", "Berlin", "techno", "0 . . 0 . . 0 . . 0 . . 0 . 0 ."),
]

# ---------------------------------------------------------------- MÉLODIES / ARPÈGES / LEADS
MELODY = [
    ("ml-arp-up", "Arpège montant", "arp", "0 3 7 12 0 3 7 12 0 3 7 12 0 3 7 12"),
    ("ml-arp-updown", "Arpège aller-retour", "arp", "0 3 7 12 15 12 7 3 0 3 7 12 15 12 7 3"),
    ("ml-arp-oct", "Arpège octaves", "arp", "0 12 7 12 0 12 7 12 0 12 7 12 0 12 10 12"),
    ("ml-arp-sus", "Arpège sus", "arp", "0 5 7 12 0 5 7 12 0 5 7 12 0 5 7 14"),
    ("ml-arp-trance", "Arpège trance", "trance", "0 7 12 7 15 7 12 7 0 7 12 7 15 7 19 7"),
    ("ml-arp-berlin", "École de Berlin", "berlin-school", "0 12 7 3 0 12 7 3 0 12 7 5 0 12 7 5"),
    ("ml-arp-synthwave", "Arpège synthwave", "synthwave", "0 7 12 15 0 7 12 15 -2 5 10 14 -2 5 10 14"),
    ("ml-stab", "Stab techno", "techno", ". . 0 . . . . . . . 0 . . . . ."),
    ("ml-stab2", "Stab décalé", "techno", ". . . 0 . . 0 . . . . 0 . . . ."),
    ("ml-hook-1", "Gimmick 3 notes", "techno", "0 . 3 . 7 . . . 0 . 3 . 5 . . ."),
    ("ml-hook-2", "Gimmick question", "house", "0 - 3 - 5 - 7 - 10 - 7 - 5 - 3 -"),
    ("ml-hook-3", "Riff hypnotique", "techno", "12 . 10 . 12 . 7 . 12 . 10 . 7 . 3 ."),
    ("ml-hook-4", "Riff rave", "rave", "0 0 12 0 0 12 0 0 10 10 22 10 10 22 10 10"),
    ("ml-hook-5", "Hoover", "rave", "0 - - - 1 - - - 0 - - - -2 - - -"),
    ("ml-hook-6", "Mélodie trance", "trance", "12 - 10 - 7 - 10 - 12 - 15 - 14 - 10 -"),
    ("ml-lead-1", "Lead synthwave", "synthwave", "7 - - - 5 - 3 - 5 - - - 3 - 2 -"),
    ("ml-lead-2", "Lead sombre", "techno", "0 - - - - - 1 - 0 - - - -2 - - -"),
    ("ml-seq-1", "Séquence 303 aiguë", "acid", "12 0 12 0 15 0 12 0 10 0 12 0 7 0 10 0"),
    ("ml-seq-2", "Séquence EBM", "ebm", "0 0 12 0 3 0 12 0 5 0 12 0 3 0 12 0"),
    ("ml-seq-3", "Séquence minimal", "minimal", "0 . . 7 . . 12 . . 7 . . 0 . . ."),
    ("ml-seq-4", "Pluck house", "house", ". . 7 . . 7 . . 10 . . 7 . . 5 ."),
    ("ml-seq-5", "Pluck en 3", "techno", "0 . . 7 . . 12 . . 0 . . 7 . . 12"),
    ("ml-bell", "Cloches", "ambient", "12 - - - 19 - - - 15 - - - 14 - - -"),
    ("ml-2bar-1", "Phrase 2 mesures", "techno", "0 - 3 - 7 - 5 - 3 - 0 - . . . . "
                                               "0 - 3 - 7 - 10 - 12 - 10 - 7 - . ."),
    ("ml-4bar-1", "Phrase 4 mesures", "melodic-techno",
     "12 - - - 10 - - - 7 - - - 10 - - - "
     "12 - - - 15 - - - 14 - - - 10 - - - "
     "12 - - - 10 - - - 7 - - - 5 - - - "
     "3 - - - 5 - - - 7 - - - - - - -"),
]

# ---------------------------------------------------------------- ACCORDS / NAPPES
# Degrés en chiffres romains dans la gamme choisie (minuscule = mineur, ° = diminué) ;
# une case = une mesure, « - » = même accord qui continue.
CHORDS = [
    ("ch-01", "i – VI – III – VII", "techno", "i VI III VII"),
    ("ch-02", "i – iv", "techno", "i iv"),
    ("ch-03", "i – VII", "techno", "i VII"),
    ("ch-04", "i – v", "techno", "i v"),
    ("ch-05", "i – VI", "techno", "i VI"),
    ("ch-06", "i – iv – v – i", "techno", "i iv v i"),
    ("ch-07", "i – VII – VI – VII", "trance", "i VII VI VII"),
    ("ch-08", "i – VI – VII – i", "trance", "i VI VII i"),
    ("ch-09", "VI – VII – i – i", "trance", "VI VII i i"),
    ("ch-10", "i – III – VII – IV", "progressive", "i III VII IV"),
    ("ch-11", "i7 – iv7", "deep-house", "i7 iv7"),
    ("ch-12", "i9 – IVmaj7", "deep-house", "i9 IVmaj7"),
    ("ch-13", "ii7 – V7 – Imaj7 – vi7", "house", "ii7 V7 Imaj7 vi7"),
    ("ch-14", "Imaj7 – vi7", "house", "Imaj7 vi7"),
    ("ch-15", "vi – IV – I – V", "house", "vi IV I V"),
    ("ch-16", "I – V – vi – IV", "house", "I V vi IV"),
    ("ch-17", "i – i – VI – VII", "synthwave", "i i VI VII"),
    ("ch-18", "i – VI – iv – VII", "synthwave", "i VI iv VII"),
    ("ch-19", "i – II (phrygien)", "industrial", "i II"),
    ("ch-20", "i – II – i – VII", "industrial", "i II i VII"),
    ("ch-21", "i sus2 – i", "dub-techno", "isus2 i"),
    ("ch-22", "i9 seul (dub)", "dub-techno", "i9"),
    ("ch-23", "i7 – VII7", "dub-techno", "i7 VII7"),
    ("ch-24", "i – iv – VII – III", "melodic-techno", "i iv VII III"),
    ("ch-25", "i – VI – III – v", "melodic-techno", "i VI III v"),
    ("ch-26", "iv – i – v – i", "melodic-techno", "iv i v i"),
    ("ch-27", "i – IV (dorien)", "house", "i IV"),
    ("ch-28", "i7 – IV7 (dorien)", "deep-house", "i7 IV7"),
    ("ch-29", "Isus4 – I", "trance", "Isus4 I"),
    ("ch-30", "i – VI – i – VII", "rave", "i VI i VII"),
]
PADS = [  # nappes : 8 mesures, accords longs
    ("pad-01", "Nappe sombre", "ambient", "i - - - VI - VII -"),
    ("pad-02", "Nappe qui monte", "ambient", "i - VI - III - VII -"),
    ("pad-03", "Nappe dub", "dub-techno", "i9 - - - VII7 - - -"),
    ("pad-04", "Nappe mélancolique", "melodic-techno", "i - iv - VI - v -"),
    ("pad-05", "Nappe lumineuse", "ambient", "Imaj7 - - - IVmaj7 - - -"),
    ("pad-06", "Nappe suspendue", "ambient", "isus2 - - - VIsus2 - - -"),
    ("pad-07", "Nappe trance", "trance", "i - VI - III - VII -"),
    ("pad-08", "Nappe drone", "drone", "i - - - - - - -"),
    ("pad-09", "Nappe phrygienne", "industrial", "i - - - II - - -"),
    ("pad-10", "Nappe synthwave", "synthwave", "i - VI - iv - VII -"),
    ("pad-11", "Nappe deep", "deep-house", "i7 - - - iv7 - - -"),
    ("pad-12", "Nappe cyclique", "ambient", "i - III - VI - VII -"),
]
STABS = [  # rythmes pour jouer les accords (une mesure)
    ("st-01", "Contretemps", "house", [3, 7, 11, 15]),
    ("st-02", "Charleston", "house", [1, 4]),
    ("st-03", "Stab dub", "dub-techno", [4, 11]),
    ("st-04", "Stab dub 2", "dub-techno", [3, 10, 15]),
    ("st-05", "Syncopé", "techno", [1, 4, 7, 11, 14]),
    ("st-06", "Tresillo", "techno", [1, 4, 7]),
    ("st-07", "Rave piano", "rave", [1, 4, 7, 9, 12, 15]),
    ("st-08", "Croches", "trance", [1, 3, 5, 7, 9, 11, 13, 15]),
    ("st-09", "Doubles croches gated", "trance", list(range(1, 17))),
    ("st-10", "Un coup", "techno", [1]),
    ("st-11", "Chicago", "house", [1, 3, 6, 9, 11, 14]),
    ("st-12", "Deep", "deep-house", [1, 7, 12]),
    ("st-13", "Minimal", "minimal", [4, 14]),
    ("st-14", "Tenu", "pad", [1]),
]

def build_lines(kind, items, default_genre=None, extra=""):
    out = []
    for it in items:
        if len(it) == 3:
            pid, name, notes = it; genre = default_genre
        else:
            pid, name, genre, notes = it
        n = len(notes.split())
        out.append(line(kind, pid, name, genre, notes, bars=n // 16, extra=extra))
    return "\n".join(out)

def build_chords():
    out = ["# Grilles d'accords et nappes : degrés en chiffres romains dans la gamme choisie dans MLG Alpha.",
           "# Minuscule = accord mineur, majuscule = majeur, ° = diminué ; 7, maj7, 9, sus2, sus4 acceptés.",
           "# Une case = une mesure ; « - » = l'accord précédent continue.  @rhythm = rythme de jeu des accords.\n"]
    for pid, name, genre, prog in CHORDS:
        bars = len(prog.split())
        out.append(f'@chords id={pid} name="{name}" genre={genre} bars={bars}\nC  {prog}\n')
    for pid, name, genre, prog in PADS:
        out.append(f'@chords id={pid} name="{name}" genre={genre} bars={len(prog.split())} tags=nappe\nC  {prog}\n')
    for pid, name, genre, hits in STABS:
        out.append(f'@rhythm id={pid} name="{name}" genre={genre} bars=1 steps=16\nR  {grid(hits)}\n')
    return "\n".join(out)

if __name__ == "__main__":
    LIB.mkdir(exist_ok=True)
    (LIB / "drums_electronic.txt").write_text(build_drums())
    (LIB / "acid.txt").write_text(
        "# Lignes acid (notation 303) : intervalle en demi-tons depuis la tonique ; a = accent, s = slide ;\n"
        "# . = silence ; - = note tenue.  Transposées dans la tonique choisie dans MLG Alpha.\n\n"
        + build_lines("acid", ACID, default_genre="acid"))
    (LIB / "bass.txt").write_text(
        "# Lignes de basse électroniques : même notation que acid.txt (sans accents ni slides).\n\n"
        + build_lines("bass", BASS))
    (LIB / "melody.txt").write_text(
        "# Mélodies, arpèges, riffs et séquences : même notation que acid.txt.\n\n"
        + build_lines("melody", MELODY))
    (LIB / "chords.txt").write_text(build_chords())
    print("ok")
