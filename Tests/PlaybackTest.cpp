// Simule un hôte qui joue : vérifie que chaque note-on a son note-off,
// que les notes tombent sur la grille et qu'un arrêt coupe tout.
#include "../Source/PluginProcessor.h"
#include <iostream>
#include <map>

struct FakePlayHead : juce::AudioPlayHead
{
    double ppq = 0.0, bpm = 120.0; bool playing = true;
    juce::Optional<PositionInfo> getPosition() const override
    {
        PositionInfo p; p.setIsPlaying (playing); p.setPpqPosition (ppq); p.setBpm (bpm); return p;
    }
};

int main()
{
    juce::ScopedJuceInitialiser_GUI init;
    int failures = 0;
    auto check = [&] (bool c, const char* what) { if (! c) { std::cerr << "ECHEC: " << what << "\n"; ++failures; } };

    for (int legato = 0; legato < 2; ++legato)
    for (int mode = 0; mode < 2; ++mode)
    {
        MidiLinesProcessor proc;
        auto set = [&] (const char* id, float v) { auto* p = proc.apvts.getParameter (id); p->setValueNotifyingHost (p->convertTo0to1 (v)); };
        set ("legato", (float) legato); set ("rhythmMode", (float) mode); set ("swing", 30.0f);
        proc.setSeeds (42u, 99u);   // rebuild immédiat
        FakePlayHead ph; proc.setPlayHead (&ph);
        const double sr = 48000.0; const int bs = 441;  // taille de bloc volontairement "bizarre"
        proc.prepareToPlay (sr, bs);
        juce::AudioBuffer<float> buf (2, bs);

        std::map<int, int> sounding; int ons = 0, offs = 0, maxPoly = 0, poly = 0;
        const auto& pat = proc.getDisplayPattern();
        int expectedPerCycle = 0; for (int i = 0; i < pat.numSteps; ++i) expectedPerCycle += pat.steps[(size_t) i].on;

        const double ppqPerSample = ph.bpm / 60.0 / sr;
        const int blocks = (int) (8.0 * pat.cyclePpq() / (ppqPerSample * bs)); // ~8 cycles
        for (int b = 0; b < blocks; ++b)
        {
            juce::MidiBuffer midi;
            proc.processBlock (buf, midi);
            for (const auto m : midi)
            {
                const auto& msg = m.getMessage();
                const double t = ph.ppq + m.samplePosition * ppqPerSample;
                if (msg.isNoteOn())
                {
                    ++ons; ++sounding[msg.getNoteNumber()]; maxPoly = std::max (maxPoly, ++poly);
                    // sur la grille (avec swing) à 1 échantillon près
                    const double step = pat.stepPpq; const double cyc = std::fmod (t, pat.cyclePpq());
                    bool ok = false;
                    for (int s = 0; s < pat.numSteps; ++s) if (std::abs (cyc - pat.stepStartPpq (s)) < ppqPerSample * 1.5 + 1e-9 || std::abs (cyc - pat.cyclePpq() - pat.stepStartPpq (s)) < ppqPerSample * 1.5) ok = true;
                    check (ok, "note hors grille");
                    (void) step;
                }
                else if (msg.isNoteOff())
                {
                    ++offs; check (sounding[msg.getNoteNumber()] > 0, "note-off sans note-on"); --sounding[msg.getNoteNumber()]; --poly;
                }
            }
            ph.ppq += bs * ppqPerSample;
        }
        // arrêt du transport
        ph.playing = false;
        { juce::MidiBuffer midi; proc.processBlock (buf, midi); for (const auto m : midi) if (m.getMessage().isNoteOff()) { ++offs; --poly; } }
        check (poly == 0, "notes bloquees apres arret");
        check (maxPoly <= (legato ? 2 : 1), "polyphonie inattendue");
        const int cycles = (int) std::floor ((blocks * bs * ppqPerSample) / pat.cyclePpq());
        check (ons >= expectedPerCycle * cycles, "notes manquantes");
        check (ons <= expectedPerCycle * (cycles + 1), "notes en double");
        std::cout << "legato=" << legato << " mode=" << mode << " : " << ons << " on / " << offs << " off, "
                  << expectedPerCycle << " notes/cycle, poly max " << maxPoly << "\n";
        proc.setPlayHead (nullptr);
    }
    std::cout << (failures == 0 ? "OK lecture\n" : "ECHECS lecture\n");
    return failures ? 1 : 0;
}
