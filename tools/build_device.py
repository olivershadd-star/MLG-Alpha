"""Fabrique l'appareil Max for Live de MLG Alpha.

Sortie dans dist/MLG Alpha/ :
    MLG Alpha.amxd        l'appareil (effet MIDI) à glisser sur une piste MIDI d'Ableton
    MLG Alpha.maxpat      le même patch en texte (secours : copier-coller dans un appareil Max vide)
    mlg_core.js, mlg_player.js, mlg_text.js
    mlg_library.txt.gz, mlg_dictionary.txt

Le patch est écrit par ce script plutôt qu'à la souris : il reste lisible, versionné et reproductible.
Dans l'éditeur Max, chaque zone porte un titre (1. Cœur, 2. Lecture…) pour s'y retrouver.

Usage : python3 tools/build_device.py

Le conteneur .amxd (en-tête « ampf ») reprend le format documenté par py2max
(https://github.com/shakfu/py2max, licence MIT, fonction pack_amxd).
"""
import json
import os
import shutil
import struct
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "dist", "MLG Alpha")
DEVICE_WIDTH = 450

# ----------------------------------------------------------------------------- conteneur .amxd
MAX_EPOCH_OFFSET = 2_082_844_800


def _pad4(b):
    return b + b"\x00" * ((-len(b)) % 4)


def _chunk(tag, payload):
    return tag + struct.pack(">I", 8 + len(payload)) + payload


def pack_amxd(patcher_json, device_type=b"mmmm", filename="MLG Alpha.amxd"):
    json_block = patcher_json.encode("utf-8") + b"\x00"
    mtime = int(time.time()) + MAX_EPOCH_OFFSET
    dire = b"".join([
        _chunk(b"type", b"JSON"),
        _chunk(b"fnam", _pad4(filename.encode("utf-8") + b"\x00")),
        _chunk(b"sz32", struct.pack(">I", len(json_block))),
        _chunk(b"of32", struct.pack(">I", 16)),
        _chunk(b"vers", struct.pack(">I", 0)),
        _chunk(b"flag", struct.pack(">I", 17)),
        _chunk(b"mdat", struct.pack(">I", mtime)),
    ])
    dlst = _chunk(b"dlst", _chunk(b"dire", dire))
    ptch_size = 16 + len(json_block) + len(dlst)
    mxac = b"mx@c" + struct.pack(">I", 16) + struct.pack(">I", 0) + struct.pack(">I", 16 + len(json_block)) + json_block
    return b"ampf" + struct.pack("<I", 4) + device_type + b"ptch" + struct.pack("<I", ptch_size) + mxac + dlst


# ----------------------------------------------------------------------------- patch
class Patch:
    def __init__(self):
        self.boxes, self.lines, self.n = [], [], 0

    def _add(self, box):
        self.n += 1
        box["id"] = "obj-%d" % self.n
        self.boxes.append({"box": box})
        return box["id"]

    def obj(self, text, ins, outs, x, y, w=None, types=None, **kw):
        box = {"maxclass": "newobj", "text": text, "numinlets": ins, "numoutlets": outs,
               "outlettype": types if types is not None else [""] * outs,
               "patching_rect": [x, y, w or max(40, 7 * len(text) + 12), 22]}
        box.update(kw)
        return self._add(box)

    def msg(self, text, x, y, w=None):
        return self._add({"maxclass": "message", "text": text, "numinlets": 2, "numoutlets": 1, "outlettype": [""],
                          "patching_rect": [x, y, w or max(40, 7 * len(text) + 12), 22]})

    def comment(self, text, x, y, w=300, pres=None, size=None, bold=False, color=None):
        box = {"maxclass": "comment", "text": text, "numinlets": 1, "numoutlets": 0,
               "patching_rect": [x, y, w, 20]}
        if size: box["fontsize"] = size
        if bold: box["fontface"] = 1
        if color: box["textcolor"] = color
        if pres:
            box["presentation"] = 1
            box["presentation_rect"] = pres
        return self._add(box)

    def ui(self, maxclass, x, y, pres, ins, outs, types, **kw):
        box = {"maxclass": maxclass, "numinlets": ins, "numoutlets": outs, "outlettype": types,
               "patching_rect": [x, y, pres[2], pres[3]], "presentation": 1, "presentation_rect": pres}
        box.update(kw)
        return self._add(box)

    def line(self, a, outlet, b, inlet=0):
        self.lines.append({"patchline": {"source": [a, outlet], "destination": [b, inlet]}})


def param(longname, shortname, ptype, mn=None, mx=None, initial=None, unit=None, enum=None, hidden=False):
    v = {"parameter_longname": longname, "parameter_shortname": shortname, "parameter_type": ptype}
    if mn is not None: v["parameter_mmin"] = mn
    if mx is not None: v["parameter_mmax"] = mx
    if initial is not None:
        v["parameter_initial"] = initial if isinstance(initial, list) else [initial]
        v["parameter_initial_enable"] = 1
    if unit is not None: v["parameter_unitstyle"] = unit
    if enum is not None: v["parameter_enum"] = enum
    if hidden: v["parameter_invisible"] = 1
    return {"parameter_enable": 1, "saved_attribute_attributes": {"valueof": v}}


SCALES = ["Majeur", "Mineur naturel", "Dorien", "Phrygien", "Lydien", "Mixolydien", "Locrien", "Mineur harmonique",
          "Mineur mélodique", "Penta majeure", "Penta mineure", "Blues", "Chromatique"]
ROOTS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
UNIT_INT, UNIT_FLOAT, UNIT_PCT, UNIT_MIDI = 0, 1, 5, 8


def text_window(title, jsui_size):
    """Sous-patch qui s'ouvre en fenêtre (fiche technique, bilan) : une zone de texte jsui."""
    w, h = 760, 520
    boxes = [
        {"box": {"id": "obj-1", "maxclass": "inlet", "numinlets": 0, "numoutlets": 1, "outlettype": [""],
                 "patching_rect": [10, 10, 30, 30], "comment": "texte"}},
        {"box": {"id": "obj-2", "maxclass": "jsui", "filename": "mlg_text.js", "jsarguments": [jsui_size],
                 "numinlets": 1, "numoutlets": 1, "outlettype": [""], "parameter_enable": 0,
                 "patching_rect": [10, 50, w - 20, h - 60], "presentation": 1, "presentation_rect": [0, 0, w, h]}},
    ]
    lines = [{"patchline": {"source": ["obj-1", 0], "destination": ["obj-2", 0]}}]
    outs = 0
    if title == "bilan":
        boxes += [
            {"box": {"id": "obj-3", "maxclass": "textbutton", "text": "Effacer les J'aime / Bof (garde la bibliothèque perso)",
                     "numinlets": 1, "numoutlets": 3, "outlettype": ["", "", "int"], "parameter_enable": 0,
                     "patching_rect": [10, h - 0, 320, 24], "presentation": 1, "presentation_rect": [8, h + 4, 320, 24]}},
            {"box": {"id": "obj-4", "maxclass": "outlet", "numinlets": 1, "numoutlets": 0,
                     "patching_rect": [10, h + 40, 30, 30], "comment": "reset"}},
        ]
        lines.append({"patchline": {"source": ["obj-3", 0], "destination": ["obj-4", 0]}})
        outs = 1
    return {
        "fileversion": 1,
        "appversion": {"major": 8, "minor": 6, "revision": 0, "architecture": "x64", "modernui": 1},
        "classnamespace": "box", "rect": [120.0, 120.0, float(w), float(h + 40)],
        "openinpresentation": 1, "default_fontsize": 12.0, "default_fontface": 0, "default_fontname": "Arial",
        "gridsize": [15.0, 15.0], "boxes": boxes, "lines": lines,
        "toolbarvisible": 0, "statusbarvisible": 0, "enablehscroll": 0, "enablevscroll": 0,
    }, outs


def build():
    P = Patch()
    C = lambda t, x, y, w=420: P.comment(t, x, y, w, size=13, bold=True)

    # ===================================================================== 1. Cœur
    C("1. CŒUR : mlg_core.js (bibliothèque, traducteur, générateur) dans node.script", 20, 10, 700)
    node = P.obj("node.script mlg_core.js @autostart 1 @watch 0", 1, 2, 20, 360, 300)
    route = P.obj("route ready clip line fiche seeds libline state understood techfeedback bilan place status locks name",
                  2, 15, 20, 400, 760)
    O = {k: i for i, k in enumerate("ready clip line fiche seeds libline state understood techfeedback bilan place status locks name".split())}
    P.line(node, 0, route)

    # au démarrage du script : chemins des fichiers, valeurs des potards, état sauvegardé (de droite à gauche)
    t_ready = P.obj("t b b b", 1, 3, 20, 440, 60)
    P.line(route, O["ready"], t_ready)
    m_lib = P.msg("mlg_library.txt.gz", 560, 470)
    m_dict = P.msg("mlg_dictionary.txt", 720, 470)
    for m, sel, x in ((m_lib, "libfile", 560), (m_dict, "dictfile", 720)):
        ap = P.obj("absolutepath", 1, 1, x, 500, 90)
        pp = P.obj("prepend " + sel, 1, 1, x, 530, 110)
        P.line(t_ready, 2, m)
        P.line(m, 0, ap)
        P.line(ap, 0, pp)
        P.line(pp, 0, node)

    # état sauvegardé dans le set Live (seeds, verrous, ligne de bibliothèque)
    pattr = P.obj("pattr mlgstate", 1, 3, 20, 600, 100,
                  **param("MLG state", "state", 3, initial=["-"], hidden=True))
    P.line(route, O["state"], pattr)
    P.line(t_ready, 0, pattr)
    p_restore = P.obj("prepend restore", 1, 1, 20, 630, 100)
    P.line(pattr, 0, p_restore)
    P.line(p_restore, 0, node)

    # placement des potards (« place p_density 40 » -> script send p_density set 40)
    m_place = P.msg("script send $1 set $2", 200, 600, 150)
    thisp = P.obj("thispatcher", 1, 2, 200, 630, 80)
    P.line(route, O["place"], m_place)
    P.line(m_place, 0, thisp)

    # ===================================================================== 2. Lecture
    C("2. LECTURE : mlg_player.js joue la ligne calée sur Live, et l'écrit dans un clip", 820, 10, 700)
    player = P.obj("js mlg_player.js", 1, 3, 820, 200, 130)
    p_clip = P.obj("prepend clip", 1, 1, 820, 160, 90)
    P.line(route, O["clip"], p_clip)
    P.line(p_clip, 0, player)
    p_name = P.obj("prepend linename", 1, 1, 930, 160, 110)
    P.line(route, O["name"], p_name)
    P.line(p_name, 0, player)
    thisdev = P.obj("live.thisdevice", 1, 3, 820, 50, 100, types=["bang", "int", "int"])
    m_init = P.msg("init", 820, 80)
    P.line(thisdev, 0, m_init)
    P.line(m_init, 0, player)
    metro = P.obj("metro 2 @active 1", 2, 1, 960, 50, 110, types=["bang"])
    transport = P.obj("transport", 2, 9, 960, 80, 80)
    P.line(metro, 0, transport)
    p_tick = P.obj("prepend tick", 1, 1, 960, 110, 80)
    P.line(transport, 7, p_tick)
    P.line(p_tick, 0, player)
    mf = P.obj("midiformat", 7, 2, 820, 260, 80)
    mout = P.obj("midiout", 1, 0, 820, 290, 60)
    P.line(player, 0, mf)
    P.line(mf, 0, mout)
    mid = P.obj("midiin", 1, 1, 1100, 230, 60)     # les notes jouées au clavier passent à travers
    P.line(mid, 0, mout)
    r_player = P.obj("route status written", 2, 3, 960, 260, 140)
    P.line(player, 2, r_player)
    m_written = P.msg("written", 1040, 290)
    P.line(r_player, 1, m_written)
    P.line(m_written, 0, node)

    # ===================================================================== 3. Interface
    # Présentation compacte : trois pages (RYTHME, NOTES, TEXTE) à gauche, une colonne fixe à droite.
    C("3. INTERFACE : pages RYTHME / NOTES / TEXTE + colonne fixe (mode présentation)", 20, 700, 800)
    x0, y0 = 20, 740   # zone de rangement des objets d'interface dans le patch
    pages = {"rythme": [], "notes": [], "texte": []}
    counter = [0]

    def on_page(page, box_id):
        """Donne un nom de script à l'objet et le range dans sa page (cachée au départ sauf RYTHME)."""
        box = next(b["box"] for b in P.boxes if b["box"]["id"] == box_id)
        if "varname" not in box:
            counter[0] += 1
            box["varname"] = "pg_%s_%d" % (page, counter[0])
        if page != "rythme":
            box["hidden"] = 1
        pages[page].append(box["varname"])
        return box_id

    def to_node(src, outlet, prefix, x, y):
        pp = P.obj("prepend " + prefix, 1, 1, x, y, 7 * len(prefix) + 60)
        P.line(src, outlet, pp)
        P.line(pp, 0, node)
        return pp

    def button(text, pres, x, y, message, toggle=False, varname=None, page=None, **extra):
        kw = {"text": text, "mode": 1 if toggle else 0, "parameter_enable": 0}
        if toggle: kw["texton"] = text
        if varname: kw["varname"] = varname
        kw.update(extra)
        b = P.ui("live.text", x, y, pres, 1, 2, ["", ""], **kw)
        if message is not None:
            m = P.msg(message, x, y + 30)
            P.line(b, 0, m)
            P.line(m, 0, node)
        if page: on_page(page, b)
        return b

    def label(text, pres, page=None, size=9, **kw):
        c = P.comment(text, 0, 0, pres[2], pres=pres, size=size, **kw)
        if page: on_page(page, c)
        return c

    dump_targets = []   # potards à relire quand le script démarre

    def dial(pid, text, pres, x, y, mn, mx, initial, ptype=1, unit=UNIT_INT, page=None):
        d = P.ui("live.dial", x, y, pres, 1, 2, ["", "float"], varname="p_" + pid, showname=1, shownumber=1,
                 **param(text, text, ptype, mn, mx, initial, unit))
        to_node(d, 0, "param " + pid, x, y + 60)
        dump_targets.append(d)
        if page: on_page(page, d)
        return d

    def menu(pid, text, items, pres, x, y, initial, page=None):
        label(text, [pres[0], pres[1] - 12, pres[2], 12], page, size=8.5)
        m = P.ui("live.menu", x, y, pres, 1, 3, ["", "", "float"], varname="p_" + pid,
                 **param(text, text, 2, 0, len(items) - 1, initial, enum=items))
        to_node(m, 0, "param " + pid, x, y + 30)
        dump_targets.append(m)
        if page: on_page(page, m)
        return m

    # --- onglets ---
    tabs = P.ui("live.tab", x0, y0, [4, 2, 296, 16], 1, 3, ["", "", "float"], varname="pages",
                num_lines_presentation=1, num_lines_patching=1,
                **param("Page", "Page", 2, 0, 2, 0, enum=["RYTHME", "NOTES", "TEXTE"]))

    DW = 49   # largeur d'un potard
    # --- page RYTHME ---
    menu("rhythmMode", "Moteur", ["Aléatoire", "Euclidien"], [4, 34, 68, 15], x0, y0 + 80, 0, "rythme")
    menu("division", "Division", ["1/4", "1/8", "1/8T", "1/16", "1/16T", "1/32"], [76, 34, 50, 15], x0 + 110, y0 + 80, 3, "rythme")
    lr = button("Verrou rythme", [130, 32, 76, 18], x0 + 220, y0 + 80, None, toggle=True, varname="lockr", page="rythme")
    to_node(lr, 0, "lockr", x0 + 220, y0 + 110)
    label("Seed", [210, 22, 40, 12], "rythme", size=8.5)
    seedr = P.ui("textedit", x0 + 330, y0 + 80, [210, 33, 90, 17], 1, 4, ["", "int", "", ""], keymode=1, lines=1,
                 varname="seedr", parameter_enable=0, fontsize=10.0)
    on_page("rythme", seedr)
    to_node(seedr, 0, "seedr", x0 + 330, y0 + 110)
    R = [("steps", "Pas", 1, 128, 16, 1, UNIT_INT), ("density", "Densité", 0, 100, 50, 0, UNIT_PCT),
         ("pulses", "Impulsions", 0, 128, 5, 1, UNIT_INT), ("rotation", "Rotation", 0, 127, 0, 1, UNIT_INT),
         ("swing", "Swing", 0, 100, 0, 0, UNIT_PCT), ("accent", "Accent", 0, 40, 15, 1, UNIT_INT)]
    for i, (pid, text, mn, mx, ini, pt, unit) in enumerate(R):
        dial(pid, text, [4 + i * DW, 58, DW - 2, 48], x0 + i * 90, y0 + 180, mn, mx, ini, 0 if pt == 0 else 1, unit, "rythme")
    label("Pas jusqu'à 128 = 8 mesures en doubles croches. Le rythme euclidien répartit les impulsions sur les pas.",
          [4, 110, 296, 40], "rythme", size=8.5, color=[0.6, 0.64, 0.7, 1])

    # --- page NOTES ---
    menu("root", "Tonique", ROOTS, [4, 34, 44, 15], x0, y0 + 300, 0, "notes")
    menu("scale", "Gamme", SCALES, [52, 34, 96, 15], x0 + 110, y0 + 300, 1, "notes")
    menu("octave", "Octave", ["-3", "-2", "-1", "0", "+1", "+2", "+3"], [152, 34, 40, 15], x0 + 220, y0 + 300, 3, "notes")
    leg = P.ui("live.text", x0 + 330, y0 + 300, [196, 32, 50, 18], 1, 2, ["", ""], text="Legato", texton="Legato", mode=1,
               varname="p_legato", **param("Legato", "Legato", 2, 0, 1, 0, enum=["off", "on"]))
    on_page("notes", leg)
    to_node(leg, 0, "param legato", x0 + 330, y0 + 330)
    dump_targets.append(leg)
    lp = button("Verrou haut.", [250, 32, 50, 18], x0 + 440, y0 + 300, None, toggle=True, varname="lockp", page="notes")
    to_node(lp, 0, "lockp", x0 + 440, y0 + 330)
    N = [("lowNote", "Note basse", 24, 108, 48, 1, UNIT_MIDI), ("highNote", "Note haute", 24, 108, 67, 1, UNIT_MIDI),
         ("maxJump", "Écart max", 0, 12, 3, 1, UNIT_INT), ("lenMin", "Durée min", 5, 400, 50, 0, UNIT_PCT),
         ("lenMax", "Durée max", 5, 400, 100, 0, UNIT_PCT), ("velMin", "Vél. min", 1, 127, 80, 1, UNIT_INT),
         ("velMax", "Vél. max", 1, 127, 110, 1, UNIT_INT)]
    for i, (pid, text, mn, mx, ini, pt, unit) in enumerate(N):
        pres = [4 + i * DW, 58, DW - 2, 48] if i < 6 else [4, 110, DW - 2, 48]
        dial(pid, text, pres, x0 + i * 90, y0 + 400, mn, mx, ini, 0 if pt == 0 else 1, unit, "notes")
    label("Seed", [60, 122, 40, 12], "notes", size=8.5)
    seedp = P.ui("textedit", x0 + 650, y0 + 300, [88, 120, 100, 17], 1, 4, ["", "int", "", ""], keymode=1, lines=1,
                 varname="seedp", parameter_enable=0, fontsize=10.0)
    on_page("notes", seedp)
    to_node(seedp, 0, "seedp", x0 + 650, y0 + 330)

    # --- page TEXTE ---
    words = P.ui("textedit", x0 + 900, y0 + 300, [4, 22, 226, 20], 1, 4, ["", "int", "", ""],
                 keymode=1, lines=1, varname="words", parameter_enable=0, fontsize=11.0)
    on_page("texte", words)
    gate = P.obj("gate 2 1", 2, 2, x0 + 900, y0 + 340, 60)
    P.line(words, 0, gate, 1)
    to_node(gate, 0, "words", x0 + 900, y0 + 370)
    to_node(gate, 1, "keep", x0 + 1000, y0 + 370)
    t_keep = P.obj("t 1 b 2", 1, 3, x0 + 1100, y0 + 300, 60)   # Garder : les mots de la case partent vers « keep »
    P.line(t_keep, 2, gate)
    P.line(t_keep, 1, words)
    P.line(t_keep, 0, gate)
    search = button("CHERCHER", [234, 22, 66, 20], x0 + 1100, y0 + 340, None, page="texte")
    P.line(search, 0, words)
    tx = x0 + 900
    button("J'aime", [4, 46, 70, 17], tx, y0 + 420, "like 1", page="texte")
    button("Bof", [78, 46, 70, 17], tx + 90, y0 + 420, "like 0", page="texte")
    fiche_btn = button("Fiche", [152, 46, 72, 17], tx + 180, y0 + 420, None, page="texte")
    button("Bilan", [228, 46, 72, 17], tx + 270, y0 + 420, "bilan", page="texte")
    understood = P.ui("jsui", tx, y0 + 500, [4, 66, 296, 56], 1, 1, [""], filename="mlg_text.js",
                      jsarguments=[9.5], parameter_enable=0)
    on_page("texte", understood)
    pu = P.obj("prepend settext", 1, 1, tx, y0 + 470, 100)
    P.line(route, O["understood"], pu)
    P.line(pu, 0, understood)
    label("Commande technique : « 2 mesures, division 1/16, tonique la »", [4, 124, 296, 12], "texte", size=8.5)
    tech = P.ui("textedit", tx, y0 + 580, [4, 138, 250, 18], 1, 4, ["", "int", "", ""], keymode=1, lines=1,
                varname="tech", parameter_enable=0, fontsize=10.0)
    on_page("texte", tech)
    to_node(tech, 0, "tech", tx, y0 + 610)
    ok = button("OK", [258, 138, 42, 18], tx + 300, y0 + 580, None, page="texte")
    P.line(ok, 0, tech)

    # changement de page : script show / hide
    sel = P.obj("sel 0 1 2", 2, 4, x0, y0 + 30, 80)
    P.line(tabs, 0, sel)
    for k, page in enumerate(("rythme", "notes", "texte")):
        cmds = ["script show " + v for v in pages[page]]
        cmds += ["script hide " + v for other in pages if other != page for v in pages[other]]
        m = P.msg(", ".join(cmds), x0 + k * 200, y0 + 55, 180)
        P.line(sel, k, m)
        P.line(m, 0, thisp)

    # --- colonne fixe (x 306..446) ---
    line_c = P.comment("MLG Alpha", 0, 0, 140, pres=[306, 0, 140, 42], size=9, bold=True)
    pl = P.obj("prepend set", 1, 1, x0 + 1300, y0 + 260, 80)
    P.line(route, O["line"], pl)
    P.line(pl, 0, line_c)
    button("GÉNÉRER", [306, 44, 68, 18], x0 + 1500, y0, "generate")
    button("MUTER", [378, 44, 68, 18], x0 + 1590, y0, "mutate")
    button("Une autre", [306, 66, 68, 18], x0 + 1680, y0, "again")
    keep = button("Garder", [378, 66, 68, 18], x0 + 1770, y0, None)
    P.line(keep, 0, t_keep)
    lect = P.ui("live.text", x0 + 1500, y0 + 80, [306, 88, 68, 18], 1, 2, ["", ""], text="Lecture", texton="Lecture",
                mode=1, varname="p_play", **param("Lecture", "Lecture", 2, 0, 1, 1, enum=["off", "on"]))
    p_en = P.obj("prepend enable", 1, 1, x0 + 1500, y0 + 110, 100)
    P.line(lect, 0, p_en)
    P.line(p_en, 0, player)
    sw = P.ui("live.menu", x0 + 1600, y0 + 80, [378, 90, 68, 15], 1, 3, ["", "", "float"], varname="p_switchAt",
              **param("Changement", "Changement", 2, 0, 1, 0, enum=["Immédiat", "À la mesure"]))
    to_node(sw, 0, "param switchAt", x0 + 1600, y0 + 110)
    p_sw = P.obj("prepend switchat", 1, 1, x0 + 1600, y0 + 140, 100)
    P.line(sw, 0, p_sw)
    P.line(p_sw, 0, player)
    dump_targets += [sw, lect]
    wr = button("→ Écrire dans un clip", [306, 110, 140, 20], x0 + 1500, y0 + 150, None)
    m_write = P.msg("write", x0 + 1500, y0 + 180)
    P.line(wr, 0, m_write)
    P.line(m_write, 0, player)
    status = P.comment("Bibliothèque : chargement…", 0, 0, 140, pres=[306, 134, 140, 34], size=8.5,
                       color=[0.6, 0.64, 0.7, 1])
    for k, (src, outlet) in enumerate(((route, O["status"]), (route, O["techfeedback"]), (r_player, 0))):
        pp = P.obj("prepend set", 1, 1, x0 + 1300, y0 + k * 30, 80)
        P.line(src, outlet, pp)
        P.line(pp, 0, status)

    # retours vers l'interface : seeds, verrous
    useeds = P.obj("unpack s s", 1, 2, x0 + 1300, y0 + 120, 80)
    P.line(route, O["seeds"], useeds)
    for k, te in enumerate((seedr, seedp)):
        pp = P.obj("prepend set", 1, 1, x0 + 1300 + k * 90, y0 + 150, 80)
        P.line(useeds, k, pp)
        P.line(pp, 0, te)
    ulocks = P.obj("unpack 0 0", 1, 2, x0 + 1300, y0 + 190, 80)
    P.line(route, O["locks"], ulocks)
    for k, b in enumerate((lr, lp)):
        pp = P.obj("prepend set", 1, 1, x0 + 1300 + k * 90, y0 + 220, 80)
        P.line(ulocks, k, pp)
        P.line(pp, 0, b)

    # fenêtres : fiche technique et bilan
    fiche_p, _ = text_window("fiche", 13)
    bilan_p, bilan_outs = text_window("bilan", 13)
    p_fiche = P.obj("p fiche", 1, 0, tx + 600, y0 + 500, 70, patcher=fiche_p)
    p_bilan = P.obj("p bilan", 1, bilan_outs, tx + 700, y0 + 500, 70, patcher=bilan_p)
    pf = P.obj("prepend settext", 1, 1, tx + 600, y0 + 440, 100)
    P.line(route, O["fiche"], pf)
    P.line(pf, 0, p_fiche)
    m_open1 = P.msg("open", tx + 600, y0 + 470)
    pc1 = P.obj("pcontrol", 1, 1, tx + 650, y0 + 470, 60)
    P.line(fiche_btn, 0, m_open1)
    P.line(m_open1, 0, pc1)
    P.line(pc1, 0, p_fiche)
    t_bilan = P.obj("t b l", 1, 2, tx + 700, y0 + 410, 50)
    P.line(route, O["bilan"], t_bilan)
    pb = P.obj("prepend settext", 1, 1, tx + 760, y0 + 440, 100)
    P.line(t_bilan, 1, pb)
    P.line(pb, 0, p_bilan)
    m_open2 = P.msg("open", tx + 700, y0 + 470)
    pc2 = P.obj("pcontrol", 1, 1, tx + 750, y0 + 470, 60)
    P.line(t_bilan, 0, m_open2)
    P.line(m_open2, 0, pc2)
    P.line(pc2, 0, p_bilan)
    m_reset = P.msg("reset", tx + 700, y0 + 540)
    P.line(p_bilan, 0, m_reset)
    P.line(m_reset, 0, node)

    # relecture des potards au démarrage du script
    for d in dump_targets:
        P.line(t_ready, 1, d)

    patcher = {
        "fileversion": 1,
        "appversion": {"major": 8, "minor": 6, "revision": 0, "architecture": "x64", "modernui": 1},
        "classnamespace": "box",
        "rect": [60.0, 80.0, 1500.0, 900.0],
        "openrect": [0.0, 0.0, float(DEVICE_WIDTH), 169.0],
        "bglocked": 0, "openinpresentation": 1,
        "default_fontsize": 10.0, "default_fontface": 0, "default_fontname": "Arial Bold",
        "gridonopen": 1, "gridsize": [8.0, 8.0], "gridsnaponopen": 1, "objectsnaponopen": 1,
        "statusbarvisible": 2, "toolbarvisible": 1, "lefttoolbarpinned": 0, "toptoolbarpinned": 0,
        "righttoolbarpinned": 0, "bottomtoolbarpinned": 0, "toolbars_unpinned_last_save": 0,
        "tallnewobj": 0, "boxanimatetime": 200, "enablehscroll": 1, "enablevscroll": 1,
        "devicewidth": float(DEVICE_WIDTH), "description": "MLG Alpha — MIDI Line Generator (ANKS Labs)",
        "digest": "", "tags": "", "style": "", "subpatcher_template": "", "assistshowspatchername": 0,
        "boxes": P.boxes, "lines": P.lines,
        "dependency_cache": [
            {"name": f, "bootpath": ".", "patcherrelativepath": ".", "type": t, "implicit": 1}
            for f, t in (("mlg_core.js", "TEXT"), ("mlg_player.js", "TEXT"),
                         ("mlg_text.js", "TEXT"), ("mlg_library.txt.gz", "DATA"), ("mlg_dictionary.txt", "TEXT"))],
        "latency": 0, "is_mpe": 0, "minimum_live_version": "", "minimum_max_version": "", "platform_compatibility": 0,
        "project": {
            "version": 1, "creationdate": 3590052493, "modificationdate": 3590052493,
            "viewrect": [0.0, 0.0, 300.0, 500.0], "autoorganize": 1, "hideprojectwindow": 1, "showdependencies": 1,
            "autolocalize": 0, "contents": {"patchers": {}}, "layout": {}, "searchpath": {}, "detailsvisible": 0,
            "amxdtype": 1835887981, "readonly": 0, "devpathtype": 0, "devpath": ".", "sortmode": 0, "viewmode": 0,
            "includepackages": 0,
        },
        "autosave": 0,
    }
    return {"patcher": patcher}, P


def check(doc):
    """Vérifications de base : identifiants uniques, câbles valides, objets de présentation dans le cadre."""
    p = doc["patcher"]
    ids = {}
    for b in p["boxes"]:
        bid = b["box"]["id"]
        assert bid not in ids, bid
        ids[bid] = b["box"]
    for l in p["lines"]:
        s, so = l["patchline"]["source"]
        d, di = l["patchline"]["destination"]
        assert s in ids and d in ids, (s, d)
        assert so < ids[s]["numoutlets"], ("sortie", ids[s].get("text", ids[s]["maxclass"]), so)
        assert di < ids[d]["numinlets"], ("entrée", ids[d].get("text", ids[d]["maxclass"]), di)
    names = [b["box"]["saved_attribute_attributes"]["valueof"]["parameter_longname"]
             for b in p["boxes"] if "saved_attribute_attributes" in b["box"]]
    assert len(names) == len(set(names)), "noms de paramètres en double"
    for b in p["boxes"]:
        r = b["box"].get("presentation_rect")
        if r:
            assert r[0] >= 0 and r[1] >= 0 and r[0] + r[2] <= DEVICE_WIDTH and r[1] + r[3] <= 169, (b["box"]["maxclass"], r)
    return len(p["boxes"]), len(p["lines"]), len(names)


def main():
    doc, _ = build()
    nb, nl, npar = check(doc)
    text = json.dumps(doc, ensure_ascii=False, indent=2)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "MLG Alpha.amxd"), "wb") as f:
        f.write(pack_amxd(text))
    with open(os.path.join(OUT, "MLG Alpha.maxpat"), "w", encoding="utf-8") as f:
        f.write(text)
    for name in ("mlg_core.js", "mlg_player.js", "mlg_text.js"):
        shutil.copy(os.path.join(ROOT, "max", name), OUT)
    for name in ("mlg_library.txt.gz", "mlg_dictionary.txt"):
        shutil.copy(os.path.join(ROOT, "Resources", name), OUT)
    print(f"{OUT} : {nb} objets, {nl} câbles, {npar} paramètres Live")


if __name__ == "__main__":
    main()
