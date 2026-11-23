// Vérifications du moteur MLG Alpha (hors plugin).
#include "../Source/Engine.h"
#include <iostream>

using namespace mlg;

static int failures = 0;
#define CHECK(cond) do { if (! (cond)) { std::cerr << "ECHEC: " #cond " (ligne " << __LINE__ << ")\n"; ++failures; } } while (0)

static bool inScale (int note, int root, const std::vector<int>& sc)
{
    const int rel = ((note - root) % 12 + 12) % 12;
    return std::find (sc.begin(), sc.end(), rel) != sc.end();
}

static juce::String dump (const Pattern& p)
{
    juce::String s;
    for (int i = 0; i < p.numSteps; ++i)
        s << (p.steps[(size_t) i].on ? noteName (p.steps[(size_t) i].pitch).paddedRight (' ', 4) : juce::String ("--  "));
    return s;
}

int main()
{
    Settings s;
    Seeds seeds { 1234u, 5678u, 0, 0 };

    // 1. Déterminisme
    const auto a = generate (s, seeds), b = generate (s, seeds);
    for (int i = 0; i < kMaxSteps; ++i)
        CHECK (a.steps[(size_t) i].on == b.steps[(size_t) i].on && a.steps[(size_t) i].pitch == b.steps[(size_t) i].pitch);
    std::cout << "Aleatoire  : " << dump (a) << "\n";

    // 2. Gamme et plage respectées
    const std::vector<int> minor { 0, 2, 3, 5, 7, 8, 10 };
    for (int seed = 1; seed < 200; ++seed)
    {
        const auto p = generate (s, { (juce::uint32) seed, (juce::uint32) seed * 7u, 0, 0 });
        for (int i = 0; i < p.numSteps; ++i)
            if (p.steps[(size_t) i].on)
            {
                const int note = p.steps[(size_t) i].pitch;
                CHECK (note >= s.lowNote && note <= s.highNote);
                CHECK (inScale (note, s.root, minor));
                CHECK (p.steps[(size_t) i].velocity >= 1 && p.steps[(size_t) i].velocity <= 127);
            }
    }

    // 3. Densité monotone : plus de densité = mêmes notes + des nouvelles
    {
        Settings lo = s, hi = s;
        lo.density = 0.3; hi.density = 0.7;
        const auto pl = generate (lo, seeds), ph = generate (hi, seeds);
        for (int i = 0; i < s.numSteps; ++i)
            if (pl.steps[(size_t) i].on) CHECK (ph.steps[(size_t) i].on);
    }

    // 4. Euclidien : 16 pas, 5 impulsions -> 5 notes
    {
        Settings e = s;
        e.rhythmMode = RhythmMode::euclidean; e.pulses = 5;
        const auto p = generate (e, seeds);
        int count = 0;
        for (int i = 0; i < p.numSteps; ++i) count += p.steps[(size_t) i].on ? 1 : 0;
        CHECK (count == 5);
        std::cout << "Euclide 5/16: " << dump (p) << "\n";
        e.rotation = 2;
        std::cout << "  rotation 2: " << dump (generate (e, seeds)) << "\n";
    }

    // 5. Écart max : 1 degré -> notes voisines dans la gamme
    {
        Settings j = s; j.maxJump = 1; j.density = 1.0;
        const auto p = generate (j, seeds);
        std::vector<int> notes;
        for (int n = j.lowNote; n <= j.highNote; ++n) if (inScale (n, j.root, minor)) notes.push_back (n);
        int prev = -1;
        for (int i = 0; i < p.numSteps; ++i)
        {
            const auto idx = (int) (std::find (notes.begin(), notes.end(), p.steps[(size_t) i].pitch) - notes.begin());
            if (prev >= 0) CHECK (std::abs (idx - prev) <= 1);
            prev = idx;
        }
        std::cout << "Ecart max 1 : " << dump (p) << "\n";
    }

    // 6. Verrou : muter le rythme seul ne change pas la suite de hauteurs
    {
        Seeds m = seeds; m.rhythmMutations = 3;
        const auto p = generate (s, m);
        std::cout << "Mutation x3 : " << dump (p) << "\n";
        std::vector<int> m0, m1;
        for (int i = 0; i < s.numSteps; ++i) if (a.steps[(size_t) i].on) m0.push_back (a.steps[(size_t) i].pitch);
        for (int i = 0; i < s.numSteps; ++i) if (p.steps[(size_t) i].on) m1.push_back (p.steps[(size_t) i].pitch);
        for (size_t i = 0; i < std::min (m0.size(), m1.size()); ++i) CHECK (m0[i] == m1[i]);
    }

    // 7. Export MIDI : une paire on/off par note, dans le cycle
    {
        auto file = toMidiFile (a);
        const auto* track = file.getTrack (0);
        int ons = 0, offs = 0, expected = 0;
        for (int i = 0; i < a.numSteps; ++i) expected += a.steps[(size_t) i].on ? 1 : 0;
        for (auto* e : *track)
        {
            if (e->message.isNoteOn()) { ++ons; CHECK (e->noteOffObject != nullptr); }
            if (e->message.isNoteOff()) ++offs;
            CHECK (e->message.getTimeStamp() <= a.cyclePpq() * 960 + 0.5);
        }
        CHECK (ons == expected && offs == expected);

        juce::MemoryOutputStream mos;
        CHECK (file.writeTo (mos));
        CHECK (mos.getDataSize() > 20);
    }

    std::cout << (failures == 0 ? "OK : tous les tests passent\n" : "Des tests ont echoue\n");
    return failures == 0 ? 0 : 1;
}
