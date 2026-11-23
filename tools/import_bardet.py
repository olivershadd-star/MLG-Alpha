"""Importe les rythmes de « 200 / 260 Drum Machine Patterns » (R.-P. Bardet) depuis les fichiers JSON
du dépôt gvellut/dmp_midi.  Seules les mesures en 4/4 sur 16 pas sont gardées.
Usage : python3 import_bardet.py Patterns_200.json Patterns_260.json > drums_bardet.txt"""
import json, re, sys

INST = {"BassDrum": "BD", "SnareDrum": "SN", "Clap": "CL", "RimShot": "RS", "ClosedHiHat": "CH",
        "OpenHiHat": "OH", "Cymbal": "CY", "LowTom": "LT", "MediumTom": "MT", "HighTom": "HT",
        "Cowbell": "CB", "Tambourine": "SH", "Accent": "AC"}
ORDER = ["BD", "SN", "CL", "RS", "CH", "OH", "CY", "LT", "MT", "HT", "CB", "SH", "AC"]
GENRE = {"Funk": "funk", "Rock": "rock", "Rhythm&Blues": "rnb", "Rnb": "rnb", "Ballad": "ballad", "Slow": "ballad",
         "Pop": "pop", "Reggae": "reggae", "Disco": "disco", "Afro-Cuban": "afro-cuban", "AfroCub": "afro-cuban",
         "Samba": "samba", "Blues": "blues", "Shuffle": "shuffle", "BossaNova": "bossa", "Bossa": "bossa",
         "Twist": "twist", "Cha-Cha": "chacha", "ChaCha": "chacha", "Ska": "ska", "Boogie": "boogie",
         "Jazz": "jazz", "Swing": "swing", "March": "march", "Paso": "paso", "Endings": "fill"}

print("# Rythmes de boîte à rythmes de René-Pierre Bardet (« 200 » et « 260 Drum Machine Patterns »),")
print("# d'après les données JSON du dépôt gvellut/dmp_midi (licence MIT du code). Mesures en 4/4 sur 16 pas.")
print("# Même format que drums_pocket_operations.txt.\n")
count = 0
for path, book in zip(sys.argv[1:], ["200", "260"]):
    for p in json.load(open(path)):
        if p["signature"] != "4/4" or p["length"] != 16: continue
        title = p["title"]
        m = re.match(r"([A-Za-z&\-]+)", title)
        fam = m.group(1) if m else "misc"
        genre = next((g for k, g in GENRE.items() if fam.startswith(k)), "misc")
        kind = "fill" if re.search(r"Break|Fill|Ending", title) else ""
        rows = {}
        for k, v in p["tracks"].items():
            code = INST.get(k)
            if not code: continue
            cells = "".join("x" if s == "Note" else ("X" if s == "Accent" else ".") for s in v)
            cells = (cells + "." * 16)[:16]
            if "x" in cells or "X" in cells:
                rows[code] = cells
        if not rows: continue
        pid = "rpb" + book + "-" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        tags = f" tags={kind}" if kind else ""
        print(f'@drums id={pid} name="{title}" genre={genre} bars=1 steps=16 src=bardet{book}{tags}')
        for k in ORDER:
            if k in rows: print(f"{k:2s} {rows[k]}")
        print(); count += 1
print(f"# {count} motifs", file=sys.stderr)
