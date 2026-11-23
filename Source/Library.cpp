#include "Library.h"
#include "BinaryData.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <string>

namespace mlg
{
// ---------------------------------------------------------------------------
// Noms

const juce::StringArray& roleKeys()
{
    static const juce::StringArray k { "kick", "drums", "perc", "bass", "lead", "chords", "pad" };
    return k;
}

const juce::StringArray& roleNames()
{
    static const juce::StringArray k { "Kick", "Batterie", "Percussion", "Basse", fr ("Mélodie / lead"), "Accords", "Nappe" };
    return k;
}

const juce::StringArray& familyKeys()
{
    static const juce::StringArray k { "techno", "techno-dure", "minimal-dub", "house", "acid", "ebm", "rock-indus",
                                       "electro-breaks", "trance-rave", "ambient", "idm", "melodique", "hors-cible" };
    return k;
}

const juce::StringArray& familyNames()
{
    static const juce::StringArray k { "Techno", "Techno dure / indus", "Minimal / dub", "House / tech house", "Acid",
                                       fr ("EBM / électro-indus"), "Rock et noise indus", "Electro / breaks", "Trance / rave",
                                       "Ambient / textures", "IDM / Boards of Canada", fr ("Électronique mélodique"), "Hors cible" };
    return k;
}

int familyIndex (const juce::String& key) { return juce::jmax (0, familyKeys().indexOf (key)); }

const juce::StringArray& tagKeys()
{
    static const juce::StringArray k = []
    {
        const char* words =
            "rectiligne hypnotique roulant martelé haché saccadé syncopé bancal boiteux cassé "
            "régulier mécanique galopant sautillant lancinant obsédant répétitif pulsé chaloupé groovy "
            "calme posé lent tendu nerveux agressif brutal explosif frénétique puissant lourd léger retenu montant "
            "sombre mélancolique triste déprimé nostalgique inquiétant menaçant angoissant oppressant glacial "
            "froid mystérieux solennel martial rêveur apaisé lumineux euphorique "
            "mineur majeur dissonant consonant tendu-h suspendu modal exotique chromatique atonal ouvert épuré "
            "dense chargé rempli aéré clairsemé minimal dépouillé vide ample planant flottant suspendu-t étiré serré "
            "grave sub médium aigu profond perché "
            "gras épais sec claquant distordu saturé grinçant métallique étouffé feutré sale crade rugueux "
            "chaud brillant acide";
        return juce::StringArray::fromTokens (juce::String::fromUTF8 (words), " ", "");
    }();
    return k;
}

juce::String tagLabel (const juce::String& key)
{
    if (key == "tendu-h") return "tendu (harmonie)";
    if (key == "suspendu-t") return "suspendu (temps)";
    return key;
}

// ---------------------------------------------------------------------------
// Query / traducteur

juce::String Query::summary() const
{
    if (understood.isEmpty()) return fr ("Rien de reconnu : tirage au hasard dans tout ce qui est en cible.");
    auto s = fr ("Compris : ") + understood.joinIntoString (fr (" · "));
    if (! unknown.isEmpty())
        s << fr ("   (mots inconnus : ") << unknown.joinIntoString (", ") << ")";
    return s;
}

juce::String Translator::normalise (const juce::String& in)
{
    auto s = in.toLowerCase();
    static const std::pair<const char*, const char*> rep[] = {
        { "à", "a" }, { "â", "a" }, { "ä", "a" }, { "é", "e" }, { "è", "e" }, { "ê", "e" }, { "ë", "e" },
        { "î", "i" }, { "ï", "i" }, { "ô", "o" }, { "ö", "o" }, { "ù", "u" }, { "û", "u" }, { "ü", "u" },
        { "ç", "c" }, { "œ", "oe" }, { "À", "a" }, { "Â", "a" }, { "É", "e" }, { "È", "e" }, { "Ê", "e" }, { "Ë", "e" },
        { "Î", "i" }, { "Ï", "i" }, { "Ô", "o" }, { "Ù", "u" }, { "Û", "u" }, { "Ç", "c" }, { "Œ", "oe" }, { "æ", "ae" }, { "’", " " }, { "'", " " }, { "-", " " } };
    for (auto& r : rep)
        s = s.replace (juce::String::fromUTF8 (r.first), r.second);
    juce::String out;
    for (auto c : s)
        out += (juce::CharacterFunctions::isLetterOrDigit (c) || c == '/' || c == '.') ? juce::String::charToString (c) : " ";
    return [&] { auto a = juce::StringArray::fromTokens (out, " ", ""); a.removeEmptyStrings(); return a.joinIntoString (" "); }();
}

void Translator::load (const juce::String& text)
{
    phrases.clear();
    maxWords = 1;
    for (auto line : juce::StringArray::fromLines (text))
    {
        line = line.trim();
        if (line.isEmpty() || line.startsWith ("#") || ! line.contains ("=")) continue;
        const auto head = line.upToFirstOccurrenceOf ("=", false, false).trim();
        const auto body = line.fromFirstOccurrenceOf ("=", false, false);
        const auto kind = head.upToFirstOccurrenceOf (" ", false, false).trim();
        const auto targets = juce::StringArray::fromTokens (head.fromFirstOccurrenceOf (" ", false, false).trim(), ",", "");
        for (auto form : juce::StringArray::fromTokens (body, ",", ""))
        {
            const auto key = normalise (form);
            if (key.isEmpty()) continue;
            maxWords = juce::jmax (maxWords, key.retainCharacters (" ").length() + 1);
            auto& v = phrases[key];
            if (targets.isEmpty())
                v.push_back ({ kind, {} });
            for (auto t : targets)
                if (std::find (v.begin(), v.end(), std::make_pair (kind, t.trim())) == v.end())
                    v.push_back ({ kind, t.trim() });
        }
    }
}

Query Translator::parse (const juce::String& text) const
{
    Query q;
    auto toks = juce::StringArray::fromTokens (normalise (text), " ", "");
    toks.removeEmptyStrings();
    static const juce::StringArray stop { "de", "la", "le", "les", "un", "une", "des", "et", "avec", "qui", "en", "du", "au",
                                          "aux", "pour", "truc", "quelque", "chose", "me", "moi", "je", "veux", "voudrais",
                                          "genre", "style", "type", "fais", "donne", "mets", "fait", "ca", "cette", "ce",
                                          "son", "sa", "ses", "mon", "ma", "a", "y", "il", "faut", "comme", "sur", "dans",
                                          "ou", "mais", "plus", "moins", "bon", "tout", "trucs", "facon", "of", "the", "and" };
    static const std::map<juce::String, int> numbers { { "une", 1 }, { "un", 1 }, { "deux", 2 }, { "trois", 3 },
                                                        { "quatre", 4 }, { "cinq", 5 }, { "six", 6 }, { "sept", 7 }, { "huit", 8 } };
    float mod = 1.0f;
    bool neg = false;
    const auto& tk = tagKeys();

    for (int i = 0; i < toks.size();)
    {
        // « 2 mesures », « deux mesures »
        if (i + 1 < toks.size() && toks[i + 1].startsWith ("mesure"))
        {
            int n = toks[i].getIntValue();
            if (n == 0 && numbers.count (toks[i])) n = numbers.at (toks[i]);
            if (n > 0)
            {
                q.bars = juce::jlimit (1, 8, n);
                q.understood.add (juce::String (q.bars) + " mesure" + (q.bars > 1 ? "s" : ""));
                i += 2;
                continue;
            }
        }

        int len = juce::jmin (maxWords, toks.size() - i);
        const std::vector<std::pair<juce::String, juce::String>>* hit = nullptr;
        juce::String phrase;
        for (; len > 0; --len)
        {
            juce::StringArray part;
            for (int k = 0; k < len; ++k) part.add (toks[i + k]);
            phrase = part.joinIntoString (" ");
            auto it = phrases.find (phrase);
            if (it != phrases.end()) { hit = &it->second; break; }
        }

        if (hit == nullptr)
        {
            if (! stop.contains (toks[i]) && toks[i].length() > 2 && ! toks[i].containsOnly ("0123456789"))
                q.unknown.addIfNotAlreadyThere (toks[i]);
            ++i;
            continue;
        }
        i += len;

        bool consumed = false;
        juce::StringArray what;
        for (const auto& [kind, target] : *hit)
        {
            if (kind == "mod") mod = (float) target.getDoubleValue();
            else if (kind == "neg") neg = true;
            else if (kind == "tag")
            {
                const int t = tk.indexOf (target);
                if (t < 0) continue;
                q.tags[t] += (neg ? -1.0f : 1.0f) * mod;
                what.addIfNotAlreadyThere ((neg ? "pas " : "") + tagLabel (target));
                consumed = true;
            }
            else if (kind == "family" && ! neg)
            {
                q.families.insert (familyIndex (target));
                what.addIfNotAlreadyThere (familyNames()[familyIndex (target)]);
                consumed = true;
            }
            else if (kind == "role" && ! neg)
            {
                const int r = roleKeys().indexOf (target);
                if (r >= 0) { q.roles.insert (r); what.addIfNotAlreadyThere (roleNames()[r].toLowerCase()); }
                consumed = true;
            }
            else if (kind == "tech")
            {
                if (target == "triplet") { q.triplet = true; what.add ("triolets"); }
                if (target == "binary") { q.binary = true; what.add ("binaire"); }
                consumed = true;
            }
        }
        if (consumed)
        {
            for (auto w : what)
                q.understood.add (std::abs (mod - 1.0f) > 0.01f && ! w.startsWith ("pas ")
                                      ? (mod > 1.0f ? fr ("très ") : fr ("un peu ")) + w : w);
            mod = 1.0f;
            neg = false;
        }
    }
    return q;
}

// ---------------------------------------------------------------------------
// Chargement

namespace
{
juce::String gunzip (const void* data, int size)
{
    juce::MemoryInputStream raw (data, (size_t) size, false);
    juce::GZIPDecompressorInputStream gz (&raw, false, juce::GZIPDecompressorInputStream::gzipFormat);
    return gz.readEntireStreamAsString();
}

juce::uint64 fnv (juce::uint64 h, juce::int64 v)
{
    for (int b = 0; b < 8; ++b) { h ^= (juce::uint64) ((v >> (b * 8)) & 0xff); h *= 1099511628211ull; }
    return h;
}

// Empreinte commune : (temps en 1/12 de pas, hauteur relative), période minimale, octave ramenée.
juce::uint64 fingerprintEvents (std::vector<std::pair<int, int>> ev, int stepsPerBar, int bars, bool drums)
{
    if (ev.empty()) return 0;
    std::sort (ev.begin(), ev.end());
    if (! drums)
    {
        int lo = ev.front().second;
        for (auto& e : ev) lo = juce::jmin (lo, e.second);
        const int shift = (int) std::floor (lo / 12.0) * 12;
        for (auto& e : ev) e.second -= shift;
    }
    const int bar = stepsPerBar * 12;
    int period = bars;
    for (int b = 1; b < bars; ++b)
    {
        if (bars % b) continue;
        std::vector<std::pair<int, int>> first;
        for (auto& e : ev) if (e.first < b * bar) first.push_back (e);
        if (first.size() * (size_t) (bars / b) != ev.size()) continue;
        bool same = true;
        for (auto& e : ev)
            if (! std::binary_search (first.begin(), first.end(), std::make_pair (e.first % (b * bar), e.second))) { same = false; break; }
        if (same) { period = b; break; }
    }
    juce::uint64 h = 1469598103934665603ull;
    h = fnv (h, stepsPerBar); h = fnv (h, drums ? 1 : 0); h = fnv (h, period);
    for (auto& e : ev)
        if (e.first < period * bar) { h = fnv (h, e.first); h = fnv (h, e.second); }
    return h;
}
} // namespace

class LoaderThread : public juce::Thread
{
public:
    explicit LoaderThread (std::function<void()> f) : Thread ("MLG library"), fn (std::move (f)) {}
    void run() override { fn(); }
private:
    std::function<void()> fn;
};

Library::Library()
{
    loader = std::make_unique<LoaderThread> ([this] { loadAll(); });
    loader->startThread();
}

Library::~Library()
{
    if (loader) loader->stopThread (10000);
}

juce::File Library::dataFolder()
{
    auto d = juce::File::getSpecialLocation (juce::File::userApplicationDataDirectory).getChildFile ("ANKS Labs").getChildFile ("MLG Alpha");
    d.createDirectory();
    return d;
}

void Library::loadAll()
{
    dict.load (juce::String::fromUTF8 (BinaryData::mlg_dictionary_txt, BinaryData::mlg_dictionary_txtSize));
    parseCompiled (gunzip (BinaryData::mlg_library_txt_gz, BinaryData::mlg_library_txt_gzSize), false);
    const auto perso = dataFolder().getChildFile ("perso.txt");
    if (perso.existsAsFile())
        parseCompiled (perso.loadFileAsString(), true);
    loadLearning();
    ready.store (true);
}

void Library::index (LibPattern& p)
{
    std::vector<std::pair<int, int>> ev;
    float sum = 0;
    for (auto& e : p.events) { ev.push_back ({ e.t, e.p }); sum += (float) e.p; }
    p.meanPitch = p.events.empty() ? 0.0f : sum / (float) p.events.size();
    p.fingerprint = fingerprintEvents (ev, p.steps, p.bars, p.drums);
}

void Library::parseCompiled (const juce::String& text, bool personal)
{
    const std::string s = text.toStdString();
    const auto& tk = tagKeys();
    std::map<std::string, int> tagIdx;
    for (int i = 0; i < tk.size(); ++i) tagIdx[tk[i].toStdString()] = i;

    size_t pos = 0;
    while (pos < s.size())
    {
        size_t end = s.find ('\n', pos);
        if (end == std::string::npos) end = s.size();
        if (end > pos && s[pos] != '#')
        {
            std::vector<std::string> f;
            size_t a = pos;
            for (size_t b = pos; b <= end; ++b)
                if (b == end || s[b] == '|') { f.emplace_back (s, a, b - a); a = b + 1; }
            if (f.size() >= 11)
            {
                LibPattern p;
                p.id = juce::String::fromUTF8 (f[0].c_str());
                p.role = juce::jmax (0, roleKeys().indexOf (f[1]));
                p.family = familyIndex (f[2]);
                p.bars = juce::jlimit (1, 16, std::atoi (f[3].c_str()));
                p.steps = juce::jlimit (1, 64, std::atoi (f[4].c_str()));
                p.drums = f[6] == "1";
                p.name = juce::String::fromUTF8 (f[9].c_str());
                p.personal = personal;
                if (f.size() > 11) p.words = juce::String::fromUTF8 (f[11].c_str());
                if (f.size() > 12) p.settings = juce::String::fromUTF8 (f[12].c_str());
                // étiquettes « mot:conf,mot:conf »
                size_t q = 0;
                const auto& t = f[7];
                while (q < t.size())
                {
                    size_t c = t.find (',', q); if (c == std::string::npos) c = t.size();
                    const auto item = t.substr (q, c - q);
                    const auto colon = item.find (':');
                    if (colon != std::string::npos)
                    {
                        auto it = tagIdx.find (item.substr (0, colon));
                        if (it != tagIdx.end()) p.tags.push_back ({ it->second, std::atoi (item.c_str() + colon + 1) });
                    }
                    q = c + 1;
                }
                // notes « t,l,p,v t,l,p,v »
                const char* c = f[10].c_str();
                while (*c)
                {
                    while (*c == ' ') ++c;
                    if (! *c) break;
                    LibEvent e {};
                    char* nx;
                    e.t = (int) std::strtol (c, &nx, 10); c = nx; if (*c == ',') ++c;
                    e.l = (int) std::strtol (c, &nx, 10); c = nx; if (*c == ',') ++c;
                    e.p = (int) std::strtol (c, &nx, 10); c = nx; if (*c == ',') ++c;
                    e.v = (int) std::strtol (c, &nx, 10); c = nx;
                    p.events.push_back (e);
                    while (*c && *c != ' ') ++c;
                }
                if (! p.events.empty())
                {
                    index (p);
                    byFingerprint.emplace (p.fingerprint, (int) all.size());
                    byId[p.id] = (int) all.size();
                    all.push_back (std::move (p));
                }
            }
        }
        pos = end + 1;
    }
}

// ---------------------------------------------------------------------------
// Clip et empreinte

int Library::defaultCentre (int role)
{
    switch (role)
    {
        case roleBass:   return 43;
        case roleLead:   return 64;
        case roleChords: return 62;
        case rolePad:    return 60;
        default:         return 60;
    }
}

Clip Library::toClip (const LibPattern& p, int root, int centre) const
{
    Clip c;
    c.stepsPerBar = p.steps;
    c.stepPpq = 4.0 / p.steps;
    c.lengthPpq = 4.0 * p.bars;
    c.drums = p.drums;
    const int k = (int) std::round ((centre - root - p.meanPitch) / 12.0);
    const int base = root + 12 * k;
    for (auto& e : p.events)
    {
        ClipNote n;
        n.start = e.t / 12.0 * c.stepPpq;
        n.length = juce::jmax (0.02, e.l / 12.0 * c.stepPpq);
        n.pitch = juce::jlimit (0, 127, p.drums ? e.p : base + e.p);
        n.velocity = juce::jlimit (1, 127, e.v);
        if (n.start < c.lengthPpq) c.notes.push_back (n);
    }
    std::sort (c.notes.begin(), c.notes.end(), [] (auto& a, auto& b) { return a.start < b.start; });
    return c;
}

juce::uint64 Library::fingerprintOf (const Clip& c, int root)
{
    std::vector<std::pair<int, int>> ev;
    for (auto& n : c.notes)
        ev.push_back ({ (int) std::round (n.start / c.stepPpq * 12.0), c.drums ? n.pitch : n.pitch - root });
    const int bars = juce::jmax (1, (int) std::round (c.lengthPpq / 4.0));
    return fingerprintEvents (ev, c.stepsPerBar, bars, c.drums);
}

const LibPattern* Library::findDuplicate (juce::uint64 fp) const
{
    auto it = byFingerprint.find (fp);
    return it != byFingerprint.end() ? &all[(size_t) it->second] : nullptr;
}

// ---------------------------------------------------------------------------
// Tirage

float Library::tagDelta (const juce::String& id, int tag) const
{
    auto it = deltas.find (id);
    if (it == deltas.end()) return 0.0f;
    auto jt = it->second.find (tag);
    return jt != it->second.end() ? jt->second : 0.0f;
}

int Library::draw (const Query& q, const Clip* kick, juce::Random& rng)
{
    if (! ready.load()) return -1;
    const juce::ScopedLock sl (lock);

    std::vector<double> kickOnsets;
    if (kick != nullptr)
        for (auto& n : kick->notes)
            if (n.pitch == 36) kickOnsets.push_back (std::fmod (n.start, 1.0));

    bool wantsPositive = false;
    for (auto& [t, w] : q.tags) if (w > 0) wantsPositive = true;
    const int horsCible = familyKeys().indexOf ("hors-cible");

    for (int pass = 0; pass < 4; ++pass)   // style + mots exigés ; style + mots préférés ; sans le style…
    {
        const bool useFamily = pass < 2, strict = (pass % 2) == 0;
        std::vector<std::pair<int, double>> cand;
        double total = 0.0;
        for (int i = 0; i < (int) all.size(); ++i)
        {
            const auto& p = all[(size_t) i];
            if (! q.roles.empty() && ! q.roles.count (p.role)) continue;
            if (useFamily && ! q.families.empty()) { if (! q.families.count (p.family)) continue; }
            else if (p.family == horsCible && ! p.personal && ! q.families.count (horsCible)) continue;
            const bool trip = p.steps == 12 || p.steps == 24;
            if (q.triplet && ! trip) continue;
            if (q.binary && trip) continue;

            double score = 1.0;
            if (q.bars > 0 && p.bars != q.bars) score *= 0.1;

            if (! q.tags.empty())
            {
                double s = 0.0;
                bool matched = false;
                for (auto& [t, w] : q.tags)
                {
                    float conf = 0.0f;
                    for (auto& [pt, c] : p.tags) if (pt == t) conf = (float) c;
                    if (conf > 0.0f) conf += tagDelta (p.id, t);
                    if (conf > 0.0f && w > 0) matched = true;
                    s += w * juce::jmax (0.0f, conf) / 9.0 * (w < 0 ? 1.5 : 1.0);
                }
                if (strict)
                {
                    if (wantsPositive && ! matched) continue;
                    if (wantsPositive && s <= 0.0) continue;
                    score *= wantsPositive ? s * s : juce::jmax (0.05, 1.0 + s);
                }
                else score *= juce::jmax (0.02, 1.0 + 3.0 * s);
            }

            auto ls = likeScore.find (p.id);
            if (ls != likeScore.end()) score *= juce::jlimit (0.1, 3.0, 1.0 + 0.3 * ls->second);
            if (std::find (recent.begin(), recent.end(), p.id) != recent.end()) score *= 0.03;
            auto st = stats.find (p.id);
            if (st == stats.end() || st->second.proposed == 0) score *= 1.3;
            if (p.personal) score *= 1.5;

            if (! kickOnsets.empty() && p.role == roleBass)
            {
                int on = 0, hit = 0;
                const double sp = 4.0 / p.steps;
                for (auto& e : p.events)
                {
                    const double t = std::fmod (e.t / 12.0 * sp, 1.0);
                    ++on;
                    for (auto k : kickOnsets) if (std::abs (k - t) < 0.01) { ++hit; break; }
                }
                score *= 1.6 - 1.2 * (on ? (double) hit / on : 0.0);
            }

            if (score > 0.0) { cand.push_back ({ i, score }); total += score; }
        }

        if (cand.empty()) continue;
        lastNote = pass == 0 ? juce::String()
                 : pass == 1 ? fr ("Aucune ligne de ce style ne porte tous ces mots : voici la plus proche.")
                 : pass == 2 ? fr ("Rien dans ce style : cherché dans tous les styles.")
                             : fr ("Aucune ligne ne réunit tout ça : voici la plus proche, tous styles confondus.");
        double r = rng.nextDouble() * total;
        for (auto& [i, s] : cand) { r -= s; if (r <= 0.0) return i; }
        return cand.back().first;
    }
    lastNote = fr ("Rien ne correspond dans la bibliothèque : ligne générée avec les potards, réglés d'après tes mots.");
    return -1;
}

// ---------------------------------------------------------------------------
// Bibliothèque perso

juce::String Library::savePersonal (const Clip& c, int root, const juce::String& words, const Query& meaning,
                                    int role, int family, const juce::String& settings)
{
    if (c.notes.empty()) return fr ("Rien à garder : la ligne est vide.");
    const juce::ScopedLock sl (lock);
    const auto fp = fingerprintOf (c, root);
    const auto* dup = findDuplicate (fp);
    if (dup != nullptr && dup->personal)
        return fr ("Déjà gardée dans ta bibliothèque : « ") + dup->name + fr (" ».");

    LibPattern p;
    p.id = "perso-" + juce::String (juce::Time::currentTimeMillis());
    p.name = words.isNotEmpty() ? words : fr ("Ligne gardée ") + juce::Time::getCurrentTime().toString (true, true, false);
    p.words = words;
    p.role = role;
    p.family = family;
    p.steps = c.stepsPerBar;
    p.bars = juce::jmax (1, (int) std::round (c.lengthPpq / 4.0));
    p.drums = c.drums;
    p.personal = true;
    p.settings = settings;
    int lo = 127;
    for (auto& n : c.notes) lo = juce::jmin (lo, n.pitch - root);
    const int shift = c.drums ? 0 : (int) std::floor (lo / 12.0) * 12;
    for (auto& n : c.notes)
        p.events.push_back ({ (int) std::round (n.start / c.stepPpq * 12.0), juce::jmax (1, (int) std::round (n.length / c.stepPpq * 12.0)),
                              c.drums ? n.pitch : n.pitch - root - shift, n.velocity });
    for (auto& [t, w] : meaning.tags)
        if (w > 0 && p.tags.size() < 5) p.tags.push_back ({ t, 7 });
    if (p.tags.empty() && dup != nullptr) p.tags = dup->tags;
    index (p);

    // ligne au format compilé, plus les mots et les réglages
    juce::StringArray tags, ev;
    for (auto& [t, cf] : p.tags) tags.add (tagKeys()[t] + ":" + juce::String (cf));
    for (auto& e : p.events) ev.add (juce::String (e.t) + "," + juce::String (e.l) + "," + juce::String (e.p) + "," + juce::String (e.v));
    const auto clean = [] (juce::String s) { return s.replace ("|", "/").replace ("\n", " "); };
    const auto grid = p.steps == 12 ? "1/8T" : p.steps == 24 ? "1/16T" : "1/16";
    juce::String line;
    line << p.id << "|" << roleKeys()[p.role] << "|" << familyKeys()[p.family] << "|" << p.bars << "|" << p.steps << "|"
         << grid << "|" << (p.drums ? 1 : 0) << "|" << tags.joinIntoString (",") << "|" << juce::String::toHexString ((juce::int64) p.fingerprint)
         << "|" << clean (p.name) << "|" << ev.joinIntoString (" ") << "|" << clean (words) << "|" << clean (settings) << "\n";
    dataFolder().getChildFile ("perso.txt").appendText (line, false, false, "\n");

    byFingerprint[p.fingerprint] = (int) all.size();
    byId[p.id] = (int) all.size();
    all.push_back (std::move (p));
    noteKept (all.back().id);

    if (dup != nullptr)
        return fr ("Cette ligne existe déjà dans la bibliothèque (« ") + dup->name + fr (" ») : gardée quand même avec tes mots.");
    return fr ("Gardée dans ta bibliothèque perso.");
}

// ---------------------------------------------------------------------------
// Apprentissage et statistiques

void Library::like (const juce::String& id, const Query& context, bool up)
{
    const juce::ScopedLock sl (lock);
    auto it = byId.find (id);
    if (it == byId.end()) return;
    const auto& p = all[(size_t) it->second];
    likeScore[id] += up ? 1 : -1;
    bool asked = false;
    for (auto& [t, c] : p.tags)
        if (context.tags.count (t) && context.tags.at (t) > 0)
        {
            asked = true;
            deltas[id][t] = juce::jlimit (-6.0f, 6.0f, deltas[id][t] + (up ? 1.0f : -1.0f));
        }
    if (! asked)   // pas de mots demandés : toutes les étiquettes du motif bougent un peu
        for (auto& [t, c] : p.tags)
            deltas[id][t] = juce::jlimit (-6.0f, 6.0f, deltas[id][t] + (up ? 0.5f : -0.5f));
    auto& s = stats[id];
    (up ? s.liked : s.disliked)++;
    saveLearning();
    saveStats();
}

void Library::resetLearning()
{
    const juce::ScopedLock sl (lock);
    deltas.clear();
    likeScore.clear();
    for (auto& [id, s] : stats) { s.liked = 0; s.disliked = 0; }
    dataFolder().getChildFile ("apprentissage.txt").deleteFile();
    saveStats();
}

void Library::loadLearning()
{
    for (auto line : juce::StringArray::fromLines (dataFolder().getChildFile ("apprentissage.txt").loadFileAsString()))
    {
        auto f = juce::StringArray::fromTokens (line, "|", "");
        if (f.size() < 2) continue;
        likeScore[f[0]] = f[1].getIntValue();
        if (f.size() > 2)
            for (auto item : juce::StringArray::fromTokens (f[2], ",", ""))
            {
                const int t = tagKeys().indexOf (item.upToFirstOccurrenceOf (":", false, false));
                if (t >= 0) deltas[f[0]][t] = item.fromFirstOccurrenceOf (":", false, false).getFloatValue();
            }
    }
    for (auto line : juce::StringArray::fromLines (dataFolder().getChildFile ("stats.txt").loadFileAsString()))
    {
        auto f = juce::StringArray::fromTokens (line, " ", "");
        if (f.size() < 7) continue;
        stats[f[0]] = { f[1].getIntValue(), f[2].getIntValue(), f[3].getIntValue(), f[4].getIntValue(), f[5].getIntValue(), f[6].getIntValue() };
    }
}

void Library::saveLearning() const
{
    juce::String out;
    std::set<juce::String> ids;
    for (auto& [id, v] : likeScore) ids.insert (id);
    for (auto& [id, v] : deltas) ids.insert (id);
    for (auto& id : ids)
    {
        juce::StringArray d;
        if (auto it = deltas.find (id); it != deltas.end())
            for (auto& [t, v] : it->second) d.add (tagKeys()[t] + ":" + juce::String (v, 1));
        auto ls = likeScore.find (id);
        out << id << "|" << (ls != likeScore.end() ? ls->second : 0) << "|" << d.joinIntoString (",") << "\n";
    }
    dataFolder().getChildFile ("apprentissage.txt").replaceWithText (out);
}

void Library::saveStats() const
{
    juce::String out;
    for (auto& [id, s] : stats)
        out << id << " " << s.proposed << " " << s.skipped << " " << s.listened << " " << s.liked << " " << s.disliked << " " << s.kept << "\n";
    dataFolder().getChildFile ("stats.txt").replaceWithText (out);
}

void Library::noteProposed (const juce::String& id)
{
    const juce::ScopedLock sl (lock);
    stats[id].proposed++;
    recent.push_back (id);
    if (recent.size() > 60) recent.erase (recent.begin());
    saveStats();
}

void Library::noteListenTime (const juce::String& id, double seconds)
{
    const juce::ScopedLock sl (lock);
    if (seconds < 4.0) stats[id].skipped++;
    else if (seconds > 30.0) stats[id].listened++;
    else return;
    saveStats();
}

void Library::noteKept (const juce::String& id)
{
    stats[id].kept++;
    saveStats();
}

const Stats* Library::statsFor (const juce::String& id) const
{
    auto it = stats.find (id);
    return it != stats.end() ? &it->second : nullptr;
}

juce::String Library::report() const
{
    const juce::ScopedLock sl (lock);
    Stats tot;
    std::map<int, Stats> perFamily;
    std::map<int, int> sizeFamily;
    int perso = 0;
    for (auto& p : all) { sizeFamily[p.family]++; perso += p.personal ? 1 : 0; }
    int seen = 0;
    std::vector<std::pair<int, juce::String>> liked, skippedMost;
    for (auto& [id, s] : stats)
    {
        tot.proposed += s.proposed; tot.skipped += s.skipped; tot.listened += s.listened;
        tot.liked += s.liked; tot.disliked += s.disliked; tot.kept += s.kept;
        auto it = byId.find (id);
        if (it == byId.end()) continue;
        if (s.proposed > 0) ++seen;
        auto& f = perFamily[all[(size_t) it->second].family];
        f.proposed += s.proposed; f.skipped += s.skipped; f.listened += s.listened; f.liked += s.liked; f.kept += s.kept;
        if (s.liked > 0) liked.push_back ({ s.liked, all[(size_t) it->second].name });
    }
    std::sort (liked.begin(), liked.end(), [] (auto& a, auto& b) { return a.first > b.first; });

    juce::String r;
    r << fr ("BILAN\n\n");
    r << fr ("Bibliothèque : ") << (int) all.size() << fr (" lignes, dont ") << perso << fr (" dans ta bibliothèque perso.\n");
    r << fr ("Déjà proposées au moins une fois : ") << seen << " ("
      << juce::String (all.empty() ? 0.0 : 100.0 * seen / (double) all.size(), 1) << fr (" %). Jamais entendues : ")
      << (int) all.size() - seen << ".\n\n";
    r << fr ("Propositions : ") << tot.proposed << fr ("   écartées vite (< 4 s) : ") << tot.skipped
      << fr ("   écoutées longtemps (> 30 s) : ") << tot.listened << "\n";
    r << fr ("J'aime : ") << tot.liked << fr ("   Bof : ") << tot.disliked << fr ("   gardées : ") << tot.kept << "\n\n";
    r << fr ("Par style (proposées / écartées vite / écoutées longtemps / aimées / gardées, sur la taille du style) :\n");
    for (int f = 0; f < familyKeys().size(); ++f)
    {
        const auto& s = perFamily[f];
        r << "  " << familyNames()[f].paddedRight (' ', 26) << s.proposed << " / " << s.skipped << " / " << s.listened
          << " / " << s.liked << " / " << s.kept << fr ("   sur ") << sizeFamily[f] << "\n";
    }
    if (! liked.empty())
    {
        r << fr ("\nLes plus aimées :\n");
        for (size_t i = 0; i < juce::jmin ((size_t) 8, liked.size()); ++i)
            r << "  " << liked[i].second << " (" << liked[i].first << ")\n";
    }
    r << fr ("\nFichiers : ") << dataFolder().getFullPathName();
    return r;
}
} // namespace mlg
