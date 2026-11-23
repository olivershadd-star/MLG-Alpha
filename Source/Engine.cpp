#include "Engine.h"

#include <algorithm>
#include <vector>

namespace mlg
{
namespace
{
const std::vector<std::vector<int>>& scaleTable()
{
    static const std::vector<std::vector<int>> t {
        { 0, 2, 4, 5, 7, 9, 11 },               // Majeur
        { 0, 2, 3, 5, 7, 8, 10 },               // Mineur naturel
        { 0, 2, 3, 5, 7, 9, 10 },               // Dorien
        { 0, 1, 3, 5, 7, 8, 10 },               // Phrygien
        { 0, 2, 4, 6, 7, 9, 11 },               // Lydien
        { 0, 2, 4, 5, 7, 9, 10 },               // Mixolydien
        { 0, 1, 3, 5, 6, 8, 10 },               // Locrien
        { 0, 2, 3, 5, 7, 8, 11 },               // Mineur harmonique
        { 0, 2, 3, 5, 7, 9, 11 },               // Mineur mélodique
        { 0, 2, 4, 7, 9 },                      // Penta majeure
        { 0, 3, 5, 7, 10 },                     // Penta mineure
        { 0, 3, 5, 6, 7, 10 },                  // Blues
        { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 } // Chromatique
    };
    return t;
}

// Graine dérivée pour la i-ème mutation (déterministe).
juce::int64 derive (juce::uint32 seed, int index, juce::uint32 salt)
{
    juce::uint64 x = ((juce::uint64) seed << 32) ^ (juce::uint64) (juce::uint32) (index + 1) * 0x9E3779B97F4A7C15ull ^ salt;
    x ^= x >> 33; x *= 0xff51afd7ed558ccdull; x ^= x >> 33;
    return (juce::int64) x;
}

int reflect (int idx, int size)
{
    if (size <= 1) return 0;
    const int period = 2 * (size - 1);
    idx %= period;
    if (idx < 0) idx += period;
    return idx < size ? idx : period - idx;
}
} // namespace

juce::StringArray scaleNames()
{
    return { fr ("Majeur"), fr ("Mineur naturel"), fr ("Dorien"), fr ("Phrygien"), fr ("Lydien"),
             fr ("Mixolydien"), fr ("Locrien"), fr ("Mineur harmonique"), fr ("Mineur mélodique"),
             fr ("Penta majeure"), fr ("Penta mineure"), fr ("Blues"), fr ("Chromatique") };
}

juce::StringArray divisionNames() { return { "1/4", "1/8", "1/8T", "1/16", "1/16T", "1/32" }; }

juce::StringArray rootNames() { return { "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B" }; }

double divisionToPpq (int division)
{
    static const double v[] = { 1.0, 0.5, 1.0 / 3.0, 0.25, 1.0 / 6.0, 0.125 };
    return v[juce::jlimit (0, 5, division)];
}

juce::String noteName (int midiNote)
{
    return rootNames()[((midiNote % 12) + 12) % 12] + juce::String (midiNote / 12 - 2);
}

Pattern generate (const Settings& s, const Seeds& seeds)
{
    Pattern p;
    p.numSteps = juce::jlimit (1, kMaxSteps, s.numSteps);
    p.stepPpq = divisionToPpq (s.division);
    p.swing = juce::jlimit (0.0, 1.0, s.swing);
    p.legato = s.legato;
    const int n = p.numSteps;

    // ---------- Couche rythme ----------
    // On tire toujours 64 valeurs : changer le nombre de pas ou la densité
    // garde les mêmes notes au même endroit (la densité ajoute/retire progressivement).
    std::array<bool, kMaxSteps> gate {};
    std::array<int, kMaxSteps> vel {};
    std::array<double, kMaxSteps> len {};
    {
        juce::Random rr ((juce::int64) seeds.rhythm);
        const int vlo = juce::jmin (s.velMin, s.velMax), vhi = juce::jmax (s.velMin, s.velMax);
        const double llo = juce::jmin (s.lenMin, s.lenMax), lhi = juce::jmax (s.lenMin, s.lenMax);
        std::array<double, kMaxSteps> chance {};

        for (int i = 0; i < kMaxSteps; ++i)
        {
            chance[(size_t) i] = rr.nextDouble();
            vel[(size_t) i] = vlo + rr.nextInt (vhi - vlo + 1);
            len[(size_t) i] = llo + rr.nextDouble() * (lhi - llo);
        }

        if (s.rhythmMode == RhythmMode::euclidean)
        {
            const int k = juce::jlimit (0, n, s.pulses);
            const int rot = ((s.rotation % n) + n) % n;
            for (int i = 0; i < n; ++i)
            {
                const int idx = (i + n - rot) % n;
                gate[(size_t) i] = k > 0 && ((idx * k) % n) < k;
            }
        }
        else
        {
            for (int i = 0; i < n; ++i)
                gate[(size_t) i] = chance[(size_t) i] < s.density;
        }

        // Mutations : on bascule 1 ou 2 pas et on varie une vélocité.
        for (int m = 0; m < seeds.rhythmMutations; ++m)
        {
            juce::Random mr (derive (seeds.rhythm, m, 0x52594854u));
            const int flips = 1 + mr.nextInt (2);
            for (int f = 0; f < flips; ++f)
            {
                const int idx = mr.nextInt (n);
                gate[(size_t) idx] = ! gate[(size_t) idx];
            }
            const int vIdx = mr.nextInt (n);
            vel[(size_t) vIdx] = vlo + mr.nextInt (vhi - vlo + 1);
        }

        bool any = false;
        for (int i = 0; i < n; ++i) any = any || gate[(size_t) i];
        if (! any) gate[0] = true;
    }

    // ---------- Couche hauteurs ----------
    // Liste des notes autorisées (gamme entre note basse et note haute),
    // puis marche aléatoire dans cette liste avec un écart max.
    std::vector<int> notes;
    {
        const auto& table = scaleTable();
        const auto& sc = table[(size_t) juce::jlimit (0, (int) table.size() - 1, s.scale)];
        const int lo = juce::jmin (s.lowNote, s.highNote), hi = juce::jmax (s.lowNote, s.highNote);
        for (int note = lo; note <= hi; ++note)
        {
            const int rel = ((note - s.root) % 12 + 12) % 12;
            if (std::find (sc.begin(), sc.end(), rel) != sc.end())
                notes.push_back (note);
        }
        if (notes.empty()) notes.push_back (lo);
    }

    const int size = (int) notes.size();
    const int jump = juce::jmax (0, s.maxJump);
    std::array<int, kMaxSteps> melody {};
    {
        juce::Random pr ((juce::int64) seeds.pitch);
        int idx = (int) (pr.nextDouble() * size);
        for (int j = 0; j < kMaxSteps; ++j)
        {
            melody[(size_t) j] = reflect (idx, size);
            idx = melody[(size_t) j] + pr.nextInt (2 * jump + 1) - jump;
        }

        int active = 0;
        for (int i = 0; i < n; ++i) active += gate[(size_t) i] ? 1 : 0;

        for (int m = 0; m < seeds.pitchMutations; ++m)
        {
            juce::Random mp (derive (seeds.pitch, m, 0x50495443u));
            const int count = 1 + mp.nextInt (3);
            for (int c = 0; c < count; ++c)
            {
                const int j = mp.nextInt (juce::jmax (1, active));
                const int delta = (1 + mp.nextInt (juce::jmax (1, jump))) * (mp.nextBool() ? 1 : -1);
                melody[(size_t) j] = reflect (melody[(size_t) j] + delta, size);
            }
        }
    }

    // ---------- Assemblage ----------
    int k = 0;
    for (int i = 0; i < n; ++i)
    {
        auto& st = p.steps[(size_t) i];
        st.on = gate[(size_t) i];
        if (! st.on) continue;

        st.pitch = notes[(size_t) melody[(size_t) (k % kMaxSteps)]];
        st.velocity = juce::jlimit (1, 127, vel[(size_t) i] + ((i % 4) == 0 ? s.accent : 0));
        st.lengthSteps = juce::jmax (0.05, len[(size_t) i]);
        ++k;
    }

    // Legato : chaque note tient jusqu'à la suivante (léger chevauchement pour le glide).
    if (p.legato)
    {
        for (int i = 0; i < n; ++i)
        {
            if (! p.steps[(size_t) i].on) continue;
            int d = 1;
            while (d < n && ! p.steps[(size_t) ((i + d) % n)].on) ++d;
            p.steps[(size_t) i].lengthSteps = d + 0.6;
        }
    }

    return p;
}

Clip clipFromPattern (const Pattern& p)
{
    Clip c;
    c.lengthPpq = p.cyclePpq();
    c.stepPpq = p.stepPpq;
    c.stepsPerBar = juce::jmax (1, juce::roundToInt (4.0 / p.stepPpq));
    const double cycle = p.cyclePpq();

    std::vector<int> onSteps;
    for (int i = 0; i < p.numSteps; ++i)
        if (p.steps[(size_t) i].on) onSteps.push_back (i);

    for (size_t a = 0; a < onSteps.size(); ++a)
    {
        const auto& st = p.steps[(size_t) onSteps[a]];
        const double start = p.stepStartPpq (onSteps[a]);
        // note suivante (en bouclant) : la ligne reste monophonique
        const double nextStart = (a + 1 < onSteps.size()) ? p.stepStartPpq (onSteps[a + 1])
                                                          : cycle + p.stepStartPpq (onSteps[0]);
        double end = start + st.lengthSteps * p.stepPpq;
        end = p.legato ? juce::jmin (end, nextStart + 0.02) : juce::jmin (end, nextStart);
        if (end <= start) end = start + 0.01;
        c.notes.push_back ({ start, end - start, st.pitch, st.velocity });
    }
    return c;
}

juce::MidiFile toMidiFile (const Clip& c)
{
    constexpr int ticksPerQuarter = 960;
    juce::MidiMessageSequence seq;
    for (const auto& n : c.notes)
    {
        const double end = juce::jmin (n.start + n.length, c.lengthPpq);
        seq.addEvent (juce::MidiMessage::noteOn (kMidiChannel, n.pitch, (juce::uint8) juce::jlimit (1, 127, n.velocity)), n.start * ticksPerQuarter);
        seq.addEvent (juce::MidiMessage::noteOff (kMidiChannel, n.pitch), juce::jmax (n.start + 0.01, end) * ticksPerQuarter);
    }
    seq.addEvent (juce::MidiMessage::endOfTrack(), c.lengthPpq * ticksPerQuarter);
    seq.sort();
    seq.updateMatchedPairs();
    juce::MidiFile file;
    file.setTicksPerQuarterNote (ticksPerQuarter);
    file.addTrack (seq);
    return file;
}

juce::MidiFile toMidiFile (const Pattern& p)
{
    constexpr int ticksPerQuarter = 960;
    const double cycle = p.cyclePpq();
    juce::MidiMessageSequence seq;

    std::vector<int> onSteps;
    for (int i = 0; i < p.numSteps; ++i)
        if (p.steps[(size_t) i].on) onSteps.push_back (i);

    for (size_t a = 0; a < onSteps.size(); ++a)
    {
        const auto& st = p.steps[(size_t) onSteps[a]];
        const double start = p.stepStartPpq (onSteps[a]);
        const double nextStart = (a + 1 < onSteps.size()) ? p.stepStartPpq (onSteps[a + 1]) : cycle;
        double end = start + st.lengthSteps * p.stepPpq;

        // Monophonique : une note s'arrête quand la suivante commence
        // (en legato, on garde un petit chevauchement).
        end = p.legato ? juce::jmin (end, nextStart + 0.02) : juce::jmin (end, nextStart);
        end = juce::jmin (end, cycle);
        if (end <= start) end = start + 0.01;

        seq.addEvent (juce::MidiMessage::noteOn (kMidiChannel, st.pitch, (juce::uint8) st.velocity), start * ticksPerQuarter);
        seq.addEvent (juce::MidiMessage::noteOff (kMidiChannel, st.pitch), end * ticksPerQuarter);
    }

    seq.addEvent (juce::MidiMessage::endOfTrack(), cycle * ticksPerQuarter);
    seq.sort();
    seq.updateMatchedPairs();

    juce::MidiFile file;
    file.setTicksPerQuarterNote (ticksPerQuarter);
    file.addTrack (seq);
    return file;
}
} // namespace mlg
