// MLG Alpha — zone de texte ([jsui] de Max, JavaScript ES5) : retour à la ligne automatique,
// défilement en glissant la souris. Message : « settext … ». Argument : taille de police.

autowatch = 1;
mgraphics.init();
mgraphics.relative_coords = 0;
mgraphics.autofill = 0;

var txt = "";
var size = jsarguments.length > 1 ? jsarguments[1] : 10;
var scroll = 0;
var lastY = 0;

function settext() {
    txt = arrayfromargs(arguments).join(" ");
    scroll = 0;
    mgraphics.redraw();
}

function wrap(g, maxW) {
    var out = [];
    var paras = txt.split("\n");
    for (var p = 0; p < paras.length; ++p) {
        var words = paras[p].split(" ");
        var line = "";
        for (var i = 0; i < words.length; ++i) {
            var test = line.length ? line + " " + words[i] : words[i];
            if (g.text_measure(test)[0] > maxW && line.length) { out.push(line); line = words[i]; }
            else line = test;
        }
        out.push(line);
    }
    return out;
}

function paint() {
    var g = mgraphics;
    var w = box.rect[2] - box.rect[0], h = box.rect[3] - box.rect[1];
    g.set_source_rgba(0.11, 0.12, 0.15, 1);
    g.rectangle(0, 0, w, h);
    g.fill();
    g.select_font_face("Arial");
    g.set_font_size(size);
    var lines = wrap(g, w - 8);
    var lh = size * 1.3;
    var maxScroll = Math.max(0, lines.length * lh - (h - 6));
    scroll = Math.max(0, Math.min(scroll, maxScroll));
    g.set_source_rgba(0.85, 0.87, 0.91, 1);
    for (var i = 0; i < lines.length; ++i) {
        var y = 3 + (i + 1) * lh - size * 0.3 - scroll;
        if (y < 0 || y > h + lh) continue;
        g.move_to(4, y);
        g.show_text(lines[i]);
    }
}

function onclick(x, y) { lastY = y; }
function ondrag(x, y, but) {
    if (!but) return;
    scroll += lastY - y;
    lastY = y;
    mgraphics.redraw();
}
function onresize() { mgraphics.redraw(); }
