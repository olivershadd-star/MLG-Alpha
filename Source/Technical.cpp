#include "Technical.h"

#include <algorithm>
#include <cmath>
#include <cstring>

namespace mlg
{
namespace
{
const std::vector<std::vector<int>>& scales()
{
    static const std::vector<std::vector<int>> t {
        { 0, 2, 4, 5, 7, 9, 11 }, { 0, 2, 3, 5, 7, 8, 10 }, { 0, 2, 3, 5, 7, 9, 10 }, { 0, 1, 3, 5, 7, 8, 10 },
        { 0, 2, 4, 6, 7, 9, 11 }, { 0, 2, 4, 5, 7, 9, 10 }, { 0, 1, 3, 5, 6, 8, 10 }, { 0, 2, 3, 5, 7, 8, 11 },
        { 0, 2, 3, 5, 7, 9, 11 }, { 0, 2, 4, 7, 9 }, { 0, 3, 5, 7, 10 }, { 0, 3, 5, 6, 7, 10 },
        { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 } };
    return t;
}

juce::String gridName (int stepsPerBar)
{
    switch (stepsPerBar)
    {
        case 4:  return fr ("noires (1/4)");
        case 8:  return fr ("croches (1/8)");
        case 12: return fr ("croches de triolet (1/8T)");
        case 16: return fr ("doubles croches (1/16)");
        case 24: return fr ("doubles croches de triolet (1/16T)");
        case 32: return fr ("triples croches (1/32)");
        default: return juce::String (stepsPerBar) + fr (" pas par mesure");
    }
}

int divisionFor (int stepsPerBar)
{
    switch (stepsPerBar) { case 4: return 0; case 8: return 1; case 12: return 2; case 24: return 4; case 32: return 5; default: return 3; }
}

const char* drumName (int n)
{
    switch (n)
    {
        case 36: return "kick"; case 37: return "rimshot"; case 38: return "caisse claire"; case 39: return "clap";
        case 42: return "charleston fermé"; case 46: return "charleston ouvert"; case 45: return "tom grave";
        case 47: return "tom médium"; case 50: return "tom aigu"; case 51: return "ride"; case 56: return "cloche";
        case 70: return "shaker"; case 75: return "claves"; default: return "percussion";
    }
}

juce::String num (double v, int dec = 1)
{
    return juce::String (v, dec).replace (".", ",").trimCharactersAtEnd ("0").trimCharactersAtEnd (",");
}
} // namespace

int parseNoteName (const juce::String& tokIn)
{
    auto t = tokIn.toLowerCase().trim();
    static const std::pair<const char*, int> names[] = { { "do", 0 }, { "re", 2 }, { "mi", 4 }, { "fa", 5 }, { "sol", 7 },
                                                         { "la", 9 }, { "si", 11 }, { "c", 0 }, { "d", 2 }, { "e", 4 },
                                                         { "f", 5 }, { "g", 7 }, { "a", 9 }, { "b", 11 } };
    for (auto& [n, v] : names)
    {
        if (! t.startsWith (n)) continue;
        auto rest = t.substring ((int) strlen (n));
        int pc = v;
        if (rest.startsWith ("#")) { ++pc; rest = rest.substring (1); }
        else if (rest.startsWith ("b") && rest.length() > 1) { --pc; rest = rest.substring (1); }
        if (rest.isEmpty() || ! rest.containsOnly ("-0123456789")) return -1;
        return juce::jlimit (0, 127, (rest.getIntValue() + 2) * 12 + pc);
    }
    return -1;
}

juce::String describe (const Clip& c, const LineInfo& info, int root)
{
    juce::String r;
    const int bars = juce::jmax (1, (int) std::round (c.lengthPpq / 4.0));
    const int totalSteps = juce::jmax (1, (int) std::round (c.lengthPpq / c.stepPpq));

    r << info.source;
    if (info.name.isNotEmpty()) r << fr (" : ") << info.name;
    r << "\n";
    if (info.role >= 0)
        r << roleNames()[info.role] << fr (" · ") << familyNames()[juce::jmax (0, info.family)] << "\n";
    if (! info.tags.empty())
    {
        juce::StringArray t;
        for (auto& [k, conf] : info.tags) t.add (tagLabel (tagKeys()[k]) + " " + juce::String (conf) + "/9");
        r << fr ("Étiquettes : ") << t.joinIntoString (", ") << "\n";
    }
    r << "\n";

    r << fr ("Longueur : ") << bars << fr (" mesure") << (bars > 1 ? "s" : "") << fr (" en 4/4, grille en ")
      << gridName (c.stepsPerBar) << " = " << totalSteps << fr (" pas.\n");

    if (c.notes.empty()) return r + fr ("Aucune note.");

    // attaques
    std::vector<double> starts;
    for (auto& n : c.notes)
        if (starts.empty() || std::abs (n.start - starts.back()) > 1e-6) starts.push_back (n.start);
    const double density = (double) starts.size() / totalSteps;
    r << fr ("Notes : ") << (int) c.notes.size() << fr (" notes, ") << (int) starts.size() << fr (" attaques, densité ")
      << juce::roundToInt (density * 100) << fr (" % (environ ") << num ((double) starts.size() / bars) << fr (" par mesure).\n");

    // placement
    int onBeat = 0, off8 = 0, other = 0, offGrid = 0;
    for (auto t : starts)
    {
        const double inBeat = std::fmod (t, 1.0);
        const double steps = t / c.stepPpq;
        if (std::abs (steps - std::round (steps)) > 0.02) ++offGrid;
        if (inBeat < 1e-3 || inBeat > 1 - 1e-3) ++onBeat;
        else if (std::abs (inBeat - 0.5) < 1e-3) ++off8;
        else ++other;
    }
    const double n = (double) starts.size();
    r << fr ("Placement : ") << juce::roundToInt (100 * onBeat / n) << fr (" % sur les temps, ")
      << juce::roundToInt (100 * off8 / n) << fr (" % sur le « et » (croche à contretemps), ")
      << juce::roundToInt (100 * other / n) << fr (" % entre les deux") << (c.stepsPerBar % 3 == 0 ? fr (" (triolets)") : fr (" (syncopes)"));
    if (offGrid > 0) r << fr (", ") << offGrid << fr (" notes hors grille (swing, ratchets ou demi-pas)");
    r << ".\n";

    // durées
    double lmin = 1e9, lmax = 0, lsum = 0;
    for (auto& x : c.notes) { const double l = x.length / c.stepPpq; lmin = juce::jmin (lmin, l); lmax = juce::jmax (lmax, l); lsum += l; }
    const double lmean = lsum / (double) c.notes.size();
    r << fr ("Durées : de ") << num (lmin, 2) << fr (" à ") << num (lmax, 2) << fr (" pas, moyenne ") << num (lmean, 2)
      << (lmean < 0.6 ? fr (" : notes courtes, piquées (staccato).") : lmean > 3 ? fr (" : notes longues, tenues.") : fr (" pas."));
    int overlaps = 0;
    for (size_t i = 1; i < c.notes.size(); ++i)
        if (c.notes[i - 1].start + c.notes[i - 1].length > c.notes[i].start + 1e-3 && c.notes[i - 1].start < c.notes[i].start) ++overlaps;
    if (overlaps > 0) r << fr (" ") << overlaps << fr (" notes se chevauchent (legato : glide sur un synthé mono).");
    r << "\n";

    // vélocités
    int vmin = 127, vmax = 0;
    for (auto& x : c.notes) { vmin = juce::jmin (vmin, x.velocity); vmax = juce::jmax (vmax, x.velocity); }
    r << fr ("Vélocités : ") << vmin << fr (" à ") << vmax
      << (vmax - vmin < 8 ? fr (" : toutes pareilles, jeu de machine.") : vmax - vmin > 40 ? fr (" : accents très marqués, ghost notes.") : fr (" : accents légers."))
      << "\n";

    // polyphonie, ratchets, répétition
    int poly = 1;
    for (size_t i = 0; i < c.notes.size();)
    {
        size_t j = i;
        while (j < c.notes.size() && std::abs (c.notes[j].start - c.notes[i].start) < 1e-6) ++j;
        poly = juce::jmax (poly, (int) (j - i));
        i = j;
    }
    if (poly > 1 && ! c.drums) r << fr ("Polyphonie : jusqu'à ") << poly << fr (" notes ensemble (accords).\n");

    if (c.drums)
    {
        std::map<int, int> count;
        for (auto& x : c.notes) count[x.pitch]++;
        juce::StringArray parts;
        for (auto& [p, k] : count) parts.add (juce::String::fromUTF8 (drumName (p)) + " (" + juce::String (p) + ") x" + juce::String (k));
        r << fr ("Instruments : ") << parts.joinIntoString (", ") << ".\n";
    }
    else
    {
        int lo = 127, hi = 0;
        std::set<int> pcs;
        for (auto& x : c.notes) { lo = juce::jmin (lo, x.pitch); hi = juce::jmax (hi, x.pitch); pcs.insert (((x.pitch - root) % 12 + 12) % 12); }
        juce::StringArray pn;
        for (auto pc : pcs) pn.add (rootNames()[(pc + root) % 12]);
        r << fr ("Hauteurs : de ") << noteName (lo) << fr (" à ") << noteName (hi) << " (" << hi - lo << fr (" demi-tons), ")
          << (int) pcs.size() << fr (" notes différentes : ") << pn.joinIntoString (" ");
        if (pcs.count (3) && ! pcs.count (4)) r << fr (" : couleur mineure");
        else if (pcs.count (4) && ! pcs.count (3)) r << fr (" : couleur majeure");
        if (pcs.count (1) || pcs.count (6)) r << fr (", avec des notes de tension (seconde mineure, triton)");
        r << ".\n";

        if (poly == 1)
        {
            double sum = 0; int big = 0, k = 0;
            for (size_t i = 1; i < c.notes.size(); ++i)
            {
                const int d = std::abs (c.notes[i].pitch - c.notes[i - 1].pitch);
                sum += d; big = juce::jmax (big, d); ++k;
            }
            if (k > 0)
                r << fr ("Intervalles : écart moyen ") << num (sum / k) << fr (" demi-tons, plus grand saut ") << big
                  << (big == 12 ? fr (" (une octave)") : big > 12 ? fr (" (plus d'une octave)") : "") << ".\n";
        }
    }

    // répétition entre mesures
    if (bars > 1)
    {
        auto barOf = [&] (int b)
        {
            std::vector<std::pair<int, int>> v;
            for (auto& x : c.notes)
                if (x.start >= b * 4.0 - 1e-6 && x.start < (b + 1) * 4.0 - 1e-6)
                    v.push_back ({ juce::roundToInt ((x.start - b * 4.0) * 48), x.pitch });
            return v;
        };
        int same = 0;
        const auto first = barOf (0);
        for (int b = 1; b < bars; ++b) same += barOf (b) == first ? 1 : 0;
        r << (same == bars - 1 ? fr ("Structure : la même mesure répétée.\n")
              : same == 0 ? fr ("Structure : chaque mesure varie (phrase de ") + juce::String (bars) + fr (" mesures).\n")
                          : fr ("Structure : ") + juce::String (same) + fr (" mesures reprennent la première, les autres varient.\n"));
    }

    r << fr ("\nCommandes possibles ici : « 2 mesures », « division 1/16 », « triolets », « 12 pas », « densité 40 », "
             "« euclidien 5 », « swing 30 », « tonique la », « gamme dorien », « notes C1 à C3 », « legato », "
             "« vélocité 80 120 », « durée 50 100 », « écart 4 », « génère », « mute ».");
    return r;
}

std::map<juce::String, float> equivalentSettings (const Clip& c, int root)
{
    std::map<juce::String, float> s;
    const int total = juce::jlimit (1, kMaxSteps, (int) std::round (c.lengthPpq / c.stepPpq));
    s["division"] = (float) divisionFor (c.stepsPerBar);
    s["steps"] = (float) total;
    s["rhythmMode"] = 0.0f;
    s["swing"] = 0.0f;
    s["accent"] = 0.0f;
    if (c.notes.empty()) return s;

    std::set<int> onSteps;
    for (auto& n : c.notes) onSteps.insert ((int) std::floor (n.start / c.stepPpq + 1e-6));
    s["density"] = juce::jlimit (0.0f, 100.0f, 100.0f * (float) onSteps.size() / (float) total);

    std::vector<double> lens;
    int vmin = 127, vmax = 1, lo = 127, hi = 0, jump = 0;
    std::set<int> pcs;
    bool overlap = false;
    for (size_t i = 0; i < c.notes.size(); ++i)
    {
        const auto& n = c.notes[i];
        lens.push_back (n.length / c.stepPpq * 100.0);
        vmin = juce::jmin (vmin, n.velocity); vmax = juce::jmax (vmax, n.velocity);
        lo = juce::jmin (lo, n.pitch); hi = juce::jmax (hi, n.pitch);
        pcs.insert (((n.pitch - root) % 12 + 12) % 12);
        if (i > 0)
        {
            jump = juce::jmax (jump, std::abs (n.pitch - c.notes[i - 1].pitch));
            if (c.notes[i - 1].start + c.notes[i - 1].length > n.start + 1e-3 && c.notes[i - 1].start < n.start) overlap = true;
        }
    }
    std::sort (lens.begin(), lens.end());
    s["lenMin"] = (float) juce::jlimit (5.0, 400.0, lens[lens.size() / 10]);
    s["lenMax"] = (float) juce::jlimit (5.0, 400.0, lens[lens.size() * 9 / 10]);
    s["velMin"] = (float) vmin;
    s["velMax"] = (float) vmax;
    s["legato"] = overlap ? 1.0f : 0.0f;

    if (! c.drums)
    {
        s["lowNote"] = (float) juce::jlimit (24, 108, lo);
        s["highNote"] = (float) juce::jlimit (24, 108, hi);
        s["maxJump"] = (float) juce::jlimit (0, 12, (jump + 1) / 2);
        static const int order[] = { 1, 0, 2, 3, 7, 5, 4, 8, 6, 11, 12 };
        for (int sc : order)
        {
            const auto& v = scales()[(size_t) sc];
            bool ok = true;
            for (int pc : pcs) ok = ok && std::find (v.begin(), v.end(), pc) != v.end();
            if (ok) { s["scale"] = (float) sc; break; }
        }
    }
    return s;
}

Command parseTechnical (const juce::String& text, int currentDivision)
{
    Command cmd;
    auto toks = juce::StringArray::fromTokens (Translator::normalise (text).replace ("%", " "), " ", "");
    toks.removeEmptyStrings();
    static const int stepsPerBarOf[] = { 4, 8, 12, 16, 24, 32 };
    int division = currentDivision;
    auto isNum = [] (const juce::String& t) { return t.isNotEmpty() && t.containsOnly ("0123456789"); };

    static const std::map<juce::String, int> scaleWords {
        { "majeur", 0 }, { "majeure", 0 }, { "mineur", 1 }, { "mineure", 1 }, { "naturel", 1 }, { "dorien", 2 }, { "phrygien", 3 },
        { "lydien", 4 }, { "mixolydien", 5 }, { "locrien", 6 }, { "harmonique", 7 }, { "melodique", 8 }, { "blues", 11 },
        { "chromatique", 12 } };
    static const std::map<juce::String, int> divWords {
        { "1/4", 0 }, { "noires", 0 }, { "1/8", 1 }, { "croches", 1 }, { "1/8t", 2 }, { "1/16", 3 }, { "doubles", 3 },
        { "1/16t", 4 }, { "1/32", 5 }, { "triples", 5 } };

    for (int i = 0; i < toks.size(); ++i)
    {
        const auto& t = toks[i];
        const auto next = i + 1 < toks.size() ? toks[i + 1] : juce::String();
        const auto next2 = i + 2 < toks.size() ? toks[i + 2] : juce::String();

        if (isNum (t) && next.startsWith ("mesure"))
        {
            const int bars = juce::jlimit (1, 8, t.getIntValue());
            cmd.params["steps"] = (float) juce::jmin (kMaxSteps, bars * stepsPerBarOf[division]);
            cmd.done.add (juce::String (bars) + " mesure" + (bars > 1 ? "s" : ""));
            ++i;
        }
        else if (isNum (t) && next == "pas")
        {
            cmd.params["steps"] = (float) juce::jlimit (1, kMaxSteps, t.getIntValue());
            cmd.done.add (t + " pas"); ++i;
        }
        else if (divWords.count (t) && ! (t == "doubles" && next != "croches") && ! (t == "triples" && next != "croches"))
        {
            division = divWords.at (t);
            if (t == "doubles" || t == "triples") ++i;
            if (next == "t" || next.startsWith ("triolet")) { division = division == 1 ? 2 : division == 3 ? 4 : division; ++i; }
            cmd.params["division"] = (float) division;
            cmd.done.add (fr ("division ") + divisionNames()[division]);
        }
        else if (t == "division" || t == "grille" || t == "de" || t == "et" || t == "en" || t == "a" || t == "sur") {}
        else if (t.startsWith ("triolet") || t == "ternaire")
        {
            division = division <= 1 ? 2 : 4;
            cmd.params["division"] = (float) division;
            cmd.done.add (fr ("division ") + divisionNames()[division]);
        }
        else if (t == "binaire")
        {
            division = division == 2 ? 1 : 3;
            cmd.params["division"] = (float) division;
            cmd.done.add (fr ("division ") + divisionNames()[division]);
        }
        else if ((t == "densite" || t == "density") && isNum (next))
        {
            cmd.params["density"] = (float) juce::jlimit (0, 100, next.getIntValue()); cmd.params["rhythmMode"] = 0.0f;
            cmd.done.add (fr ("densité ") + next + " %"); ++i;
        }
        else if (t == "swing" && isNum (next))
        {
            cmd.params["swing"] = (float) juce::jlimit (0, 100, next.getIntValue()); cmd.done.add ("swing " + next + " %"); ++i;
        }
        else if (t.startsWith ("euclid"))
        {
            cmd.params["rhythmMode"] = 1.0f;
            juce::String d = fr ("rythme euclidien");
            if (isNum (next)) { cmd.params["pulses"] = (float) next.getIntValue(); d << " " << next << fr (" impulsions"); ++i;
                if (toks[i + 1 < toks.size() ? i + 1 : i] == "sur" && isNum (i + 2 < toks.size() ? toks[i + 2] : juce::String()))
                { cmd.params["steps"] = (float) juce::jlimit (1, kMaxSteps, toks[i + 2].getIntValue()); d << " sur " << toks[i + 2]; i += 2; } }
            cmd.done.add (d);
        }
        else if (t == "aleatoire" || t == "hasard") { cmd.params["rhythmMode"] = 0.0f; cmd.done.add (fr ("rythme aléatoire")); }
        else if (t == "rotation" && isNum (next)) { cmd.params["rotation"] = (float) next.getIntValue(); cmd.done.add ("rotation " + next); ++i; }
        else if (t == "impulsions" && isNum (next)) { cmd.params["pulses"] = (float) next.getIntValue(); cmd.params["rhythmMode"] = 1.0f; cmd.done.add (next + " impulsions"); ++i; }
        else if (t == "tonique" || t == "tonalite" || t == "cle")
        {
            const int n = parseNoteName (next + "0");
            if (n >= 0)
            {
                int pc = n % 12;
                int skip = 1;
                if (next2 == "diese") { pc = (pc + 1) % 12; ++skip; }
                if (next2 == "bemol") { pc = (pc + 11) % 12; ++skip; }
                cmd.params["root"] = (float) pc; cmd.done.add (fr ("tonique ") + rootNames()[pc]); i += skip;
            }
        }
        else if (t == "gamme" || t == "mode") {}
        else if (t == "penta" || t == "pentatonique")
        {
            const bool maj = next.startsWith ("maj");
            cmd.params["scale"] = maj ? 9.0f : 10.0f; cmd.done.add (scaleNames()[maj ? 9 : 10]); if (next.startsWith ("maj") || next.startsWith ("min")) ++i;
        }
        else if (scaleWords.count (t))
        {
            int sc = scaleWords.at (t);
            if (t.startsWith ("mineur") && next == "harmonique") { sc = 7; ++i; }
            else if (t.startsWith ("mineur") && next == "melodique") { sc = 8; ++i; }
            else if (t.startsWith ("mineur") && next == "naturel") ++i;
            cmd.params["scale"] = (float) sc; cmd.done.add (fr ("gamme ") + scaleNames()[sc]);
        }
        else if (t == "notes" || t == "registre" || t == "tessiture") {}
        else if (parseNoteName (t) >= 0 && i + 1 < toks.size())
        {
            int j = i + 1;
            if (toks[j] == "a" || toks[j] == "au" || toks[j] == "jusqu") ++j;
            const int a = parseNoteName (t), b = j < toks.size() ? parseNoteName (toks[j]) : -1;
            if (b >= 0)
            {
                cmd.params["lowNote"] = (float) juce::jlimit (24, 108, juce::jmin (a, b));
                cmd.params["highNote"] = (float) juce::jlimit (24, 108, juce::jmax (a, b));
                cmd.done.add (fr ("notes de ") + noteName (juce::jmin (a, b)) + fr (" à ") + noteName (juce::jmax (a, b)));
                i = j;
            }
            else cmd.unknown.add (t);
        }
        else if (t == "legato" || t == "lie" || t == "liees" || t == "glide") { cmd.params["legato"] = 1.0f; cmd.done.add ("legato"); }
        else if (t == "staccato" || t == "detache") { cmd.params["legato"] = 0.0f; cmd.done.add ("sans legato"); }
        else if (t == "sans" && next == "legato") { cmd.params["legato"] = 0.0f; cmd.done.add ("sans legato"); ++i; }
        else if (t.startsWith ("velocite") && isNum (next))
        {
            int j = i + 2; if (j < toks.size() && toks[j] == "a") ++j;
            const int a = next.getIntValue(), b = (j < toks.size() && isNum (toks[j])) ? toks[j].getIntValue() : a;
            cmd.params["velMin"] = (float) juce::jlimit (1, 127, juce::jmin (a, b));
            cmd.params["velMax"] = (float) juce::jlimit (1, 127, juce::jmax (a, b));
            cmd.done.add (fr ("vélocité ") + juce::String (juce::jmin (a, b)) + fr (" à ") + juce::String (juce::jmax (a, b)));
            i = (j < toks.size() && isNum (toks[j])) ? j : i + 1;
        }
        else if (t == "duree" && isNum (next))
        {
            int j = i + 2; if (j < toks.size() && toks[j] == "a") ++j;
            const int a = next.getIntValue(), b = (j < toks.size() && isNum (toks[j])) ? toks[j].getIntValue() : a;
            cmd.params["lenMin"] = (float) juce::jlimit (5, 400, juce::jmin (a, b));
            cmd.params["lenMax"] = (float) juce::jlimit (5, 400, juce::jmax (a, b));
            cmd.done.add (fr ("durée ") + juce::String (juce::jmin (a, b)) + fr (" à ") + juce::String (juce::jmax (a, b)) + " %");
            i = (j < toks.size() && isNum (toks[j])) ? j : i + 1;
        }
        else if (t == "ecart" && isNum (next)) { cmd.params["maxJump"] = (float) juce::jlimit (0, 12, next.getIntValue()); cmd.done.add (fr ("écart ") + next); ++i; }
        else if (t == "accent" && isNum (next)) { cmd.params["accent"] = (float) juce::jlimit (0, 40, next.getIntValue()); cmd.done.add ("accent " + next); ++i; }
        else if (t.startsWith ("gener") || t == "nouvelle" || t == "nouveau") { cmd.generate = true; cmd.done.add (fr ("nouvelle ligne")); }
        else if (t.startsWith ("mute") || t.startsWith ("variation") || t == "varie") { cmd.mutate = true; cmd.done.add ("variation"); }
        else if (! isNum (t)) cmd.unknown.add (t);
    }
    return cmd;
}
} // namespace mlg
