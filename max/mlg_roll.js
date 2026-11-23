// MLG Alpha — piano roll ([jsui] de Max, JavaScript ES5).
// Messages : « clip … » (même format que le lecteur), « playpos x » (position en noires, -1 à l'arrêt).

autowatch = 1;
mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var c = null;
var position = -1;

function clip() {
    var a = arrayfromargs(arguments);
    c = { L: a[0], stepPpq: a[1], spb: a[2], drums: a[3], notes: [] };
    for (var i = 4; i + 3 < a.length; i += 4)
        c.notes.push({ s: a[i], l: a[i + 1], p: a[i + 2], v: a[i + 3] });
    mgraphics.redraw();
}

function playpos(x) {
    position = x;
    mgraphics.redraw();
}

function paint() {
    var g = mgraphics;
    var w = box.rect[2] - box.rect[0], h = box.rect[3] - box.rect[1];
    g.set_source_rgba(0.11, 0.12, 0.15, 1);
    g.rectangle(0, 0, w, h);
    g.fill();
    if (!c || c.L <= 0) return;

    var pad = 3, iw = w - 2 * pad, ih = h - 2 * pad;
    var x = function (ppq) { return pad + ppq / c.L * iw; };

    // temps et mesures
    for (var b = 0; b <= c.L + 1e-6; b += 1) {
        var bar = Math.abs(b % 4) < 1e-6;
        g.set_source_rgba(1, 1, 1, bar ? 0.28 : 0.08);
        g.move_to(x(b), pad);
        g.line_to(x(b), h - pad);
        g.set_line_width(1);
        g.stroke();
    }
    if (!c.notes.length) return;

    var lo = 127, hi = 0, i;
    for (i = 0; i < c.notes.length; ++i) { lo = Math.min(lo, c.notes[i].p); hi = Math.max(hi, c.notes[i].p); }
    lo -= 1; hi += 1;
    var rowH = ih / (hi - lo + 1);
    for (i = 0; i < c.notes.length; ++i) {
        var n = c.notes[i];
        var x0 = x(n.s), x1 = x(Math.min(c.L, n.s + n.l));
        var y = h - pad - (n.p - lo + 1) * rowH;
        var a = 0.35 + 0.65 * n.v / 127;
        if (c.drums) g.set_source_rgba(1.0, 0.54, 0.24, a); else g.set_source_rgba(0.21, 0.82, 0.73, a);
        g.rectangle(x0, y, Math.max(2, x1 - x0 - 1), Math.max(2, rowH - 1));
        g.fill();
    }
    if (position >= 0) {
        g.set_source_rgba(1.0, 0.54, 0.24, 1);
        g.move_to(x(position % c.L), pad);
        g.line_to(x(position % c.L), h - pad);
        g.set_line_width(1.5);
        g.stroke();
    }
}

function onresize() { mgraphics.redraw(); }
