// Simule un hôte qui joue : chaque note-on a son note-off, les notes tombent au bon endroit,
// un arrêt coupe tout ; lignes des potards et de la bibliothèque, changement immédiat ou à la mesure.
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

static int failures = 0;
static void check (bool c, const char* what) { if (! c) { std::cerr << "ECHEC: " << what << "\n"; ++failures; } }

// Joue `cycles` boucles, vérifie les paires et la position des notes ; renvoie le nombre de note-on.
static int play (MLGAlphaProcessor& proc, FakePlayHead& ph, double ppqLength, const char* label,
                 std::function<void (int)> everyBlock = {})
{
    const double sr = 48000.0; const int bs = 441;
    juce::AudioBuffer<float> buf (2, bs);
    std::map<int, int> sounding; int ons = 0, poly = 0, maxPoly = 0, offGrid = 0;
    const double pps = ph.bpm / 60.0 / sr;
    const int blocks = (int) (ppqLength / (pps * bs));
    for (int b = 0; b < blocks; ++b)
    {
        if (everyBlock) everyBlock (b);
        juce::MidiBuffer midi;
        proc.processBlock (buf, midi);
        for (const auto m : midi)
        {
            const auto& msg = m.getMessage();
            const double t = ph.ppq + m.samplePosition * pps;
            if (msg.isNoteOn())
            {
                ++ons; ++sounding[msg.getNoteNumber()]; maxPoly = std::max (maxPoly, ++poly);
                const auto& c = proc.getDisplayClip();
                const double inClip = std::fmod (t, c.lengthPpq);
                bool ok = false;
                for (auto& n : c.notes)
                    if (std::abs (inClip - n.start) < pps * 1.5 || std::abs (inClip - c.lengthPpq - n.start) < pps * 1.5) ok = true;
                offGrid += ok ? 0 : 1;
            }
            else if (msg.isNoteOff())
            {
                check (sounding[msg.getNoteNumber()] > 0, "note-off sans note-on");
                --sounding[msg.getNoteNumber()]; --poly;
            }
        }
        ph.ppq += bs * pps;
    }
    ph.playing = false;
    { juce::MidiBuffer midi; proc.processBlock (buf, midi); for (const auto m : midi) if (m.getMessage().isNoteOff()) --poly; }
    ph.playing = true;
    check (poly == 0, "notes bloquees apres arret");
    std::cout << label << " : " << ons << " notes, poly max " << maxPoly << ", hors place " << offGrid << "\n";
    return offGrid;
}

int main()
{
    juce::ScopedJuceInitialiser_GUI init;

    for (int legato = 0; legato < 2; ++legato)
    {
        MLGAlphaProcessor proc;
        auto set = [&] (const char* id, float v) { auto* p = proc.apvts.getParameter (id); p->setValueNotifyingHost (p->convertTo0to1 (v)); };
        set ("legato", (float) legato); set ("swing", 30.0f); set ("steps", 32.0f);
        proc.setSeeds (42u, 99u);
        FakePlayHead ph; proc.setPlayHead (&ph); proc.prepareToPlay (48000.0, 441);
        check (play (proc, ph, 32.0, legato ? "potards legato" : "potards") == 0, "notes potards hors place");
        proc.setPlayHead (nullptr);
    }

    {
        MLGAlphaProcessor proc;
        while (! proc.libraryReady()) juce::Thread::sleep (20);
        FakePlayHead ph; proc.setPlayHead (&ph); proc.prepareToPlay (48000.0, 441);
        const char* asks[] = { "nappe sombre", "batterie techno", "basse acid", "arpège triolets", "accords dub" };
        for (auto* a : asks)
        {
            std::cout << proc.drawFromText (juce::String::fromUTF8 (a)).upToFirstOccurrenceOf ("\n", false, false) << "\n";
            check (proc.isLibraryLine(), "pas de ligne de bibliotheque");
            ph.ppq = 0.0;
            check (play (proc, ph, proc.getDisplayClip().lengthPpq * 2, a) == 0, "notes bibliotheque hors place");
        }

        // Changement à la mesure suivante : le nouveau clip ne commence qu'au début d'une mesure
        auto* sw = proc.apvts.getParameter ("switchAt"); sw->setValueNotifyingHost (1.0f);
        ph.ppq = 0.0;
        play (proc, ph, 6.0, "changement a la mesure", [&] (int b) { if (b == 100) proc.drawFromText ("kick"); });
    }
    std::cout << (failures == 0 ? "OK lecture\n" : "ECHECS lecture\n");
    return failures ? 1 : 0;
}
