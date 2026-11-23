"""Rend quelques motifs de la bibliothèque en fichiers .mid pour les écouter dans Ableton.
Usage : python3 tools/render_samples.py <dossier_sortie>"""
import random, struct, sys, re
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "Library"
DRUM = {"BD": 36, "RS": 37, "SN": 38, "CL": 39, "CH": 42, "OH": 46, "LT": 45, "MT": 47, "HT": 50,
        "CY": 51, "CB": 56, "SH": 70, "PC": 75}
TPQ = 480; STEP = TPQ // 4


def vlq(n):
    out = [n & 0x7F]; n >>= 7
    while n: out.append((n & 0x7F) | 0x80); n >>= 7
    return bytes(reversed(out))


def write_mid(path, events, length_ticks, channel=0):
    """events : (début, fin, note, vélocité) en ticks."""
    msgs = []
    for s, e, n, v in events:
        msgs.append((s, 1, bytes([0x90 | channel, n, v])))
        msgs.append((e, 0, bytes([0x80 | channel, n, 0])))
    msgs.sort(key=lambda m: (m[0], m[1]))
    data = b""; t = 0
    for tick, _, b in msgs:
        data += vlq(tick - t) + b; t = tick
    data += vlq(max(0, length_ticks - t)) + b"\xff\x2f\x00"
    with open(path, "wb") as f:
        f.write(b"MThd" + struct.pack(">IHHH", 6, 0, 1, TPQ))
        f.write(b"MTrk" + struct.pack(">I", len(data)) + data)


def blocks(fname):
    txt = (LIB / fname).read_text()
    for b in txt.split("\n@")[1:]:
        lines = b.strip().splitlines()
        head = lines[0]
        yield head, lines[1:]


def render_notes(head, lines, root):
    bars = int(re.search(r"bars=(\d+)", head).group(1))
    N = [t for l in lines if l.startswith("N ") for t in l.split()[1:]]
    V = [t for l in lines if l.startswith("V ") for t in l.split()[1:]] or None
    ev = []
    for i, t in enumerate(N):
        if t in (".", "-"): continue
        j = i + 1
        while j < len(N) and N[j] == "-": j += 1
        accent = "a" in t
        slide = "s" in t
        name = t.rstrip("as")
        note = DRUM[name] if name in DRUM else root + int(name)
        vel = int(V[i]) if V and V[i] != "." else (120 if accent else 96)
        end = j * STEP - 10
        if slide and j < len(N): end = j * STEP + 30   # chevauchement = glide
        ev.append((i * STEP, end, note, vel))
    return ev, bars * 16 * STEP


def render_drums(head, lines):
    bars = int(re.search(r"bars=(\d+)", head).group(1))
    ev = []
    for l in lines:
        parts = l.split()
        if not parts or parts[0] not in DRUM: continue
        steps = "".join(parts[1:])
        for i, c in enumerate(steps):
            if c in "xX":
                ev.append((i * STEP, i * STEP + STEP - 10, DRUM[parts[0]], 120 if c == "X" or i % 4 == 0 else 100))
            elif c == "r":
                ev.append((i * STEP, i * STEP + STEP // 2 - 5, DRUM[parts[0]], 100))
                ev.append((i * STEP + STEP // 2, i * STEP + STEP - 10, DRUM[parts[0]], 90))
    return ev, bars * 16 * STEP


def main(out, preset="general"):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(7)
    if preset == "techno":
        picks = [("techno_bass.txt", 10, 36), ("techno_synth.txt", 12, 60), ("techno_perc.txt", 14, 0)]
    else:
      picks = [("gen_bass.txt", 8, 36), ("gen_acid.txt", 5, 36), ("gen_synth.txt", 6, 60), ("gen_perc.txt", 5, 0),
             ("acid.txt", 3, 36), ("bass.txt", 3, 36), ("drums_electronic.txt", 5, 0), ("drums_pocket_operations.txt", 3, 0)]
    for fname, count, root in picks:
        items = list(blocks(fname)); rng.shuffle(items)
        for head, lines in items[:count]:
            pid = re.search(r"id=(\S+)", head).group(1)
            if fname.startswith("drums"):
                ev, length = render_drums(head, lines)
            else:
                ev, length = render_notes(head, lines, root)
            write_mid(out / f"{pid}.mid", ev, length, channel=9 if (fname.startswith("drums") or "perc" in fname) else 0)
    print(len(list(out.glob("*.mid"))), "fichiers")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "general")
