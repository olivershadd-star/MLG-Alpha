"""Importe les grilles d'accords du pack libre de Ludovic Drolez (github.com/ldrolez/free-midi-chords, licence MIT)
vers chords_drolez.txt.  Le fichier chords.py est lu comme du texte (jamais exécuté).
Usage : python3 import_drolez.py chords.py > chords_drolez.txt"""
import re, sys

text = open(sys.argv[1], encoding="utf-8").read()
print("# Grilles d'accords du Free MIDI Chords Pack de Ludovic Drolez (licence MIT).")
print("# Une case = une mesure ; tags = ambiance indiquée par l'auteur.\n")
n = 0
for group, mode in (("prog_maj", "majeur"), ("prog_min", "mineur"), ("prog_modal", "modal")):
    m = re.search(group + r"\s*=\s*\[(.*?)\]", text, re.S)
    if not m: continue
    for line in re.findall(r'"([^"]+)"', m.group(1)):
        prog, _, mood = line.partition("=")
        chords = prog.split()
        if not chords: continue
        n += 1
        mood_tag = "-".join(w.lower() for w in mood.split()) or "neutre"
        print(f'@chords id=ld-{n:03d} name="{" – ".join(chords)}" genre={mode} bars={len(chords)} tags={mood_tag} src=drolez')
        print("C  " + " ".join(chords) + "\n")
print(f"# {n} grilles", file=sys.stderr)
