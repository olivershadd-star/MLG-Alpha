"""Importe les basses NeuralAcid (intrect/neuralacid-basslines, CC BY 4.0) vers le format MIDI LINES.
Les notes (hauteur, durée, ordre) viennent du fichier .jsonl ; leur position dans la mesure vient du
piano roll .npy (indexé par roll_idx).  Usage :
  python3 -I import_neuralacid.py <out.txt> <jsonl> <pianorolls.npy> [<jsonl> <pianorolls.npy> ...]"""
import json, sys
import numpy as np

PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
      "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
PITCH_MIN = 24


def convert(d, roll):
    """roll : (60, 64) vélocités 0..1.  Renvoie (tokens, vels) sur 64 pas ou None si incohérent."""
    notes = []  # (hauteur, durée) dans l'ordre
    t = d["tokens"]; i = 0
    while i < len(t):
        if t[i].startswith("NOTE_"):
            notes.append((int(t[i][5:]), int(t[i + 1][4:]))); i += 3
        else:
            i += 1
    steps = roll.shape[1]
    active = [None] * steps
    for s in range(steps):
        col = roll[:, s]; nz = np.nonzero(col)[0]
        if len(nz): active[s] = (PITCH_MIN + int(nz[0]), float(col[nz[0]]))
    toks = ["."] * steps; vels = ["."] * steps
    cur = 0
    for pitch, dur in notes:
        s = cur
        while s < steps and not (active[s] and active[s][0] == pitch):
            s += 1
        if s >= steps:
            break  # notes au-delà des 4 mesures dans le fichier texte : on garde ce qui est dans la grille
        toks[s] = pitch; vels[s] = str(max(1, min(127, round(active[s][1] * 127))))
        # durée réelle = min(durée du jeton, durée visible dans la grille) — la grille est « clampée »
        k = s + 1
        while k < min(steps, s + max(1, dur)) and active[k] and active[k][0] == pitch:
            toks[k] = "-"; k += 1
        cur = k
    placed = [x for x in toks if isinstance(x, int)]
    if len(placed) < max(4, 0.8 * len(notes)):
        return None
    return toks, vels, placed


def main():
    out_path = sys.argv[1]; pairs = list(zip(sys.argv[2::2], sys.argv[3::2]))
    out = ["# Basses NeuralAcid (jeu de données intrect/neuralacid-basslines, Hugging Face, licence CC BY 4.0 ;",
           "# générateur Electr-o-matic de unohee). 4 mesures, grille de doubles croches, suivent une grille d'accords.",
           "# N = intervalle depuis la tonique (= fondamentale du 1er accord), - tenue ; V = vélocité.",
           "# chords = accords par mesure : décalage en demi-tons depuis la tonique + type.\n"]
    ok = bad = 0
    for jsonl, npy in pairs:
        rolls = np.load(npy, allow_pickle=False)
        for line in open(jsonl, encoding="utf-8"):
            d = json.loads(line)
            if d["roll_idx"] >= len(rolls): bad += 1; continue
            res = convert(d, rolls[d["roll_idx"]])
            if res is None: bad += 1; continue
            toks, vels, pitches = res
            root_pc = PC[d["chords"][0]["root"]]
            low = min(pitches)
            root = low - ((low - root_pc) % 12)
            toks = [str(x - root) if isinstance(x, int) else x for x in toks]
            chords = ",".join(f'{(PC[c["root"]] - root_pc) % 12}{c["type"]}' for c in d["chords"])
            p = d["params"]
            out.append(f'@bass id=na-{d["id"]:05d} name="NeuralAcid {d["chord_progression"].replace(" ", "")}" '
                       f'genre=acid bars=4 steps=16 tags={p["mode"]} chords={chords} src=neuralacid')
            for b in range(4):
                out.append("N  " + " ".join(toks[b * 16:(b + 1) * 16]))
                out.append("V  " + " ".join(vels[b * 16:(b + 1) * 16]))
            out.append("")
            ok += 1
    open(out_path, "w", encoding="utf-8").write("\n".join(out))
    print(f"{ok} convertis, {bad} rejetés")


if __name__ == "__main__":
    main()
