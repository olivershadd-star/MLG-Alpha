"""Importe les familles électroniques de Pocket Operations (données MIT de darosh/pocket-patterns)
vers le format texte de la bibliothèque MLG Alpha.  Usage : python3 import_pocket_operations.py groups.json > drums_po.txt"""
import json, re, sys

KEEP = {  # famille PO -> genre MLG Alpha
    "Basic Patterns": "basic", "Standard Breaks": "breaks", "Electro": "electro", "House": "house",
    "Miami Bass": "miami-bass", "Hip Hop": "hiphop", "Drum And Bass": "dnb", "EDM": "edm",
    "Dub": "dub", "Breaks": "breaks", "Hybrid Breaks": "breaks", "Irregular Breaks": "breaks",
    "Rolling Breaks": "breaks", "Breaks — Snare": "breaks", "Ghost Snares": "breaks",
    "Breaks — Kick": "breaks", "Drum Rolls": "fill",
}
ORDER = ["BD", "SN", "CL", "RS", "CH", "OH", "CY", "LT", "MT", "HT", "CB", "SH", "AC"]
EDM_GENRE = {"Techno": "techno", "Dubstep": "dubstep", "UK Garage": "ukg", "Synth Wave": "synthwave"}

def slug(s):
    s = s.lower().replace("’", "").replace("—", "-")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def grid(hits, steps):
    cells = ["."] * steps
    sub = {}
    for h in hits:
        if isinstance(h, str):
            st, part = h.split("."); sub.setdefault(int(st), set()).add(int(part))
        else:
            cells[h - 1] = "x"
    for st, parts in sub.items():
        cells[st - 1] = "r" if parts == {1, 2} else ("h" if parts == {2} else "x")
    return "".join(cells)

groups = json.load(open(sys.argv[1]))
out, seen = [], {}
for g in groups:
    if g["title"] not in KEEP: continue
    pats = g["patterns"]; i = 0
    while i < len(pats):
        p = pats[i]; bars = [p]
        # parties A/B consécutives du même titre = un motif de plusieurs mesures
        while i + len(bars) < len(pats) and pats[i + len(bars)]["title"] == p["title"] and pats[i + len(bars)].get("part"):
            bars.append(pats[i + len(bars)])
        i += len(bars)
        title = p["title"].replace("↳ ", "").replace("…", "")
        genre = EDM_GENRE.get(title.split(" —")[0], KEEP[g["title"]]) if g["title"] == "EDM" else KEEP[g["title"]]
        base = "po-" + slug(title); n = seen.get(base, 0) + 1; seen[base] = n
        pid = base if n == 1 else f"{base}-{n}"
        maxhit = max([int(str(h).split(".")[0]) for b in bars for ins in b["instruments"] for h in ins["hits"]] + [16])
        steps = 16 if maxhit <= 16 else 32
        keys = [k for k in ORDER if any(ins["key"] in (k, "HC" if k == "CL" else k) for b in bars for ins in b["instruments"])]
        out.append(f'@drums id={pid} name="{title}" genre={genre} bars={len(bars)} steps={steps} src=po')
        for k in keys:
            row = []
            for b in bars:
                hits = [h for ins in b["instruments"] if ins["key"] == k or (k == "CL" and ins["key"] == "HC") for h in ins["hits"]]
                row.append(grid(hits, steps))
            out.append(f"{k:2s} " + " ".join(row))
        out.append("")
print("# Pocket Operations — familles électroniques (source : darosh/pocket-patterns, licence MIT ;")
print("# collection d'origine : Pocket Operations, Shitty Recording Studio / Paul Wenzel).")
print("# Format : une ligne par instrument, un caractère par pas ; mesures séparées par un espace.")
print("# x = coup, r = double coup (ratchet), h = coup décalé d'un demi-pas, . = silence ; AC = accent.\n")
print("\n".join(out))
