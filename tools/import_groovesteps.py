"""Importe les grooves GrooveSteps (CC0) vers le format MIDI LINES.  Usage : python3 -I import_groovesteps.py drum_patterns.json"""
import json, sys
VOICES = [("kick", "BD"), ("snare", "SN"), ("hihat", "CH"), ("openhat", "OH"), ("crash", "CY"), ("ride", "CY")]
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("# GrooveSteps Drum Patterns (groovesteps.com, licence CC0).\n")
for p in d["patterns"]:
    rows = {}
    for key, code in VOICES:
        if key in p:
            cells = "".join("x" if v else "." for v in p[key])
            rows[code] = "".join("x" if a == "x" or b == "x" else "." for a, b in zip(rows.get(code, "." * 16), cells))
    print(f'@drums id=gs-{p["id"]} name="{p["name"]}" genre=basic bars=1 steps=16 tags=bpm{p["bpm"]} src=groovesteps')
    for code in ["BD", "SN", "CH", "OH", "CY"]:
        if code in rows: print(f"{code:2s} {rows[code]}")
    print()
