// MLG Alpha — lecteur ([js] de Max, JavaScript ES5).
//
// Reçoit la ligne (« clip … ») depuis mlg_core.js, et la joue calée sur le transport de Live :
//   - entrée « tick » : position du transport en ticks (480 par noire), envoyée en continu ;
//   - sortie 0 : listes « hauteur vélocité » (vélocité 0 = note-off) vers [midiformat] ;
//   - sortie 1 : « playpos x » pour le piano roll (au plus 30 fois par seconde) ;
//   - sortie 2 : messages pour le cœur et l'affichage (« written », « status … »).
// Le message « write » écrit la ligne dans un clip de la piste (API de Live).

autowatch = 1;
inlets = 1;
outlets = 3;

var play = null;          // clip joué
var queued = null;        // clip en attente de la mesure suivante
var switchAtBar = 0;
var isPlaying = 0;
var last = -1;            // dernière position lue (en noires)
var active = [];          // notes en cours : {p, end}
var lastPosOut = 0;
var observer = null;
var lineName = "MLG Alpha";
var enabled = 1;          // interrupteur « Lecture » : 0 = MLG se tait (pour écouter les clips écrits)

function parseClip(a) {
    var c = { L: a[0], stepPpq: a[1], spb: a[2], drums: a[3], notes: [] };
    for (var i = 4; i + 3 < a.length; i += 4)
        c.notes.push({ s: a[i], l: a[i + 1], p: a[i + 2], v: a[i + 3] });
    return c;
}

function clip() {
    var c = parseClip(arrayfromargs(arguments));
    if (switchAtBar && isPlaying && play) queued = c;
    else { play = c; queued = null; }
}

function linename() { lineName = arrayfromargs(arguments).join(" "); }

function switchat(v) { switchAtBar = v ? 1 : 0; }

function enable(v) {
    enabled = v ? 1 : 0;
    if (!enabled) { allOff(); last = -1; }
}

// Appelé par [live.thisdevice] quand l'appareil est prêt : on surveille lecture / arrêt de Live.
function init() {
    observer = new LiveAPI(onLive, "live_set");
    observer.property = "is_playing";
}

function onLive(args) {
    if (args[0] !== "is_playing") return;
    var v = args[1] ? 1 : 0;
    if (v === isPlaying) return;
    isPlaying = v;
    if (!v) {
        allOff();
        if (queued) { play = queued; queued = null; }
        last = -1;
        outlet(1, "playpos", -1);
    }
}

function allOff() {
    for (var i = 0; i < active.length; ++i) outlet(0, active[i].p, 0);
    active = [];
}

function releaseDue(t) {
    for (var i = 0; i < active.length;) {
        if (active[i].end <= t) {
            outlet(0, active[i].p, 0);
            active[i] = active[active.length - 1];
            active.pop();
        } else ++i;
    }
}

function render(c, from, to) {
    if (!c || c.L <= 0 || to <= from) { releaseDue(to); return; }
    var c0 = Math.floor(from / c.L), c1 = Math.floor(to / c.L);
    for (var cy = c0; cy <= c1; ++cy) {
        for (var k = 0; k < c.notes.length; ++k) {
            var n = c.notes[k];
            var t = cy * c.L + n.s;
            if (t < from) continue;
            if (t >= to) break;
            releaseDue(t);
            for (var i = 0; i < active.length; ++i) {
                if (active[i].p === n.p) {
                    outlet(0, n.p, 0);
                    active[i] = active[active.length - 1];
                    active.pop();
                    break;
                }
            }
            if (active.length >= 256) continue;
            outlet(0, n.p, n.v);
            active.push({ p: n.p, end: t + n.l });
        }
    }
    releaseDue(to);
}

function tick(ticks) {
    if (!isPlaying || !play || !enabled) return;
    var now = ticks / 480.0;
    var from;
    if (last < 0 || now < last - 1e-6 || now - last > 0.5) {
        // départ ou saut de lecture : on coupe et on repart d'ici (petite marge pour ne pas rater le premier temps)
        allOff();
        from = Math.max(0, now - 0.02);
    } else from = last;
    if (now <= from) return;

    if (queued) {
        var bar = Math.ceil(from / 4.0 - 1e-9) * 4.0;
        if (bar < now) {
            render(play, from, bar);
            play = queued;
            queued = null;
            render(play, bar, now);
        } else render(play, from, now);
    } else render(play, from, now);
    last = now;

    var ms = new Date().getTime();
    if (ms - lastPosOut > 33) {
        lastPosOut = ms;
        outlet(1, "playpos", play.L > 0 ? now % play.L : -1);
    }
}

// ---------------------------------------------------------------------------
// Écrire la ligne dans un clip de la piste qui porte l'appareil.

function cleanPath(p) { return String(p).replace(/"/g, ""); }

function nameOf(api) {
    var v = api.get("name");
    if (v && typeof v === "object" && v.length !== undefined) v = Array.prototype.join.call(v, " ");
    return String(v).replace(/"/g, "");
}

function write() {
    var c = queued || play;
    if (!c || !c.notes.length) { outlet(2, "status", "Rien à écrire : la ligne est vide."); return; }

    var dev = new LiveAPI("this_device");
    var devPath = cleanPath(dev.path);              // « live_set tracks 2 devices 0 »
    var parts = devPath.split(" ");
    if (parts.length < 3 || parts[1] !== "tracks") {
        outlet(2, "status", "Écriture possible seulement sur une piste MIDI normale.");
        return;
    }
    var trackPath = parts[0] + " " + parts[1] + " " + parts[2];

    // Case choisie : la case sélectionnée si elle est sur cette piste et vide ou déjà remplie par MLG ;
    // sinon la première case libre. Un clip qui n'est pas de MLG (ton clip vide de lecture…) n'est jamais écrasé.
    var track = new LiveAPI(trackPath);
    var count = track.getcount("clip_slots");
    var isMlg = function (slotP) {
        var s = new LiveAPI(slotP);
        if (!s.get("has_clip")[0]) return false;
        var cl = new LiveAPI(slotP + " clip");
        return nameOf(cl).indexOf("MLG Alpha") >= 0;
    };
    var slotPath = null;
    var view = new LiveAPI("live_set view");
    var hs = view.get("highlighted_clip_slot");
    if (hs && hs.length >= 2 && hs[1] > 0) {
        var sel = new LiveAPI("id " + hs[1]);
        var sp = cleanPath(sel.path);
        if (sp.indexOf(trackPath + " clip_slots") === 0 && (!sel.get("has_clip")[0] || isMlg(sp))) slotPath = sp;
    }
    if (!slotPath) {
        for (var i = 0; i < count; ++i) {
            var s = new LiveAPI(trackPath + " clip_slots " + i);
            if (!s.get("has_clip")[0]) { slotPath = trackPath + " clip_slots " + i; break; }
        }
    }
    if (!slotPath) { outlet(2, "status", "Pas de case libre sur cette piste."); return; }

    // numéro suivant pour « MLG Alpha loop N »
    var next = 1;
    for (var j = 0; j < count; ++j) {
        var sj = new LiveAPI(trackPath + " clip_slots " + j);
        if (!sj.get("has_clip")[0]) continue;
        var nm = nameOf(new LiveAPI(trackPath + " clip_slots " + j + " clip"));
        var mm = nm.match(/MLG Alpha loop (\d+)/);
        if (mm) next = Math.max(next, parseInt(mm[1], 10) + 1);
    }

    var slot = new LiveAPI(slotPath);
    var clipApi, keepName = "";
    if (slot.get("has_clip")[0]) {
        clipApi = new LiveAPI(slotPath + " clip");
        keepName = nameOf(clipApi);
        clipApi.call("remove_notes_extended", 0, 128, -16384, 65536);
        clipApi.set("loop_start", 0);
        clipApi.set("loop_end", c.L);
        clipApi.set("end_marker", c.L);
    } else {
        slot.call("create_clip", c.L);
        clipApi = new LiveAPI(slotPath + " clip");
    }

    var notes = [];
    for (var k = 0; k < c.notes.length; ++k) {
        var n = c.notes[k];
        var d = Math.max(0.01, Math.min(n.l, c.L - n.s));
        notes.push({ pitch: n.p, start_time: n.s, duration: d, velocity: n.v, mute: 0 });
    }
    clipApi.call("add_new_notes", { notes: notes });
    var clipName = keepName.indexOf("MLG Alpha loop") >= 0 ? keepName : "MLG Alpha loop " + next;
    clipApi.set("name", clipName);

    var idx = slotPath.split(" ").pop();
    outlet(2, "status", "« " + clipName + " » écrit dans la case " + (parseInt(idx, 10) + 1) + ".");
    outlet(2, "written");
}
