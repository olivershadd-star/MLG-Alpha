#include "PluginProcessor.h"
#include "PluginEditor.h"

using mlg::fr;

namespace
{
const char* const kParamIds[] = { "rhythmMode", "steps", "division", "density", "pulses", "rotation", "swing",
                                  "root", "scale", "lowNote", "highNote", "maxJump",
                                  "lenMin", "lenMax", "legato", "velMin", "velMax", "accent", "octave", "switchAt" };
}

MLGAlphaProcessor::MLGAlphaProcessor()
    : AudioProcessor (BusesProperties().withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
      apvts (*this, nullptr, "MLGALPHA", createLayout())
{
    for (auto* id : kParamIds)
        apvts.addParameterListener (id, this);

    active.reserve (256);
    seeds.rhythm = (juce::uint32) juce::Random::getSystemRandom().nextInt();
    seeds.pitch = (juce::uint32) juce::Random::getSystemRandom().nextInt();
    rng.setSeedRandomly();
    rebuild();
    startTimerHz (30);
}

MLGAlphaProcessor::~MLGAlphaProcessor()
{
    stopTimer();
    closeListening();
    for (auto* id : kParamIds)
        apvts.removeParameterListener (id, this);
}

juce::AudioProcessorValueTreeState::ParameterLayout MLGAlphaProcessor::createLayout()
{
    using namespace juce;
    std::vector<std::unique_ptr<RangedAudioParameter>> p;

    auto pct = AudioParameterFloatAttributes().withStringFromValueFunction ([] (float v, int) { return String (roundToInt (v)) + " %"; });
    auto note = AudioParameterIntAttributes().withStringFromValueFunction ([] (int v, int) { return mlg::noteName (v); });

    // Rythme
    p.push_back (std::make_unique<AudioParameterChoice> (ParameterID { "rhythmMode", 1 }, fr ("Mode rythme"),
                                                         StringArray { fr ("Aléatoire"), fr ("Euclidien") }, 0));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "steps", 1 }, fr ("Pas"), 1, mlg::kMaxSteps, 16));
    p.push_back (std::make_unique<AudioParameterChoice> (ParameterID { "division", 1 }, fr ("Division"), mlg::divisionNames(), 3));
    p.push_back (std::make_unique<AudioParameterFloat> (ParameterID { "density", 1 }, fr ("Densité"), NormalisableRange<float> (0.0f, 100.0f, 1.0f), 50.0f, pct));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "pulses", 1 }, fr ("Impulsions"), 0, mlg::kMaxSteps, 5));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "rotation", 1 }, fr ("Rotation"), 0, mlg::kMaxSteps - 1, 0));
    p.push_back (std::make_unique<AudioParameterFloat> (ParameterID { "swing", 1 }, fr ("Swing"), NormalisableRange<float> (0.0f, 100.0f, 1.0f), 0.0f, pct));

    // Hauteurs
    p.push_back (std::make_unique<AudioParameterChoice> (ParameterID { "root", 1 }, fr ("Tonique"), mlg::rootNames(), 0));
    p.push_back (std::make_unique<AudioParameterChoice> (ParameterID { "scale", 1 }, fr ("Gamme"), mlg::scaleNames(), 1));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "lowNote", 1 }, fr ("Note basse"), 24, 108, 48, note));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "highNote", 1 }, fr ("Note haute"), 24, 108, 67, note));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "maxJump", 1 }, fr ("Écart max"), 0, 12, 3));

    // Notes
    p.push_back (std::make_unique<AudioParameterFloat> (ParameterID { "lenMin", 1 }, fr ("Durée min"), NormalisableRange<float> (5.0f, 400.0f, 1.0f), 50.0f, pct));
    p.push_back (std::make_unique<AudioParameterFloat> (ParameterID { "lenMax", 1 }, fr ("Durée max"), NormalisableRange<float> (5.0f, 400.0f, 1.0f), 100.0f, pct));
    p.push_back (std::make_unique<AudioParameterBool> (ParameterID { "legato", 1 }, fr ("Legato"), false));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "velMin", 1 }, fr ("Vélocité min"), 1, 127, 80));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "velMax", 1 }, fr ("Vélocité max"), 1, 127, 110));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "accent", 1 }, fr ("Accent"), 0, 40, 15));

    // Lecture
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "octave", 1 }, fr ("Octave"), -3, 3, 0));
    p.push_back (std::make_unique<AudioParameterChoice> (ParameterID { "switchAt", 1 }, fr ("Changement"),
                                                         StringArray { fr ("Immédiat"), fr ("Mesure suivante") }, 0));

    return { p.begin(), p.end() };
}

bool MLGAlphaProcessor::isBusesLayoutSupported (const BusesLayout& layouts) const
{
    const auto out = layouts.getMainOutputChannelSet();
    return out == juce::AudioChannelSet::stereo() || out == juce::AudioChannelSet::mono();
}

void MLGAlphaProcessor::prepareToPlay (double sampleRate, int)
{
    currentSampleRate = sampleRate > 0.0 ? sampleRate : 44100.0;
    wasPlaying = false;
    active.clear();
}

// ---------------------------------------------------------------------------
// Potards (thread principal)

mlg::Settings MLGAlphaProcessor::readSettings() const
{
    mlg::Settings s;
    s.rhythmMode = (int) raw ("rhythmMode") == 1 ? mlg::RhythmMode::euclidean : mlg::RhythmMode::random;
    s.numSteps = (int) raw ("steps");
    s.division = (int) raw ("division");
    s.density = raw ("density") / 100.0;
    s.pulses = (int) raw ("pulses");
    s.rotation = (int) raw ("rotation");
    s.swing = raw ("swing") / 100.0;
    s.root = (int) raw ("root");
    s.scale = (int) raw ("scale");
    s.lowNote = (int) raw ("lowNote");
    s.highNote = (int) raw ("highNote");
    s.maxJump = (int) raw ("maxJump");
    s.lenMin = raw ("lenMin") / 100.0;
    s.lenMax = raw ("lenMax") / 100.0;
    s.legato = raw ("legato") > 0.5f;
    s.velMin = (int) raw ("velMin");
    s.velMax = (int) raw ("velMax");
    s.accent = (int) raw ("accent");
    return s;
}

void MLGAlphaProcessor::publish (const mlg::Clip& c)
{
    displayClip = c;
    ++version;
    {
        const juce::SpinLock::ScopedLockType lock (clipLock);
        pendingClip = c;
        hasPending.store (true);
    }
    if (onLineChanged) onLineChanged();
}

void MLGAlphaProcessor::rebuild()
{
    const auto clip = mlg::clipFromPattern (mlg::generate (readSettings(), seeds));
    info = {};
    info.source = fr ("Potards");
    info.name = fr ("seeds ") + juce::String (seeds.rhythm) + " / " + juce::String (seeds.pitch);
    publish (clip);
}

void MLGAlphaProcessor::parameterChanged (const juce::String& id, float)
{
    if (placing || id == "switchAt") return;
    if (fromLibrary && (id == "root" || id == "octave")) { libDirty.store (true); return; }
    if (id == "octave") return;
    dirty.store (true);
}

void MLGAlphaProcessor::timerCallback()
{
    if (dirty.exchange (false))
    {
        if (fromLibrary) { closeListening(); fromLibrary = false; libIndex = -1; }
        rebuild();
    }
    if (pendingLibId.isNotEmpty() && library->isReady())
    {
        const auto& all = library->patterns();
        for (int i = 0; i < (int) all.size(); ++i)
            if (all[(size_t) i].id == pendingLibId) { setLibraryLine (i); break; }
        pendingLibId.clear();
    }
    if (libDirty.exchange (false) && fromLibrary)
        refreshLibraryClip();
}

void MLGAlphaProcessor::generateNew()
{
    if (! lockRhythm) { seeds.rhythm = (juce::uint32) rng.nextInt(); seeds.rhythmMutations = 0; }
    if (! lockPitch)  { seeds.pitch = (juce::uint32) rng.nextInt();  seeds.pitchMutations = 0; }
    if (fromLibrary) { closeListening(); fromLibrary = false; libIndex = -1; }
    rebuild();
}

void MLGAlphaProcessor::mutate()
{
    if (! lockRhythm) ++seeds.rhythmMutations;
    if (! lockPitch)  ++seeds.pitchMutations;
    if (fromLibrary) { closeListening(); fromLibrary = false; libIndex = -1; }
    rebuild();
}

void MLGAlphaProcessor::setRhythmLocked (bool b) { lockRhythm = b; }
void MLGAlphaProcessor::setPitchLocked (bool b) { lockPitch = b; }

void MLGAlphaProcessor::setSeeds (juce::uint32 r, juce::uint32 p)
{
    if (r != seeds.rhythm) { seeds.rhythm = r; seeds.rhythmMutations = 0; }
    if (p != seeds.pitch)  { seeds.pitch = p;  seeds.pitchMutations = 0; }
    if (fromLibrary) { closeListening(); fromLibrary = false; libIndex = -1; }
    rebuild();
}

void MLGAlphaProcessor::setParam (const juce::String& id, float value)
{
    if (auto* p = apvts.getParameter (id))
        p->setValueNotifyingHost (p->convertTo0to1 (value));
}

// ---------------------------------------------------------------------------
// Bibliothèque

void MLGAlphaProcessor::closeListening()
{
    if (fromLibrary && libIndex >= 0 && libIndex < (int) library->patterns().size())
        library->noteListenTime (library->patterns()[(size_t) libIndex].id,
                                 juce::Time::getMillisecondCounterHiRes() / 1000.0 - shownSince);
}

void MLGAlphaProcessor::refreshLibraryClip()
{
    const auto& p = library->patterns()[(size_t) libIndex];
    const int centre = mlg::Library::defaultCentre (p.role) + 12 * (int) raw ("octave");
    const auto clip = library->toClip (p, (int) raw ("root"), centre);
    info = {};
    info.source = p.personal ? fr ("Bibliothèque perso") : fr ("Bibliothèque");
    info.id = p.id;
    info.name = p.name;
    info.role = p.role;
    info.family = p.family;
    info.tags = p.tags;
    if (p.role == mlg::roleKick || p.role == mlg::roleDrums) { kickCompanion = clip; hasKick = true; }
    publish (clip);
}

void MLGAlphaProcessor::setLibraryLine (int index)
{
    closeListening();
    libIndex = index;
    fromLibrary = true;
    refreshLibraryClip();
    placeKnobs (displayClip);
    library->noteProposed (library->patterns()[(size_t) index].id);
    shownSince = juce::Time::getMillisecondCounterHiRes() / 1000.0;
}

void MLGAlphaProcessor::placeKnobs (const mlg::Clip& c)
{
    placing = true;
    for (auto& [id, v] : mlg::equivalentSettings (c, (int) raw ("root")))
        setParam (id, v);
    placing = false;
    dirty.store (false);
}

void MLGAlphaProcessor::fallbackFromTags (const mlg::Query& q)
{
    // la bibliothèque n'a rien : on règle les potards d'après les mots et on génère
    auto w = [&] (std::initializer_list<const char*> keys)
    {
        float s = 0;
        for (auto k : keys) { const int t = mlg::tagKeys().indexOf (juce::String::fromUTF8 (k)); if (t >= 0 && q.tags.count (t)) s += q.tags.at (t); }
        return s;
    };
    if (w ({ "dense", "rempli", "chargé", "frénétique", "nerveux" }) > 0) setParam ("density", 80);
    if (w ({ "aéré", "clairsemé", "minimal", "dépouillé", "vide", "calme", "posé" }) > 0) setParam ("density", 25);
    if (w ({ "grave", "sub", "profond", "lourd" }) > 0) { setParam ("lowNote", 28); setParam ("highNote", 43); }
    if (w ({ "aigu", "perché", "brillant", "léger" }) > 0) { setParam ("lowNote", 72); setParam ("highNote", 88); }
    if (w ({ "médium" }) > 0) { setParam ("lowNote", 55); setParam ("highNote", 70); }
    if (w ({ "mineur", "sombre", "mélancolique", "triste", "déprimé", "menaçant" }) > 0) setParam ("scale", 1);
    if (w ({ "majeur", "lumineux", "euphorique", "apaisé" }) > 0) setParam ("scale", 0);
    if (w ({ "dissonant", "chromatique", "atonal", "angoissant" }) > 0) setParam ("scale", 12);
    if (w ({ "modal", "mystérieux" }) > 0) setParam ("scale", 2);
    if (w ({ "exotique" }) > 0) setParam ("scale", 7);
    if (w ({ "étiré", "planant", "lent", "flottant", "suspendu-t" }) > 0) { setParam ("lenMin", 200); setParam ("lenMax", 400); }
    if (w ({ "serré", "sec", "haché", "claquant", "saccadé" }) > 0) { setParam ("lenMin", 20); setParam ("lenMax", 50); }
    if (w ({ "syncopé", "groovy", "chaloupé", "bancal" }) > 0) setParam ("swing", 25);
    if (w ({ "martelé", "régulier", "mécanique", "martial", "rectiligne" }) > 0) { setParam ("rhythmMode", 1); setParam ("pulses", 4); }
    if (w ({ "agressif", "brutal", "puissant", "explosif" }) > 0) { setParam ("velMin", 100); setParam ("velMax", 127); }
    if (w ({ "legato" }) > 0) setParam ("legato", 1);
    dirty.store (false);
    generateNew();
}

juce::String MLGAlphaProcessor::drawFromText (const juce::String& words)
{
    if (! library->isReady()) return fr ("La bibliothèque se charge encore, réessaie dans une seconde.");
    lastQuery = library->translator().parse (words);
    return drawAgain();
}

juce::String MLGAlphaProcessor::drawAgain()
{
    if (! library->isReady()) return fr ("La bibliothèque se charge encore, réessaie dans une seconde.");
    const int idx = library->draw (lastQuery, hasKick ? &kickCompanion : nullptr, rng);
    juce::String out = lastQuery.summary();
    if (idx < 0) fallbackFromTags (lastQuery);
    else setLibraryLine (idx);
    if (library->lastDrawNote().isNotEmpty()) out << "\n" << library->lastDrawNote();
    return out;
}

juce::String MLGAlphaProcessor::applyTechnical (const juce::String& text)
{
    const auto cmd = mlg::parseTechnical (text, (int) raw ("division"));
    for (auto& [id, v] : cmd.params) setParam (id, v);
    if (cmd.generate) generateNew();
    else if (cmd.mutate) mutate();
    juce::String out;
    if (! cmd.done.isEmpty()) out << fr ("Fait : ") << cmd.done.joinIntoString (", ") << ".";
    if (! cmd.unknown.isEmpty()) out << (out.isEmpty() ? "" : "  ") << fr ("Pas compris : ") << cmd.unknown.joinIntoString (" ") << ".";
    if (out.isEmpty()) out = fr ("Rien à faire.");
    return out;
}

juce::String MLGAlphaProcessor::like (bool up)
{
    if (! fromLibrary || libIndex < 0)
        return fr ("J'aime / Bof servent à la bibliothèque : tire d'abord une ligne avec des mots.");
    library->like (library->patterns()[(size_t) libIndex].id, lastQuery, up);
    return up ? fr ("Noté : cette ligne remontera plus souvent avec ces mots.")
              : fr ("Noté : cette ligne sortira moins souvent avec ces mots.");
}

juce::String MLGAlphaProcessor::settingsString() const
{
    juce::StringArray s;
    for (auto* id : kParamIds) s.add (juce::String (id) + "=" + juce::String (raw (id)));
    s.add ("seedRhythm=" + juce::String (seeds.rhythm)); s.add ("mutRhythm=" + juce::String (seeds.rhythmMutations));
    s.add ("seedPitch=" + juce::String (seeds.pitch));   s.add ("mutPitch=" + juce::String (seeds.pitchMutations));
    return s.joinIntoString (";");
}

juce::String MLGAlphaProcessor::keep (const juce::String& words)
{
    if (! library->isReady()) return fr ("La bibliothèque se charge encore, réessaie dans une seconde.");
    const auto meaning = library->translator().parse (words);
    int role = mlg::roleLead, family = mlg::familyIndex ("techno");
    if (fromLibrary && libIndex >= 0)
    {
        const auto& p = library->patterns()[(size_t) libIndex];
        role = p.role; family = p.family;
    }
    else
    {
        double mean = 0;
        for (auto& n : displayClip.notes) mean += n.pitch;
        if (! displayClip.notes.empty() && mean / (double) displayClip.notes.size() < 50) role = mlg::roleBass;
    }
    if (! meaning.roles.empty()) role = *meaning.roles.begin();
    else if (! lastQuery.roles.empty() && ! fromLibrary) role = *lastQuery.roles.begin();
    if (! meaning.families.empty()) family = *meaning.families.begin();
    else if (! lastQuery.families.empty() && ! fromLibrary) family = *lastQuery.families.begin();

    if (fromLibrary && libIndex >= 0) library->noteKept (library->patterns()[(size_t) libIndex].id);
    return library->savePersonal (displayClip, (int) raw ("root"), words, meaning, role, family,
                                  fromLibrary ? juce::String() : settingsString());
}

juce::String MLGAlphaProcessor::getTechnicalText() const
{
    return mlg::describe (displayClip, info, (int) raw ("root"));
}

juce::File MLGAlphaProcessor::writeMidiFile()
{
    auto dir = juce::File::getSpecialLocation (juce::File::tempDirectory).getChildFile ("MLG Alpha");
    dir.createDirectory();
    juce::String name = fromLibrary ? info.name : "seeds_" + juce::String (seeds.rhythm) + "_" + juce::String (seeds.pitch);
    name = juce::File::createLegalFileName (name.replace ("/", "-")).substring (0, 60);
    auto file = dir.getChildFile ("MLG_Alpha_" + name + ".mid");
    file.deleteFile();

    juce::FileOutputStream os (file);
    if (os.openedOk())
    {
        mlg::toMidiFile (displayClip).writeTo (os);
        os.flush();
    }
    if (fromLibrary && libIndex >= 0) library->noteKept (library->patterns()[(size_t) libIndex].id);
    return file;
}

// ---------------------------------------------------------------------------
// Lecture (thread audio)

void MLGAlphaProcessor::releaseDue (double t, double blockPpq, double pps, int numSamples, juce::MidiBuffer& out)
{
    for (size_t i = 0; i < active.size();)
    {
        if (active[i].end <= t)
        {
            const int smp = juce::jlimit (0, numSamples - 1, (int) std::floor ((active[i].end - blockPpq) / pps));
            out.addEvent (juce::MidiMessage::noteOff (mlg::kMidiChannel, active[i].pitch), smp);
            active[i] = active.back();
            active.pop_back();
        }
        else ++i;
    }
}

void MLGAlphaProcessor::allNotesOff (juce::MidiBuffer& out)
{
    for (auto& a : active)
        out.addEvent (juce::MidiMessage::noteOff (mlg::kMidiChannel, a.pitch), 0);
    active.clear();
}

void MLGAlphaProcessor::render (const mlg::Clip& c, double from, double to, double blockPpq, double pps, int numSamples, juce::MidiBuffer& out)
{
    const double L = c.lengthPpq;
    if (L <= 0.0 || c.notes.empty() || to <= from) { releaseDue (to, blockPpq, pps, numSamples, out); return; }

    const auto toSample = [&] (double t) { return juce::jlimit (0, numSamples - 1, (int) std::floor ((t - blockPpq) / pps)); };
    const auto c0 = (juce::int64) std::floor (from / L), c1 = (juce::int64) std::floor (to / L);
    for (auto cy = c0; cy <= c1; ++cy)
    {
        for (const auto& n : c.notes)
        {
            const double t = (double) cy * L + n.start;
            if (t < from) continue;
            if (t >= to) break;
            releaseDue (t, blockPpq, pps, numSamples, out);
            const int smp = toSample (t);
            for (size_t i = 0; i < active.size(); ++i)
                if (active[i].pitch == n.pitch)
                {
                    out.addEvent (juce::MidiMessage::noteOff (mlg::kMidiChannel, n.pitch), smp);
                    active[i] = active.back();
                    active.pop_back();
                    break;
                }
            if (active.size() >= 256) continue;
            out.addEvent (juce::MidiMessage::noteOn (mlg::kMidiChannel, n.pitch, (juce::uint8) juce::jlimit (1, 127, n.velocity)), smp);
            active.push_back ({ n.pitch, t + n.length });
        }
    }
    releaseDue (to, blockPpq, pps, numSamples, out);
}

void MLGAlphaProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midi)
{
    juce::ScopedNoDenormals noDenormals;
    buffer.clear();   // aucun son : seulement du MIDI

    const bool atNextBar = raw ("switchAt") > 0.5f;
    if (hasPending.load())
    {
        const juce::SpinLock::ScopedTryLockType lock (clipLock);
        if (lock.isLocked())
        {
            if (atNextBar && wasPlaying) { std::swap (queuedClip, pendingClip); hasQueued = true; }
            else { std::swap (playClip, pendingClip); hasQueued = false; }
            hasPending.store (false);
        }
    }

    const int numSamples = buffer.getNumSamples();
    juce::MidiBuffer out;
    for (const auto m : midi)            // les notes jouées au clavier passent à travers
        out.addEvent (m.getMessage(), m.samplePosition);

    bool playing = false;
    double ppq = 0.0, bpm = 120.0;
    if (auto* ph = getPlayHead())
        if (auto pos = ph->getPosition())
        {
            playing = pos->getIsPlaying();
            if (auto v = pos->getPpqPosition()) ppq = *v;
            if (auto b = pos->getBpm()) bpm = *b;
        }

    if (! playing || numSamples <= 0 || bpm <= 0.0)
    {
        allNotesOff (out);
        if (hasQueued) { std::swap (playClip, queuedClip); hasQueued = false; }
        wasPlaying = false;
        playPos.store (-1.0);
        midi.swapWith (out);
        return;
    }

    const double pps = bpm / (60.0 * currentSampleRate);
    const double endPpq = ppq + numSamples * pps;

    // Saut de lecture (boucle, déplacement du curseur) : on coupe les notes en cours.
    const bool contiguous = wasPlaying && std::abs (ppq - expectedPpq) < 0.05;
    if (! contiguous) allNotesOff (out);
    const double scanStart = contiguous ? expectedPpq : ppq;
    wasPlaying = true;
    expectedPpq = endPpq;

    if (hasQueued)
    {
        const double bar = std::ceil (scanStart / 4.0 - 1e-9) * 4.0;
        if (bar < endPpq)
        {
            render (playClip, scanStart, bar, ppq, pps, numSamples, out);
            std::swap (playClip, queuedClip);
            hasQueued = false;
            render (playClip, bar, endPpq, ppq, pps, numSamples, out);
        }
        else render (playClip, scanStart, endPpq, ppq, pps, numSamples, out);
    }
    else render (playClip, scanStart, endPpq, ppq, pps, numSamples, out);

    playPos.store (playClip.lengthPpq > 0 ? std::fmod (endPpq, playClip.lengthPpq) : -1.0);
    midi.swapWith (out);
}

// ---------------------------------------------------------------------------
// Sauvegarde

void MLGAlphaProcessor::getStateInformation (juce::MemoryBlock& dest)
{
    auto state = apvts.copyState();
    state.setProperty ("seedRhythm", (juce::int64) seeds.rhythm, nullptr);
    state.setProperty ("seedPitch", (juce::int64) seeds.pitch, nullptr);
    state.setProperty ("mutRhythm", seeds.rhythmMutations, nullptr);
    state.setProperty ("mutPitch", seeds.pitchMutations, nullptr);
    state.setProperty ("lockRhythm", lockRhythm, nullptr);
    state.setProperty ("lockPitch", lockPitch, nullptr);
    state.setProperty ("libId", fromLibrary && libIndex >= 0 ? library->patterns()[(size_t) libIndex].id : juce::String(), nullptr);

    if (auto xml = state.createXml())
        copyXmlToBinary (*xml, dest);
}

void MLGAlphaProcessor::setStateInformation (const void* data, int size)
{
    auto xml = getXmlFromBinary (data, size);
    if (xml == nullptr || ! xml->hasTagName (apvts.state.getType()))
        return;

    auto state = juce::ValueTree::fromXml (*xml);
    seeds.rhythm = (juce::uint32) (juce::int64) state.getProperty ("seedRhythm", (juce::int64) seeds.rhythm);
    seeds.pitch = (juce::uint32) (juce::int64) state.getProperty ("seedPitch", (juce::int64) seeds.pitch);
    seeds.rhythmMutations = state.getProperty ("mutRhythm", 0);
    seeds.pitchMutations = state.getProperty ("mutPitch", 0);
    lockRhythm = state.getProperty ("lockRhythm", false);
    lockPitch = state.getProperty ("lockPitch", false);
    pendingLibId = state.getProperty ("libId", "").toString();

    placing = true;
    apvts.replaceState (state);
    placing = false;
    fromLibrary = false;
    libIndex = -1;
    dirty.store (true);
}

juce::AudioProcessorEditor* MLGAlphaProcessor::createEditor() { return new MLGAlphaEditor (*this); }

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new MLGAlphaProcessor(); }
